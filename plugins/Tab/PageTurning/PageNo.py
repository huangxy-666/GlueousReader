"""
显示当前页码。
"""

from tkinter import ttk
from typing import override

from glueous_plugin import Plugin


class PageNoPlugin(Plugin):
    """
    页码显示插件：在状态栏显示当前页码和总页数。
    """

    # 插件信息
    name = "PageNoPlugin"
    description = "在状态栏显示当前页码和总页数"


    @override
    def loaded(self) -> None:
        """
        初始化页码标签并添加到状态栏。
        """
        # 创建页码显示标签
        self.page_label = self.context.add_tool(
            ttk.Label,
            padx = 10,
            kwargs = {
                "text": "0/0",
            }
        )

        # 绑定标签页切换事件，以更新页码显示
        self.context.bind_notebook("<<NotebookTabChanged>>", self.update_page_number)

        # 方便其他插件调用
        self.context.update_page_number = self.update_page_number


    def update_page_number(self, event = None) -> None:
        """
        更新页码显示。
        """
        current_tab = self.context.get_current_tab()
        if current_tab and current_tab.total_pages > 0:
            self.page_label.config(
                text=f"{current_tab.page_no + 1}/{current_tab.total_pages}"
            )
        else:
            self.page_label.config(text = "0/0")


    @override
    def run(self) -> None:
        """
        插件执行方法（此处无需特殊处理）。
        """
        pass


    @override
    def unloaded(self) -> None:
        pass
