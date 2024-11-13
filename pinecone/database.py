from pinecone import Pinecone, ServerlessSpec

# 环境变量设置api_key
pc = Pinecone(api_key="YOUR_API_KEY")

# 填入索引名，类似于数据库名
index_name = "documentation-read"

pc.create_index(
    name=index_name,
    dimension=1024, # Replace with your model dimensions
    metric="cosine", # Replace with your model metric
    spec=ServerlessSpec(
        cloud="aws",
        region="us-east-1"
    ) 
)

# 一次最多存入96条数据，id最大到96
data = data[0:96]

embeddings = pc.inference.embed(
    model="multilingual-e5-large",
    inputs=[d['text'] for d in data],
    parameters={"input_type": "passage", "truncate": "END"}
)
print(embeddings[0])

# Wait for the index to be ready
while not pc.describe_index(index_name).status['ready']:
    time.sleep(1)

index = pc.Index(index_name)

vectors = []
for d, e in zip(data, embeddings):
    vectors.append({
        "id": d['id'],
        "values": e['values'],
        # 需要存入元数据的都要在这里指定匹配
        "metadata": {
            'text': d['text'],
            'chapter': d['chapter'],  
            'paragraph': d['paragraph'],  
            'sentence': d['sentence']  
        }
    })

# 在这里设置命名空间的名字，我用书名设定的
index.upsert(
    vectors=vectors,
    namespace="tong-wang-nu-yi-zhi-lu"
)

print(index.describe_index_stats())

# 设定查询问题
query = "战时的敌对国家如何影响我们对自身价值的理解？"

embedding = pc.inference.embed(
    model="multilingual-e5-large",
    inputs=[query],
    parameters={
        "input_type": "query"
    }
)

results = index.query(
    namespace="tong-wang-nu-yi-zhi-lu",
    vector=embedding[0].values,
    top_k=3,
    include_values=False,
    include_metadata=True
)

print(results)
