"""
显示当前页码信息插件
"""

from tkinter import messagebox
from glueous_plugin import Plugin


# 继承 Plugin
class ShowPageInfoPlugin(Plugin):
    """
    显示当前页码和总页数的简单插件
    """

    # 插件唯一标识
    name = "ShowPageInfoPlugin"
    
    # 插件描述
    description = "显示当前页码信息，快捷键: Ctrl+I"
    
    # 快捷键绑定（格式同 Tkinter）
    hotkeys = ["<Control-i>"]

    def loaded(self) -> None:
        """
        插件加载时执行：注册菜单项
        """
        self.context.add_menu_command(
            path = ["工具"],           # 菜单路径
            label = "显示页码信息",     # 菜单项名称
            command = self.run,        # 点击时执行的函数
            accelerator = "Ctrl+I"     # 显示快捷键提示
        )


    def run(self) -> None:
        """
        插件主逻辑：获取并显示当前页码信息
        """
        # 通过 context 获取当前标签页
        current_tab = self.context.get_current_tab()
        
        if current_tab is None:
            # 没有打开的文件
            messagebox.showwarning("提示", "请先打开一个PDF文件")
            return
        
        # 获取页码信息（注意：Tab 类中页码是 0-based 的）
        current_page = current_tab.page_no + 1
        total_pages = current_tab.total_pages
        
        # 显示信息
        messagebox.showinfo(
            "页码信息",
            f"当前页码: {current_page}\n总页数: {total_pages}"
        )


    def unloaded(self) -> None:
        """
        插件卸载时执行（清理资源）
        """
        # 这个简单插件无需清理
        pass