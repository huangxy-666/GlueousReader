from __future__ import annotations

import importlib.util
from pathlib import Path
from typing import Any, Dict, Iterable, List, Set, cast, TYPE_CHECKING

from glueous_plugin import Plugin
from plugins import plugin_loading_order

if TYPE_CHECKING:
    from .ReaderAccess import ReaderAccess



class PluginManager:
    """
    插件管理器，负责加载和管理插件。
    """

    def __init__(self, context: ReaderAccess):
        self.context = context

        # 存储所有加载的插件实例
        self.plugins: List[Plugin] = []

        # 插件名到插件的映射
        self.name_mapping: Dict[str, Plugin] = {}

        # 快捷键到插件的映射
        self.hotkey_mapping: Dict[str, Plugin] = {}


    def __iter__(self) -> Iterable[Plugin]:
        return iter(self.plugins)


    def __getitem__(self, key) -> Plugin | List[Plugin]:
        """
        - 若输入整数或切片，则调用 `self.plugins` 的 `__getitem__`
        - 若输入字符串，则调用 `self.name_mapping` 的 `__getitem__`
        """
        if isinstance(key, (int, slice)):
            return self.plugins[key]
        if isinstance(key, str):
            return self.name_mapping[key]
        raise TypeError(f"unsupported operand type(s) for []: '{type(key).__name__}' and '{self.__class__.__name__}'")


    def __repr__(self) -> str:
        return f"{self.__class__.__name__}()"


    def __str__(self) -> str:
        return self.__class__.__name__ + str({
            plugin.name: plugin.hotkeys
            for plugin in self.plugins
        })


    def append(self, plugin: Plugin) -> None:
        """
        添加一个插件。
        """
        self.plugins.append(plugin)
        self.name_mapping[plugin.name] = plugin
        for hotkey in plugin.hotkeys:
            self.hotkey_mapping[hotkey] = plugin


    def load_plugins_from_file(self, plugin_file: Path) -> int:
        """
        加载 `plugin_file` 文件中的所有插件， `plugin_file` 文件应为一个 .py 文件。

        “插件”类应该为 `Plugin` 类的子类。

        返回加载成功的插件数目。
        """
        if not plugin_file.is_file():
            raise FileNotFoundError(f"Plugin file not found: {plugin_file}")

        spec = importlib.util.spec_from_file_location(plugin_file.stem, plugin_file)
        if spec is None or spec.loader is None:
            raise ImportError(f"Cannot load plugin from file: {plugin_file}")

        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)

        # 遍历模块中的所有类，找到 Plugin 的子类并实例化
        count = 0
        for attr_name in dir(module):
            attr = getattr(module, attr_name)
            if isinstance(attr, type) and issubclass(attr, Plugin) and attr is not Plugin:
                plugin_instance = attr(self.context)
                self.append(plugin_instance)
                count += 1

        return count


    def load_plugins_from_directory(self, plugin_directory: Path, recursion: bool = True) -> int:
        """
        加载 `plugin_directory` 文件夹中的所有插件， `plugin_directory` 应为一个文件夹。

        “插件”类应该为 `Plugin` 类的子类。

        若 `recursion` 为 True，则递归地加载 `plugin_directory` 的子目录中的插件。

        返回加载成功的插件数目。
        """
        if not plugin_directory.is_dir():
            raise ValueError(f"`{plugin_directory}` is not a directory.")

        count = 0

        # 使用 Path.glob 递归或非递归地查找 .py 文件
        pattern = "**/*.py" if recursion else "*.py"
        for plugin_file in plugin_directory.glob(pattern):
            if plugin_file.name.startswith("_"):  # 跳过以下划线开头的文件
                continue
            count += self.load_plugins_from_file(plugin_file)

        return count


    @staticmethod
    def _call_plugin(plugin: Plugin, method_name: str, /, *args, **kwargs) -> Any:
        """
        安全地调用插件对象 `plugin` 的某个方法 `method_name`。
        """
        try:
            return getattr(plugin, method_name)(*args, **kwargs)
        except Exception as error:
            print(f"{plugin.name}.{method_name}: {error.__class__.__name__}: {error}")
        return None


    def loaded(self) -> None:
        """
        按顺序加载所有插件。
        """
        plugin_names: Set[str] = set(self.name_mapping.keys())

        for plugin_name in plugin_loading_order:
            if plugin_name in plugin_names:
                plugin = self[plugin_name]
                if plugin.able:
                    self._call_plugin(plugin, "loaded")
                plugin_names.remove(plugin_name)

        for plugin_name in plugin_names:
            plugin = self[plugin_name]
            if plugin.able:
                self._call_plugin(plugin, "loaded")


    def run(self, hotkey: str) -> None:
        """
        根据指定的 hotkey 运行插件。
        """
        plugin = self.hotkey_mapping.get(hotkey)
        if plugin and plugin.able:
            self._call_plugin(plugin, "run")


    def unloaded(self) -> None:
        """
        卸下所有插件。
        """
        for plugin in self.plugins:
            if plugin.able:
                self._call_plugin(plugin, "unloaded")


    def bind_hotkeys(self) -> None:
        """
        绑定所有快捷键。
        """
        for hotkey in self.hotkey_mapping:
            self.context.bind_root(hotkey, lambda event, hotkey = hotkey: self.run(hotkey))
