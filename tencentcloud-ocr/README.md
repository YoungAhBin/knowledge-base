# 文字识别使用腾讯云的智能文档识别接口进行识别
```python
# 识别接口的输出我们不能改变，但输出的json内容中有三个参数，提取这三个参数的内容，可以呈现不同的输出方式

# ocr.py文件中使用DocumentRecognizeInfo参数的内容来规范输出，但是这段代码在处理已经识别到文档的最后一页，继续识别会报错的问题时，采用的是识别加载错误的返回时，停止识别循环
req.from_json_string(json.dumps(params))

try:
    # 调用 API 并获取响应
    resp = client.ReconstructDocument(req)
except TencentCloudSDKException as err:
    if err.code == "FailedOperation.FileDecodeFailed":
        print(f"已到达文档末尾，无法处理页面 {start_page} 至 {end_page}。结束处理。")
        break
    else:
        raise err

response_json = json.loads(resp.to_json_string())

# 使用另一个输出参数规范输出，这个参数生成一个文件夹，里面包含识别的图片和一个markdown文件，markdown文件中通过链接插入了图片
# 处理返回的 InsetImagePackage 字段
inset_image_package_base64 = response_json.get("InsetImagePackage")
if inset_image_package_base64:
    # 将 base64 解码，并作为一个 ZIP 文件加载
    zip_data = base64.b64decode(inset_image_package_base64)
    with zipfile.ZipFile(io.BytesIO(zip_data)) as zip_file:
        zip_file.extractall("extracted_content")
    print("图片包已解压到 'extracted_content' 文件夹")
else:
    print("InsetImagePackage 字段未返回有效数据。")
```
