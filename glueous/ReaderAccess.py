from __future__ import annotations

import tkinter as tk
from tkinter import ttk
from typing import Any, Dict, Iterable, List, Type, TYPE_CHECKING

if TYPE_CHECKING:
    from .Reader import Reader


class ReaderAccess:
    """
    插件访问 Reader 的接口。
    """

    def __init__(self, reader: Reader):
        # Do not directly access this attribute
        # unless you have a clear understanding of what you are doing.
        self._reader: Reader = reader


    def get_setting(self, key: str, default: Any = None) -> Any:
        """
        访问全局设置。
        """
        return self._reader.settings.get(key, default)


    def set_setting(self, key: str, value: Any) -> None:
        """
        修改全局设置。
        """
        self._reader.settings[key] = value


    def add_menu(self, path: Iterable[str]) -> Dict[str, Any]:
        """
        添加一个空的菜单，其访问路径为 `path` 。
        """
        # 获取菜单结构
        current_menu: Dict[str, List[Dict[str, Any]]] = {"children": self._reader.menu_structure}

        # 遍历路径，逐级查找或创建菜单
        for menu_name in path:
            # 查找当前层级是否已存在同名菜单
            found = False
            for item in current_menu["children"]:
                if (item.get("label") == menu_name) and (item.get("type") == "menu"):
                    current_menu = item
                    found = True
                    break

            # 不存在则创建新菜单
            if not found:
                new_menu = {
                    "type": "menu",
                    "label": menu_name,
                    "tearoff": 0,
                    "children": []
                }
                current_menu["children"].append(new_menu)
                current_menu = new_menu

        self.update_menubar()
        return current_menu


    def add_menu_separator(self, path: Iterable[str]) -> None:
        """
        在访问路径为 `path` 的菜单下添加分割线。

        如果指定菜单不存在，则会新建这个菜单。
        """
        menu = self.add_menu(path)
        menu["children"].append({"type": "seperator"})
        self.update_menubar()


    def add_menu_command(self, path: Iterable[str], **kwargs: Dict[str, Any]) -> None:
        """
        在访问路径为 `path` 的菜单下添加命令。

        如果指定菜单不存在，则会新建这个菜单。

        `kwargs` 传入 `tk.Menu.add_command` 方法。
        """
        menu = self.add_menu(path)
        menu["children"].append({"type": "command", **kwargs})
        self.update_menubar()


    def update_menubar(self) -> None:
        """
        更新菜单栏。
        """
        self._reader.update_menubar()


    def add_tool(
        self,
        Widget: Type, *,
        args: List[Any] = None, kwargs: Dict[str, Any] = None,
        side: str = tk.LEFT, padx: int = 5, pady: int = 5,
    ) -> tk.Widget:
        """
        添加一个工具。

        `Widget` 为继承自 `tk.Widget` 的组件类，如 `tk.Button` ；
        `args` 和 `kwargs` 传入 `Widget` 的构造方法。

        返回创建的组件实例。
        """
        if args is None:
            args = []
        if kwargs is None:
            kwargs = {}
        # 创建组件实例
        widget_instance = Widget(self._reader.toolbar, *args, **kwargs)
        # 添加到工具栏
        widget_instance.pack(side = side, padx = padx, pady = pady)
        return widget_instance


    def bind_root(self, *args, **kwargs) -> None:
        """
        绑定事件到主窗口。
        """
        self._reader.root.bind(*args, **kwargs)


    def bind_notebook(self, *args, **kwargs) -> None:
        """
        绑定事件到标签页。
        """
        self._reader.notebook.bind(*args, **kwargs)


    def get_notebook(self) -> ttk.Notebook:
        """
        获取标签页容器。
        """
        return self._reader.notebook


    def get_data(self) -> Dict[str, Any]:
        """
        返回对应用数据的引用，插件可以写入该对象以实现数据持久化。
        """
        return self._reader.data
