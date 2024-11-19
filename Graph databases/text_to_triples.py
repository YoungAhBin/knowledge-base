import os
from openai import OpenAI

def text_to_triples(prompt, api_key=None):
    """
    提取文本中的三元组关系（主语、谓语、宾语）。

    参数：
    - prompt: 要处理的输入文本。
    - api_key: OpenAI 的 API 密钥。如果未提供，将从环境变量中获取。

    返回：
    - 返回三元组列表，直接来自模型输出。
    """
    if not api_key:
        api_key = os.environ.get("OPENAI_API_KEY")
    
    # 实例化一个 OpenAI 客户端
    client = OpenAI(api_key=api_key)

    # 定义消息模板
    assistant_instructions = """
    从文本中提取所有可能的三元组关系（主语，谓语，宾语）：

    示例文本：
    "爱因斯坦于1905年提出了相对论，这对现代物理学产生了深远影响。"

    示例输出：
    [
        ("爱因斯坦", "提出了", "相对论"),
        ("相对论", "产生了", "深远影响"),
        ("深远影响", "作用于", "现代物理学")
    ]
    """

    messages = [
        {"role": "system", "content": assistant_instructions},
        {"role": "user", "content": "仅以简体中文输出。"},
        {"role": "user", "content": prompt}
    ]

    # 使用流式输出模式
    stream = client.chat.completions.create(
        messages=messages,
        model="gpt-4o",
        stream=True,
    )

    # 拼接生成内容
    result = ""
    for chunk in stream:
        result += chunk.choices[0].delta.content or ""

    # 返回生成的三元组列表
    return result.strip()
