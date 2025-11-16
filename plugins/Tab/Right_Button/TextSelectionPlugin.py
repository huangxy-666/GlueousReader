"""
鼠标长按划取 PDF 文字插件
"""

from tkinter import messagebox
import threading
from glueous_plugin import Plugin


class TextSelectionPlugin(Plugin):
    """
    实现鼠标长按划取文字功能
    - 长按鼠标左键 500ms 后开始划取
    - 释放鼠标时提取选中区域的文字
    """

    name = "TextSelectionPlugin"
    description = """
# TextSelectionPlugin

- name: TextSelectionPlugin
- author: Little Liu
- hotkeys: None (使用鼠标交互)
- menu entrance: `工具 → 启用文字选取`

## Function

长按鼠标左键划取 PDF 文字内容。
- 长按 500ms 后开始划取
- 释放鼠标时提取选中区域的文字
- 文字将显示在弹窗中

## Api

- `context.setup_text_selection(tab)` - 为指定 tab 的 canvas 绑定文字选取事件

## Depend

Python extension library: None

Other plugins:
- TabPlugin
"""

    hotkeys = []

    def __init__(self, context):
        super().__init__(context)

    def loaded(self) -> None:
        """
        插件加载时：向菜单添加选项，并为 ReaderAccess 扩展新方法
        """
        # 向菜单栏添加选项
        self.context.add_menu_command(
            path=["工具"],
            label="启用文字选取",
            command=self.run,
            accelerator="None"
        )

        # 为 ReaderAccess 扩展新方法，供 Tab 插件调用
        self.context.setup_text_selection = self._setup_text_selection_for_tab

    def run(self) -> None:
        """
        菜单点击时执行：显示帮助提示
        """
        messagebox.showinfo(
            "文字选取",
            "长按鼠标左键并拖动以选取文字。\n释放鼠标时会提取选中区域的文字。"
        )

    def _setup_text_selection_for_tab(self, tab) -> None:
        """
        为指定的 tab 的 canvas 绑定鼠标事件
        （由 Tab 插件在 canvas 创建后调用）
        
        Args:
            tab: Tab 对象实例
        """
        canvas = tab.canvas
        
        # 为此 canvas 创建独立的状态对象
        selection_state = {
            "start": None,
            "rect": None,
            "timer": None,
            "is_selecting": False,
            "canvas_id": None,
        }

        # 定义事件处理函数（闭包捕获 tab 和 selection_state）
        def on_mouse_down(event):
            selection_state["start"] = (event.x, event.y)
            selection_state["is_selecting"] = False

            def start_selection():
                selection_state["is_selecting"] = True

            selection_state["timer"] = threading.Timer(0.5, start_selection)
            selection_state["timer"].start()

        def on_mouse_drag(event):
            if not selection_state["is_selecting"] or selection_state["start"] is None:
                return

            x1, y1 = selection_state["start"]
            x2, y2 = event.x, event.y

            # 删除旧的选框
            if selection_state["canvas_id"] is not None:
                canvas.delete(selection_state["canvas_id"])

            # 绘制新的选框
            selection_state["canvas_id"] = canvas.create_rectangle(
                x1, y1, x2, y2,
                outline="blue",
                width=2,
                fill="lightblue",
                stipple="gray50"
            )

            selection_state["rect"] = (min(x1, x2), min(y1, y2), max(x1, x2), max(y1, y2))

        def on_mouse_up(event):
            if selection_state["timer"] is not None:
                selection_state["timer"].cancel()
                selection_state["timer"] = None

            if not selection_state["is_selecting"] or selection_state["rect"] is None:
                selection_state["is_selecting"] = False
                return

            # 删除选框
            if selection_state["canvas_id"] is not None:
                canvas.delete(selection_state["canvas_id"])
                selection_state["canvas_id"] = None

            try:
                text = self._extract_text_from_rect(tab, selection_state["rect"])

                if text.strip():
                    messagebox.showinfo("提取文字", f"选中文字:\n\n{text[:300]}")
                else:
                    messagebox.showinfo("提示", "选中区域无文字内容")

            except Exception as e:
                messagebox.showerror("错误", f"提取失败: {str(e)}")

            selection_state["is_selecting"] = False
            selection_state["rect"] = None

        # 绑定鼠标事件到此 canvas
        canvas.bind("<Button-1>", on_mouse_down)
        canvas.bind("<B1-Motion>", on_mouse_drag)
        canvas.bind("<ButtonRelease-1>", on_mouse_up)

    def _extract_text_from_rect(self, tab, rect) -> str:
        """从矩形区域提取文字"""
        import fitz

        canvas = tab.canvas
        scale = tab.zoom  # 使用 tab 的 zoom 属性

        # 获取滚动偏移
        x_scroll = canvas.xview()[0]
        y_scroll = canvas.yview()[0]

        x1, y1, x2, y2 = rect

        # 转换为 PDF 坐标
        page_rect = tab.page.rect
        pdf_x1 = (x1 / scale + page_rect.width * x_scroll)
        pdf_y1 = (y1 / scale + page_rect.height * y_scroll)
        pdf_x2 = (x2 / scale + page_rect.width * x_scroll)
        pdf_y2 = (y2 / scale + page_rect.height * y_scroll)

        # 创建 PDF 矩形
        rect_pdf = fitz.Rect(pdf_x1, pdf_y1, pdf_x2, pdf_y2)

        # 提取文字
        text = tab.page.get_text("text", clip=rect_pdf)

        return text

    def unloaded(self) -> None:
        """插件卸载时清理"""
        pass