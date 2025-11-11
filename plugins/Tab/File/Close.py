"""
关闭当前标签页。
"""

from glueous_plugin import Plugin


class ClosePlugin(Plugin):
    """
    关闭当前标签页插件：允许用户关闭当前打开的文件标签页。
    """

    # 插件信息
    name = "ClosePlugin"
    description = "关闭当前标签页，快捷键: Ctrl+W"

    # 快捷键设置
    hotkey = "<Control-w>"

    def loaded(self) -> None:
        """
        注册菜单项。
        """
        self.context.add_menu_command(
            path = ["文件"],
            label = "关闭",
            command = self.run,
            accelerator = self.hotkey
        )


    def run(self) -> None:
        """
        执行关闭当前标签页操作。
        """
        current_tab = self.context.get_current_tab()
        if current_tab is None:
            return

        # 关闭当前标签页
        self.context.close_tab(current_tab)


    def unloaded(self) -> None:
        return
