"""
A folder used to store plugins.
"""
from typing import List

# 插件加载顺序
plugin_loading_order: List[str] = [
    "TabPlugin",
    "OpenPlugin",
    "ClosePlugin",
    "PageUpPlugin",
    "PageNoPlugin",
    "PageDownPlugin",
    "ZoomPlugin",
    "ZoomOutPlugin",
    "ZoomInPlugin",
    "ScrollPlugin",
    "HorizontalScrollPlugin",
    "VerticalScrollUpPlugin",
    "HorizontalScrollLeftPlugin",
    "HorizontalScrollRightPlugin",
]
