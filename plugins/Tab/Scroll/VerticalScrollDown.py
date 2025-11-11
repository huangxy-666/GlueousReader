"""
向下滚动。
"""

from tkinter import ttk
from typing import override

from glueous_plugin import Plugin


class VerticalScrollDownPlugin(Plugin):
    """
    向下滚动插件：允许用户通过快捷键或菜单项向下滚动页面。
    """

    # 插件信息
    name = "VerticalScrollDownPlugin"
    description = "向下滚动页面，快捷键: Down"

    # 快捷键设置
    hotkeys = ["<Down>"]


    @override
    def loaded(self) -> None:
        """
        注册菜单项、快捷键。
        """
        # 注册菜单项、快捷键
        self.context.add_menu_command(
            path = ["前往"],
            label = "向下滚动",
            command = self.run,
            accelerator = self.hotkey
        )

        # 当 notebook 显示的标签页改变时，将鼠标滚轮事件绑定到当前活跃的标签页，可以用鼠标滚轮控制滚动条
        self.context.bind_notebook("<<NotebookTabChanged>>", lambda event: self._bind_mousewheel_to_current_tab())


    def _bind_mousewheel_to_current_tab(self) -> None:
        """
        将鼠标滚轮事件绑定到当前标签页的画布上。
        """
        current_tab = self.context.get_current_tab()
        if current_tab is not None:
            current_tab.canvas.unbind("<MouseWheel>")
            current_tab.canvas.unbind("<Button-4>")
            current_tab.canvas.unbind("<Button-5>")

            # 绑定新的滚轮事件
            current_tab.canvas.bind("<MouseWheel>", self._on_mousewheel_windows)      # Windows
            current_tab.canvas.bind("<Button-4>", self._on_mousewheel_linux_up)      # Linux 向上
            current_tab.canvas.bind("<Button-5>", self._on_mousewheel_linux_down)    # Linux 向下


    def _on_mousewheel_windows(self, event) -> None:
        """
        Windows 系统下的鼠标滚轮事件处理。
        """
        current_tab = self.context.get_current_tab()
        if current_tab is not None:
            current_tab.canvas.yview_scroll(int(-1*(event.delta/120)), "units")


    def _on_mousewheel_linux_up(self, event) -> None:
        """
        Linux 系统下鼠标滚轮向上滚动事件处理。
        """
        current_tab = self.context.get_current_tab()
        if current_tab is not None:
            current_tab.canvas.yview_scroll(-1, "units")


    def _on_mousewheel_linux_down(self, event) -> None:
        """
        Linux 系统下鼠标滚轮向下滚动事件处理。
        """
        current_tab = self.context.get_current_tab()
        if current_tab is not None:
            current_tab.canvas.yview_scroll(1, "units")


    @override
    def run(self) -> None:
        """
        执行向下滚动操作。
        """
        current_tab = self.context.get_current_tab()
        if current_tab is None:
            return

        # 向下滚动画布
        current_tab.canvas.yview_scroll(1, "units")


    @override
    def unloaded(self) -> None:
        pass

