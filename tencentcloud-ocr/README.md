# 文字识别使用腾讯云的智能文档识别接口进行识别

（来源于https://console.cloud.tencent.com/api/explorer?Product=ocr&Version=2018-11-19&Action=ReconstructDocument）

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
        "FileUrl": "https://book-1326911228.cos.ap-guangzhou.myqcloud.com/%E9%80%9A%E5%90%91%E5%A5%B4%E5%BD%B9%E4%B9%8B%E8%B7%AF-1.pdf?q-sign-algorithm=sha1&q-ak=AKID_h515wDmj8uTJSPIDL5WSgbcFQTqFiT9KT5hxvVngu7mFGF8Pcx462tOzqPRnhTp&q-sign-time=1731050776;1731054376&q-key-time=1731050776;1731054376&q-header-list=host&q-url-param-list=&q-signature=635a00d30916d8fe67e1ebbd081b2ebdfbdcc7fd&x-cos-security-token=DJcATjeQ8qlPxM1rEcpJYMQSMDsuHqXa55d18ad0f62b9a08220e79c2fd45161eExLSNpXTM9C01c6RqfVvyVX-kV9OuXY4ECwoV_kk7s4WJgONVLPw2zbeA3qL-trWzuLGkcfnOEoFbL51nh3fK2qE9n4ocTMoItvjHd7NZH0BVAWzvVFjArz1zfzyu7vGa0NsOlrWaqLfXSy3zBY4NbTZOS-Kp1Shg2xAQ2Qn_bHQRq-agMxfW9NZnWk6eJYQ",
        "FileStartPageNumber": 1,
        "FileEndPageNumber": 10,
        "Config": {
            "EnableInsetImage": True
        }
    }
    req.from_json_string(json.dumps(params))

    # 调用 API 并获取响应
    resp = client.ReconstructDocument(req)
    response_json = json.loads(resp.to_json_string())

    # 输出没有参数可以控制，需要您收到接口返回的参数，然后您自行转成您想要的文件格式,MarkdownBase64\InsetImagePackage就是接口返回的参数。也就是说输出肯定是json格式，我们可以在输出中找到这两个参数，然后利用这两个参数再格式化输出。

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


except TencentCloudSDKException as err:
    print(err)
```
