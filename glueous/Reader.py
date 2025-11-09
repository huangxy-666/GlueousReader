from __future__ import annotations

from pathlib import Path
import tkinter as tk
from tkinter import filedialog, messagebox, ttk, Menu
from typing import Any, Dict, List, TYPE_CHECKING
from types import ModuleType

from .ReaderAccess  import ReaderAccess
from .PluginManager import PluginManager

if TYPE_CHECKING:
    from .Tab import Tab


def construct_menu(menu: tk.Menu, menu_structure: List[Dict[str, Any]]) -> None:
    """
    从菜单的字典结构 `menu_structure` 为菜单组件 `menu` 添加内容。

    Params:

    - `menu_structure`: 菜单的字典结构，like:

        ```python
        [
            {
                "type" : "menu",
                "label" : "文件",
                "children": [
                    {
                        "type" : "command",
                        "label" : "新建",
                        "command" : create_new,
                        "accelerator": "Ctrl+N",
                    },
                    {
                        "type" : "separator",
                    },
                    {
                        "type" : "menu",
                        "label" : "打开",
                        "children": [
                            {
                                "type" : "command",
                                "label" : "PDF 文件",
                                "command" : open_pdf,
                                "accelerator": "Ctrl+O",
                            },
                        ],
                    }
                ],
            }
        ]
        ```
    
    Return:

    - tkinter.Menu
    """

    for sublabel in menu_structure:
        if sublabel["type"] == "separator":
            menu.add_separator()
        elif sublabel["type"] == "command":
            menu.add_command(**{k: v for (k, v) in sublabel.items() if (k != "type")})
        elif sublabel["type"] == "menu":
            submenu = tk.Menu(menu, **{k: v for (k, v) in sublabel.items() if (k not in ("type", "children", "label"))})
            construct_menu(submenu, sublabel["children"]) # 递归构造子菜单项
            menu.add_cascade(label = sublabel["label"], menu=submenu)



class Reader:
    """
    主程序类，管理多标签页和全局状态。
    """

    def __init__(self, settings: Dict[str, Any]):
        self.settings: Dict[str, Any] = settings

        # 创建窗口
        self.root = tk.Tk()
        self.root.title(self.settings["window_title"])
        self.root.geometry(f"{self.settings['window_width']}x{self.settings['window_height']}")

        # 创建菜单栏
        self.menubar = tk.Menu(self.root)
        self.menu_structure: List[Dict] = []
        """
        Like:
            [
                {
                    "type"    : "menu",
                    "label"   : "example",
                    "children": [
                        {
                            "type"    : "command"
                            "label"   : "run",
                            "command" : Function,
                        }
                    ],
                }
            ]
        """
        self.update_menubar()
        self.root.config(menu = self.menubar)

        # 创建工具栏
        self.toolbar = ttk.Frame(self.root)
        self.toolbar.pack(side = tk.TOP, fill = tk.X, padx = 5, pady = 5)

        # 创建标签页容器
        self.notebook = ttk.Notebook(self.root)
        self.notebook.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
        self.tabs: List[Tab] = []

        self.access = ReaderAccess(self)
        self.plugin_manager = PluginManager(self.access)
        self.plugin_manager.load_plugins_from_directory(Path(self.settings["plugin_directory_path"]))
        self.plugin_manager.bind_hotkeys()
        self.plugin_manager.loaded()


    def update_menubar(self) -> None:
        """
        根据 self.menu_structure 更新 self.menubar
        """
        self.menubar.delete(0, tk.END)
        construct_menu(self.menubar, self.menu_structure)


    def get_current_tab(self) -> Tab | None:
        """
        获取当前激活的标签页实例。
        """
        if not self.tabs:
            return None

        # 获取当前选中标签页的路径字符串
        current_frame_path = self.notebook.select()
        if not current_frame_path:
            return None

        # 将路径字符串转换为窗口对象
        try:
            current_frame = self.root.nametowidget(current_frame_path)
        except KeyError:
            return None

        # 3. 从标签页列表中找到匹配的 Tab
        for tab in self.tabs:
            if tab.frame == current_frame:
                return tab
        return None


    def mainloop(self) -> None:
        """
        进入主循环。
        """
        self.root.mainloop()
