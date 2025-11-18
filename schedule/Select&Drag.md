# Select & Drag

你需要完成两个插件：`SelectPlugin` 和 `DragPlugin` 。

## Function

### SelectPlugin

绑定 `Ctrl+鼠标拖动` 事件到当前活跃 canvas 。（可以参考 `ZoomPlugin` 和 `ScrollPlugin` ）

当发生该事件时，要在画布上绘制一个半透明的选择区域（矩形），绘制方法参见 https://www.kimi.com/share/19a963f4-ea62-890e-8000-0000f41ba67c 的方法2。

当鼠标接近窗口边缘时，还向相应方向要滚动。

为 `ReaderAccess` 添加/扩展 `get_selected_text` 方法，获得选中区域的内的文字对象，该方法接受的参数和返回值与 `pymupdf.Page.get_text` 相同。

目标效果：

<video src="./Select&amp;Drag.assets/Select-demo1.mp4"></video>

<video src="./Select&amp;Drag.assets/Select-demo2.mp4"></video>

### DragPlugin

绑定 `鼠标拖动` 事件到当前活跃 canvas 。

当发生该事件时，现判断拖动起点是否落在某个文字的矩形框内，若是，则为划词，否则，视为拖动。划词的具体实现方案参见[划动选择的可能实现方案](划动选择的可能实现方案.md)，当接近窗口边缘时，还要滚动。

为 `ReaderAccess` 添加/扩展 `get_selected_text` 方法（可参考 `TabPlugin` 和 `PageNoPlugin` ），获得选中区域的内的文字对象，该方法接受的参数和返回值与 `pymupdf.Page.get_text` 相同。

目标效果：

<video src="./Select&amp;Drag.assets/Drag-demo1.mp4"></video>

<video src="./Select&amp;Drag.assets/Drag-demo2.mp4"></video>

## API

你需要为 `ReaderAccess` （即 `self.context` 对象）添加/扩展的方法：

- `get_selected_text(...)` ：获取当前选中的文本。
    - 输入：同 `pymupdf.Page.get_text(...)` 。
    - 输出：同 `pymupdf.Page.get_text(...)` 。

## Something Useful

- `ReaderAccess.add_at_notebook_tab_changed_function()` ：添加一个在标签页切换时执行的函数。
- `ReaderAccess.get_current_tab()` ：由 `TagPlugin` 添加，可获取当前激活的标签页对象（`Tab`）。
- `Tab.selectable_page_positions` ：`List[(可被选择的页面, 该页面的在整块 canvas 上的位置矩形)]` 。
- `Tab.coord2real()` ：将“用户视界”上的坐标转换为在整个画布上的坐标。
- `pymupdf.Page` ：页面类，下面简记为 `Page` ，具体细节自行搜索。
- `Page.get_text()` ：按指定格式返回页面上指定区域内的文字。
- `Page.rect` ：页面矩形，可以获得页面宽度、高度。

为 `ReaderAccess` 添加方法可参考 `TabPlugin` 和 `PageNoPlugin` 。

为 `ReaderAccess` 的已有方法扩展功能可参考 Python 的修饰器。

以上关于 `ReaderAccess` 和 `Tab` 的函数的具体细节可以直接翻阅源码。

如需使用其他函数，也可以直接看源码。