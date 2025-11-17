"""
右键菜单文本操作插件：实现选中文本的搜索、翻译、复制功能
"""

import subprocess
import sys
import threading
import webbrowser
from tkinter import messagebox
import tkinter as tk

from glueous_plugin import Plugin


class TextContextMenuPlugin(Plugin):
    """
    文本右键菜单插件：实现对选中文本的搜索、翻译、复制操作
    """

    name = "TextContextMenuPlugin"
    description = """
# TextContextMenuPlugin

- name: TextContextMenuPlugin
- author: Zhenghongbo
- hotkeys: None (鼠标右键菜单)
- menu entrance: None

## Function

为 PDF 中的选中文本提供右键菜单，支持以下功能：
- 搜索：在浏览器中搜索选中文本（使用必应搜索）
- 翻译：在浏览器中打开翻译页面（使用谷歌翻译）
- 复制：将选中文本复制到剪贴板

## Api

None

## Depend

Python extension library: None

Other plugins:
- TabPlugin
- SelectPlugin 或 DragPlugin
"""

    hotkeys = []

    def __init__(self, context) -> None:
        super().__init__(context)
        self.context_menu = None

    def loaded(self) -> None:
        """
        插件加载时：为所有 Tab 的 canvas 绑定右键菜单事件
        """
        self.context.add_at_notebook_tab_changed_function(self._bind_context_menu_to_current_tab)
        # 为当前标签页绑定
        if self.context.get_current_tab() is not None:
            self._bind_context_menu_to_current_tab()

    def _bind_context_menu_to_current_tab(self, event=None) -> None:
        """
        为当前标签页的画布绑定右键菜单事件
        """
        current_tab = self.context.get_current_tab()
        if current_tab is None:
            return

        canvas = current_tab.canvas
        
        # 绑定右键点击事件
        canvas.bind("<Button-3>", self._on_right_click)

    def _on_right_click(self, event) -> None:
        """
        右键点击事件处理
        """
        current_tab = self.context.get_current_tab()
        if current_tab is None:
            return

        # 检查是否有已选中的文本（由 SelectPlugin 或 DragPlugin 保存）
        if hasattr(current_tab, '_selected_text') and current_tab._selected_text:
            self._show_context_menu(event, current_tab._selected_text)
        else:
            messagebox.showinfo("提示", "请先用 Ctrl+拖动 或 鼠标拖动 选中文本")

    def _show_context_menu(self, event, selected_text) -> None:
        """
        显示右键菜单
        """
        current_tab = self.context.get_current_tab()
        if current_tab is None:
            return

        # 销毁旧菜单
        if self.context_menu:
            self.context_menu.destroy()

        # 创建菜单
        self.context_menu = tk.Menu(current_tab.canvas, tearoff=0)
        
        self.context_menu.add_command(
            label="搜索",
            command=lambda: self._search_text(selected_text)
        )
        
        self.context_menu.add_command(
            label="翻译",
            command=lambda: self._translate_text(selected_text)
        )
        
        self.context_menu.add_command(
            label="复制",
            command=lambda: self._copy_text(selected_text)
        )
        
        # 在点击位置显示菜单
        try:
            self.context_menu.tk_popup(event.x_root, event.y_root)
        finally:
            self.context_menu.grab_release()

    def _search_text(self, selected_text) -> None:
        """
        在浏览器中搜索选中的文本
        """
        if not selected_text:
            messagebox.showwarning("提示", "没有选中文本")
            return
        
        # 使用必应搜索
        search_url = f"https://www.bing.com/search?q={selected_text}"
        webbrowser.open(search_url)

    def _translate_text(self, selected_text) -> None:
        """
        在浏览器中翻译选中的文本
        """
        if not selected_text:
            messagebox.showwarning("提示", "没有选中文本")
            return
        
        # 使用谷歌翻译
        translate_url = f"https://translate.google.com/?sl=auto&tl=zh-CN&text={selected_text}"
        webbrowser.open(translate_url)

    def _copy_text(self, selected_text) -> None:
        """
        复制选中的文本到剪贴板
        """
        if not selected_text:
            messagebox.showwarning("提示", "没有选中文本")
            return
        
        try:
            # 使用 tkinter 的剪贴板
            current_tab = self.context.get_current_tab()
            if current_tab:
                # 清空剪贴板
                current_tab.canvas.clipboard_clear()
                # 复制文本
                current_tab.canvas.clipboard_append(selected_text)
                current_tab.canvas.update()
            
            messagebox.showinfo("成功", "文本已复制到剪贴板")
        except Exception as e:
            messagebox.showerror("错误", f"复制失败: {str(e)}")

    def run(self) -> None:
        """
        插件主方法（右键菜单通过事件触发，无需此方法）
        """
        pass

    def unloaded(self) -> None:
        """
        插件卸载时清理
        """
        if self.context_menu:
            self.context_menu.destroy()
