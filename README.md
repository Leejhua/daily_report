# GitHub Discussions 自动化分析服务

一个基于Python的智能化GitHub Discussions分析服务，提供日报/日计划内容检查、工作偏离度分析、飞书群组通知等功能。

## 🚀 主要功能特性

### 📊 智能分析
- **GitHub Discussions日报/日计划内容检查** - 自动检查用户提交的日报和日计划内容
- **工作偏离度智能分析** - 基于GLM-4模型分析工作计划与实际执行的偏离情况
- **数据一致性检查** - 确保GitHub数据的完整性和准确性

### 🔔 自动通知
- **飞书群组自动通知** - 支持管理层通知和普通群组消息推送
- **定时提醒** - 自动提醒用户提交日报和日计划
- **周报汇总** - 每周自动生成和发送工作总结报告

### 🤖 AI增强
- **GLM-4模型集成** - 利用智谱AI的GLM-4模型进行智能分析
- **Langfuse监控** - 完整的AI调用链路追踪和性能监控
- **智能汇报** - 自动生成结构化的分析报告

### ⏰ 定时任务
- **灵活调度** - 支持多时间点的定时任务配置
- **周末控制** - 可配置是否在周末执行检查任务
- **任务监控** - 实时监控任务执行状态和结果

## 🛠️ 技术栈

- **核心语言**: Python 3.8+
- **API集成**: GitHub API, 飞书API, GLM-4 API
- **数据处理**: PyYAML, Pydantic, python-dateutil
- **任务调度**: croniter
- **容器化**: Docker, Gunicorn
- **监控**: Langfuse, colorlog
- **测试**: pytest, pytest-asyncio

## 🚀 快速开始

### 环境要求

- Python 3.8 或更高版本
- Docker (可选，用于容器化部署)

### 安装步骤

1. **克隆项目**
   ```bash
   git clone <repository-url>
   cd cursor_glm
   ```

2. **安装依赖**
   ```bash
   pip install -r requirements.txt
   ```

3. **配置环境变量**
   ```bash
   cp .env.example .env
   # 编辑 .env 文件，填入必要的API密钥
   ```

4. **配置服务**
   ```bash
   cp config/config.yaml.example config/config.yaml
   # 根据需要修改配置文件
   ```

### 配置说明

#### 必需配置项

- **GitHub配置**
  ```yaml
  github:
    token: "your_github_token"
    repo_owner: "your_username"
    repo_name: "your_repo"
    discussion_category: "Daily Reports"
  ```

- **GLM配置**
  ```yaml
  glm:
    api_key: "your_glm_api_key"
    model: "glm-4-plus"
  ```

- **飞书配置**
  ```yaml
  feishu:
    app_id: "your_app_id"
    app_secret: "your_app_secret"
    webhook_url: "your_webhook_url"
  ```

#### 可选配置项

- **Langfuse监控**
  ```yaml
  langfuse:
    enabled: true
    secret_key: "your_secret_key"
    public_key: "your_public_key"
    host: "https://cloud.langfuse.com"
  ```

### 运行方式

#### 开发模式
```bash
python main.py
```

#### 生产模式
```bash
gunicorn -c gunicorn.conf.py main:app
```

## ⏰ 定时任务说明

系统支持以下定时任务：

| 任务类型 | 执行时间 | 功能描述 |
|---------|---------|----------|
| 日报/日计划检查 | 每天 12:00, 19:00 | 检查用户是否提交了当日的日报和日计划 |
| 日常分析任务 | 每天 13:00, 20:00 | 执行偏离度分析、工作分析报告、数据一致性检查 |
| 周报汇总 | 每周五 17:00 | 生成并发送周报总结 |

### 时间配置

可以通过修改 `config/config.yaml` 中的相关配置来调整执行时间：

```yaml
daily_content_check:
  content_check_cron: ["0 12 * * *", "0 19 * * *"]  # 日报检查时间
  analysis_cron: ["0 13 * * *", "0 20 * * *"]        # 分析任务时间
  weekend_check_enabled: false                        # 是否在周末执行

weekly_summary:
  enabled: true
  execution_hour: 17                                   # 周报执行时间（小时）
```

## 🐳 Docker部署

### 构建镜像
```bash
docker build -t cursor-glm .
```

### 运行容器
```bash
docker run -d \
  --name cursor-glm-service \
  -v $(pwd)/config:/app/config \
  -v $(pwd)/data:/app/data \
  -v $(pwd)/logs:/app/logs \
  -p 8000:8000 \
  cursor-glm
```

### Docker Compose
```yaml
version: '3.8'
services:
  cursor-glm:
    build: .
    container_name: cursor-glm-service
    volumes:
      - ./config:/app/config
      - ./data:/app/data
      - ./logs:/app/logs
    ports:
      - "8000:8000"
    restart: unless-stopped
```

## 📁 项目结构

```
cursor_glm/
├── src/                    # 源代码目录
│   ├── analysis/          # 分析模块
│   ├── feishu/           # 飞书集成
│   ├── github_client/    # GitHub API客户端
│   ├── glm/              # GLM模型集成
│   ├── config.py         # 配置管理
│   ├── scheduler.py      # 任务调度器
│   └── main.py           # 主程序入口
├── config/               # 配置文件目录
│   ├── config.yaml       # 主配置文件
│   └── config.yaml.example
├── data/                 # 数据存储目录
├── logs/                 # 日志文件目录
├── tests/                # 测试文件
├── requirements.txt      # Python依赖
├── Dockerfile           # Docker配置
├── gunicorn.conf.py     # Gunicorn配置
└── README.md            # 项目文档
```

## 🔧 开发指南

### 代码规范

项目使用以下工具确保代码质量：

- **Black**: 代码格式化
- **Flake8**: 代码风格检查
- **MyPy**: 类型检查

运行代码检查：
```bash
# 格式化代码
black src/

# 检查代码风格
flake8 src/

# 类型检查
mypy src/
```

### 运行测试

```bash
# 运行所有测试
pytest

# 运行特定测试文件
pytest tests/test_analysis.py

# 运行测试并生成覆盖率报告
pytest --cov=src tests/
```

### 添加新功能

1. 在 `src/` 目录下创建相应的模块
2. 添加配置项到 `config/config.yaml.example`
3. 编写单元测试
4. 更新文档

### 日志配置

系统使用结构化日志，支持多种日志级别：

```yaml
logging:
  level: INFO
  format: "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
  file_enabled: true
  file_path: "logs/app.log"
  max_file_size: 10485760  # 10MB
  backup_count: 5
```

## 📄 许可证

本项目采用 MIT 许可证。详情请参阅 [LICENSE](LICENSE) 文件。

## 🤝 贡献

欢迎提交 Issue 和 Pull Request 来改进这个项目！

## 📞 支持

如果您在使用过程中遇到问题，请：

1. 查看日志文件 `logs/app.log`
2. 检查配置文件是否正确
3. 提交 Issue 描述问题详情

---

**注意**: 请确保在生产环境中妥善保管API密钥和敏感配置信息。