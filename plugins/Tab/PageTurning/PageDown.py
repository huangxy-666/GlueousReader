"""
下一页。
"""

from tkinter import ttk
from typing import override
from types import MethodType

from glueous import ReaderAccess
from glueous_plugin import Plugin


class PageDownPlugin(Plugin):
    """
    下一页插件：允许用户通过快捷键或菜单项切换到下一页。
    """

    # 插件信息
    name = "PageDownPlugin"
    description = "切换到下一页，快捷键: PageDown"

    # 快捷键设置
    hotkey = "<Next>"  # 对应 PageDown 键


    @staticmethod
    def update_page_turning_button(access: ReaderAccess, event = None) -> None:
        """
        更新 prev_button 和 next_button 的启用/禁用状态。
        """
        # 获取“上一页”和“下一页”按钮
        prev_button = access.get_prev_button()
        next_button = access.get_next_button()

        current_tab = access.get_current_tab()
        if current_tab is None:
            prev_button.config(state = "disabled")
            next_button.config(state = "disabled")
            return

        # 检查当前页码并更新按钮状态
        if current_tab.page_no <= 0:
            prev_button.config(state = "disabled")
        else:
            prev_button.config(state = "normal")

        if current_tab.page_no >= current_tab.total_pages - 1:
            next_button.config(state = "disabled")
        else:
            next_button.config(state = "normal")


    @override
    def loaded(self) -> None:
        """
        注册菜单项、快捷键、“下一页”按钮。
        """
        # 注册菜单项、快捷键
        self.context.add_menu_command(
            path = ["前往"],
            label = "下一页",
            command = self.run,
            accelerator = self.hotkey
        )

        # “下一页”按钮
        next_btn = self.context.add_tool(
            ttk.Button,
            kwargs = {
                "text": "→",
                "command": self.run,
                "width": 3,
            }
        )

        # 将这个按钮组件添加到 context 中，以便其他插件访问
        self.context.get_next_button = lambda: next_btn
        self.context.update_page_turning_button = MethodType(self.update_page_turning_button, self.context)

        # 绑定标签页切换事件，以更新按钮显示
        self.context.bind_notebook("<<NotebookTabChanged>>", self.context.update_page_turning_button)


    @override
    def run(self) -> None:
        """
        执行下一页操作。
        """
        current_tab = self.context.get_current_tab()
        if current_tab is None:
            return

        # 切换到下一页
        if current_tab.page_no < current_tab.total_pages - 1:
            current_tab.page_no += 1
            current_tab.show_page()
            self.context.update_page_number()
            self.context.update_page_turning_button()
        else:
            print("已经是最后一页")


    @override
    def unloaded(self) -> None:
        pass
