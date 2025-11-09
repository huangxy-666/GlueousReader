"""
A folder used to store plugins.
"""
from typing import List

# 插件加载顺序
plugin_loading_order: List[str] = [
    "OpenPlugin",
    "ClosePlugin",
    "PageUpPlugin",
    "PageNoPlugin",
    "PageDownPlugin",
]
