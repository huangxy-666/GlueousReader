# OCR

你需要完成 ` OCRPlugin` 插件。

## Function

调用 Python 的 OCR 拓展库（自行搜索），对文档中的图像进行 OCR ，得到图像中的文本及其位置。

> [!TIP]
>
> 不用自己去训练一个模型来识别文字，用 Python 现有的扩展库！

用户可以在菜单栏中关闭/打开自动OCR；可以要求重新识别。

### 优先级

若用户打开了自动 OCR ：

- 用 `current_tab.visible_page_positions` 获得所有可见页面。
- 用 `current_tab.selectable_page_positions` 获得所有可选择页面。
- 用 `current_tab.page_no` 获取当前页面编号

优先识别当前页面及其周围的页面，当 `visible_page_positions` 中的页面全部识别完成后，再对 `selectable_page_positions` 中的页面进行识别。

### 性能

建议将识别一页的内容（以 A4 的教科书为标准）控制在2秒内，需要在准确度与速度之间进行权衡。

### 缓存

为避免重复 OCR 带来的开销，每个页面只识别一次，可以将识别到的内容进行 JSON 化，通过 `ReaderAccess` 的 `data` 属性，存储在本地的 `config/data.json` 文件中，实现数据持久化，下次再打开时可直接读取，无需再次识别。（参见 `Tab.py` 中的 `Tab.__init__` ）

## Implement

由于重载 `Page.get_text()` 方法的工作量较大，可以改为向 `Page` 对象插入文本的方式来实现同样的效果。下面提供关键代码的可能的实现思路，其他代码（如 注册菜单和快捷键、缓存OCR数据到`ReaderAccess.data`、打印信息 等）略去。

重载 `Tab.open` 方法，在打开文件时导入 OCR 文本数据，伪代码如下：

```python
class OCRPlugin(Plugin):
    # 其他代码...

    @override
    def loaded(self) -> None:
        # 其他代码...
        Tab = self.context.Tab
        original_open = Tab.open

        def open_with_ocr(tab: Tab) -> None:
            original_open(tab: Tab)

            if 自动OCR:
                从ReaderAccess.data中获取该文件的OCR缓存数据
                调用Page.insert_text将这些之前识别到的文本数据添加到tab的对应页

        Tab.open = open_with_ocr
```

在运行过程中，实时检测 `current_tab` 的 `visible_page_positions` 、 `selectable_page_positions` 中有哪些页面还没有被 OCR ，若有，则按照上文所说的优先级依次对单个页面进行 OCR ，后期可以通过多进程并发来加速。这部分的伪代码如下：

```python
class OCRPlugin(Plugin):
    # 其他代码...

    @override
    def loaded(self) -> None:
        # 其他代码...
        self.context.add_periodically_execute_function(self.实时检测并对页面进行OCR)

        
    def 找出哪些页面没有被OCR(self) -> List[Page]:
        result: List[Page] = []
        current_tab = self.context.get_current_tab()
        
        for (page, _, _) in current_tab.visible_page_positions:
            if 在 ReaderAccess.data 中没有页面 page 的OCR数据记录:
                result.append(page)
        
        for (page, _) in current_tab.selectable_page_positions:
            if 在 ReaderAccess.data 中没有页面 page 的OCR数据记录:
                result.append(page)
        
        return result

    
    @staticmethod
    def 对一个页面进行OCR(page: Page) -> None:
        通过 page.get_images 获取该页面上的图像
        通过 page.get_image_bbox 获取这些图像的位置
        
        for 单个图像 in 该页面上的所有图像:
            对该图像进行OCR，获得该图像上的文字及其位置
            结合该图像在页面上的位置，计算出文字在页面上的位置
            通过 page.insert_text 向页面插入文本

            
    def 实时检测并对页面进行OCR(self) -> None:
        if 自动OCR:
            pages = self.找出哪些页面没有被OCR()
            for page in pages: # 后期可以使用多进程并发来加速
                self.对一个页面进行OCR(page)
```

- 可以向 `Page.insert_text` 传入参数 `render_mode = 3` ，这样渲染时就不会显示 OCR 出来的文本。不过前期调试时还是显示出来吧。
- 完成这一步后， `page.get_text` 就能返回 OCR 识别出来的文字啦！

如果用户要重新对当前页面进行OCR识别，伪代码如下：

```python
class OCRPlugin(Plugin):
    # 其他代码...
    
    def 重新识别当前页(self) -> None:
        current_tab = self.context.get_current_tab()
        page_no = current_tab.page_no
        在 ReaderAccess.data 中删除这一页的OCR识别数据（如果有的话）
        current_tab.reset()
        current_tab.open()
        if 没有开启自动OCR:
	        self.对一个页面进行OCR(current_tab.page)
```

如果用户要重新对所有页面进行OCR识别（需要用户手动开启“自动OCR”才能生效，否则仅仅删除之前OCR结果），伪代码如下：

```python
class OCRPlugin(Plugin):
    # 其他代码...
    
    def 重新识别当前文件(self) -> None:
        current_tab = self.context.get_current_tab()
        在 ReaderAccess.data 中删除这个文件的OCR识别数据（如果有的话）
        current_tab.reset()
        current_tab.open()
```

## API

重载 `Tab` 类的 `open` 方法，在原有功能的基础上，再导入过往的 OCR 数据。详见 [Implement](#Implement) 部分。

## Something Useful

- `ReaderAccess.data` ：返回对应用数据的引用，插件可以写入该对象以实现数据持久化。（只能写入可JSON化的对象）（参见 `Tab.__init__`）
- `Tab.doc` ：`fitz.Document` 对象，可视为 `Sequence[Page]` 和 `Iterable[Page]` 。
- `Tab.visible_page_positions` 
- `Tab.selectable_page_positions` 
- `Tab.page_no` 
- `Tab.page` ：当前页对象
- `Tab.reset()` ：重置标签页。
- `Tab.open()` ：打开文件并初始化标签页。
- `Page.get_images()` ：返回一个**列表**，列表中的每个元素都是一个元组，代表页面上的一张图像信息。（详细信息自行搜索）
- `Page.get_image_bbox()` ：获取页面中指定图像所占用的矩形区域。（详细信息自行搜索）用于计算识别出的文字在整个页面上的坐标。
- `Page.insert_text()` ：在页面上的指定位置插入文字。
