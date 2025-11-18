"""
翻译选中文本插件：实现翻译 PDF 中选中的文本
"""

import webbrowser
from tkinter import messagebox
import tkinter as tk

from glueous_plugin import Plugin


class TranslatePlugin(Plugin):
    """
    翻译插件：实现在浏览器中翻译 PDF 中选中的文本
    """

    name = "TranslatePlugin"
    description = """
# TranslatePlugin

- name: TranslatePlugin
- author: Jerry
- hotkeys: None
- menu entrance: `选择 → 翻译`

## Function

Translate the selected text from the PDF in browser (using Google Translate).

If no text is selected, nothing will be done.

## Api

None

## Depend

Python extension library: None

Other plugins:
- TabPlugin
- SelectPlugin or DragPlugin
- ContextMenu

## Others

None
"""

    hotkeys = []


    def loaded(self) -> None:
        """
        插件加载时：注册菜单项
        """
        # 添加到顶部菜单栏
        self.context.add_menu_command(
            path = ["选择"],
            label = "翻译",
            command = self.run
        )

        # 添加到上下文菜单
        self.context.context_menu_manager.add_context_menu_command(
            context = self.context.Tab.CANVAS_CONTEXT_NAME,
            path = [],
            label = "翻译",
            command = self.run
        )


    def run(self) -> None:
        """
        执行翻译操作。

        如果没有选中文本，则什么都不做。
        """
        try:
            # 获取选中的文本
            selected_text = self.context.get_selected_text()

            if not selected_text:
                print("没有被选中的文本")
                return

            # 在浏览器中翻译
            translate_url = f"https://translate.google.com/?sl=auto&tl=zh-CN&text={selected_text}"
            webbrowser.open(translate_url)

            print("翻译成功")

        except Exception as e:
            messagebox.showerror("错误", f"翻译失败: {str(e)}")


    def unloaded(self) -> None:
        """
        插件卸载时清理
        """
        pass
