import configparser
import json
import datetime
import logging
import os
import random
import time
from pathlib import Path
from typing import Optional

import uvicorn
from fastapi import FastAPI, HTTPException, Depends, Header, UploadFile, File, Form, Body
from pydantic import BaseModel
from qcloud_cos import CosConfig
from qcloud_cos import CosS3Client
from starlette.staticfiles import StaticFiles
import mimetypes
import requests

# 设置输出路径
output_path = "/root/code/html_output"
print("完整路径-html_output:", output_path)
# 设置图片输出路径
image_output_path = "/root/code/images"
port = 8000
outport = 7789

app = FastAPI()
app.mount("/html_output", StaticFiles(directory=output_path), name="html_output")
app.mount("/images", StaticFiles(directory=image_output_path), name="images")  # 新增图片静态目录


# 读取配置文件中的API密钥
config = configparser.ConfigParser()
config.read('config.ini', encoding='utf-8')

# Tencent Cloud COS configuration
region = config.get('common', 'region')
secret_id = config.get('common', 'secret_id')
secret_key = config.get('common', 'secret_key')
bucket = config.get('common', 'bucket')
ser_ip = config.get('common', 'ser_ip')

# 确保目录存在
os.makedirs(image_output_path, exist_ok=True)
os.makedirs(output_path, exist_ok=True)

log_dir = "/fast_api/logs/7789/"
os.makedirs(log_dir, exist_ok=True)
# 设置日志
logging.basicConfig(
    level=logging.INFO,
    filename=log_dir+'img_html.log',
    filemode='a',
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# 允许的图片类型
ALLOWED_IMAGE_TYPES = {'image/jpeg', 'image/png', 'image/gif', 'image/webp'}

class HTMLRequest(BaseModel):
    html_content: str
    filename: Optional[str] = None

def verify_auth_token(authorization: str = Header(None)):
    """验证 Authorization Header 中的 Bearer Token"""
    if not authorization:
        raise HTTPException(status_code=401, detail="Missing Authorization Header")

    scheme, _, token = authorization.partition(" ")
    if scheme.lower() != "bearer":
        raise HTTPException(status_code=401, detail="Invalid Authorization Scheme")

    valid_tokens = json.loads(config.get('auth', 'valid_tokens'))
    if token not in valid_tokens:
        raise HTTPException(status_code=403, detail="Invalid or Expired Token")
    return token

def generate_timestamp_filename(extension='html'):
    timestamp = datetime.datetime.now().strftime("%Y%m%d%H%M%S")
    random_number = random.randint(1000, 9999)
    filename = f"{timestamp}_{random_number}.{extension}"
    return filename

def generate_filename(extension: str):
    """生成带时间戳和随机数的文件名"""
    timestamp = datetime.datetime.now().strftime("%Y%m%d%H%M%S")
    random_number = random.randint(1000, 9999)
    return f"{timestamp}_{random_number}.{extension}"

def save_html_file(html_content, filename=None, output_dir=None):
    # 如果没有提供文件名，则生成一个
    if not filename:
        filename = generate_timestamp_filename()

    # 如果没有提供输出目录，则使用默认目录
    if not output_dir:
        output_dir = output_path

    # 确保输出目录存在
    os.makedirs(output_dir, exist_ok=True)

    # 组合完整的输出路径
    file_path = os.path.join(output_dir, filename)

    # 写入HTML内容
    with open(file_path, 'w', encoding='utf-8') as file:
        file.write(html_content)

    # 返回文件名和输出路径
    return filename, file_path

def upload_cos(region, secret_id, secret_key, bucket, file_path, cos_path):
    """上传文件到COS"""
    config = CosConfig(
        Region=region,
        SecretId=secret_id,
        SecretKey=secret_key
    )
    client = CosS3Client(config)
    
    try:
        response = client.upload_file(
            Bucket=bucket,
            LocalFilePath=file_path,
            Key=cos_path,
            PartSize=10,
            MAXThread=10,
            EnableMD5=False
        )
        if response['ETag']:
            return f"https://{bucket}.cos.{region}.myqcloud.com/{cos_path}"
        return None
    except Exception as e:
        logger.error(f"COS上传失败: {str(e)}")
        return None

@app.post("/upload-image/")
async def upload_image(
    file_url: str = Body(..., embed=True),  # 修改参数名明确表示是URL
    filename: str = Body(..., embed=True),
    auth_token: str = Depends(verify_auth_token)
    ):
    """图片上传接口（通过URL下载）"""
    try:
        start_time = time.time()
        

        response = requests.get(file_url)
        if response.status_code != 200:
            raise HTTPException(400, detail="Failed to download image from URL")
        

        # 从响应头获取内容类型
        content_type = response.headers.get('Content-Type', '')

        
        # 获取文件数据
        image_data = response.content
        

        final_filename = filename 
        
        # 创建本地路径
        local_path = image_output_path + "/" + final_filename
        
        # 保存文件到本地
        with open(local_path, "wb") as buffer:
            buffer.write(image_data)

        # 上传到COS
        cos_path = f"images/{final_filename}"
        cos_url = upload_cos(
            region, secret_id, secret_key, bucket,
            str(local_path), cos_path
        )

        if not cos_url:
            raise HTTPException(500, detail="Failed to upload image to COS")

        elapsed_time = time.time() - start_time
        logger.info(f"图片上传完成，耗时 {elapsed_time:.2f} 秒")

        return {
            "success": True,
            "local_url": cos_url,
            "filename": final_filename
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.exception(f"图片上传失败: {str(e)}")
        raise HTTPException(500, detail="Internal server error") from e

# 原有的HTML生成接口保持不变
@app.post("/generate-html/")
async def generate_html(
    request: HTMLRequest, 
    auth_token: str = Depends(verify_auth_token)
    ):
    
    try:
        logger.info("开始处理HTML生成请求")
        start_time = time.time()

        filename, file_path = save_html_file(request.html_content, request.filename, output_path)
        cos_url = upload_cos(region, secret_id, secret_key, bucket, str(file_path), filename)

        elapsed_time = time.time() - start_time
        logger.info(f"HTML生成和上传完成，耗时 {elapsed_time:.2f} 秒")
        
        return {
            "success": True,
            "html_url": cos_url,
            "local_url": f"http://{ser_ip}:{outport}/html_output/{filename}",
            "filename": filename
        }
    except Exception as e:
        logger.error(f"处理HTML生成请求时发生错误: {str(e)}")
        raise HTTPException(500, detail=str(e))

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=port)
