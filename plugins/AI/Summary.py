"""
AI 总结插件：使用大语言模型生成文档或选中区域的总结
"""

import tkinter as tk
from tkinter import messagebox, ttk, scrolledtext, filedialog
from typing import Any, Dict, Optional, override
import threading

try:
    from openai import OpenAI
except ImportError:
    OpenAI = None

from glueous_plugin import Plugin


class SummaryResultDialog(tk.Toplevel):
    """
    总结结果显示对话框，支持复制和保存
    """
    
    def __init__(self, parent: tk.Tk, summary_text: str, title: str = "AI 总结"):
        super().__init__(parent)
        self.parent = parent
        self.title(title)
        self.geometry("600x400")
        self.summary_text = summary_text
        
        # 创建界面
        self._create_widgets()
        self._layout_widgets()
        
        # 设置模态对话框
        self.transient(parent)
        self.grab_set()
    
    def _create_widgets(self):
        """创建界面组件"""
        # 主框架
        self.main_frame = ttk.Frame(self, padding="10")
        
        # 文本显示区域
        self.text_label = ttk.Label(self.main_frame, text="总结内容：", font=("Arial", 10))
        self.text_area = scrolledtext.ScrolledText(
            self.main_frame,
            wrap=tk.WORD,
            width=70,
            height=15,
            font=("Arial", 10)
        )
        self.text_area.insert("1.0", self.summary_text)
        self.text_area.config(state=tk.NORMAL)  # 允许编辑（用于复制）
        
        # 按钮框架
        self.button_frame = ttk.Frame(self.main_frame)
        self.copy_button = ttk.Button(self.button_frame, text="复制", command=self._on_copy, width=12)
        self.save_button = ttk.Button(self.button_frame, text="保存", command=self._on_save, width=12)
        self.close_button = ttk.Button(self.button_frame, text="关闭", command=self.destroy, width=12)
    
    def _layout_widgets(self):
        """布局界面组件"""
        # 主框架
        self.main_frame.pack(fill=tk.BOTH, expand=True)
        
        # 标签
        self.text_label.pack(anchor="w", pady=(0, 5))
        
        # 文本区域
        self.text_area.pack(fill=tk.BOTH, expand=True, pady=(0, 10))
        
        # 按钮
        self.button_frame.pack(fill=tk.X)
        self.close_button.pack(side=tk.RIGHT, padx=(5, 0))
        self.save_button.pack(side=tk.RIGHT, padx=(5, 0))
        self.copy_button.pack(side=tk.RIGHT, padx=(5, 0))
    
    def _on_copy(self):
        """复制文本到剪贴板"""
        try:
            text = self.text_area.get("1.0", tk.END).strip()
            if text:
                self.clipboard_clear()
                self.clipboard_append(text)
                messagebox.showinfo("成功", "已复制到剪贴板")
            else:
                messagebox.showwarning("提示", "没有可复制的内容")
        except Exception as e:
            messagebox.showerror("错误", f"复制失败: {str(e)}")
    
    def _on_save(self):
        """保存文本到文件"""
        try:
            text = self.text_area.get("1.0", tk.END).strip()
            if not text:
                messagebox.showwarning("提示", "没有可保存的内容")
                return
            
            file_path = filedialog.asksaveasfilename(
                title="保存总结",
                defaultextension=".txt",
                filetypes=[("文本文件", "*.txt"), ("所有文件", "*.*")]
            )
            
            if file_path:
                with open(file_path, "w", encoding="utf-8") as f:
                    f.write(text)
                messagebox.showinfo("成功", f"已保存到: {file_path}")
        except Exception as e:
            messagebox.showerror("错误", f"保存失败: {str(e)}")


class SummaryLengthDialog(tk.Toplevel):
    """
    总结长度配置对话框
    """
    
    # 预设的长度选项
    LENGTH_OPTIONS = [
        ("简短", "short"),
        ("中等", "medium"),
        ("详细", "detailed"),
    ]
    
    def __init__(self, parent: tk.Tk, current_length: str = "medium"):
        super().__init__(parent)
        self.parent = parent
        self.title("配置总结长度")
        self.geometry("300x200")
        self.result: Optional[str] = None
        
        # 当前选择
        self.length_var = tk.StringVar(value=current_length)
        
        # 创建界面
        self._create_widgets()
        self._layout_widgets()
        
        # 设置模态对话框
        self.transient(parent)
        self.grab_set()
        self.wait_window(self)
    
    def _create_widgets(self):
        """创建界面组件"""
        main_frame = ttk.Frame(self, padding="20")
        main_frame.pack(fill=tk.BOTH, expand=True)
        
        # 说明标签
        label = ttk.Label(main_frame, text="选择总结长度：", font=("Arial", 10))
        
        # 单选按钮
        self.radio_frame = ttk.Frame(main_frame)
        for label_text, value in self.LENGTH_OPTIONS:
            radio = ttk.Radiobutton(
                self.radio_frame,
                text=label_text,
                variable=self.length_var,
                value=value
            )
            radio.pack(anchor="w", pady=5)
        
        # 按钮
        button_frame = ttk.Frame(main_frame)
        self.confirm_button = ttk.Button(button_frame, text="确认", command=self._on_confirm, width=10)
        self.cancel_button = ttk.Button(button_frame, text="取消", command=self._on_cancel, width=10)
        
        self.label = label
        self.button_frame = button_frame
    
    def _layout_widgets(self):
        """布局界面组件"""
        main_frame = self.label.master
        
        self.label.pack(anchor="w", pady=(0, 10))
        self.radio_frame.pack(fill=tk.X, pady=(0, 20))
        self.button_frame.pack(fill=tk.X)
        self.confirm_button.pack(side=tk.RIGHT, padx=(5, 0))
        self.cancel_button.pack(side=tk.RIGHT)
    
    def _on_confirm(self):
        """确认按钮"""
        self.result = self.length_var.get()
        self.destroy()
    
    def _on_cancel(self):
        """取消按钮"""
        self.result = None
        self.destroy()


class SummaryPlugin(Plugin):
    """
    AI 总结插件：使用大语言模型生成文档或选中区域的总结
    """
    
    name = "SummaryPlugin"
    description = """
# SummaryPlugin

- name: SummaryPlugin
- author: Glueous Reader
- hotkeys: None
- menu entrance: `工具 → AI总结`, `工具 → 配置总结长度`

## Function

When the user selects "AI总结" from the menu bar, call the large language model API to generate a summary of the selected area or the entire document.

- If text is selected, generate a summary of the selected area.
- If no text is selected, generate a summary of the entire document.

Display the AI-generated summary in a popup window, where users can copy, save, etc.

Users can configure the summary length in the menu bar.

## Api

None

## Depend

Python extension library:
- openai

Other plugins:
- TabPlugin
- AIConfigurePlugin
- SelectPlugin or DragPlugin (for get_selected_text)

## Others

The summary length configuration is saved in ReaderAccess.data.
"""
    
    hotkeys = []
    
    # 总结长度提示词映射
    LENGTH_PROMPTS = {
        "short": "请用简短的语言（50-100字）总结以下内容：",
        "medium": "请用中等长度的语言（200-300字）总结以下内容：",
        "detailed": "请用详细的语言（500-800字）总结以下内容：",
    }
    
    # 默认总结长度
    DEFAULT_LENGTH = "medium"
    
    # 存储在 ReaderAccess.data 中的键名
    _DATA_LENGTH_KEY: str = "summary_length"
    
    def __init__(self, context):
        super().__init__(context)
        if OpenAI is None:
            print("警告：未安装 openai 库，请运行：pip install openai")
            self.disable()
    
    def get_summary_length(self) -> str:
        """
        获取用户配置的总结长度
        
        Returns:
            str: 总结长度，"short", "medium", 或 "detailed"
        """
        return self.context.data.get(self._DATA_LENGTH_KEY, self.DEFAULT_LENGTH)
    
    def set_summary_length(self, length: str) -> None:
        """
        设置总结长度
        
        Args:
            length: 总结长度，"short", "medium", 或 "detailed"
        """
        if length in self.LENGTH_PROMPTS:
            self.context.data[self._DATA_LENGTH_KEY] = length
    
    def get_text_to_summarize(self) -> str:
        """
        获取需要总结的文本
        
        Returns:
            str: 选中文本或整个文档的文本
        """
        # 尝试获取选中文本
        try:
            selected_text = self.context.get_selected_text()
            if selected_text and selected_text.strip():
                return selected_text.strip()
        except Exception as e:
            print(f"获取选中文本失败: {e}")
        
        # 如果没有选中文本，获取整个文档的文本
        current_tab = self.context.get_current_tab()
        if current_tab is None or current_tab.doc is None:
            return ""
        
        # 遍历所有页面获取文本
        all_text = []
        for page in current_tab.doc:
            try:
                page_text = page.get_text()
                if page_text:
                    all_text.append(page_text)
            except Exception as e:
                print(f"获取第 {page.number + 1} 页文本失败: {e}")
        
        return "\n\n".join(all_text)
    
    def call_ai_api(self, text: str, length: str) -> str:
        """
        调用 AI API 生成总结
        
        Args:
            text: 要总结的文本
            length: 总结长度
            
        Returns:
            str: AI 生成的总结
        """
        # 获取 AI 配置
        config = self.context.get_AI_configuration()
        
        if not config.get("url") or not config.get("token") or not config.get("model"):
            raise ValueError("AI 配置不完整，请先在'工具 → AI配置'中配置")
        
        # 构建提示词
        prompt = self.LENGTH_PROMPTS.get(length, self.LENGTH_PROMPTS["medium"])
        full_prompt = f"{prompt}\n\n{text}"
        
        # 创建 OpenAI 客户端
        client = OpenAI(
            api_key=config["token"],
            base_url=config["url"]
        )
        
        # 调用 API
        try:
            response = client.chat.completions.create(
                model=config["model"],
                messages=[
                    {"role": "user", "content": full_prompt}
                ],
                stream=config.get("stream", False)
            )
            
            # 处理响应
            if config.get("stream", False):
                # 流式响应
                summary = ""
                for chunk in response:
                    if chunk.choices[0].delta.content:
                        summary += chunk.choices[0].delta.content
                return summary
            else:
                # 非流式响应
                return response.choices[0].message.content
                
        except Exception as e:
            raise Exception(f"调用 AI API 失败: {str(e)}")
    
    def generate_summary(self) -> None:
        """
        生成总结的主方法
        """
        # 检查是否有文档打开
        current_tab = self.context.get_current_tab()
        if current_tab is None:
            messagebox.showwarning("提示", "请先打开一个文档")
            return
        
        # 获取要总结的文本
        try:
            text = self.get_text_to_summarize()
            if not text or not text.strip():
                messagebox.showwarning("提示", "没有可总结的内容")
                return
        except Exception as e:
            messagebox.showerror("错误", f"获取文本失败: {str(e)}")
            return
        
        # 获取总结长度
        length = self.get_summary_length()
        
        # 显示进度提示
        progress_window = tk.Toplevel(self.context._reader.root)
        progress_window.title("生成总结中...")
        progress_window.geometry("300x100")
        progress_window.transient(self.context._reader.root)
        progress_window.grab_set()  # 设置为模态窗口
        progress_label = ttk.Label(progress_window, text="正在调用 AI 生成总结，请稍候...")
        progress_label.pack(pady=20)
        progress_window.update()
        
        # 在新线程中调用 AI API（避免阻塞 UI）
        summary_result = [None]
        error_result = [None]
        finished = [False]
        
        def on_complete():
            """在主线程中处理结果"""
            progress_window.destroy()
            if error_result[0]:
                messagebox.showerror("错误", error_result[0])
            elif summary_result[0] is None:
                messagebox.showerror("错误", "生成总结失败")
            else:
                # 显示结果
                SummaryResultDialog(self.context._reader.root, summary_result[0], "AI 总结")
        
        def call_api():
            """在子线程中调用 API"""
            try:
                summary = self.call_ai_api(text, length)
                summary_result[0] = summary
            except Exception as e:
                error_result[0] = str(e)
            finally:
                finished[0] = True
                # 在主线程中执行回调
                self.context._reader.root.after(0, on_complete)
        
        thread = threading.Thread(target=call_api, daemon=True)
        thread.start()
        
        # 设置超时检查
        def timeout_check():
            if not finished[0]:
                finished[0] = True
                error_result[0] = "生成总结超时（超过60秒）"
                self.context._reader.root.after(0, on_complete)
        
        self.context._reader.root.after(60000, timeout_check)  # 60秒超时
    
    def configure_length(self) -> None:
        """
        配置总结长度
        """
        current_length = self.get_summary_length()
        dialog = SummaryLengthDialog(self.context._reader.root, current_length)
        
        if dialog.result:
            self.set_summary_length(dialog.result)
            # 创建长度选项的字典映射
            length_dict = {value: label for label, value in SummaryLengthDialog.LENGTH_OPTIONS}
            length_name = length_dict.get(dialog.result, dialog.result)
            messagebox.showinfo("成功", f"总结长度已设置为: {length_name}")
    
    @override
    def loaded(self) -> None:
        """
        插件加载时：注册菜单项
        """
        # 注册菜单项
        self.context.add_menu_command(
            path=["工具"],
            label="AI总结",
            command=self.generate_summary
        )
        
        self.context.add_menu_command(
            path=["工具"],
            label="配置总结长度",
            command=self.configure_length
        )
    
    @override
    def run(self) -> None:
        """插件执行方法"""
        self.generate_summary()
    
    @override
    def unloaded(self) -> None:
        """插件卸载时执行（无需清理）"""
        pass

