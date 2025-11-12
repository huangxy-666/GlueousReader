"""
此插件实现对页面的放大。
"""

from tkinter import ttk
from typing import override

from glueous_plugin import Plugin


class ZoomInPlugin(Plugin):
    """
    放大插件：允许用户通过快捷键或菜单项放大当前页面。
    """

    # 插件信息
    name = "ZoomInPlugin"
    description = """
# ZoomInPlugin

- name: ZoomInPlugin
- author: Jerry
- hotkeys: `Ctrl++`
- menu entrance: `缩放 → 放大`

## Function

Enlarge the current page.

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
    hotkeys = ["<Control-plus>"]


    @override
    def loaded(self) -> None:
        """
        注册菜单项、快捷键、“放大”按钮。
        """
        # 注册菜单项、快捷键
        self.context.add_menu_command(
            path = ["缩放"],
            label = "放大",
            command = self.run,
            accelerator = self.hotkey
        )

        # “放大”按钮
        zoom_in_btn = self.context.add_tool(
        	ttk.Button,
        	kwargs = {
        		"text": "+",
        		"command": self.run,
        		"width": 2,
        	}
        )

        # 将这个按钮组件添加到 context 中，以便其他插件访问
        self.context.get_zoom_in_button = lambda: zoom_in_btn


    @override
    def run(self) -> None:
        """
        执行放大操作。
        """
        current_tab = self.context.get_current_tab()
        if current_tab is None:
            return

        # 获取当前缩放级别
        current_zoom = current_tab.zoom

        # 获取预设的缩放等级列表
        zoom_levels = self.context.get_setting("zoom_levels", [100])

        # 找到下一个更大的缩放级别
        new_zoom = zoom_levels[-1]  # 默认最大级别
        for level in zoom_levels:
            if level > current_zoom:
                new_zoom = level
                break

        # 更新缩放级别
        current_tab.zoom = new_zoom


    @override
    def unloaded(self) -> None:
        pass
