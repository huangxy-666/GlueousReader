"""
下一页。
"""

from tkinter import ttk
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


    def loaded(self) -> None:
        """
        注册菜单项、快捷键、“下一页”按钮。
        """
        # 注册菜单项、快捷键
        self.context.add_menu_command(
            path=["前往"],
            label="下一页",
            command=self.run,
            accelerator=self.hotkey
        )
        self.context.update_menubar()

        # “下一页”按钮
        next_btn = self.context.add_tool(ttk.Button, text="下一页", command = self.run)

        # 将这个按钮组件添加到 context 中，以便其他插件访问
        self.context.get_next_button = lambda: next_btn


    def run(self) -> None:
        """
        执行下一页操作。
        """
        current_tab = self.context.get_current_tab()
        if current_tab is None:
            return

        # 切换到下一页
        if current_tab.page_down():
            self.context.update_page_number()
        else:
            print("已经是最后一页")


    def unloaded(self) -> None:
        pass
