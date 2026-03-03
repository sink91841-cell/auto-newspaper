# 自媒体报刊抓取解析工具

一个用于下载和解析报纸内容的自动化工具，支持人民日报、纽约时报等报纸的抓取和AI解析。

## 功能特点

-  支持下载人民日报（PDF）和纽约时报（图片）
-  使用通义千问AI解析报纸内容
-  支持将解析结果保存到文件和数据库
-  自动创建数据库和数据表
-  友好的用户交互界面
-  完善的错误处理和日志记录

## 目录结构

```
自动化报纸程序/
├── main.py                # 主入口文件
├── services/
│   └── newspaper_tool.py  # 核心工具类
├── downloader.py          # 下载模块
├── ai_client.py           # AI客户端模块
├── file_processor.py      # 文件处理模块
├── database.py            # 数据库模块
├── utils.py               # 工具函数模块
├── config.py              # 配置文件
├── logger.py              # 日志模块
├── test.py                # 单元测试
├── CHANGELOG.md           # 修改日志
└── .env.example           # 环境配置示例
```

## 模块说明

### 1. 主入口模块 (`main.py`)
- 程序的启动入口
- 检查依赖库是否安装
- 验证API Key配置
- 初始化并运行NewspaperTool

### 2. 核心工具模块 (`services/newspaper_tool.py`)
- 整合所有核心功能
- 处理用户交互（日期选择、报纸选择）
- 协调下载、AI解析和保存流程
- 管理数据库连接

### 3. 下载模块 (`downloader.py`)
- 负责下载报纸文件（PDF/图片）
- 支持动态提取人民日报PDF链接
- 实现网络请求重试机制
- 处理文件保存和验证

### 4. AI客户端模块 (`ai_client.py`)
- 调用通义千问API解析报纸内容
- 处理文件转base64编码
- 构建AI请求消息
- 实现请求重试和错误处理

### 5. 文件处理模块 (`file_processor.py`)
- 图片转base64编码
- PDF转图片并编码
- 解析AI生成的内容
- 保存解析结果到文件

### 6. 数据库模块 (`database.py`)
- 管理数据库连接
- 自动创建数据库和数据表
- 提供数据插入和批量操作
- 处理数据库错误

### 7. 工具函数模块 (`utils.py`)
- 日期格式化
- 文件夹初始化
- 用户交互（日期选择、报纸选择）
- 依赖库检查

### 8. 配置模块 (`config.py`)
- 管理环境变量和配置项
- 加载.env文件
- 提供默认配置值

### 9. 日志模块 (`logger.py`)
- 配置日志记录
- 提供不同级别的日志输出

## 安装要求

### 必要依赖
- Python 3.8+
- requests
- pillow
- pdf2image
- python-dotenv
- openai

### 可选依赖
- psycopg2-binary (用于数据库功能)

### 系统依赖
- Windows用户需要安装poppler：https://github.com/oschwartz10612/poppler-windows/releases
- Mac用户：`brew install poppler`

## 安装步骤

1. 克隆或下载项目到本地
2. 安装依赖：
   ```bash
   pip install -r requirements.txt
   ```
3. 配置API Key：
   - 复制 `.env.example` 为 `.env`
   - 在 `.env` 文件中填写通义千问API Key

## 使用方法

1. 运行程序：
   ```bash
   python main.py
   ```

2. 按照提示操作：
   - 选择日期（今天、昨天、前天或自定义）
   - 选择报纸（人民日报或纽约时报）
   - 等待下载完成
   - 选择是否使用AI解析
   - 选择是否保存结果到文件
   - 选择是否保存结果到数据库

## 配置说明

### 核心配置项
- `TONGYI_API_KEY` - 通义千问API Key（必填）
- `AI_ANALYSIS_PROMPT` - AI解析提示词
- `DB_PASSWORD` - 数据库密码

### 报纸配置
- 人民日报：PDF格式，动态提取链接
- 纽约时报：图片格式，直接URL下载

## 常见问题

### 1. 下载失败
- **纽约时报**：需要稳定的网络连接（可能需要VPN）
- **人民日报**：可能是日期未发布或停刊

### 2. AI解析失败
- 检查API Key是否正确
- 检查网络连接
- 可能是内容审核不通过

### 3. 数据库连接失败
- 检查PostgreSQL服务是否运行
- 检查数据库密码是否正确
- 程序会自动创建数据库和数据表

## 错误处理

程序包含完善的错误处理机制，会提供详细的错误信息和解决方案。常见错误包括：
- 网络连接问题
- API Key配置错误
- 数据库连接问题
- 内容审核失败

## 单元测试

运行单元测试：
```bash
python test.py
```

测试覆盖：
- 日期格式化
- URL拼接
- 提示词构建
- 报纸配置
- 日期验证

## 技术栈

- Python 3.8+
- requests (网络请求)
- Pillow (图片处理)
- pdf2image (PDF处理)
- OpenAI SDK (AI调用)
- psycopg2 (数据库连接)
- Python-dotenv (环境配置)

## 许可证

MIT License

## 更新日志

详见 [CHANGELOG.md](CHANGELOG.md)
