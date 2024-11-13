import re
from sentence_transformers import SentenceTransformer
from langchain.text_splitter import SentenceTransformersTokenTextSplitter

# 按章节拆分
def split_by_title(document):
    chapters = re.split(r'元素类型：title', document)
    return chapters[1:]  # 跳过第一个部分，返回从第二章开始的内容

# 按段落拆分
def split_by_paragraph(chapter):
    # 拆分段落并去掉空段落
    paragraph_list = re.split(r'元素类型：paragraph', chapter)
    paragraph_list = [p.strip() for p in paragraph_list if p.strip()]
    return paragraph_list

def split_by_sentence(paragraph):
    # 使用正则表达式按中文句号拆分句子
    sentences = re.split(r'(?<=[。])', paragraph)  # 匹配中文句号，并将其作为句子的分隔符
    sentences = [sentence.strip() for sentence in sentences if sentence.strip()]  # 去除空句子
    return sentences
    
# 按句子拆分（单个段落输入）,**以下是使用langchain的库函数拆分的方法，对电脑性能要求高，处理大文本jupyter notebook内核会报错重启
# def split_by_sentence(paragraph):
    # 使用 SentenceTransformersTokenTextSplitter 进行句子拆分
    # sentence_splitter = SentenceTransformersTokenTextSplitter(chunk_overlap=50, model_name='sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2')
    
    # sentences = sentence_splitter.split_text(paragraph)  # 直接对单个段落进行句子拆分
    # return sentences

# 从本地TXT文件读取文档内容
def read_document_from_file(file_path):
    with open(file_path, 'r', encoding='utf-8') as file:
        document = file.read()
    return document

# 生成数据
# 生成数据
def generate_data(document):
    chapters = split_by_title(document)
    
    data = []
    
    for chapter_id, chapter in enumerate(chapters, 1):  # 使用enumerate获取章节索引
        paragraphs = split_by_paragraph(chapter)  # 按章节拆分段落
        for paragraph_id, paragraph in enumerate(paragraphs, 1):  # 使用enumerate获取段落索引
            sentences = split_by_sentence(paragraph)  # 按段落拆分句子
            for sentence_id, sentence in enumerate(sentences, 1):  # 使用enumerate获取句子索引
                data.append({
                    "id": str(len(data) + 1),
                    "chapter": str(chapter_id),
                    "paragraph": str(paragraph_id),
                    "sentence": str(sentence_id),
                    "text": sentence
                })
    
    return data

# 示例用法：
file_path = r"C:\Users\传防科电脑\Desktop\output.txt"  # 请确保文件路径正确
document = read_document_from_file(file_path)  # 读取文件内容
data = generate_data(document)

# 打印结果（可以选择保存到文件或数据库）
data
