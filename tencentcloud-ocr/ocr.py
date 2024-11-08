import os
import json
from tencentcloud.common import credential
from tencentcloud.common.profile.client_profile import ClientProfile
from tencentcloud.common.profile.http_profile import HttpProfile
from tencentcloud.common.exception.tencent_cloud_sdk_exception import TencentCloudSDKException
from tencentcloud.ocr.v20181119 import ocr_client, models

def process_pdf(file_url):
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

        # 实例化 OCR 客户端
        client = ocr_client.OcrClient(cred, "ap-guangzhou", clientProfile)

        # 清空或创建输出文件
        with open("output.txt", "w", encoding="utf-8") as file:
            pass

        start_page = 1
        max_pages_per_request = 10

        while True:
            end_page = start_page + max_pages_per_request - 1

            # 实例化请求对象并设置参数
            req = models.ReconstructDocumentRequest()
            params = {
                "FileType": "PDF",
                "FileUrl": file_url,
                "FileStartPageNumber": start_page,
                "FileEndPageNumber": end_page,
                "Config": {
                    "EnableInsetImage": True
                }
            }
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

            # 输出处理
            with open("output.txt", "a", encoding="utf-8") as file:
                document_info_list = response_json.get("DocumentRecognizeInfo", [])
                if document_info_list:
                    for page_info in document_info_list:
                        page_number = page_info.get("PageNumber", "未知页码")
                        adjusted_page_number = page_number + start_page - 1
                        file.write(f"正在处理页面：{adjusted_page_number}\n")

                        # 页面尺寸和角度
                        height = page_info.get("Height")
                        width = page_info.get("Width")
                        rotated_angle = page_info.get("RotatedAngle")
                        file.write(f"尺寸：{width}x{height}，旋转角度：{rotated_angle}\n")

                        # 遍历页面中的每个元素
                        elements = page_info.get("Elements", [])
                        for element in elements:
                            element_type = element.get("Type")
                            text_content = element.get("Text", "")
                            polygon = element.get("Polygon", {})

                            # 写入元素信息
                            file.write(f"元素类型：{element_type}\n")
                            file.write(f"内容：{text_content}\n")
                            # file.write(f"多边形坐标：{polygon}\n")
                        file.write("\n")  # 页面之间留空行分隔
                else:
                    file.write(f"页面 {start_page} 至 {end_page} 没有返回有效数据。\n")
                    print(f"页面 {start_page} 至 {end_page} 没有数据。结束处理。")
                    break

            print(f"已处理页面 {start_page} 至 {end_page}。")

            # 增加起始页码
            start_page += max_pages_per_request

    except TencentCloudSDKException as err:
        print(err)

# 调用函数并传入文件 URL
if __name__ == "__main__":
    file_url = "https://book-1326911228.cos.ap-guangzhou.myqcloud.com/通向奴役之路-1.pdf?..."  # 请替换为实际的文件 URL
    process_pdf(file_url)
