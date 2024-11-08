import os
import json
from tencentcloud.common import credential
from tencentcloud.common.profile.client_profile import ClientProfile
from tencentcloud.common.profile.http_profile import HttpProfile
from tencentcloud.common.exception.tencent_cloud_sdk_exception import TencentCloudSDKException
from tencentcloud.ocr.v20181119 import ocr_client, models
import base64
import zipfile
import io

try:
    # 实例化认证对象，使用环境变量中的 SecretId 和 SecretKey
    cred = credential.Credential(
        os.environ.get("TENCENTCLOUD_SECRET_ID"),
        os.environ.get("TENCENTCLOUD_SECRET_KEY")
    )

    # 设置 httpProfile 和 clientProfile
    httpProfile = HttpProfile()
    httpProfile.endpoint = "ocr.tencentcloudapi.com"
    clientProfile = ClientProfile()
    clientProfile.httpProfile = httpProfile

    # 实例化 OCR client
    client = ocr_client.OcrClient(cred, "ap-guangzhou", clientProfile)

    # 实例化请求对象并设置参数
    req = models.ReconstructDocumentRequest()
    params = {
        "FileType": "PDF",
        "FileUrl": "https://book-1326911228.cos.ap-guangzhou.myqcloud.com/%E9%80%9A%E5%90%91%E5%A5%B4%E5%BD%B9%E4%B9%8B%E8%B7%AF-1.pdf?q-sign-algorithm=sha1&q-ak=AKIDg5u_EhC9gK-0Yw7J4Pvl3u1CK9q6DKmLwmoAsGAqcbkHAZdO4pOUuZ_LaVNjifeE&q-sign-time=1731034205;1731037805&q-key-time=1731034205;1731037805&q-header-list=host&q-url-param-list=&q-signature=3dfa14bce7c83b5aa1aa15a0e2b827e32bde3b80&x-cos-security-token=DJcATjeQ8qlPxM1rEcpJYMQSMDsuHqXa6f15d9127d68239f76cbbf350af8a867ExLSNpXTM9C01c6RqfVvyQW_UadAELnjJZETNjBV-d-4Aajuo9-vXZadaLSuMWSmnSICvttx9Yt8iqDgDSE_f1-MNXu7JuIcbpX31VzYdSxj0hnj4HSLjDN8WSg9QSkDc4vMdIYpH8iAYxmExV9zCt1a1hJxV5WUm8BmEnYRCG8VFlQHEm3idx1h_sZGnvh-",
        "FileStartPageNumber": 1,
        "FileEndPageNumber": 3,
        "Config": {
            "EnableInsetImage": True
        }
    }
    req.from_json_string(json.dumps(params))

    # 调用 API 并获取响应
    resp = client.ReconstructDocument(req)
    response_json = json.loads(resp.to_json_string())

    # 输出没有参数可以控制，需要您收到接口返回的参数，然后您自行转成您想要的文件格式,MarkdownBase64\InsetImagePackage就是接口返回的参数。也就是说输出肯定是json格式，我们可以在输出中找到这两个参数，然后利用这两个参数再格式化输出。

    # 处理返回的 MarkdownBase64 字段
    markdown_base64 = response_json.get("MarkdownBase64")
    if markdown_base64:
        markdown_content = base64.b64decode(markdown_base64).decode("utf-8")
        with open("output.md", "w", encoding="utf-8") as md_file:
            md_file.write(markdown_content)
        print("Markdown 文件已成功保存为 output.md")
    else:
        print("MarkdownBase64 字段未返回有效数据。")

    # 处理返回的 InsetImagePackage 字段
    inset_image_package_base64 = response_json.get("InsetImagePackage")
    if inset_image_package_base64:
        # 将 base64 解码，并作为一个 ZIP 文件加载
        zip_data = base64.b64decode(inset_image_package_base64)
        with zipfile.ZipFile(io.BytesIO(zip_data)) as zip_file:
            zip_file.extractall("extracted_images")
        print("图片包已解压到 'extracted_images' 文件夹")
    else:
        print("InsetImagePackage 字段未返回有效数据。")

except TencentCloudSDKException as err:
    print(err)
