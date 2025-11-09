from __future__ import annotations

import tkinter as tk
from typing import Any, Dict, Iterable, List, Type, TYPE_CHECKING

from .Tab import Tab

if TYPE_CHECKING:
    from .Reader import Reader


class ReaderAccess:
    """
    插件访问 Reader 的接口。
    """

    def __init__(self, reader: Reader):
        # 非必要情况，插件最好不要直接访问这个属性
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

        return current_menu


    def add_menu_separator(self, path: Iterable[str]) -> None:
        """
        在访问路径为 `path` 的菜单下添加分割线。

        如果指定菜单不存在，则会新建这个菜单。
        """
        menu = self.add_menu(path)
        menu["children"].append({"type": "seperator"})


    def add_menu_command(self, path: Iterable[str], **kwargs: Dict[str, Any]) -> None:
        """
        在访问路径为 `path` 的菜单下添加命令。

        如果指定菜单不存在，则会新建这个菜单。

        `kwargs` 传入 `tk.Menu.add_command` 方法。
        """
        menu = self.add_menu(path)
        menu["children"].append({"type": "command", **kwargs})


    def update_menubar(self) -> None:
        """
        更新菜单栏。
        """
        self._reader.update_menubar()


    def add_tool(
        self,
        Widget: Type, *args,
        side: str = tk.LEFT, padx: int = 5, pady: int = 5,
        **kwargs
    ) -> tk.Widget:
        """
        添加一个工具。

        `Widget` 为继承自 `tk.Widget` 的组件类，如 `tk.Button` ；
        `args` 和 `kwargs` 传入 `Widget` 的构造方法。

        返回创建的组件实例。
        """
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


    def create_tab(self, file_path: str | None = None) -> Tab:
        """
        创建新标签页
        """
        new_tab = Tab(self._reader.notebook)

        if file_path:
            new_tab.open_pdf(file_path)

        # 激活新标签页
        self._reader.notebook.select(new_tab.frame)

        # 添加到标签页列表
        self._reader.tabs.append(new_tab)


    @property
    def tabs(self) -> List[Tab]:
        return self._reader.tabs


    def get_current_tab(self) -> Tab | None:
        """
        获取当前激活的标签页实例。
        """
        return self._reader.get_current_tab()


    def close_tab(self, tab: Tab):
        """
        关闭一个标签页，返回是否成功关闭。
        """
        if tab in self._reader.tabs:
            self._reader.tabs.remove(tab)

        tab.reset_tab()
        self._reader.notebook.forget(tab.frame)
