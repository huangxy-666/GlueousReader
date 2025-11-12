from __future__ import annotations

import tkinter as tk
from tkinter import messagebox, ttk
import os
from typing import Any, List, Tuple, override
from types import MethodType

from PIL import Image, ImageTk
import fitz  # PyMuPDF

from plugins.Tab.FileState import FileState

from glueous import ReaderAccess
from glueous_plugin import Plugin



class Tab:
    """
    Tab 类，单个文件的标签页容器，管理单电子书文件的显示和状态。
    """

    def __init__(self, context: ReaderAccess, file_path: str = None):
        self.context = context

        # 与父容器建立关联
        self.notebook = self.context.get_notebook() # 父标签页容器
        self.frame = ttk.Frame(self.notebook)  # 标签页内容框架
        self.notebook.add(self.frame)          # 将frame添加到Notebook

        # 从应用数据中搜索这本书的数据
        file_states = self.context.get_data().setdefault("file_states", [])
        for file_state in file_states:
            # 查找路径相同的
            if file_state["file_path"] == file_path:
                self.state = file_state
                break
        else:
            # 找遍了也没找到
            self.state = FileState(file_path).to_json()
            file_states.insert(0, self.state)
        self.doc = None  # PyMuPDF文档对象

        # 创建标签页内的UI组件
        self.create_widgets()

        # 打开文件
        self.open()


    def __del__(self):
        """释放资源"""
        if hasattr(self, 'doc'):
            self.doc.close()


    @property
    def file_path(self) -> str:
        """
        当前打开的文件的绝对路径。
        """
        return self.state["file_path"]

    @file_path.setter
    def file_path(self, path: str) -> None:
        raise AttributeError("`file_path 'is a read-only attribute. If you want to open another file, please call the `.open()` method.")


    @property
    def open_count(self) -> int:
        """
        文件被打开的次数。
        """
        return self.state["open_count"]

    @open_count.setter
    def open_count(self, count: int) -> None:
        if count < 0:
            raise ValueError(f"Open count cannot be negative, got {count}")
        self.state["open_count"] = count


    @property
    def display_mode(self) -> str:
        """
        显示模式。
        """
        return self.state["display_mode"]

    @display_mode.setter
    def display_mode(self, mode: str) -> None:
        if mode not in FileState.DISPLAY_MODES:
            raise ValueError(f"Invalid display mode: {mode}. Must in {FileState.DISPLAY_MODES}")
        self.state["display_mode"] = mode
        self.render_page()


    @property
    def scroll_pos(self) -> Tuple[float, float]:
        """
        滚动偏移量（单位：逻辑像素，Page 坐标）。
        """
        return self.state["scroll_pos"]

    @scroll_pos.setter
    def scroll_pos(self, pos: Tuple[float, float]) -> None:
        self.state["scroll_pos"] = pos
        # 更新画布滚动位置
        self.update_view_region()
        self.render_page()


    @property
    def page_no(self) -> int:
        """
        当前页码（1-based）。
        """
        return self.state["page_no"]

    @page_no.setter
    def page_no(self, page_no: int) -> None:
        if not 0 < page_no <= self.total_pages:
            raise ValueError(f"Page number out of range: {page_no} (total pages: {self.total_pages})")
        self.state["page_no"] = page_no
        self.render_page()


    @property
    def zoom(self) -> float:
        """
        缩放比例。
        """
        return self.state["zoom"]

    @zoom.setter
    def zoom(self, zoom_level: float) -> None:
        if zoom_level <= 0:
            raise ValueError(f"Zoom level must be positive, got {zoom_level}")
        self.state["zoom"] = zoom_level
        scaled_page_rect = self.scaled_page_rect

        # 更新滚动区域
        self.update_view_region()
        self.render_page()


    @property
    def rotation(self) -> int:
        """
        页面旋转角度。
        """
        return self.state["rotation"]

    @rotation.setter
    def rotation(self, angle: int) -> None:
        if angle not in FileState.ROTATIONS:
            raise ValueError(f"Invalid rotation angle: {angle}. Must in {FileState.ROTATIONS}.")
        self.state["rotation"] = angle
        self.render_page()


    @property
    def dpi(self) -> int:
        """
        分辨率。
        """
        return self.context.get_setting("dpi", 72)


    @property
    def total_pages(self) -> int:
        """
        这本书的总页数。
        """
        return len(self.doc)


    @property
    def page(self) -> fitz.Page | None:
        """
        获取当前页的 Page 对象。
        """
        if self.doc is None:
            return None
        if not 0 < self.page_no <= self.total_pages:
            raise ValueError(f"Invalid page number: {self.page_no}")
        return self.doc[self.page_no - 1]


    def auto_render(self, func):
        """
        装饰器：在函数执行后自动调用 render_page() 方法。
        """
        def wrapper(*args, **kwargs):
            result = func(*args, **kwargs)
            self.render_page()
            return result
        return wrapper


    def create_widgets(self):
        """
        创建标签页内的显示组件（画布、滚动条等）。
        """
        # 显示区域（带滚动条）
        self.display_frame = ttk.Frame(self.frame)


        # 滚动条
        self.v_scroll = ttk.Scrollbar(self.display_frame, orient=tk.VERTICAL)
        self.v_scroll.pack(side=tk.RIGHT, fill=tk.Y)

        self.h_scroll = ttk.Scrollbar(self.display_frame, orient=tk.HORIZONTAL)
        self.h_scroll.pack(side=tk.BOTTOM, fill=tk.X)

        # 画布
        self.canvas = tk.Canvas(
            self.display_frame,
            xscrollcommand=self.h_scroll.set,
            yscrollcommand=self.v_scroll.set,
            bg="gray",
            highlightthickness=0,
        )
        self.canvas.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)

        self.display_frame.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)

        # 重写 xview/yview（绑定视图变化）
        original_xview = self.canvas.xview
        original_yview = self.canvas.yview

        def custom_xview(*args):
            result = original_xview(*args)
            if args:
                proportion = min(max(float(args[1]), 0), 1)
                self.scroll_pos = (
                    self.page.rect.width * proportion,
                    self.scroll_pos[1]
                )
                self.render_page()
            return result

        def custom_yview(*args):
            result = original_yview(*args)
            if args:
                proportion = min(max(float(args[1]), 0), 1)
                self.scroll_pos = (
                    self.scroll_pos[0],
                    self.page.rect.height * proportion
                )
                self.render_page()
            return result

        self.canvas.xview = custom_xview
        self.canvas.yview = custom_yview
        self.v_scroll.config(command=self.canvas.yview)
        self.h_scroll.config(command=self.canvas.xview)

        self.canvas.xview_scroll = self.auto_render(self.canvas.xview_scroll)
        self.canvas.yview_scroll = self.auto_render(self.canvas.yview_scroll)


    def update_view_region(self):
        """更新滚动条的位置，并同步画布视图"""
        # 计算视图起始比例（基于滚动位置和页面尺寸）
        x_view_start = self.scroll_pos[0] / self.page.rect.width
        y_view_start = self.scroll_pos[1] / self.page.rect.height

        # 计算缩放后的页面尺寸，更新滚动区域
        scaled_page_rect = self.scaled_page_rect
        self.canvas.configure(scrollregion=(0, 0, scaled_page_rect.width, scaled_page_rect.height))

        # 计算视图显示长度（基于画布尺寸和页面尺寸）
        self.canvas.update_idletasks()
        x_view_length = self.canvas.winfo_width() / scaled_page_rect.width
        y_view_length = self.canvas.winfo_height() / scaled_page_rect.height

        # 限制视图范围在 [0, 1] 内
        x_view_end = min(x_view_start + x_view_length, 1.0)
        y_view_end = min(y_view_start + y_view_length, 1.0)

        # 更新滚动条位置
        self.h_scroll.set(x_view_start, x_view_end)
        self.v_scroll.set(y_view_start, y_view_end)

        # 关键：同步更新画布的视图位置（核心修复点）
        self.canvas.xview_moveto(x_view_start)  # 移动水平视图
        self.canvas.yview_moveto(y_view_start)  # 移动垂直视图


    def open(self) -> bool:
        """
        打开文件并初始化。

        返回是否打开成功。
        """
        # try:
        # 关闭已打开的文档
        if self.doc:
            self.doc.close()

        self.doc = fitz.open(self.file_path)

        # 刷新显示
        self.update_view_region()
        self.render_page()

        # 更新标签页标题（显示文件名）
        tab_title = os.path.basename(self.file_path)
        self.notebook.tab(self.frame, text = tab_title)

        # 计数打开次数
        self.state["open_count"] += 1
        return True
        # except Exception as e:
        #     messagebox.showerror("错误", f"打开失败: {str(e)}")
        #     self.reset_tab()
        #     return False


    @property
    def scaled_page_rect(self) -> fitz.Rect:
        """
        返回；经过缩放后，页面的形状矩形。
        """
        return self.page.rect * self.zoom


    @property
    def visible_page_rect(self) -> fitz.Rect:
        """
        当前页面的可见区域。
        """
        x_view_start, x_view_end = self.canvas.xview()
        y_view_start, y_view_end = self.canvas.yview()

        # 可见页面区域坐标
        page_x1 = x_view_start * self.page.rect.width
        page_y1 = y_view_start * self.page.rect.height
        page_x2 = x_view_end   * self.page.rect.width
        page_y2 = y_view_end   * self.page.rect.height

        return fitz.Rect(page_x1, page_y1, page_x2, page_y2)


    def render_page(self):
        """
        渲染当前页。

        为加速渲染，仅渲染会显示到画布上的部分。
        """
        if not self.doc or not (0 <= self.page_no < self.total_pages):
            return

        # 清空画布和缓存
        self.canvas.delete("all")

        # 渲染页面图像
        visible_page_rect = self.visible_page_rect
        pix = self.page.get_pixmap(
            clip = visible_page_rect,
            dpi = int(self.dpi * self.zoom),
            colorspace = "rgb"
        )

        # 图像转换
        img = Image.frombytes("RGB", (pix.width, pix.height), pix.samples)
        self.tk_img = ImageTk.PhotoImage(image=img)

        # 计算绘制起点
        visible_canvas_rect = visible_page_rect * self.zoom
        self.canvas.create_image(
            visible_canvas_rect.x0,
            visible_canvas_rect.y0,
            anchor = tk.NW,
            image  = self.tk_img
        )


    def reset_tab(self):
        """重置标签页状态"""
        if self.doc:
            self.doc.close()
        self.state = None
        self.doc = None
        self.total_pages = 0
        self.canvas.delete("all")
        # 仅在frame被管理时修改标签标题
        try:
            self.notebook.tab(self.frame, text="空标签页")
        except tk.TclError:
            # 若frame已被移除，忽略错误
            pass



class TabPlugin(Plugin):
    """
    标签页插件：提供对标签页的管理接口。
    """

    # 插件信息
    name = "TabPlugin"
    description = """
# TabPlugin

- name: TabPlugin
- author: Jerry
- hotkeys: None
- menu entrance: None

## Function

Manage tab operations including creating, getting current tab, and closing tabs. 

Provide core tab functionality for the PDF reader.

## Api

- `context.create_tab(file_path)`: Create a new tab with the specified file path.
- `context.get_current_tab()`: Get the currently active tab.
- `context.close_tab(tab)`: Close the specified tab.
- `context.tabs`: List of all open tabs.
- `context.Tab`: The Tab class itself.

## Depend

Python extension library:
- fitz (PyMuPDF)
- PIL (Pillow)

Other plugins: None

## Others

This plugin must be loaded before any other plugins that manipulate tabs.
"""

    @staticmethod
    def create_tab(access: ReaderAccess, file_path: str | None = None) -> Tab:
        """
        创建新标签页
        """
        new_tab = Tab(access, file_path)

        # 激活新标签页
        access._reader.notebook.select(new_tab.frame)

        # 添加到标签页列表
        access.tabs.append(new_tab)


    @staticmethod
    def get_current_tab(access: ReaderAccess) -> Tab | None:
        """
        获取当前激活的标签页实例。
        """
        reader = access._reader

        if not access.tabs:
            return None

        # 获取当前选中标签页的路径字符串
        current_frame_path = reader.notebook.select()
        if not current_frame_path:
            return None

        # 将路径字符串转换为窗口对象
        try:
            current_frame = reader.root.nametowidget(current_frame_path)
        except KeyError:
            return None

        # 从标签页列表中找到匹配的 Tab
        for tab in access.tabs:
            if tab.frame == current_frame:
                return tab
        return None


    @staticmethod
    def close_tab(access: ReaderAccess, tab: Tab):
        """
        关闭一个标签页，返回是否成功关闭。
        """
        if tab in access.tabs:
            access.tabs.remove(tab)

        tab.reset_tab()
        access._reader.notebook.forget(tab.frame)


    @override
    def loaded(self) -> None:
        """
        在插件被加载时运行。
        """

        # 添加操作标签的接口，方便其他插件调用
        self.context.create_tab      = MethodType(self.create_tab     , self.context)
        self.context.get_current_tab = MethodType(self.get_current_tab, self.context)
        self.context.close_tab       = MethodType(self.close_tab      , self.context)
        self.context.tabs: List[Tab] = []
        self.context.Tab : type      = Tab


    @override
    def run(self) -> None:
        pass


    @override
    def unloaded(self) -> None:
        pass
