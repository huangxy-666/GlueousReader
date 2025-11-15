"""
使用户可以通过 Ctrl+MouseWheel 的方式进行放大 / 缩小。
"""

from tkinter import ttk
from typing import override
from types import MethodType

from glueous import ReaderAccess
from glueous_plugin import Plugin


class ZoomPlugin(Plugin):
    """
    缩放插件：允许用户通过 Ctrl+鼠标滚轮 进行缩放。
    """

    # 插件信息
    name = "ZoomPlugin"
    description = """
# ZoomPlugin

- name: ZoomPlugin
- author: Jerry
- hotkeys: None
- menu entrance: None

## Function

Allow zooming in/out by holding Ctrl and using the mouse wheel.

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
        # 当 notebook 显示的标签页改变时，将鼠标滚轮事件绑定到当前活跃的标签页，可以用鼠标滚轮控制缩放
        self.context.add_at_notebook_tab_changed_function(self._bind_mousewheel_to_current_tab)


    def _bind_mousewheel_to_current_tab(self, event) -> None:
        """
        将鼠标滚轮事件绑定到当前标签页的画布上。
        """
        current_tab = self.context.get_current_tab()
        if current_tab is not None:
            # 绑定新的滚轮事件
            current_tab.canvas.bind("<Control-MouseWheel>", self._on_mousewheel_windows)  # Windows
            current_tab.canvas.bind("<Control-Button-4>", self._on_mousewheel_linux_up)   # Linux 向上
            current_tab.canvas.bind("<Control-Button-5>", self._on_mousewheel_linux_down) # Linux 向下


    def _on_mousewheel_windows(self, event) -> None:
        """
        Windows 系统下的鼠标滚轮事件处理。
        """
        current_tab = self.context.get_current_tab()
        if current_tab is not None:
            if event.delta > 0:
                current_tab.zoom *= 1.1
            elif event.delta < 0:
                current_tab.zoom /= 1.1


    def _on_mousewheel_linux_up(self, event) -> None:
        """
        Linux 系统下鼠标滚轮向上滚动事件处理。
        """
        current_tab = self.context.get_current_tab()
        if current_tab is not None:
            current_tab.zoom *= 1.1


    def _on_mousewheel_linux_down(self, event) -> None:
        """
        Linux 系统下鼠标滚轮向下滚动事件处理。
        """
        current_tab = self.context.get_current_tab()
        if current_tab is not None:
            current_tab.zoom /= 1.1


    @override
    def run(self) -> None:
        pass


    @override
    def unloaded(self) -> None:
        pass
