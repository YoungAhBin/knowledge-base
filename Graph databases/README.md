# openai接口访问的的示例模板（来源于github上https://github.com/openai/openai-python）

```python
import os
from openai import OpenAI

#实例化一个对象
client = OpenAI(
    api_key=os.environ.get("OPENAI_API_KEY"),  
)

client = OpenAI()

assistan = f"""
从文本中提取所有可能的三元组关系（主语，谓语，宾语），仅以简体中文输出：

示例文本：
"爱因斯坦于1905年提出了相对论，这对现代物理学产生了深远影响。"

示例输出：
[
    ("爱因斯坦", "提出了", "相对论"),
    ("相对论", "产生了", "深远影响"),
    ("深远影响", "作用于", "现代物理学")
]
"""

prompt = "當文明的進程發生一個出乎意料的轉折時一即當我們發現我們不像預期的那樣繼續前進，而是受到了我們認為和以往世代的蒙昧無知相關聯的諸般邪惡的威脅時一我們自然要怨天尤人而不會歸咎於我們自己。"

# 定义消息列表
messages = [
    {"role": "system", "content": assistan},
    {"role": "user", "content": prompt}
]

stream = client.chat.completions.create(
    messages=messages,
    model="gpt-4o",
    stream=True,
)
for chunk in stream:
    print(chunk.choices[0].delta.content or "", end="")
```
