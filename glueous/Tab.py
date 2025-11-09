import tkinter as tk
from tkinter import filedialog, messagebox, ttk, Menu
import os
from PIL import Image, ImageTk
import fitz  # PyMuPDF

from .FileState import FileState


class Tab:
    """
    Tab 类，单个文件的标签页容器，管理单电子书文件的显示和状态。
    """

    def __init__(self, parent_notebook: ttk.Notebook, file_path: str = None):
        self.notebook = parent_notebook  # 父标签页容器
        self.frame = ttk.Frame(parent_notebook)  # 标签页内容框架

        # 将frame添加到Notebook
        self.notebook.add(self.frame)

        self.file_path = file_path  # 电子书文件路径
        self.doc = None  # PyMuPDF文档对象
        self.current_page = 0
        self.total_pages = 0
        self.zoom = 1.0

        # 创建标签页内的UI组件
        self.create_widgets()


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


    def open_pdf(self, file_path: str) -> bool:
        """
        打开PDF文件并初始化。

        返回是否打开成功。
        """
        try:
            # 关闭已打开的文档
            if self.doc:
                self.doc.close()

            self.file_path = file_path
            self.doc = fitz.open(file_path)
            self.total_pages = len(self.doc)
            self.current_page = 0
            self.zoom = 1.0

            # 刷新显示
            self.show_page()

            # 更新标签页标题（显示文件名）
            tab_title = os.path.basename(file_path)
            self.notebook.tab(self.frame, text = tab_title)

            return True
        except Exception as e:
            messagebox.showerror("错误", f"打开失败: {str(e)}")
            self.reset_tab()
            return False


    def show_page(self):
        """
        渲染当前页。
        """
        if not self.doc or not (0 <= self.current_page < self.total_pages):
            return

        # 清空画布和缓存
        self.canvas.delete("all")

        # 渲染页面图像
        page = self.doc[self.current_page]
        mat = fitz.Matrix(self.zoom, self.zoom)
        pix = page.get_pixmap(matrix=mat)
        img = Image.frombytes("RGB", [pix.width, pix.height], pix.samples)
        self.tk_img = ImageTk.PhotoImage(image=img)
        self.canvas.create_image(0, 0, anchor=tk.NW, image=self.tk_img)
        self.canvas.config(scrollregion=(0, 0, pix.width, pix.height))


    def update_zoom(self, zoom_level):
        """更新缩放比例"""
        self.zoom = zoom_level
        self.show_page()


    def get_context(self):
        """获取当前标签页的上下文信息（供插件使用）"""
        return {
            "current_page": self.current_page,
            "total_pages": self.total_pages,
            "zoom": self.zoom,
            "doc": self.doc,
            "file_path": self.file_path
        }


    def reset_tab(self):
        """重置标签页状态"""
        if self.doc:
            self.doc.close()
        self.doc = None
        self.current_page = 0
        self.total_pages = 0
        self.file_path = None
        self.canvas.delete("all")
        # 仅在frame被管理时修改标签标题
        try:
            self.notebook.tab(self.frame, text="空标签页")
        except tk.TclError:
            # 若frame已被移除，忽略错误
            pass
