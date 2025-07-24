# 图片和HTML文件上传服务

这是一个基于FastAPI的文件上传服务，支持图片和HTML文件的上传、存储和管理。文件会被自动上传到腾讯云COS（对象存储）并提供访问链接。

## 功能特性

- 🖼️ **图片上传**: 支持通过URL下载并上传图片文件
- 📄 **HTML文件生成**: 接收HTML内容并生成文件
- ☁️ **云存储**: 自动上传文件到腾讯云COS
- 🔐 **Bearer Token验证**: 安全的API访问控制
- 📊 **日志记录**: 详细的操作日志和性能监控
- 🌐 **静态文件服务**: 提供本地文件访问

## 技术栈

- **FastAPI**: 现代化的Python Web框架
- **Uvicorn**: ASGI服务器
- **腾讯云COS**: 对象存储服务
- **Pydantic**: 数据验证和序列化

## 项目结构

```
7789/
├── main.py              # 主应用程序
├── config.ini           # 配置文件
├── requirements.txt     # 依赖包列表
├── README.md           # 项目说明文档
├── html_output/        # HTML文件输出目录
└── images/             # 图片文件输出目录
```

## 安装和配置

### 1. 安装依赖

```bash
pip install -r requirements.txt
```

### 2. 配置文件设置

编辑 `config.ini` 文件，配置以下信息：

```ini
[common]
region = ap-shanghai                    # 腾讯云COS区域
secret_id = your_secret_id             # 腾讯云SecretId
secret_key = your_secret_key           # 腾讯云SecretKey
bucket = your_bucket_name              # COS存储桶名称

[auth]
valid_tokens = ["your_token1", "your_token2"]  # 有效的API访问令牌
```

### 3. 启动服务

```bash
python main.py
```

服务将在 `http://localhost:8000` 启动，对外端口为 `7789`。

## API 接口

### 图片上传接口

**POST** `/upload-image/`

通过URL下载图片并上传到云存储。

**请求头:**
```http
Authorization: Bearer your_token
Content-Type: application/json
```

**请求体:**
```json
{
    "file_url": "https://example.com/image.jpg",
    "filename": "my_image.jpg"
}
```

**响应:**
```json
{
    "success": true,
    "local_url": "https://your-bucket.cos.region.myqcloud.com/images/my_image.jpg",
    "filename": "my_image.jpg"
}
```

### HTML文件生成接口

**POST** `/generate-html/`

生成HTML文件并上传到云存储。

**请求头:**
```http
Authorization: Bearer your_token
Content-Type: application/json
```

**请求体:**
```json
{
    "html_content": "<html><body><h1>Hello World</h1></body></html>",
    "filename": "my_page.html"  // 可选，不提供时自动生成
}
```

**响应:**
```json
{
    "success": true,
    "html_url": "https://your-bucket.cos.region.myqcloud.com/my_page.html",
    "local_url": "http://101.35.97.90:7789/html_output/my_page.html",
    "filename": "my_page.html"
}
```

## 静态文件访问

服务提供静态文件访问功能：

- HTML文件: `http://your-server:7789/html_output/filename.html`
- 图片文件: `http://your-server:7789/images/filename.jpg`

## 文件命名规则

如果没有指定文件名，系统会自动生成文件名，格式为：
```
YYYYMMDDHHMMSS_XXXX.extension
```
其中：
- `YYYYMMDDHHMMSS`: 时间戳
- `XXXX`: 4位随机数
- `extension`: 文件扩展名

## 日志记录

日志文件存储在 `/fast_api/logs/7789/img_html.log`，记录以下信息：
- API请求处理时间
- 文件上传状态
- 错误信息和异常详情

## 错误处理

API 返回标准的HTTP状态码：

- `200`: 请求成功
- `400`: 请求参数错误
- `401`: 缺少或无效的Authorization Header
- `403`: Token无效或已过期
- `500`: 服务器内部错误

## 环境要求

- Python 3.7+
- 腾讯云COS账户和存储桶
- 网络连接（用于上传文件到云存储）

## 安全注意事项

1. 确保 `config.ini` 文件的安全性，不要将密钥信息提交到版本控制系统
2. 定期更换API访问令牌
3. 建议在生产环境中使用HTTPS
4. 考虑添加文件大小限制和类型验证

## 许可证

此项目仅供内部使用。

## 贡献

如有问题或建议，请联系项目维护者。
