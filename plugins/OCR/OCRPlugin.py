"""
OCR 插件：对文档中的图像进行光学字符识别
"""
from __future__ import annotations

import threading
from typing import Any, Dict, List, Tuple, override
import fitz

from glueous_plugin import Plugin


class OCRPlugin(Plugin):
    """
    OCR 插件：自动识别文档中图像的文字并整合到 get_text 方法中。
    """

    # 插件信息
    name = "OCRPlugin"
    
    description = """
# OCRPlugin

- name: OCRPlugin
- author: Glueous Reader
- hotkeys: `Ctrl+Shift+O`
- menu entrance: `工具 → OCR → 开启自动OCR`, `工具 → OCR → 重新识别当前页`

## Function

使用 EasyOCR 库对文档中的图像进行光学字符识别（OCR），提取图像中的文本及其位置信息。

- 支持自动 OCR：优先识别当前可见页面，然后是可选择页面
- 支持手动重新识别当前页面
- 识别结果缓存到 `data.json`，避免重复识别
- 重载 `Page.get_text()` 方法，将 OCR 结果整合到原始文本中

## Api

重载了 `fitz.Page.get_text()` 方法，使其返回值包含 OCR 识别的文本。

## Depend

Python extension library:
- easyocr
- torch (EasyOCR 依赖)

Other plugins:
- TabPlugin

## Others

首次运行会下载 OCR 模型，可能需要较长时间。
识别性能约 2 秒/页（A4 教科书标准）。
"""

    hotkeys = ["<Control-Shift-O>"]

    def __init__(self, context):
        super().__init__(context)
        
        # OCR 引擎（延迟初始化）
        self.ocr_reader = None
        self.ocr_lock = threading.Lock()
        
        # 自动 OCR 开关
        self.auto_ocr_enabled = False
        
        # OCR 任务队列和工作线程
        self.ocr_queue: List[Tuple[str, int]] = []  # [(file_path, page_no), ...]
        self.ocr_thread = None
        self.stop_ocr_thread = False
        
        # 保存原始的 get_text 方法
        self.original_get_text = None


    def initialize_ocr_reader(self) -> None:
        """
        初始化 OCR 引擎（延迟加载）。
        """
        if self.ocr_reader is not None:
            return
            
        try:
            import easyocr
            print("正在初始化 OCR 引擎...")
            # 支持中文和英文
            self.ocr_reader = easyocr.Reader(["ch_sim", "en"], gpu=False)
            print("OCR 引擎初始化完成")
        except ImportError:
            print("错误：未安装 easyocr 库，请运行：pip install easyocr")
            self.disable()
        except Exception as e:
            print(f"OCR 引擎初始化失败: {e}")
            self.disable()


    def get_ocr_cache_key(self, file_path: str, page_no: int) -> str:
        """
        生成 OCR 缓存的键名。
        """
        return f"{file_path}#page{page_no}"


    def get_cached_ocr_result(self, file_path: str, page_no: int) -> List[Dict[str, Any]] | None:
        """
        从缓存中获取 OCR 结果。
        
        Returns:
            List of OCR results or None if not cached
        """
        ocr_cache = self.context.data.setdefault("ocr_cache", {})
        cache_key = self.get_ocr_cache_key(file_path, page_no)
        return ocr_cache.get(cache_key)


    def save_ocr_result(self, file_path: str, page_no: int, result: List[Dict[str, Any]]) -> None:
        """
        保存 OCR 结果到缓存。
        """
        ocr_cache = self.context.data.setdefault("ocr_cache", {})
        cache_key = self.get_ocr_cache_key(file_path, page_no)
        ocr_cache[cache_key] = result


    def perform_ocr_on_page(self, file_path: str, page_no: int) -> List[Dict[str, Any]]:
        """
        对指定页面执行 OCR 识别。
        
        Returns:
            List of OCR results: [{"text": str, "bbox": [x0, y0, x1, y1]}, ...]
        """
        # 检查缓存
        cached_result = self.get_cached_ocr_result(file_path, page_no)
        if cached_result is not None:
            return cached_result
        
        # 初始化 OCR 引擎
        if self.ocr_reader is None:
            self.initialize_ocr_reader()
            if self.ocr_reader is None:
                return []
        
        try:
            # 打开文档
            doc = fitz.open(file_path)
            page = doc[page_no]
            
            # 获取页面上的所有图像
            image_list = page.get_images()
            
            ocr_results = []
            
            for img_index, img_info in enumerate(image_list):
                try:
                    # 获取图像的 xref
                    xref = img_info[0]
                    
                    # 提取图像数据
                    base_image = doc.extract_image(xref)
                    image_bytes = base_image["image"]
                    
                    # 获取图像在页面上的位置
                    image_rects = page.get_image_rects(xref)
                    if not image_rects:
                        continue
                    
                    # 使用第一个矩形（通常图像只出现一次）
                    image_bbox = image_rects[0]
                    
                    # 将图像保存到临时文件或直接从字节读取
                    import io
                    from PIL import Image
                    
                    image = Image.open(io.BytesIO(image_bytes))
                    
                    # 执行 OCR
                    with self.ocr_lock:
                        ocr_output = self.ocr_reader.readtext(image, detail=1)
                    
                    # 处理 OCR 结果
                    for detection in ocr_output:
                        bbox_in_image, text, confidence = detection
                        
                        # 将图像内坐标转换为页面坐标
                        # bbox_in_image: [[x0, y0], [x1, y1], [x2, y2], [x3, y3]]
                        img_width = image.width
                        img_height = image.height
                        
                        # 计算文本框在图像中的相对位置
                        x0_rel = min(point[0] for point in bbox_in_image) / img_width
                        y0_rel = min(point[1] for point in bbox_in_image) / img_height
                        x1_rel = max(point[0] for point in bbox_in_image) / img_width
                        y1_rel = max(point[1] for point in bbox_in_image) / img_height
                        
                        # 转换为页面坐标
                        page_x0 = image_bbox.x0 + x0_rel * image_bbox.width
                        page_y0 = image_bbox.y0 + y0_rel * image_bbox.height
                        page_x1 = image_bbox.x0 + x1_rel * image_bbox.width
                        page_y1 = image_bbox.y0 + y1_rel * image_bbox.height
                        
                        ocr_results.append({
                            "text": text,
                            "bbox": [page_x0, page_y0, page_x1, page_y1],
                            "confidence": confidence
                        })
                
                except Exception as e:
                    print(f"处理图像 {img_index} 时出错: {e}")
                    continue
            
            doc.close()
            
            # 保存到缓存
            self.save_ocr_result(file_path, page_no, ocr_results)
            
            return ocr_results
            
        except Exception as e:
            print(f"OCR 识别页面 {page_no} 时出错: {e}")
            return []


    def modified_get_text(self, original_method, page_instance, *args, **kwargs):
        """
        重载后的 get_text 方法，整合 OCR 结果。
        """
        # 调用原始方法获取文本
        original_text = original_method(*args, **kwargs)
        
        # 如果插件未启用，直接返回原始文本
        if not self.able:
            return original_text
        
        try:
            # 获取页面信息
            doc = page_instance.parent
            page_no = page_instance.number
            
            # 尝试获取文件路径
            file_path = getattr(doc, "name", None)
            if not file_path:
                return original_text
            
            # 获取 OCR 结果
            ocr_results = self.get_cached_ocr_result(file_path, page_no)
            
            # 如果没有缓存且自动 OCR 开启，添加到队列
            if ocr_results is None and self.auto_ocr_enabled:
                self.add_to_ocr_queue(file_path, page_no)
                return original_text
            
            # 如果有 OCR 结果，整合到文本中
            if ocr_results:
                ocr_text = "\n".join([result["text"] for result in ocr_results])
                if ocr_text:
                    # 根据返回格式添加 OCR 文本
                    if args and args[0] in ("dict", "json", "rawdict", "rawjson"):
                        # 结构化格式，需要更复杂的整合
                        # 这里简化处理，直接在文本末尾添加
                        return original_text + "\n[OCR]\n" + ocr_text
                    else:
                        # 文本格式
                        return original_text + "\n[OCR]\n" + ocr_text
            
            return original_text
            
        except Exception as e:
            print(f"整合 OCR 结果时出错: {e}")
            return original_text


    def add_to_ocr_queue(self, file_path: str, page_no: int) -> None:
        """
        添加页面到 OCR 队列。
        """
        task = (file_path, page_no)
        if task not in self.ocr_queue:
            self.ocr_queue.append(task)


    def ocr_worker(self) -> None:
        """
        OCR 工作线程，处理队列中的识别任务。
        """
        while not self.stop_ocr_thread:
            if self.ocr_queue:
                file_path, page_no = self.ocr_queue.pop(0)
                print(f"正在识别: {file_path} 第 {page_no + 1} 页")
                self.perform_ocr_on_page(file_path, page_no)
            else:
                # 队列为空，休眠一会
                import time
                time.sleep(0.5)


    def start_ocr_thread(self) -> None:
        """
        启动 OCR 工作线程。
        """
        if self.ocr_thread is None or not self.ocr_thread.is_alive():
            self.stop_ocr_thread = False
            self.ocr_thread = threading.Thread(target=self.ocr_worker, daemon=True)
            self.ocr_thread.start()


    def stop_ocr_worker(self) -> None:
        """
        停止 OCR 工作线程。
        """
        self.stop_ocr_thread = True
        if self.ocr_thread:
            self.ocr_thread.join(timeout=2)


    def toggle_auto_ocr(self) -> None:
        """
        切换自动 OCR 开关。
        """
        self.auto_ocr_enabled = not self.auto_ocr_enabled
        
        if self.auto_ocr_enabled:
            print("已开启自动 OCR")
            self.start_ocr_thread()
            # 触发当前可见页面的识别
            self.trigger_visible_pages_ocr()
        else:
            print("已关闭自动 OCR")
            self.stop_ocr_worker()


    def trigger_visible_pages_ocr(self) -> None:
        """
        触发当前可见页面和可选择页面的 OCR 识别。
        """
        current_tab = self.context.get_current_tab()
        if not current_tab or not current_tab.doc:
            return
        
        file_path = current_tab.file_path
        
        # 优先级：当前页面
        current_page = current_tab.page_no
        self.add_to_ocr_queue(file_path, current_page)
        
        # 可见页面
        for page, _, _ in current_tab.visible_page_positions:
            self.add_to_ocr_queue(file_path, page.number)
        
        # 可选择页面
        for page, _ in current_tab.selectable_page_positions:
            self.add_to_ocr_queue(file_path, page.number)


    def reocr_current_page(self) -> None:
        """
        重新识别当前页面。
        """
        current_tab = self.context.get_current_tab()
        if not current_tab or not current_tab.doc:
            from tkinter import messagebox
            messagebox.showwarning("提示", "请先打开一个文档")
            return
        
        file_path = current_tab.file_path
        page_no = current_tab.page_no
        
        # 清除缓存
        ocr_cache = self.context.data.setdefault("ocr_cache", {})
        cache_key = self.get_ocr_cache_key(file_path, page_no)
        if cache_key in ocr_cache:
            del ocr_cache[cache_key]
        
        # 重新识别
        print(f"重新识别第 {page_no + 1} 页...")
        result = self.perform_ocr_on_page(file_path, page_no)
        
        from tkinter import messagebox
        messagebox.showinfo("完成", f"识别完成，找到 {len(result)} 个文本块")


    @override
    def loaded(self) -> None:
        """
        插件加载时执行：注册菜单项并重载 get_text 方法。
        """
        # 添加菜单项
        self.context.add_menu_command(
            path=["工具", "OCR"],
            label="开启/关闭自动OCR",
            command=self.toggle_auto_ocr,
            accelerator="Ctrl+Shift+O"
        )
        
        self.context.add_menu_command(
            path=["工具", "OCR"],
            label="重新识别当前页",
            command=self.reocr_current_page
        )
        
        # 重载 Page.get_text 方法
        if self.original_get_text is None:
            self.original_get_text = fitz.Page.get_text
            
            # 创建闭包保存 self 引用
            plugin_self = self
            
            def new_get_text(page_instance, *args, **kwargs):
                return plugin_self.modified_get_text(
                    plugin_self.original_get_text,
                    page_instance,
                    *args,
                    **kwargs
                )
            
            fitz.Page.get_text = new_get_text


    @override
    def run(self) -> None:
        """
        快捷键触发时执行：切换自动 OCR。
        """
        self.toggle_auto_ocr()


    @override
    def unloaded(self) -> None:
        """
        插件卸载时执行：恢复原始 get_text 方法并停止工作线程。
        """
        # 停止 OCR 线程
        self.stop_ocr_worker()
        
        # 恢复原始方法
        if self.original_get_text is not None:
            fitz.Page.get_text = self.original_get_text
