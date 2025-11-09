"""
上一页。
"""

from tkinter import ttk
from glueous_plugin import Plugin


class PageUpPlugin(Plugin):
    """
    上一页插件：允许用户通过快捷键或菜单项切换到上一页。
    """

    # 插件信息
    name = "PageUpPlugin"
    description = "切换到上一页，快捷键: PageUp"

    # 快捷键设置
    hotkey = "<Prior>"  # 对应 PageUp 键


    def loaded(self) -> None:
        """
        注册菜单项、快捷键、“上一页”按钮。
        """
        # 注册菜单项、快捷键
        self.context.add_menu_command(
            path=["前往"],
            label="上一页",
            command=self.run,
            accelerator=self.hotkey
        )
        self.context.update_menubar()

        # “上一页”按钮
        prev_btn = self.context.add_tool(ttk.Button, text="上一页", command = self.run)

        # 将这个按钮组件添加到 context 中，以便其他插件访问
        self.context.get_prev_button = lambda: prev_btn


    def run(self) -> None:
        """
        执行上一页操作。
        """
        current_tab = self.context.get_current_tab()
        if current_tab is None:
            return

        # 切换到上一页
        if current_tab.current_page > 0:
            current_tab.current_page -= 1
            current_tab.show_page()
            self.context.update_page_number()
        else:
            print("已经是第一页")


    def unloaded(self) -> None:
        return
