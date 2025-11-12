"""
上一页。
"""

from tkinter import ttk
from typing import override

from glueous_plugin import Plugin


class PageUpPlugin(Plugin):
    """
    上一页插件：允许用户通过快捷键或菜单项切换到上一页。
    """

    # 插件信息
    name = "PageUpPlugin"
    description = """
# PageUpPlugin

- name: PageUpPlugin
- author: Jerry
- hotkeys: `PageUp`
- menu entrance: `前往 → 上一页`

## Function

Switch to the previous page.

When the first page is reached, a prompt message "已经是第一页" will be displayed in the console.

## Api

- `context.get_prev_button()`: Get the 'Previous Page' button component.

## Depend

Python extension library: None

Other plugins:
- TabPlugin
- PageNoPlugin

## Others

Page number calculation: 'Tab.page_no' is a 0-based index.
"""

    # 快捷键设置
    hotkeys = ["<Prior>"]  # 对应 PageUp 键


    @override
    def loaded(self) -> None:
        """
        注册菜单项、快捷键、“上一页”按钮。
        """
        # 注册菜单项、快捷键
        self.context.add_menu_command(
            path = ["前往"],
            label = "上一页",
            command = self.run,
            accelerator = self.hotkey
        )

        # “上一页”按钮
        prev_btn = self.context.add_tool(
            ttk.Button,
            kwargs = {
                "text": "←",
                "command": self.run,
                "width": 3,
            }
        )

        # 将这个按钮组件添加到 context 中，以便其他插件访问
        self.context.get_prev_button = lambda: prev_btn


    @override
    def run(self) -> None:
        """
        执行上一页操作。
        """
        current_tab = self.context.get_current_tab()
        if current_tab is None:
            return

        # 切换到上一页
        if current_tab.page_no > 0:
            current_tab.page_no -= 1
            current_tab.render_page()
            self.context.update_page_number()
            self.context.update_page_turning_button()
        else:
            print("已经是第一页")


    @override
    def unloaded(self) -> None:
        pass
