"""
插件基类。
"""
from __future__ import annotations

from abc import ABC, abstractmethod

from typing import List, TYPE_CHECKING
from types import NoneType

if TYPE_CHECKING:
    from glueous.ReaderAccess import ReaderAccess


class Plugin(ABC):
    """
    插件基类，所有插件都应该是它的基类。

    调用示例：

    ```python
    # When the program starts...
    plugins = {}
    your_plugin = YourPlugin(context)
    plugins[your_plugin.name] = your_plugin
    
    for plugin in plugins.value():
        plugin.loaded()

    # When the plugin is triggered...
    your_plugin.run()

    # When the program is about to exit...
    your_plugin.unloaded()
    ```
    """

    def __init__(self, context: ReaderAccess):
        self.context: ReaderAccess = context
        self._able  : bool = True


    @abstractmethod
    def loaded(self) -> None:
        """
        每次启动程序时被调用。
        """
        raise NotImplementedError()


    @abstractmethod
    def run(self) -> None:
        """
        插件执行的主方法。
        """
        raise NotImplementedError()


    @abstractmethod
    def unloaded(self) -> None:
        """
        每次退出程序时被调用。
        """
        raise NotImplementedError()


    @property
    @abstractmethod
    def name(self) -> str:
        """
        插件名，将被用作插件的唯一标识。
        """
        raise NotImplementedError()


    @property
    def description(self) -> str:
        """
        插件描述，子类可以重载。
        """
        return "plugin"


    @property
    def hotkey(self) -> str | None:
        """
        返回默认的快捷键（ self.hotkeys 的第一个元素）。
        """
        if self.hotkeys:
            return self.hotkeys[0]
        return None


    @property
    def hotkeys(self) -> List[str]:
        """
        能够触发该插件的 run 方法的触发快捷键（可以有多个），子类可以定义，格式同 Tkinter 库的热键触发格式。
        """
        return []


    @property
    def able(self) -> bool:
        """
        是否启用该插件。
        """
        return self._able


    def enable(self) -> None:
        """
        启用该插件。
        """
        self._able = True


    def disable(self) -> None:
        """
        禁用该插件。
        """
        self._able = False
