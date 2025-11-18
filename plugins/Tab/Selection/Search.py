"""
搜索选中文本插件：实现搜索 PDF 中选中的文本
"""

import webbrowser
from tkinter import messagebox
import tkinter as tk

from glueous_plugin import Plugin


class SearchPlugin(Plugin):
    """
    搜索插件：实现在浏览器中搜索 PDF 中选中的文本
    """

    name = "SearchPlugin"
    description = """
# SearchPlugin

- name: SearchPlugin
- author: Jerry
- hotkeys: None
- menu entrance: `选择 → 搜索`

## Function

Search the selected text from the PDF in browser (using Bing search).

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
            label = "搜索",
            command = self.run
        )

        # 添加到上下文菜单
        self.context.context_menu_manager.add_context_menu_command(
            context = self.context.Tab.CANVAS_CONTEXT_NAME,
            path = [],
            label = "搜索",
            command = self.run
        )


    def run(self) -> None:
        """
        执行搜索操作。

        如果没有选中文本，则什么都不做。
        """
        try:
            # 获取选中的文本
            selected_text = self.context.get_selected_text()

            if not selected_text:
                print("没有被选中的文本")
                return

            # 在浏览器中搜索
            search_url = f"https://www.bing.com/search?q={selected_text}"
            webbrowser.open(search_url)

            print("搜索成功")

        except Exception as e:
            messagebox.showerror("错误", f"搜索失败: {str(e)}")


    def unloaded(self) -> None:
        """
        插件卸载时清理
        """
        pass
