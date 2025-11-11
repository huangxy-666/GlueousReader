"""
用于打开文件的插件。
"""

from tkinter import filedialog, messagebox
import os
from glueous_plugin import Plugin


class OpenPlugin(Plugin):
    """
    打开文件插件：允许用户选择并打开PDF或EPUB文件。
    """

    # 插件信息
    name = "OpenPlugin"
    description = """
# OpenPlugin

- name: OpenPlugin
- author: Jerry
- hotkeys: `Ctrl+O`
- menu entrance: `文件 → 打开`

## Function

Open a file dialog to select and open a PDF or EPUB file in a new tab.

If the file does not exist, an error message will be displayed.

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
    hotkeys = ["<Control-o>"]

    def loaded(self) -> None:
        """
        注册菜单项。
        """
        self.context.add_menu_command(
            path = ["文件"],
            label = "打开",
            command = self.run,
            accelerator = self.hotkey
        )


    def run(self) -> None:
        """
        执行打开文件操作。
        """

        # 打开文件选择对话框
        file_path = filedialog.askopenfilename(
            title="选择要打开的文件",
            filetypes=[
                ("PDF 文件", "*.pdf"),
                ("EPUB 文件", "*.epub"),
                ("所有文件", "*.*")
            ]
        )

        if not file_path:
            return

        # 如果用户选择了文件
        # 检查文件是否存在
        if not os.path.exists(file_path):
            messagebox.showerror("错误", f"文件不存在: {file_path}")
            return

        # 创建新标签页
        self.context.create_tab(file_path)
        self.context.update_page_number()
        self.context.update_page_turning_button()


    def unloaded(self) -> None:
        return
