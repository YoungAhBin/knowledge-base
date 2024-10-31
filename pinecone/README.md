# pinecone实现向量存储与查询的基础逻辑

```python
# 配置环境

# !pip3 install -qU \
#     langchain \
#     tiktoken \
#     datasets \
#     pinecone-client

# !pip3 install protobuf==3.20.3
# !pip3 install apache-beam==2.50.0

#  插入需要的包

from tqdm.auto import tqdm
from uuid import uuid4
from pinecone import Pinecone
from getpass import getpass
from langchain.embeddings.openai import OpenAIEmbeddings
from datasets import load_dataset
from getpass import getpass
import tiktoken
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain.schema.document import Document
import pandas as pd

# 初始化索引（建立索引），索引是管理和查询向量数据的，建立索引是通过create_index函数创建里，该函数内的所有参数都是对这个参数的定义

# Find API key in console at app.pinecone.io
# pinecone的API Key是用于访问云服务器的
YOUR_API_KEY = getpass("Pinecone API Key: ")

# Find ENV (cloud region) next to API key in console
YOUR_ENV = input("Pinecone environment: ")

INDEX_NAME = 'namespaces-demo'

# Initialize Pinecone client
pinecone.init(
    api_key=YOUR_API_KEY,
    environment=YOUR_ENV
)

# Create index
pinecone.create_index(
    name=INDEX_NAME,
    metric='cosine',
    dimension=1536)

# Confirm we indeed created our "namespaces-demo" index
pinecone.list_indexes().names()

# 查看索引

demo_index = pinecone.Index(INDEX_NAME)
demo_index.describe_index_stats()

# 加载数据

wiki_en = load_dataset("wikipedia", "20220301.en", split="train[:10]")
wiki_it = load_dataset("wikipedia", "20220301.it", split="train[:10]")
wiki_fr = load_dataset("wikipedia", "20220301.fr", split="train[:10]")

# 预览数据

wiki_en.to_pandas().head(2)

# 创建openai嵌入函数embed

OPENAI_API_KEY = getpass("OpenAI API Key: ")
model_name = 'text-embedding-ada-002'

embed = OpenAIEmbeddings(
    model=model_name,
    openai_api_key=OPENAI_API_KEY
)

# 创建一个和嵌入函数使用的模型对应的分词器

# 不同的嵌入模型使用的token列表不同，分词方式不同，openai有自己的分词定义，所以告诉分词器我们使用的是啥嵌入模型
tiktoken.encoding_for_model('text-embedding-ada-002')

# 初始化一个分词器对象
tokenizer = tiktoken.get_encoding('cl100k_base')

# 利用分词器对象创建计算文本含有多少个token的函数
def tiktoken_len(text: str) -> int:
    """
    Split up a body of text using a custom tokenizer.

    :param text: Text we'd like to tokenize.
    """
    tokens = tokenizer.encode(
        text,
        disallowed_special=()
    )
    return len(tokens)

# 创建一个文本分割函数。利用RecursiveCharacterTextSplitter（）创建了分割对象，该对象的参数定义了分割方法及块的大小，利用该分割对象的一个方法创建了文本分割函数chunk_by_size。因为块的分割的大小是用token衡量的，所以需要分词器分词计数的方式建立的token数计算函数计算文本长度。

def chunk_by_size(text: str, size: int = 50) -> list[Document]:
    """
    Chunk up text recursively.
    
    :param text: Text to be chunked up
    :return: List of Document items (i.e. chunks).|
    """
    text_splitter = RecursiveCharacterTextSplitter(
    chunk_size = size,
    chunk_overlap = 20,
    length_function = tiktoken_len,
    add_start_index = True,
)
    return text_splitter.create_documents([text])

# 文本分割。首先利用chunk_by_size函数把文本分成很多个块存储在一块；然后仅从每个块中提取出文本存放在一块；然后遍历每个块，payload获得块的元数据，id给每个块赋予一个id，value在向量编辑对象的作用下获得块的文本的向量化之后的向量值；最后用一个列表存储元数据、id、向量值。

def create_chunks_metadata_embeddings(dataset: pd.DataFrame) -> list[dict]:
    """
    Given a dataset, split text data into chunks, extract metadata, create embeddings for each chunk.

    :param dataset: Data we want to process.
    :return: List of data objects to upsert into our Pinecone index.
    """
    data_objs = []

    # For each row in our dataset:
    for index, row in tqdm(dataset.iterrows()):  # (tqdm library prints status of for-loop to console)        
        # Create chunks
        chunked_text = chunk_by_size(row["text"])
        
        # Extract just the string content from the chunk
        chunked_text = [c.page_content for c in chunked_text]

        # Extract some metadata, create an ID, and generate an embedding for the chunk. 
        # Wrap that all in a dictionary, and append that dictionary to a list (`data_objs`).
        for idx, text in enumerate(chunked_text):
            payload = {
                "metadata": {
                    "url": row["url"],
                    "title": row["title"],
                    "chunk_num": idx, 
                    "text_content": text  # there are 248 chars in this chunk of text 
                },
             "id": str(uuid4()),
            "values": embed.embed_documents([text])[0]  # --> list of len 248, each item of those 248 has a len of 1536
            }
            data_objs.append(payload)
            
    # Return list of dictionaries, each containing our metadata, ID, and embedding, per chunk.
    return data_objs

# 数据预处理。调用上面定义create_chunks_metadata_embeddings函数处理我们用dataset加载格式化的数据，处理成包含元数据、id、向量值的列表

data_objs_en = create_chunks_metadata_embeddings(wiki_en.to_pandas().head(3))
# 列表长度
len(data_objs_en)
# 第一个块的向量化数据
data_objs_en[0]

# 定义批量上传数据至索引进行管理的上传函数，每次上传100个块

BATCH_SIZE = 100

def batch_upsert(data: list[dict], index: pinecone.Index, namespace: str):
    """
    Upsert data objects to a Pinecone index in batches.

    :param data: Data objects we want to upsert.
    :param index: Index into which we want to upsert our data objects.
    :namespace: Namespace within our index into which we want to upsert our data objects.
    """
    for i in range(0, len(data), BATCH_SIZE):
        batch = data[i:i+BATCH_SIZE]
        # print(batch)
        index.upsert(vectors=batch, namespace=namespace)


# NOTE:
# - In Production, you'll want to have a try/except loop here to catch upsert errors.
# - You'll also likely want to optimize your batching as you scale your data. Parallelization and using generator objects will 
#   significantly improve your batch performance.
# - Last, you'll want to confirm that the # of vectors you upsert matches the # of vectors you intend to upsert.

# 调用批量上传函数上传数据，data_objs_en向量化处理后的数据，demo_index实例化的索引对象，'en'命名空间的空间名

batch_upsert(data_objs_en, demo_index, 'en')

# 建立查询

# 查询问题
query_en = "Who is Wilhelm Weitling?" 
# 查询字典
tenants = [{
            'name': 'Audrey',
            'native_language': 'en',
            'query': query_en
    
            }]

# 定义对查询字典进行向量化处理的函数，用对存储数据进行向量化处理的一样的函数

def vectorize_query(model: OpenAIEmbeddings, query: str) -> list[float]:
    """
    Given a vectorization model & query, create an embedding.

    :param model: Model for creating embeddings.
    :param query: Query we want to vectorize/embed.
    :return: Vector/embedding.
    """
    return model.embed_query(query)
    
# 调用问题向量化函数

query_vector_en = vectorize_query(embed, query_en)

# 建立向量化查询问题列表

# Define a list of new key-value pairs
new_key_value_pairs = [
    {'vector_query': query_vector_en},
    {'vector_query': query_vector_it},
    {'vector_query': query_vector_fr}
    
]

# Loop through the list of dictionaries and the list of new key-value pairs
for tenant, new_pair in zip(tenants, new_key_value_pairs):
    tenant.update(new_pair)

# 建立查询

# Let's send Audrey's query through to our index
audrey = [t for t in tenants if t.get('name') == 'Audrey'][0]

# Grab Audrey's vectorized query & her native language (which we'll map onto our namespaces)
audrey_query_vector = audrey['vector_query']
audrey_namespace = audrey['native_language']

# Send the query on through!demo_index索引对象，query查询函数
demo_index.query(vector=audrey_query_vector, top_k=1, include_metadata=True, namespace=audrey_namespace)

# Amazing! We get our chunk of text back that specifically mentions who Wilhelm Weitling is

# 在指定的命名空间内，利用元数据进行查询

sample_anarchy_query = "What is anarchy?"
vectorized_sample_anarchy_query = vectorize_query(embed, sample_anarchy_query)
targeted_namespace = 'en'
# Send our query through!

demo_index.query(
    vector=vectorized_sample_anarchy_query,
    filter={
        "title": {"$eq": "Anarchism"},
    },
    top_k=3,
    include_metadata=True,
    namespace=targeted_namespace
)
```

# 简单开始案例

```python
# 安装需要的库
pip install pinecone

# 配置密钥
PINECONE_API_KEY="YOUR_API_KEY"

# 导入包
from pinecone import Pinecone, ServerlessSpec

# 初始化一个pinecone对象，pinecone对象用于与pinecone建立连接上传数据使用
pc = Pinecone(api_key="YOUR_API_KEY")

# 创建一个无服务器索引对象存储管理数据。无服务器架构，会自动将数据存储在其指定的云平台（例如亚马逊的 AWS 上），并在后台管理所有的存储资源。你只需通过 Pinecone 提供的 API 来进行数据的上传、查询和管理操作，所有的底层存储和计算资源都由 Pinecone 负责配置和优化。具体来说，当你使用 ServerlessSpec 配置 AWS 云时，Pinecone 会将你的索引数据保存在 AWS 的对象存储（如 S3）上，并通过 Pinecone 的 API 调用来访问这些数据。这样，你既不需要配置 AWS 的存储资源，也不需要维护数据库和索引结构的运行状态。Pinecone 的这种架构使得用户只需按实际使用量支付费用，同时可以享受自动扩展的云资源管理。无服务器架构索引自动帮你配置数据库和管理数据，它里面有接口连接亚马逊云服务器，是他们自己的亚马逊云服务器，不需要你自己注册配置亚马逊云服务器，付费用他们的就可以。还有pod架构的服务器索引对象，在本地建立存储服务器。
index_name = "quickstart"
pc.create_index(
    name=index_name,
    dimension=1024, # Replace with your model dimensions
    metric="cosine", # Replace with your model metric
    spec=ServerlessSpec(
        cloud="aws",
        region="us-east-1"
    ) 
)

# 向量化存储数据
data = [
    {"id": "vec1", "text": "Apple is a popular fruit known for its sweetness and crisp texture."},
    {"id": "vec2", "text": "The tech company Apple is known for its innovative products like the iPhone."},
    {"id": "vec3", "text": "Many people enjoy eating apples as a healthy snack."},
    {"id": "vec4", "text": "Apple Inc. has revolutionized the tech industry with its sleek designs and user-friendly interfaces."},
    {"id": "vec5", "text": "An apple a day keeps the doctor away, as the saying goes."},
    {"id": "vec6", "text": "Apple Computer Company was founded on April 1, 1976, by Steve Jobs, Steve Wozniak, and Ronald Wayne as a partnership."}
]

embeddings = pc.inference.embed(
    model="multilingual-e5-large",
    inputs=[d['text'] for d in data],
    parameters={"input_type": "passage", "truncate": "END"}
)
print(embeddings[0])

# 上传数据到索引
# Wait for the index to be ready
while not pc.describe_index(index_name).status['ready']:
    time.sleep(1)

index = pc.Index(index_name)

vectors = []
for d, e in zip(data, embeddings):
    vectors.append({
        "id": d['id'],
        "values": e['values'],
        "metadata": {'text': d['text']}
    })

index.upsert(
    vectors=vectors,
    namespace="ns1"
)

# 核查索引
print(index.describe_index_stats())

# 查询问题向量化
query = "Tell me about the tech company known as Apple."

embedding = pc.inference.embed(
    model="multilingual-e5-large",
    inputs=[query],
    parameters={
        "input_type": "query"
    }
)

# 建立查询
results = index.query(
    namespace="ns1",
    vector=embedding[0].values,
    top_k=3,
    include_values=False,
    include_metadata=True
)

print(results)
```
