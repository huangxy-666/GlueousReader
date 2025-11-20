# AIConfigure

你需要完成 `AIConfigurePlugin` 插件。这是为其他 AI 功能提供配置参数的基础插件。

## Function

用户可以通过点击菜单栏中的一个命令来设置自己要调用的大语言模型（用 `openai` 库提供的接口）参数（如 url 、 model 、 token 等参数）。

> [!NOTE]
>
> 给用户以充足的自由度。

用户配置好了之后，将配置进行 JSON 序列化，并存入 `ReaderAccess.data` ，每次启动时读取。

## API

你需要为 `ReaderAccess` 添加方法：

- `get_AI_configuration()` ：返回用户的 AI 配置。返回示例：

    ```python
    {
        "url": "https://api-inference.modelscope.cn/v1/chat/completions",
        "token": "12345678",
        "model": "Qwen/Qwen3-Coder-30B-A3B-Instruct",
        "stream": True,
    }
    ```