from __future__ import annotations

import tkinter as tk
from tkinter import filedialog, messagebox, ttk, Menu
import os
from typing import Any, Callable, Dict, List, TYPE_CHECKING, override
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

        # 创建标签页内的UI组件
        self.create_widgets()

        # 打开文件
        self.doc = None  # PyMuPDF文档对象
        self.total_pages = 0
        self.open()


    def __getattr__(self, attr_name: str) -> Any:
        """
        返回此对象的属性。如果在此对象本身上找不到，则再在 self.state 里找。
        """
        state = self.__dict__.get('state')
        if state is not None and attr_name in state:
            return state[attr_name]
        raise AttributeError(f"'{self.__class__.__name__}' object has no attribute '{attr_name}'")


    def __setattr__(self, attr_name: str, value: Any) -> None:
        """
        设置此对象的属性。如果 attr_name 在 __annotations__ 中，则设置到 self.state 中。
        """
        # 特殊处理 state 属性本身的设置
        if attr_name == 'state':
            super().__setattr__(attr_name, value)
            return

        # 获取类的 annotations（即类型提示）
        annotations = getattr(self.__class__, '__annotations__', {})

        # 安全地获取 state
        state = self.__dict__.get('state')

        # 如果 attr_name 是类中声明的字段，或 state 还未初始化，或属性不在 state 中
        # 则直接设置到对象上
        if (attr_name in annotations) or (state is None) or (attr_name not in state):
            super().__setattr__(attr_name, value)
        else:
            # 设置到 state 中
            state[attr_name] = value


    def create_widgets(self):
        """
        创建标签页内的显示组件（画布、滚动条等）。
        """
        # 显示区域（带滚动条）
        self.display_frame = ttk.Frame(self.frame)

        self.vscroll = ttk.Scrollbar(self.display_frame, orient=tk.VERTICAL)
        self.vscroll.pack(side=tk.RIGHT, fill=tk.Y)

        self.hscroll = ttk.Scrollbar(self.display_frame, orient=tk.HORIZONTAL)
        self.hscroll.pack(side=tk.BOTTOM, fill=tk.X)

        self.canvas = tk.Canvas(
            self.display_frame,
            yscrollcommand=self.vscroll.set,
            xscrollcommand=self.hscroll.set,
            bg="white",
            highlightthickness=0
        )
        self.canvas.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)

        self.vscroll.config(command=self.canvas.yview)
        self.hscroll.config(command=self.canvas.xview)

        self.display_frame.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)


    def open(self) -> bool:
        """
        打开文件并初始化。

        返回是否打开成功。
        """
        try:
            # 关闭已打开的文档
            if self.doc:
                self.doc.close()

            self.doc = fitz.open(self.file_path)
            self.total_pages = len(self.doc)

            # 刷新显示
            self.show_page()

            # 更新标签页标题（显示文件名）
            tab_title = os.path.basename(self.file_path)
            self.notebook.tab(self.frame, text = tab_title)


            # 计数打开次数
            self.state["open_count"] += 1
            return True
        except Exception as e:
            messagebox.showerror("错误", f"打开失败: {str(e)}")
            self.reset_tab()
            return False


    def show_page(self):
        """
        渲染当前页。
        """
        if not self.doc or not (0 <= self.page_no < self.total_pages):
            return

        # 清空画布和缓存
        self.canvas.delete("all")

        # 渲染页面图像
        page = self.doc[self.page_no]
        mat = fitz.Matrix(self.zoom / 100, self.zoom / 100)
        pix = page.get_pixmap(matrix=mat)
        img = Image.frombytes("RGB", [pix.width, pix.height], pix.samples)
        self.tk_img = ImageTk.PhotoImage(image=img)
        ####
        self.canvas.create_image(self.scroll_pos[0], self.scroll_pos[1], anchor=tk.NW, image=self.tk_img)
        self.canvas.config(scrollregion=(0, 0, pix.width, pix.height))


    def update_zoom(self, zoom_level):
        """更新缩放比例"""
        self.zoom = zoom_level
        self.show_page()


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
    description = "提供对标签页的管理接口"


    @staticmethod
    def create_tab(access: ReaderAccess, file_path: str | None = None) -> Tab:
        """
        创建新标签页
        """
        new_tab = Tab(access, file_path)

        # 激活新标签页
        access._reader.notebook.select(new_tab.frame)

        # 添加到标签页列表
        access._reader.tabs.append(new_tab)


    @staticmethod
    def get_current_tab(access: ReaderAccess) -> Tab | None:
        """
        获取当前激活的标签页实例。
        """
        reader = access._reader

        if not reader.tabs:
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
        for tab in reader.tabs:
            if tab.frame == current_frame:
                return tab
        return None


    @staticmethod
    def close_tab(access: ReaderAccess, tab: Tab):
        """
        关闭一个标签页，返回是否成功关闭。
        """
        reader = access._reader

        if tab in reader.tabs:
            reader.tabs.remove(tab)

        tab.reset_tab()
        reader.notebook.forget(tab.frame)


    @override
    def loaded(self) -> None:
        """
        在插件被加载时运行。
        """
        reader = self.context._reader
        reader.tabs: List[Tab] = []

        # 添加操作标签的接口，方便其他插件调用
        self.context.create_tab      = MethodType(self.create_tab     , self.context)
        self.context.get_current_tab = MethodType(self.get_current_tab, self.context)
        self.context.close_tab       = MethodType(self.close_tab      , self.context)
        self.context.tabs: List[Tab] = reader.tabs
        self.context.Tab : type      = Tab


    @override
    def run(self) -> None:
        pass


    @override
    def unloaded(self) -> None:
        pass
