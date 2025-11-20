"""
AI 配置插件：允许用户配置 AI 模型参数
"""

from dataclasses import dataclass
import os
import subprocess
import tkinter as tk
from tkinter import messagebox, ttk
from typing import Any, Dict, Optional, override

from glueous_plugin import Plugin



def set_windows_env_variable(key, value, scope='user'):
    """
    在 Windows 上设置永久环境变量
    scope: 'user' (用户级) 或 'system' (系统级，需要管理员权限)
    """
    try:
        # 使用 setx 命令
        cmd = ['setx', key, value]
        if scope == 'system':
            cmd.insert(1, '/M')  # 系统级变量需要 /M 参数

        subprocess.run(cmd, check=True, capture_output=True)
        print(f"✅ 成功设置环境变量: {key}={value} (scope: {scope})")
        return True
    except subprocess.CalledProcessError as e:
        print(f"❌ 设置失败: {e.stderr.decode()}")
        return False



@dataclass
class AIConfiguration:
    """
    大模型调用配置数据类
    """
    url: str
    token: str
    model: str
    stream: bool

    def to_dict(self) -> Dict[str, Any]:
        """
        转换为字典格式，方便直接用于API调用
        """
        return {
            "url": self.url,
            "token": self.token,
            "model": self.model,
            "stream": self.stream
        }



class AIConfigDialog(tk.Toplevel):
    """
    大模型配置输入对话框。
    """

    def __init__(self, parent: tk.Tk, title: str = "AI Config", **kwargs: Dict[str, Any]):
        """
        Params:

        - `parent`: 父组件。
        - `title`: 窗口标题。
        - `kwargs`: 初始文本或选项。
        """

        super().__init__(parent)
        self.parent = parent
        self.title(title)
        self.geometry("450x320")
        self.resizable(True, False)

        # 初始化变量
        self.url_var = tk.StringVar(value = kwargs.get("url", ""))
        self.token_var = tk.StringVar(value = kwargs.get("token", ""))
        self.model_var = tk.StringVar(value = kwargs.get("model", ""))
        self.stream_var = tk.BooleanVar(value = kwargs.get("stream", False))

        self.config_result: Optional[AIConfiguration] = None

        # 创建界面
        self._create_widgets()
        self._layout_widgets()

        # 设置模态对话框
        self.transient(parent)
        self.grab_set()
        self.wait_window(self)


    def _create_widgets(self):
        """
        创建所有界面组件。
        """

        # 主框架
        main_frame = ttk.Frame(self, padding="20")
        main_frame.pack(fill=tk.BOTH, expand=True)

        # URL输入框
        self.url_label = ttk.Label(main_frame, text="url:", font=("Arial", 10))
        self.url_entry = ttk.Entry(main_frame, textvariable=self.url_var, width=50, font=("Arial", 10))

        # Token输入框
        self.token_label = ttk.Label(main_frame, text="token:", font=("Arial", 10))
        self.token_entry = ttk.Entry(main_frame, textvariable=self.token_var, width=50, font=("Arial", 10), show="*")

        # Model选择框
        self.model_label = ttk.Label(main_frame, text="model:", font=("Arial", 10))
        self.model_entry = ttk.Entry(main_frame, textvariable=self.model_var, width=50, font=("Arial", 10))

        # Stream单选框
        self.stream_check = tk.Checkbutton(
            main_frame,
            text="stream",
            variable=self.stream_var,
            command=self._on_stream_toggle,
            font=("Arial", 10)
        )

        # 按钮框架
        self.button_frame = ttk.Frame(main_frame)
        self.confirm_button = ttk.Button(self.button_frame, text="确认", command=self._on_confirm, width=12)
        self.cancel_button = ttk.Button(self.button_frame, text="取消", command=self._on_cancel, width=12)


    def _layout_widgets(self):
        """布局所有界面组件"""
        # 使用网格布局
        main_frame = self.url_label.master

        # URL行
        self.url_label.grid(row=0, column=0, sticky="w", pady=(0, 5))
        self.url_entry.grid(row=1, column=0, columnspan=2, sticky="ew", pady=(0, 15))

        # Token行
        self.token_label.grid(row=2, column=0, sticky="w", pady=(0, 5))
        self.token_entry.grid(row=3, column=0, columnspan=2, sticky="ew", pady=(0, 15))

        # Model行
        self.model_label.grid(row=4, column=0, sticky="w", pady=(0, 5))
        self.model_entry.grid(row=5, column=0, columnspan=2, sticky="ew", pady=(0, 15))

        # Stream行
        self.stream_check.grid(row=6, column=0, columnspan=2, sticky="w", pady=(0, 20))

        # 按钮行
        self.button_frame.grid(row=7, column=0, columnspan=2, pady=(10, 0))
        self.confirm_button.pack(side="right", padx=(0, 10))
        self.cancel_button.pack(side="right")

        # 设置列权重
        main_frame.columnconfigure(1, weight=1)


    def _on_stream_toggle(self):
        """流式传输选项切换时的处理"""
        is_stream = self.stream_var.get()
        if is_stream:
            messagebox.showinfo("提示", "已启用流式传输模式\n注意：部分模型可能不支持此功能")


    def _validate_input(self) -> bool:
        """验证用户输入"""
        if not self.url_var.get().strip():
            messagebox.showerror("错误", "请输入 url")
            self.url_entry.focus()
            return False

        if not self.token_var.get().strip():
            messagebox.showerror("错误", "请输入 token")
            self.token_entry.focus()
            return False

        if not self.model_var.get().strip():
            messagebox.showerror("错误", "请输入 model")
            self.model_entry.focus()
            return False

        return True


    def _on_confirm(self):
        """确认按钮点击事件"""
        if self._validate_input():
            self.config_result = AIConfiguration(
                url = self.url_var.get().strip(),
                token = self.token_var.get().strip(),
                model = self.model_var.get().strip(),
                stream = self.stream_var.get()
            )
            self.destroy()


    def _on_cancel(self):
        """取消按钮点击事件"""
        self.destroy()



def ask_AI_configuration(parent: Optional[tk.Tk] = None, **kwargs) -> Optional[AIConfiguration]:
    """
    弹出大模型配置对话框并返回配置
    
    Args:
        parent: 父窗口
        
    Returns:
        包含用户输入配置的LLMConfig对象，用户取消时返回None
    """
    if parent is None:
        parent = tk.Tk()
        parent.withdraw()  # 隐藏主窗口

    dialog = AIConfigDialog(parent, **kwargs)
    return dialog.config_result



class AIConfigurePlugin(Plugin):
    """
    AI 配置插件：允许用户设置大语言模型的参数
    """

    name = "AIConfigurePlugin"
    description = """
# AIConfigurePlugin

- name: AIConfigurePlugin
- author: Jerry
- hotkeys: None
- menu entrance: `工具 → AI配置`

## Function

Allow users to configure parameters for calling large language models, such as `url`, `model`, `token`, etc.

The configuration information will be saved in `ReaderAccess.data` and can be restored after program restart.

Specifically, to protect privacy, the token field will be stored in the environment variable.

## Api

- `context.get_AI_configuration()`: Obtain the user's AI configuration parameters.

## Depend

Python extension library: None

Other plugins: None

## Others

The configuration parameters are saved in JSON format in config/data.json.

The `token` field is saved in the environment variable.
"""

    hotkeys = []

    # 默认配置
    DEFAULT_CONFIGURATION: Dict[str, Any] = {
        "url": "",
        "token": "",
        "model": "",
        "stream": True,
    }

    # 存在 ReaderAccess.data 中的键名
    _DATA_CONFIG_KEY: str = "ai_configuration"

    _ENVIRONMENT_TOKEN_KEY: str = "GLUEOUS_READER_AI_TOKEN"


    def get_AI_configuration(self) -> Dict[str, Any]:
        """
        获取用户的AI配置参数

        Returns:
            Dict[str, Any]: AI配置参数，例如：
            {
                "url": "https://api-inference.modelscope.cn/v1/chat/completions",
                "token": "12345678",
                "model": "Qwen/Qwen3-Coder-30B-A3B-Instruct",
                "stream": True,
            }
        """
        # 从数据中获取配置，如果没有则返回默认配置
        configuration = self.context.data.get(self._DATA_CONFIG_KEY, self.DEFAULT_CONFIGURATION)

        # 从环境变量中读入 token，并加入 configuration 中
        token_from_env = os.environ.get(self._ENVIRONMENT_TOKEN_KEY, "")
        configuration["token"] = token_from_env

        return configuration


    @override
    def loaded(self) -> None:
        """
        插件加载时：注册菜单项，从数据文件恢复配置
        """
        # 注册菜单项
        self.context.add_menu_command(
            path = ["工具"],
            label = "AI配置",
            command = self.run
        )

        # 提供获取配置的方法
        self.context.get_AI_configuration = self.get_AI_configuration


    @override
    def run(self) -> None:
        try:
            # 获取当前配置
            current_configuration = self.get_AI_configuration()

            # 创建配置对话框
            new_configuration: AIConfiguration = ask_AI_configuration(
                parent = self.context._reader.root,
                **current_configuration
            )

            if new_configuration:
                # 验证并保存配置
                self._save_configuration(new_configuration.to_dict())
                messagebox.showinfo("成功", "AI配置已保存")

        except Exception as e:
            messagebox.showerror("错误", f"配置失败: {str(e)}")


    def _save_configuration(self, config: Dict[str, Any]) -> None:
        """
        url、model、stream 保存到 ReaderAccess.data ，token 永久保存到环境变量，保证下次重启程序仍能访问

        Args:
            config: 要保存的配置字典
        """
        # url、model、stream 保存到 ReaderAccess.data
        self.context.data[self._DATA_CONFIG_KEY] = {
            "url": config["url"],
            "model": config["model"],
            "stream": config["stream"]
        }

        # 将 token 永久保存到环境变量中
        set_windows_env_variable(self._ENVIRONMENT_TOKEN_KEY, config["token"], "user")
        os.environ[self._ENVIRONMENT_TOKEN_KEY] = config["token"]


    @override
    def unloaded(self) -> None:
        pass
