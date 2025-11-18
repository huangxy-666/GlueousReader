"""
上下文菜单组件，当鼠标右键单击画布时，会显示一个菜单。
"""

from collections import namedtuple
import tkinter as tk
from tkinter import Widget
from typing import Any, Dict, Iterable, List, override
from types import MethodType

from glueous import ReaderAccess
from glueous.Reader import construct_menu
from glueous.ReaderAccess import add_menu_to_menu_structure
from glueous_plugin import Plugin


ContextMenuInfo = namedtuple("ContextMenuInfo", ["widget", "structure", "menu"])

class ContextMenuPlugin(Plugin):
    """
    为指定位置添加上下文菜单，并为 context 添加 add_context_menu_command 方法，作为接口供其他插件添加上下文菜单项。
    """

    name = "ContextMenuPlugin"
    description = """
# ContextMenuPlugin

- name: ContextMenuPlugin
- author: Jerry
- hotkeys: None
- menu entrance: None

## Function

Manage all context menus.

Developers can customize the context and context menu.

## Api

- context.context_menu_manager: The ContextMenuPlugin that manages all context menus.
- context.context_menu_manager.set_context(context: str, widget: Widget): Add new context or modify existing context.
- context.context_menu_manager.add_context_menu_separator(context: str, path: Iterable[str]): Add a dividing line at the specified location in the menu of specified context.
- context.context_menu_manager.add_context_menu_command(context: str, path: Iterable[str], **kwargs): Add a command at the specified location in the menu of specified context.

## Depend

Python extension library: None

Other plugins: None
"""

    hotkeys = []

    def __init__(self, context: ReaderAccess):
        Plugin.__init__(self, context)

        # 存储上下文菜单的结构及触发各种上下文菜单的部件
        self.context_menus: Dict[str, namedtuple[Widget | None, List[Dict[str, Any]], tk.Menu]] = {}


    def loaded(self) -> None:
        """
        在插件被加载时运行。
        """
        # 提供接口，供其他插件来自定义上下文菜单
        self.context.context_menu_manager = self


    def set_context(self, context: str, widget: Widget | None):
        """
        设置上下文 context 为在部件 widget 上。

        如果 widget 为 None，则此次操作视为占位，后续可以再指定特定组件，在这期间对该上下文菜单的修改将被保留。
        """
        if context not in self.context_menus:
            self.context_menus[context] = ContextMenuInfo(widget, [], tk.Menu(widget, tearoff=0))
        else:
            (_, menu_structure, menu) = self.context_menus[context]
            self.context_menus[context] = ContextMenuInfo(widget, menu_structure, menu)
        self.update_context_menu(context)


    def add_context_menu(self, context: str, path: Iterable[str]) -> Dict[str, Any]:
        """
        在上下文 `context` 的菜单中添加一个空的菜单，其访问路径为 `path` 。
        """
        if context not in self.context_menus:
            raise KeyError(f"context `{context!r}` does not exist")
        current_menu = add_menu_to_menu_structure(self.context_menus[context].structure, path)
        self.update_context_menu(context)
        return current_menu


    def add_context_menu_separator(self, context: str, path: Iterable[str]) -> None:
        """
        在上下文 `context` 的菜单中访问路径为 `path` 的菜单下添加分割线。

        如果指定菜单不存在，则会新建这个菜单。
        """
        menu = self.add_context_menu(context, path)
        menu["children"].append({"type": "seperator"})
        self.update_context_menu(context)


    def add_context_menu_command(self, context: str, path: Iterable[str], **kwargs) -> None:
        """
        在上下文 `context` 的菜单中访问路径为 `path` 的菜单下添加命令。

        如果指定菜单不存在，则会新建这个菜单。

        `kwargs` 传入 `tk.Menu.add_command` 方法。
        """
        menu = self.add_context_menu(context, path)
        menu["children"].append({"type": "command", **kwargs})
        self.update_context_menu(context)


    def update_context_menu(self, context: str) -> None:
        """
        根据 self.context_menus 更新应绑定在上下文 `context` 的菜单。
        """
        if context not in self.context_menus:
            raise KeyError(f"context `{context!r}` does not exist")

        # 获取菜单结构和菜单组件
        (widget, menu_structure, menu) = self.context_menus[context]

        # 清空菜单组件
        menu.delete(0, tk.END)

        # 重新构建菜单
        construct_menu(menu, menu_structure)

        if widget is None:
            return

        # 绑定到鼠标右键单击组件
        widget.bind("<Button-3>", lambda event: self._show_context_menu(event, context))


    def _show_context_menu(self, event, context: str) -> None:
        """
        在指定位置显示上下文菜单。
        """
        if context not in self.context_menus:
            raise KeyError(f"context `{context!r}` does not exist")

        # 获取菜单组件
        (_, _, menu) = self.context_menus[context]

        # 在鼠标右键单击位置显示菜单
        try:
            menu.tk_popup(event.x_root, event.y_root)
        finally:
            menu.grab_release()


    @override
    def run(self) -> None:
        pass


    @override
    def unloaded(self) -> None:
        pass
