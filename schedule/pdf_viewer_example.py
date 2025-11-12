import tkinter as tk
from tkinter import ttk, filedialog
import fitz  # PyMuPDF
from PIL import Image, ImageTk

class PDFViewer(tk.Toplevel):
    def __init__(self, master, pdf_path):
        super().__init__(master)
        self.title("高效 PDF 查看器 (视觉连续版)")
        self.pdf_path = pdf_path

        # --- PDF 文档和页面初始化 ---
        self.doc = fitz.open(self.pdf_path)
        self.current_page_num = 0
        self.page = self.doc[self.current_page_num]
        self.page_rect = self.page.rect  # PDF 原始尺寸（磅）

        # --- 渲染参数（平衡连续、清晰、性能）---
        self.dpi = 200  # 保持优化后的 DPI，兼顾清晰和速度
        self.scale = self.dpi / 72.0  # 缩放因子（PDF默认72 DPI）

        # 总像素尺寸
        self.total_pix_width = int(self.page_rect.width * self.scale)
        self.total_pix_height = int(self.page_rect.height * self.scale)

        # --- UI 组件 ---
        self.canvas = tk.Canvas(self, bg="gray")

        # 重写 xview/yview（绑定视图变化）
        original_xview = self.canvas.xview
        original_yview = self.canvas.yview

        def custom_xview(*args):
            result = original_xview(*args)
            self.schedule_render()
            return result

        def custom_yview(*args):
            result = original_yview(*args)
            self.schedule_render()
            return result

        self.canvas.xview = custom_xview
        self.canvas.yview = custom_yview

        # 滚动条配置
        self.v_scroll = ttk.Scrollbar(self, orient=tk.VERTICAL, command=self.canvas.yview)
        self.h_scroll = ttk.Scrollbar(self, orient=tk.HORIZONTAL, command=self.canvas.xview)

        self.canvas.configure(
            xscrollcommand=self.h_scroll.set,
            yscrollcommand=self.v_scroll.set,
            scrollregion=(0, 0, self.total_pix_width, self.total_pix_height)
        )

        # 布局
        self.v_scroll.pack(side="right", fill="y")
        self.h_scroll.pack(side="bottom", fill="x")
        self.canvas.pack(side="left", fill="both", expand=True)

        # --- 缓存与优化变量 ---
        self.tk_img = None  # 持有 PhotoImage 引用
        self.rendered_region = None  # 上一次渲染区域
        self.render_after_id = None  # 防抖任务ID
        self.render_threshold = 15  # 区域变化阈值（像素）
        self.render_margin = 80  # 核心优化：扩大渲染边距（80像素，可调整）

        # --- 绑定事件 ---
        self.canvas.bind("<Configure>", lambda e: self.schedule_render())
        self.canvas.bind("<MouseWheel>", self.on_mousewheel)
        self.canvas.bind("<Button-4>", self.on_mousewheel)
        self.canvas.bind("<Button-5>", self.on_mousewheel)

        # 首次渲染
        self.schedule_render(delay=100)

    def calculate_visible_rect(self):
        """计算当前可见区域（含扩大边距）"""
        x_view_start, x_view_end = self.canvas.xview()
        y_view_start, y_view_end = self.canvas.yview()

        # 可见区域像素坐标
        pix_x1 = x_view_start * self.total_pix_width
        pix_y1 = y_view_start * self.total_pix_height
        pix_x2 = x_view_end * self.total_pix_width
        pix_y2 = y_view_end * self.total_pix_height

        # 核心修改：扩大边距（80像素），提前渲染周边区域
        margin = self.render_margin
        pix_x1 = max(0, pix_x1 - margin)
        pix_y1 = max(0, pix_y1 - margin)
        pix_x2 = min(self.total_pix_width, pix_x2 + margin)
        pix_y2 = min(self.total_pix_height, pix_y2 + margin)

        # 转换为PDF坐标（磅）
        pdf_x1 = pix_x1 / self.scale
        pdf_y1 = pix_y1 / self.scale
        pdf_x2 = pix_x2 / self.scale
        pdf_y2 = pix_y2 / self.scale

        return fitz.Rect(pdf_x1, pdf_y1, pdf_x2, pdf_y2)

    def schedule_render(self, delay=5):
        """防抖渲染（延迟缩短到60ms，更即时）"""
        if self.render_after_id:
            self.after_cancel(self.render_after_id)
        self.render_after_id = self.after(delay, self.render_visible_area)

    def is_region_changed(self, new_rect):
        """判断区域是否需要重新渲染"""
        if self.rendered_region is None:
            return True

        # 计算中心偏移量
        old_center_x = (self.rendered_region.x0 + self.rendered_region.x1) / 2 * self.scale
        old_center_y = (self.rendered_region.y0 + self.rendered_region.y1) / 2 * self.scale
        new_center_x = (new_rect.x0 + new_rect.x1) / 2 * self.scale
        new_center_y = (new_rect.y0 + new_rect.y1) / 2 * self.scale

        offset_x = abs(new_center_x - old_center_x)
        offset_y = abs(new_center_y - old_center_y)
        return offset_x > self.render_threshold or offset_y > self.render_threshold

    def render_visible_area(self):
        """渲染扩大后的可见区域"""
        visible_pdf_rect = self.calculate_visible_rect()

        if not self.is_region_changed(visible_pdf_rect):
            return

        self.rendered_region = visible_pdf_rect

        # 渲染扩大后的区域
        pix = self.page.get_pixmap(
            clip=visible_pdf_rect,
            dpi=self.dpi,
            colorspace="rgb"
        )

        # 图像转换
        img = Image.frombytes("RGB", (pix.width, pix.height), pix.samples)

        # 绘制图像（位置对齐原始可见区域）
        self.canvas.delete("all")
        self.tk_img = ImageTk.PhotoImage(image=img)

        # 计算绘制起点（含边距的区域左上角）
        pix_x1 = visible_pdf_rect.x0 * self.scale
        pix_y1 = visible_pdf_rect.y0 * self.scale
        self.canvas.create_image(pix_x1, pix_y1, anchor=tk.NW, image=self.tk_img)

    def on_mousewheel(self, event):
        """鼠标滚轮事件"""
        if event.num == 4:
            self.canvas.yview_scroll(-1, "units")
        elif event.num == 5:
            self.canvas.yview_scroll(1, "units")
        elif event.delta:
            self.canvas.yview_scroll(int(-1*(event.delta/120)), "units")

    def __del__(self):
        """释放资源"""
        if hasattr(self, 'doc'):
            self.doc.close()
        print("PDF文档已关闭，资源释放完成")

# --- 主程序 ---
if __name__ == "__main__":
    root = tk.Tk()
    root.withdraw()

    pdf_path = filedialog.askopenfilename(
        title="选择PDF文件",
        filetypes=[("PDF文件", "*.pdf"), ("所有文件", "*.*")]
    )

    if pdf_path:
        viewer = PDFViewer(root, pdf_path)
        viewer.mainloop()
    else:
        print("未选择文件")