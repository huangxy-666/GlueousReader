"""
思维导图插件：使用 AI 生成 PDF 文档的思维导图
"""

import asyncio
import os
import subprocess
import tkinter as tk
from tkinter import filedialog, messagebox, ttk
import threading
from typing import Any, Dict, List, Tuple
import webbrowser

from openai import AsyncOpenAI, BadRequestError, OpenAI, RateLimitError
import pyperclip
import tiktoken

from glueous_plugin import Plugin



MIND_MAP_HELP_WEBSITE = "https://github.com/Jerry-Wu-GitHub/GlueousReader/blob/main/docs/MindMap.md"


def show_help_in_browser(event = None) -> None:
    """打开帮助网页"""
    webbrowser.open(MIND_MAP_HELP_WEBSITE)


def check_markmap() -> bool:
    """
    检查 Markmap 是否已正确安装。
    """
    try:
        subprocess.run(['markmap.cmd', '--version'])
    except FileNotFoundError:
        messagebox.showerror("错误", "没有找到 Markmap，可能是因为您没有正确安装 Markmap。")
        show_help_in_browser()
        return False
    return True


def extract_document_text(tab, page_range: Tuple[int, int | float]) -> List[str]:
    """
    提取指定页面范围的文档文本。
    """
    start_page, end_page = page_range
    return [
        tab.doc[i].get_text()
        for i in range(start_page - 1, min(end_page, tab.total_pages))
    ]


def count_tokens(text: str) -> int:
    """
    计算文本的 token 数量。
    """
    try:
        encoding = tiktoken.get_encoding("cl100k_base")
        return len(encoding.encode(text))
    except Exception:
        # 如果无法计算，返回字符数作为估计
        return len(text) // 4


async def _compress_chunk(
    chunk     : str,
    ai_config : Dict[str, Any]
) -> str:
    """
    异步压缩单个文本块
    """
    prompt = f"请压缩以下文本，保留核心信息和逻辑结构，使其更简洁：\n\n{chunk}"

    client = AsyncOpenAI(
        base_url = ai_config["url"],
        api_key  = ai_config["api_key"],
    )

    response = await client.chat.completions.create(
        model    = ai_config["model"],
        messages = [{"role": "user", "content": prompt}],
    )

    return response.choices[0].message.content


def _split_text_into_chunks(texts: List[str], max_tokens: int) -> List[str]:
    """
    将文本分割成适合AI处理的块。
    """
    # 存储结果
    chunks = []
    current_chunk = ""
    current_tokens = 0

    for text in texts:
        # 第一段文本
        tokens = count_tokens(text)
        if not current_chunk:
            current_chunk  = text
            current_tokens = tokens
            continue

        # 检查添加这部分后是否会超过token限制
        if current_tokens + tokens < max_tokens:
            current_chunk  += f"\n{text}"
            current_tokens += tokens
        else:
            chunks.append(current_chunk)
            current_chunk  = text
            current_tokens = tokens

    # 添加最后一个块
    if current_chunk:
        chunks.append(current_chunk.strip())

    return chunks


def _compress_text(texts: List[str], ai_config: Dict[str, Any], label: ttk.Label = None) -> List[str]:
    """
    根据 ai_config["concurrent"] 选择压缩策略。
    """
    chunks = _split_text_into_chunks(
        texts,
        ai_config["max_tokens"] - 32 # 减去 _compress_chunk 已有的 prompt 的 token 数
    )

    # 手动创建和管理事件循环
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)

    if ai_config["concurrent"]:
        # 异步并发
        tasks = [
            _compress_chunk(chunk, ai_config)
            for chunk in chunks
        ]

        try:
            compressed_texts = loop.run_until_complete(asyncio.gather(*tasks))
        finally:
            loop.close()

    else:
        # 不并发
        count = 0
        compressed_texts = []
        for chunk in chunks:
            label.config(text = f"正在压缩文本... ({count} / {len(chunks)})")
            compressed_texts.append(loop.run_until_complete(_compress_chunk(chunk, ai_config)))
            count += 1

    return compressed_texts


def compress_text(texts: List[str], ai_config: Dict[str, Any], fix_tokens: int = 0, label: ttk.Label = None) -> str:
    """
    异步并发调用 AI api，压缩文本以适应token限制。
    """
    tokens_limit = ai_config["max_tokens"] - fix_tokens

    # 压缩所有块
    while sum(map(count_tokens, texts)) > tokens_limit:
        texts = _compress_text(texts, ai_config, label)

    # 合并所有压缩后的文本块
    return "\n".join(texts)



class MindMapPlugin(Plugin):
    """
    思维导图插件：调用 AI API 生成 PDF 文档的思维导图
    """
    name = "MindMapPlugin"

    description = """
# MindMapPlugin

- name: MindMapPlugin
- author: Jerry
- hotkeys: None
- menu entrance: `工具 → AI思维导图`

## Function

Allow users to generate a mind map of the entire document by calling the API of a large language model.

The mind map is fed back to the user in a pop-up browser window, where users can perform operations such as copying and screenshotting.

Users can configure parameters such as the depth and page range of the generated mind map.

When the total number of words in the file exceeds max_tokens, the text needs to be split into chunks (to facilitate asynchronous concurrent acceleration) and compressed by the large model until the word count does not exceed max_tokens.

## Api

None.

## Depend

Python extension library:
- openai
- pyperclip
- tiktoken

Other plugins:
- TabPlugin
- AIConfigurePlugin

## Others

The mind map will be generated in Markdown format and converted to an interactive HTML file using the `markmap` tool.

For large documents, the text will be compressed using AI to fit within token limits before generating the mind map.
"""

    def loaded(self) -> None:
        """
        插件加载时执行：注册菜单项
        """
        # 注册菜单项
        self.context.add_menu_command(
            path = ["工具"],
            label = "AI思维导图",
            command = self.run
        )


    @staticmethod
    def _build_mind_map_prompt(text: str, depth: int) -> str:
        """
        构建生成思维导图的 AI 提示词。
        """
        return f"""
请为以下文档内容生成一个思维导图。要求：
1. 使用能够被 Markmap 转换的 Markdown 格式
2. 仅输出 Markdown 内容，不要有附加的内容
3. 最多 {depth} 层结构
4. 使用原文的语言
5. 突出文档的核心要点和逻辑关系
6. 简洁明了

文档内容：

{text}
"""


    def _show_progress_window(self) -> (tk.Toplevel, ttk.Label):
        """显示进度窗口"""
        progress_window = tk.Toplevel(self.context._reader.root)
        progress_window.title("生成中...")
        progress_window.geometry("300x100")
        progress_window.resizable(False, False)

        # 居中显示
        progress_window.transient(self.context._reader.root)
        progress_window.grab_set()

        label = ttk.Label(progress_window, text = "正在生成思维导图，请稍候...")
        label.pack(expand = True)

        return (progress_window, label)


    @staticmethod
    def _generate_mindmap_text(ai_config: Dict[str, Any], prompt: str) -> str:
        """
        调用 AI API 生成思维导图文本
        """
        client = OpenAI(
            base_url = ai_config["url"],
            api_key  = ai_config["api_key"],
        )

        response = client.chat.completions.create(
            model    = ai_config["model"],
            messages = [{"role": "user", "content": prompt}],
        )

        return response.choices[0].message.content


    def _generate_mindmap(
        self,
        tab,
        ai_config : Dict[str, Any],
        params    : Dict[str, Any],
        progress_window: tk.Toplevel,
        label     : ttk.Label
    ) -> None:
        """
        在后台线程中生成思维导图。
        """
        try:
            # 获取文档文本
            label.config(text = "正在获取文档文本...")
            doc_texts: List[str] = extract_document_text(tab, params["page_range"])

            # 如果文本过长，先进行压缩
            label.config(text = "正在压缩文本...")
            doc_text = compress_text(doc_texts, ai_config, 128, label)

            # 调用AI API
            label.config(text = "正在生成思维导图的结构...")
            prompt = self._build_mind_map_prompt(doc_text, params["depth"])
            mindmap_text = self._generate_mindmap_text(ai_config, prompt).strip()

            # 去掉开头的 ```markdown 和结尾的 ```
            if mindmap_text.startswith("`"):
                mindmap_text = "\n".join(mindmap_text.split("\n")[1:-1])

            # 在主线程中显示结果
            MindmapTextResult(mindmap_text, self.context._reader.root)

        except RateLimitError:
            messagebox.showerror("错误", f"请求过快。您可以在AI配置中取消并发，或者换用可接受 token 数更大的模型。")

        except BadRequestError as error:
            messagebox.showerror("错误", f"生成失败: \n{error.__class__.__name__}: {str(error)}\n这个错误可能是由单次发送太多引起的，您可以尝试在AI配置中降低单次最大发送 token 数。")

        except Exception as error:
            messagebox.showerror("错误", f"生成失败: \n{error.__class__.__name__}: {str(error)}")

        finally:
            # 关闭进度窗口
            progress_window.destroy()


    def run(self) -> None:
        """
        插件主逻辑：调用AI生成思维导图
        """
        # 检查 Markmap 有没有安装
        if not check_markmap():
            return

        # 获取当前标签页
        current_tab = self.context.get_current_tab()
        if current_tab is None:
            messagebox.showwarning("提示", "请先打开一个PDF文件")
            return

        # 获取AI配置
        ai_config = self.context.get_AI_configuration()
        if (not ai_config) or (not ai_config.get("url")) or (not ai_config.get("api_key")) or (not ai_config.get("model")):
            messagebox.showerror("错误", "请先配置AI参数")
            return

        # 创建参数输入对话框
        dialog = MindMapDialog(self.context._reader.root, ai_config)
        params = dialog.get_parameters()

        if not params:  # 用户取消
            return

        # 显示生成中提示
        progress_window, label = self._show_progress_window()

        try:
            # 在新线程中生成思维导图
            thread = threading.Thread(
                target = self._generate_mindmap,
                args = (current_tab, ai_config, params, progress_window, label),
                daemon = True
            )
            thread.start()

        except Exception as e:
            messagebox.showerror("错误", f"生成思维导图失败: {str(e)}")


    def unloaded(self) -> None:
        """
        插件卸载时执行
        """
        pass



class MindMapDialog():

    HELP_WEBSITE = "https://github.com/Jerry-Wu-GitHub/GlueousReader/blob/main/docs/MindMap.md"

    def __init__(self, parent, ai_config: Dict[str, Any]):
        self.parent = parent
        self.ai_config = ai_config
        self.result = None

        # 创建对话框
        self.dialog = tk.Toplevel(parent)
        self.dialog.title("思维导图参数设置")
        self.dialog.geometry("400x300")
        self.dialog.resizable(False, False)

        # 居中显示
        self.dialog.transient(parent)
        self.dialog.grab_set()

        # 初始化变量
        self.depth_var      = tk.StringVar(value = "3")
        self.start_page_var = tk.StringVar(value = "1")
        self.end_page_var   = tk.StringVar(value = "" )

        self._create_widgets()
        self._layout_widgets()

        # 等待对话框关闭
        self.dialog.wait_window()


    def _create_widgets(self):
        """创建界面组件"""
        # 主框架
        main_frame = ttk.Frame(self.dialog, padding="20")
        main_frame.pack(fill=tk.BOTH, expand=True)

        # 深度设置
        depth_frame = ttk.Frame(main_frame)
        depth_frame.pack(fill=tk.X, pady=(0, 15))

        ttk.Label(depth_frame, text="思维导图深度:").pack(side=tk.LEFT)
        depth_spinbox = ttk.Spinbox(
            depth_frame,
            from_=1,
            to=10,
            width=10,
            textvariable=self.depth_var
        )
        depth_spinbox.pack(side=tk.RIGHT)

        # 页面范围设置
        page_frame = ttk.LabelFrame(main_frame, text="页面范围", padding="10")
        page_frame.pack(fill=tk.X, pady=(0, 15))

        ttk.Label(page_frame, text="起始页:").grid(row=0, column=0, sticky=tk.W, pady=5)
        start_spinbox = ttk.Spinbox(
            page_frame,
            from_=1,
            to=9999,
            width=10,
            textvariable=self.start_page_var
        )
        start_spinbox.grid(row=0, column=1, sticky=tk.E, pady=5)

        ttk.Label(page_frame, text="结束页:").grid(row=1, column=0, sticky=tk.W, pady=5)
        end_spinbox = ttk.Spinbox(
            page_frame,
            from_=1,
            to=9999,
            width=10,
            textvariable=self.end_page_var
        )
        end_spinbox.grid(row=1, column=1, sticky=tk.E, pady=5)
        ttk.Label(page_frame, text="(留空表示到最后一页)").grid(row=2, column=0, columnspan=2, sticky=tk.W, pady=(5, 0))

        # 按钮框架
        button_frame = ttk.Frame(main_frame)
        button_frame.pack(fill=tk.X, pady=(20, 0))

        self.cancel_button = ttk.Button(button_frame, text="取消", command=self._on_cancel)
        self.cancel_button.pack(side=tk.RIGHT)

        self.ok_button = ttk.Button(button_frame, text="确定", command=self._on_ok)
        self.ok_button.pack(side=tk.RIGHT, padx=(10, 0))

        # 链接标签（蓝色、下划线）
        self.help_link = tk.Label(
            main_frame,
            text   = "How to configure?",
            fg     = "blue",  # 文字颜色：蓝色
            cursor = "hand2",  # 鼠标悬停时显示“手”形指针
            font   = ("SimHei", 10)
        )
        self.help_link.config(state = "normal")  # 确保标签可交互

        # 绑定点击事件（左键点击触发 self.help 函数）
        self.help_link.bind("<Button-1>", show_help_in_browser)
        self.help_link.pack(fill=tk.X, pady=(20, 0))


    def _layout_widgets(self):
        """布局界面组件"""
        pass  # 在_create_widgets中已完成布局


    def _on_ok(self):
        """确定按钮点击事件"""
        try:
            depth = int(self.depth_var.get())
            start_page = int(self.start_page_var.get())

            end_page_text = self.end_page_var.get()
            end_page = int(end_page_text) if end_page_text else None

            if end_page and start_page > end_page:
                messagebox.showerror("错误", "起始页不能大于结束页")
                return

            self.result = {
                "depth": depth,
                "page_range": (start_page, end_page or float('inf'))
            }
            self.dialog.destroy()

        except ValueError:
            messagebox.showerror("错误", "请输入有效的数字")


    def _on_cancel(self):
        """取消按钮点击事件"""
        self.result = None
        self.dialog.destroy()


    def get_parameters(self):
        """获取用户设置的参数"""
        return self.result



class MindmapTextResult():
    """
    用于显示、编辑、保存和生成思维导图的文本结果。
    """

    DEFAULT_FILENAME = "untitled_mindmap"

    INVALID_FILENAME_CHARS = ['\\', '/', ':', '*', '?', '"', '<', '>', '|']

    def __init__(self, mindmap_text: str, parent):
        self.parent = parent
        self.text_widget = None
        self._create_widgets(mindmap_text)


    @property
    def mindmap_text(self) -> str:
        """
        返回思维导图 Markdown 文档。
        """
        if self.text_widget is None:
            return ""
        # 从Text组件获取所有内容，并去除末尾可能的空字符
        return self.text_widget.get('1.0', tk.END).strip()


    def _create_widgets(self, mindmap_text: str) -> None:
        """
        显示思维导图文本结果，并创建所有相关控件。
        """
        result_window = tk.Toplevel(self.parent)
        result_window.title("思维导图结构")
        result_window.geometry("1200x800")

        # 文本框上方的提示文字
        tip_frame = ttk.Frame(result_window)
        tip_frame.pack(fill=tk.X, padx=10, pady=(10, 5)) # 调整边距，使其位于text_frame上方

        tip_label = ttk.Label(
            tip_frame,
            text="💡你可以直接在下面修改思维导图的结构和内容：",
            font=("SimSun", 12), # 使用宋体，斜体
            foreground="#404040" # 灰色文字
        )
        tip_label.pack(anchor="w") # 左对齐

        # 创建文本框和滚动条
        text_frame = ttk.Frame(result_window)
        text_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=5)

        scrollbar = ttk.Scrollbar(text_frame)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)

        self.text_widget = tk.Text(text_frame, wrap=tk.WORD, yscrollcommand=scrollbar.set, font=("SimSun", 12))
        self.text_widget.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)

        scrollbar.config(command=self.text_widget.yview)

        # 插入思维导图文本
        self.text_widget.insert(tk.END, mindmap_text)

        # 添加按钮框架
        button_frame = ttk.Frame(result_window)
        button_frame.pack(fill=tk.X, padx=10, pady=(5, 10))

        # 按钮顺序：Generate -> Save -> Copy

        # Copy 按钮
        copy_button = ttk.Button(
            button_frame,
            text="复制",
            command=self._copy_to_clipboard
        )
        copy_button.pack(side=tk.RIGHT, padx=5)

        # Save 按钮
        save_button = ttk.Button(
            button_frame,
            text="保存",
            command=self.save
        )
        save_button.pack(side=tk.RIGHT, padx=5)

        # Generate 按钮
        generate_button = ttk.Button(
            button_frame,
            text="生成！",
            command=self.md_to_interactive_map
        )
        generate_button.pack(side=tk.RIGHT, padx=5)


    def _copy_to_clipboard(self) -> bool:
        """
        将 `self.mindmap_text` 复制到系统剪贴板。
        """
        try:
            pyperclip.copy(self.mindmap_text)
            messagebox.showinfo("成功", "已复制到剪贴板")
            return True
        except Exception as error:
            messagebox.showerror("错误", f"复制失败：{error}")
        return False


    @staticmethod
    def _get_title(markdown_text: str) -> str:
        """
        从 markdown_text 中提取标题（H1）
        """
        title = ""
        lines = markdown_text.splitlines()
        for line in lines:
            stripped_line = line.strip()
            if stripped_line.startswith('# '):
                # 提取 # 后面的文字
                title = stripped_line[2:].strip()
                if title:
                    break
        return title


    def _get_initial_filename(self) -> str:
        # 尝试从内容中提取标题（H1）作为默认文件名
        filename = self._get_title(self.mindmap_text) or self.DEFAULT_FILENAME
        # 替换文件名中不能包含的非法字符
        for char in self.INVALID_FILENAME_CHARS:
            filename = filename.replace(char, '_')
        return filename


    def save(self):
        """
        将 `self.mindmap_text` 保存为 Markdown 文档。
        """
        if not self.mindmap_text:
            messagebox.showwarning("警告", "没有可保存的内容。")
            return

        # 弹出保存文件对话框
        file_path = filedialog.asksaveasfilename(
            parent = self.parent,
            title = "保存思维导图为 Markdown 文档",
            defaultextension = ".md",
            filetypes = [("Markdown 文件", "*.md"), ("所有文件", "*.*")],
            initialfile = self._get_initial_filename()
        )

        if not file_path:
            return

        try:
            with open(file_path, 'w', encoding='utf-8') as file:
                file.write(self.mindmap_text)
            messagebox.showinfo("成功", f"文件已成功保存到:\n{file_path}")
        except Exception as e:
            messagebox.showerror("错误", f"保存文件失败: {e}")


    def md_to_interactive_map(self):
        """
        生成按钮的回调方法。

        从 Markdown 文档生成思维导图。
        """
        if not self.mindmap_text:
            messagebox.showwarning("警告", "没有可生成的内容。")
            return

        initial_filename = self._get_initial_filename()

        # 弹出保存文件对话框
        output_file_path = filedialog.asksaveasfilename(
            parent = self.parent,
            title = "保存思维导图为 HTML 格式",
            defaultextension = ".html",
            filetypes = [("HTML 文件", "*.html"), ("所有文件", "*.*")],
            initialfile = initial_filename
        )

        if not output_file_path:
            return

        os.makedirs("temp", exist_ok = True)
        md_file = os.path.abspath(f"temp/{initial_filename}.md")
        with open(md_file, mode = "w", encoding = "utf-8") as file:
            file.write(self.mindmap_text)

        # print("markmap.cmd", md_file, '-o', output_file_path)

        try:
            subprocess.run(['markmap.cmd', md_file, '-o', output_file_path])
            messagebox.showinfo("成功", f"文件已成功保存到:\n{output_file_path}")
        except Exception as error:
            messagebox.showerror("错误", f"保存文件失败: {error}")

        os.remove(md_file)
