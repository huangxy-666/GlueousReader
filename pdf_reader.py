import tkinter as tk
from tkinter import filedialog, messagebox, ttk, Menu
import fitz  # PyMuPDF
from PIL import Image, ImageTk
import pyperclip
import os
import importlib.util
import inspect
from pathlib import Path

# 确保plugins文件夹存在
Path("plugins").mkdir(exist_ok=True)

class PluginBase:
    """插件基类，所有插件必须继承此类并实现必要的方法"""
    
    # 插件名称，子类必须定义
    name = "BasePlugin"
    
    # 插件描述，子类可以定义
    description = "基础插件类"
    
    # 触发快捷键，子类可以定义，格式如 "<Control-c>"
    hotkey = None
    
    def __init__(self, reader):
        """初始化插件
        
        Args:
            reader: PDFReader实例，提供对主程序的访问
        """
        self.reader = reader
    
    def run(self, event=None):
        """插件执行的主方法，子类必须实现"""
        raise NotImplementedError("插件必须实现run方法")
    
    def get_context(self):
        """获取当前激活标签页的上下文信息"""
        current_tab = self.reader.get_current_tab()
        if not current_tab:
            return None
        return current_tab.get_context()


class PluginManager:
    """插件管理器，负责加载和管理插件"""
    
    def __init__(self, reader):
        self.reader = reader
        self.plugins = []  # 存储所有加载的插件实例
        self.hotkey_map = {}  # 快捷键到插件的映射
    
    def load_plugins(self):
        """加载plugins文件夹中的所有插件"""
        plugins_dir = "plugins"
        self.plugins = []
        self.hotkey_map = {}
        
        # 遍历plugins文件夹中的所有Python文件（跳过以下划线开头的文件）
        for filename in os.listdir(plugins_dir):
            if filename.endswith(".py") and not filename.startswith("_"):
                module_name = filename[:-3]
                file_path = os.path.join(plugins_dir, filename)
                
                try:
                    # 动态导入模块
                    spec = importlib.util.spec_from_file_location(module_name, file_path)
                    module = importlib.util.module_from_spec(spec)
                    spec.loader.exec_module(module)
                    
                    # 查找继承自PluginBase的类
                    for name, cls in inspect.getmembers(module, inspect.isclass):
                        if issubclass(cls, PluginBase) and cls != PluginBase:
                            # 创建插件实例
                            plugin_instance = cls(self.reader)
                            self.plugins.append(plugin_instance)
                            
                            # 注册快捷键
                            if plugin_instance.hotkey:
                                self.hotkey_map[plugin_instance.hotkey] = plugin_instance
                            
                            print(f"加载插件: {plugin_instance.name}")
                except Exception as e:
                    print(f"加载插件 {filename} 失败: {str(e)}")
        
        # 绑定所有快捷键到主窗口（作用于当前激活标签页）
        self.bind_hotkeys()
    
    def bind_hotkeys(self):
        """为插件绑定快捷键"""
        for hotkey, plugin in self.hotkey_map.items():
            self.reader.root.bind(hotkey, lambda e, p=plugin: p.run(e))
            print(f"绑定快捷键 {hotkey} 到插件 {plugin.name}")


class PDFTab:
    """单个PDF文件的标签页容器，管理单PDF的显示和状态"""
    
    def __init__(self, parent_notebook, file_path=None):
        self.notebook = parent_notebook  # 父标签页容器
        self.frame = ttk.Frame(parent_notebook)  # 标签页内容框架
        self.file_path = file_path  # PDF文件路径
        self.pdf_doc = None  # PyMuPDF文档对象
        self.current_page = 0
        self.total_pages = 0
        self.zoom = 1.0
        self.selected_area = None  # 选中区域 (x1, y1, x2, y2)
        self.text_segments = []  # 当前页文本片段
        self.image_segments = []  # 当前页图像位置
        self.select_rect = None  # 画布上的选择框
        self.last_mouse_pos = (0, 0)  # 最后记录的鼠标位置
        
        # 创建标签页内的UI组件
        self.create_widgets()
        self.bind_events()
        
        # 关键修改：取消初始化时自动打开PDF，改为由外部调用
        # if file_path:
        #     self.open_pdf(file_path)
    
    def create_widgets(self):
        """创建标签页内的显示组件（画布、滚动条等）"""
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
        
        # 右键菜单
        self.right_click_menu = Menu(self.frame, tearoff=0)
        self.right_click_menu.add_command(label="复制", command=self.copy_legacy)

    def bind_events(self):
        """绑定鼠标事件"""
        self.canvas.bind("<ButtonPress-1>", self.on_mouse_down)  # 鼠标按下
        self.canvas.bind("<B1-Motion>", self.on_mouse_drag)      # 鼠标拖动
        self.canvas.bind("<ButtonRelease-1>", self.on_mouse_up)  # 鼠标释放
        self.canvas.bind("<ButtonPress-3>", self.show_right_click_menu)  # 右键菜单
        self.canvas.bind("<Motion>", self.on_mouse_move)  # 鼠标移动

    def on_mouse_move(self, event):
        """记录鼠标位置"""
        self.last_mouse_pos = (event.x, event.y)

    def open_pdf(self, file_path):
        """打开PDF文件并初始化"""
        try:
            # 关闭已打开的文档
            if self.pdf_doc:
                self.pdf_doc.close()
            
            self.file_path = file_path
            self.pdf_doc = fitz.open(file_path)
            self.total_pages = len(self.pdf_doc)
            self.current_page = 0
            self.zoom = 1.0
            
            # 刷新显示
            self.show_page()
            
            # 更新标签页标题（显示文件名）
            tab_title = os.path.basename(file_path)
            self.notebook.tab(self.frame, text=tab_title)
            
            return True
        except Exception as e:
            messagebox.showerror("错误", f"打开失败: {str(e)}")
            self.reset_tab()
            return False

    def show_page(self):
        """渲染当前页并提取文本和图像坐标"""
        if not self.pdf_doc or not (0 <= self.current_page < self.total_pages):
            return
        
        # 清空画布和缓存
        self.canvas.delete("all")
        self.text_segments = []
        self.image_segments = []
        self.selected_area = None
        
        # 渲染页面图像
        page = self.pdf_doc[self.current_page]
        mat = fitz.Matrix(self.zoom, self.zoom)
        pix = page.get_pixmap(matrix=mat)
        img = Image.frombytes("RGB", [pix.width, pix.height], pix.samples)
        self.tk_img = ImageTk.PhotoImage(image=img)
        self.canvas.create_image(0, 0, anchor=tk.NW, image=self.tk_img)
        self.canvas.config(scrollregion=(0, 0, pix.width, pix.height))
        
        # 提取文本片段（带坐标）
        text_blocks = page.get_text("words")  # 格式: (x0, y0, x1, y1, text, ...)
        for block in text_blocks:
            x0, y0, x1, y1, text = block[:5]
            # 转换为缩放后的坐标（与画布显示匹配）
            self.text_segments.append((
                x0 * self.zoom, y0 * self.zoom,
                x1 * self.zoom, y1 * self.zoom,
                text
            ))
        
        # 提取图像位置
        images = page.get_images(full=True)
        for img in images:
            xref = img[0]
            # 获取图像在页面中的位置
            img_rects = page.get_image_rects(xref)
            for rect in img_rects:
                x0, y0, x1, y1 = rect
                self.image_segments.append((
                    x0 * self.zoom, y0 * self.zoom,
                    x1 * self.zoom, y1 * self.zoom,
                    xref  # 图像唯一标识
                ))

    def on_mouse_down(self, event):
        """记录鼠标按下位置（选择起点）"""
        self.start_x = event.x
        self.start_y = event.y
        self.selected_area = None
        if self.select_rect:
            self.canvas.delete(self.select_rect)

    def on_mouse_drag(self, event):
        """绘制选择框（随鼠标拖动更新）"""
        if self.select_rect:
            self.canvas.delete(self.select_rect)
        # 确保选择框坐标正确（左上角到右下角）
        x1, y1 = event.x, event.y
        self.select_rect = self.canvas.create_rectangle(
            min(self.start_x, x1), min(self.start_y, y1),
            max(self.start_x, x1), max(self.start_y, y1),
            outline="blue", dash=(2, 2), fill=""
        )

    def on_mouse_up(self, event):
        """确定选择区域并匹配内容"""
        x1, y1 = event.x, event.y
        # 存储选中区域（缩放后的坐标）
        self.selected_area = (
            min(self.start_x, x1), min(self.start_y, y1),
            max(self.start_x, x1), max(self.start_y, y1)
        )

    def show_right_click_menu(self, event):
        """右键菜单"""
        self.right_click_menu.post(event.x_root, event.y_root)

    def copy_legacy(self):
        """传统复制方法，供右键菜单使用"""
        # 查找CopyPlugin并调用其run方法（通过主程序的插件管理器）
        reader = self.notebook.master  # 获取主程序实例
        for plugin in reader.plugin_manager.plugins:
            if plugin.name == "CopyPlugin":
                plugin.run()
                return
        messagebox.showinfo("提示", "未找到复制插件")

    def prev_page(self):
        """上一页"""
        if self.current_page > 0:
            self.current_page -= 1
            self.show_page()
            return True
        return False

    def next_page(self):
        """下一页"""
        if self.current_page < self.total_pages - 1:
            self.current_page += 1
            self.show_page()
            return True
        return False

    def update_zoom(self, zoom_level):
        """更新缩放比例"""
        self.zoom = zoom_level
        self.show_page()

    def get_context(self):
        """获取当前标签页的上下文信息（供插件使用）"""
        return {
            "current_page": self.current_page,
            "total_pages": self.total_pages,
            "selected_area": self.selected_area,
            "mouse_position": self.last_mouse_pos,
            "text_segments": self.text_segments,
            "image_segments": self.image_segments,
            "zoom": self.zoom,
            "pdf_doc": self.pdf_doc,
            "file_path": self.file_path
        }

    def reset_tab(self):
        """重置标签页状态"""
        if self.pdf_doc:
            self.pdf_doc.close()
        self.pdf_doc = None
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


class PDFReader:
    """主程序类，管理多标签页和全局状态"""
    
    def __init__(self, root):
        self.root = root
        self.root.title("PDF 阅读器（多标签页）")
        self.root.geometry("1200x800")
        
        # 存储所有标签页实例
        self.tabs = []
        
        # 先创建菜单栏和工具栏（关键修改：提前创建工具栏组件）
        self.create_menubar()
        self.create_toolbar()
        
        # 再创建标签页容器和初始标签页
        self.notebook = ttk.Notebook(root)
        self.notebook.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
        
        # 创建初始空标签页
        self.create_new_tab()
        
        # 初始化插件系统
        self.plugin_manager = PluginManager(self)
        self.plugin_manager.load_plugins()
        
        # 更新工具栏状态（与当前标签页联动）
        self.notebook.bind("<<NotebookTabChanged>>", self.update_toolbar_state)
    
    def create_menubar(self):
        """创建菜单栏"""
        menubar = tk.Menu(self.root)
        
        # 文件菜单
        file_menu = tk.Menu(menubar, tearoff=0)
        file_menu.add_command(label="新建标签页", command=self.create_new_tab, accelerator="Ctrl+T")
        file_menu.add_command(label="打开 PDF", command=self.open_pdf_in_new_tab, accelerator="Ctrl+O")
        file_menu.add_command(label="关闭当前标签页", command=self.close_current_tab, accelerator="Ctrl+W")
        file_menu.add_separator()
        file_menu.add_command(label="退出", command=self.root.quit)
        menubar.add_cascade(label="文件", menu=file_menu)
        
        # 插件菜单
        self.plugin_menu = tk.Menu(menubar, tearoff=0)
        menubar.add_cascade(label="插件", menu=self.plugin_menu)
        
        self.root.config(menu=menubar)
        
        # 绑定菜单快捷键
        self.root.bind("<Control-t>", lambda e: self.create_new_tab())
        self.root.bind("<Control-o>", lambda e: self.open_pdf_in_new_tab())
        self.root.bind("<Control-w>", lambda e: self.close_current_tab())

    def create_toolbar(self):
        """创建工具栏（与当前标签页联动）"""
        toolbar = ttk.Frame(self.root)
        
        # 页面导航
        self.prev_btn = ttk.Button(toolbar, text="上一页", command=self.prev_page)
        self.prev_btn.pack(side=tk.LEFT, padx=5, pady=5)
        
        self.page_label = ttk.Label(toolbar, text="页码: 0/0")
        self.page_label.pack(side=tk.LEFT, padx=10)
        
        self.next_btn = ttk.Button(toolbar, text="下一页", command=self.next_page)
        self.next_btn.pack(side=tk.LEFT, padx=5, pady=5)
        
        # 缩放控制
        ttk.Label(toolbar, text="缩放:").pack(side=tk.LEFT, padx=10)
        self.zoom_var = tk.DoubleVar(value=1.0)
        self.zoom_scale = ttk.Scale(
            toolbar, from_=0.5, to=2.0, variable=self.zoom_var, 
            command=lambda v: self.update_zoom(float(v))
        )
        self.zoom_scale.pack(side=tk.LEFT, padx=5)
        self.zoom_label = ttk.Label(toolbar, text="100%")
        self.zoom_label.pack(side=tk.LEFT, padx=5)
        
        toolbar.pack(side=tk.TOP, fill=tk.X, padx=5, pady=5)

    def create_new_tab(self):
        """创建新的空标签页"""
        new_tab = PDFTab(self.notebook)
        self.notebook.add(new_tab.frame, text="空标签页")
        self.notebook.select(new_tab.frame)  # 激活新标签页
        self.tabs.append(new_tab)  # 新增：将标签页加入列表
        self.update_toolbar_state()  # 更新工具栏状态

    def open_pdf_in_new_tab(self):
        """在新标签页中打开PDF"""
        file_path = filedialog.askopenfilename(filetypes=[("PDF 文件", "*.pdf"), ("EPUB 文件", "*.epub")])
        if not file_path:
            return
        
        # 1. 创建新标签页（不自动打开PDF）
        new_tab = PDFTab(self.notebook)
        # 2. 先将frame添加到Notebook（关键：确保frame被管理）
        self.notebook.add(new_tab.frame, text="加载中...")
        # 3. 再调用open_pdf打开文件（此时frame已被管理）
        if new_tab.open_pdf(file_path):
            # 打开成功后更新标签标题
            self.notebook.tab(new_tab.frame, text=os.path.basename(file_path))
        # 4. 激活新标签页
        self.notebook.select(new_tab.frame)
        # 5. 添加到标签页列表并更新工具栏
        self.tabs.append(new_tab)
        self.update_toolbar_state()

    def get_current_tab(self):
        """获取当前激活的标签页实例（修复路径字符串问题）"""
        if not self.tabs:
            return None
        
        # 1. 获取当前选中标签页的路径字符串
        current_frame_path = self.notebook.select()
        if not current_frame_path:
            return None
        
        # 2. 将路径字符串转换为窗口对象
        try:
            current_frame = self.root.nametowidget(current_frame_path)
        except KeyError:
            return None
        
        # 3. 从标签页列表中找到匹配的PDFTab
        for tab in self.tabs:
            if tab.frame == current_frame:
                return tab
        return None

    def close_current_tab(self):
        """关闭当前标签页"""
        current_frame_path = self.notebook.select()
        if not current_frame_path:
            return
        
        # 至少保留一个标签页
        if self.notebook.index("end") <= 1:
            messagebox.showinfo("提示", "至少保留一个标签页")
            return
        
        # 从列表中移除当前标签页
        current_tab = self.get_current_tab()
        if current_tab in self.tabs:
            self.tabs.remove(current_tab)
        
        # 关闭文档并移除标签页
        if current_tab:
            current_tab.reset_tab()
        self.notebook.forget(current_frame_path)
        self.update_toolbar_state()

    def prev_page(self):
        """当前标签页上一页"""
        current_tab = self.get_current_tab()
        if current_tab:
            current_tab.prev_page()
            self.update_page_label()

    def next_page(self):
        """当前标签页下一页"""
        current_tab = self.get_current_tab()
        if current_tab:
            current_tab.next_page()
            self.update_page_label()

    def update_zoom(self, zoom_level):
        """更新当前标签页的缩放比例"""
        current_tab = self.get_current_tab()
        if current_tab:
            current_tab.update_zoom(zoom_level)
            self.zoom_label.config(text=f"{int(zoom_level * 100)}%")

    def update_page_label(self):
        """更新页码标签（显示当前标签页的页码）"""
        current_tab = self.get_current_tab()
        if current_tab and current_tab.total_pages > 0:
            self.page_label.config(
                text=f"页码: {current_tab.current_page + 1}/{current_tab.total_pages}"
            )
        else:
            self.page_label.config(text="页码: 0/0")

    def update_toolbar_state(self, event=None):
        """根据当前标签页状态更新工具栏"""
        current_tab = self.get_current_tab()
        if current_tab and current_tab.total_pages > 0:
            # 启用导航按钮并更新状态
            self.prev_btn.config(state=tk.NORMAL)
            self.next_btn.config(state=tk.NORMAL)
            self.zoom_scale.set(current_tab.zoom)
            self.zoom_label.config(text=f"{int(current_tab.zoom * 100)}%")
            self.update_page_label()
        else:
            # 禁用导航按钮（空标签页）
            self.prev_btn.config(state=tk.DISABLED)
            self.next_btn.config(state=tk.DISABLED)
            self.page_label.config(text="页码: 0/0")


if __name__ == "__main__":
    root = tk.Tk()
    app = PDFReader(root)
    root.mainloop()
