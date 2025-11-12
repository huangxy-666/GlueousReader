"""
此插件实现对页面的缩小。
"""

from tkinter import ttk
from typing import override

from glueous_plugin import Plugin


class ZoomOutPlugin(Plugin):
    """
    缩小插件：允许用户通过快捷键或菜单项缩小当前页面。
    """

    # 插件信息
    name = "ZoomOutPlugin"
    description = """
# ZoomOutPlugin

- name: ZoomOutPlugin
- author: Jerry
- hotkeys: `Ctrl+-`
- menu entrance: `缩放 → 缩小`

## Function

Shrink the current page.

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
    hotkeys = ["<Control-minus>"]


    @override
    def loaded(self) -> None:
        """
        注册菜单项、快捷键、“缩小”按钮。
        """
        # 注册菜单项、快捷键
        self.context.add_menu_command(
            path = ["缩放"],
            label = "缩小",
            command = self.run,
            accelerator = self.hotkey
        )

        # “缩小”按钮
        zoom_out_btn = self.context.add_tool(
            ttk.Button,
            kwargs = {
                "text": "-",
                "command": self.run,
                "width": 2,
            }
        )

        # 将这个按钮组件添加到 context 中，以便其他插件访问
        self.context.get_zoom_out_button = lambda: zoom_out_btn


    @override
    def run(self) -> None:
        """
        执行缩小操作。
        """
        current_tab = self.context.get_current_tab()
        if current_tab is None:
            return

        # 获取当前缩放级别
        current_zoom = current_tab.zoom

        # 获取预设的缩放等级列表
        zoom_levels = self.context.get_setting("zoom_levels", [100])

        # 找到下一个更小的缩放级别
        new_zoom = zoom_levels[0]  # 默认最小级别
        for level in reversed(zoom_levels):
            if level < current_zoom:
                new_zoom = level
                break

        # 更新缩放级别
        current_tab.zoom = new_zoom


    @override
    def unloaded(self) -> None:
        pass
