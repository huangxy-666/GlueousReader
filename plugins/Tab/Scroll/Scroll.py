"""
统一绑定水平和垂直的鼠标滚轮滚动。
"""

from tkinter import ttk
from typing import override
from types import MethodType

from glueous import ReaderAccess
from glueous_plugin import Plugin


class ScrollPlugin(Plugin):
    """
    滚动插件：整合垂直和水平滚动功能。
    """

    # 插件信息
    name = "ScrollPlugin"
    description = """
# ScrollPlugin

- name: ScrollPlugin
- author: Jerry
- hotkeys: None
- menu entrance: None

## Function

Integrate vertical and horizontal scrolling into a single plugin.

- <MouseWheel>: Vertical scrolling.
- <Shift-MouseWheel>: Horizontal scroll.

## Api

None.

## Depend

Python extension library: None

Other plugins:
- TabPlugin

## Others

None.
"""

    # 快捷键设置
    hotkeys = []


    @override
    def loaded(self) -> None:
        """
        注册快捷键。
        """
        # 当 notebook 显示的标签页改变时，将鼠标滚轮事件绑定到当前活跃的标签页，可以用鼠标滚轮控制滚动条
        self.context.add_at_notebook_tab_changed_function(self._bind_mousewheel_to_current_tab)


    def _bind_mousewheel_to_current_tab(self, event) -> None:
        """
        将鼠标滚轮事件绑定到当前标签页的画布上。
        """
        current_tab = self.context.get_current_tab()
        if current_tab is None:
            return
        # 绑定新的滚轮事件
        current_tab.canvas.bind("<MouseWheel>", self._on_vertical_mousewheel_windows)  # Windows 垂直
        current_tab.canvas.bind("<Button-4>", self._on_vertical_mousewheel_linux_up)   # Linux 向上
        current_tab.canvas.bind("<Button-5>", self._on_vertical_mousewheel_linux_down) # Linux 向下
        current_tab.canvas.bind("<Shift-MouseWheel>", self._on_horizontal_mousewheel_windows)  # Windows 水平
        current_tab.canvas.bind("<Shift-Button-4>", self._on_horizontal_mousewheel_linux_up)   # Linux 向左
        current_tab.canvas.bind("<Shift-Button-5>", self._on_horizontal_mousewheel_linux_down) # Linux 向右


    def _on_vertical_mousewheel_windows(self, event) -> None:
        """
        Windows 系统下的鼠标滚轮事件处理。
        """
        current_tab = self.context.get_current_tab()
        if current_tab is not None:
            current_tab.canvas.yview_scroll(int(-1*(event.delta/120)), "units")


    def _on_vertical_mousewheel_linux_up(self, event) -> None:
        """
        Linux 系统下鼠标滚轮向上滚动事件处理。
        """
        current_tab = self.context.get_current_tab()
        if current_tab is not None:
            current_tab.canvas.yview_scroll(-1, "units")


    def _on_vertical_mousewheel_linux_down(self, event) -> None:
        """
        Linux 系统下鼠标滚轮向下滚动事件处理。
        """
        current_tab = self.context.get_current_tab()
        if current_tab is not None:
            current_tab.canvas.yview_scroll(1, "units")


    def _on_horizontal_mousewheel_windows(self, event) -> None:
        """
        Windows 系统下的水平鼠标滚轮事件处理。
        """
        current_tab = self.context.get_current_tab()
        if current_tab is not None:
            current_tab.canvas.xview_scroll(int(-1*(event.delta/120)), "units")


    def _on_horizontal_mousewheel_linux_up(self, event) -> None:
        """
        Linux 系统下鼠标滚轮向左滚动事件处理。
        """
        current_tab = self.context.get_current_tab()
        if current_tab is not None:
            current_tab.canvas.xview_scroll(-1, "units")


    def _on_horizontal_mousewheel_linux_down(self, event) -> None:
        """
        Linux 系统下鼠标滚轮向右滚动事件处理。
        """
        current_tab = self.context.get_current_tab()
        if current_tab is not None:
            current_tab.canvas.xview_scroll(1, "units")


    @override
    def run(self) -> None:
        pass


    @override
    def unloaded(self) -> None:
        pass
