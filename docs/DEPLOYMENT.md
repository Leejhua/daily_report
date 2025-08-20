# 部署指南

本文档详细说明了GitHub Discussions自动化分析服务的各种部署方式。

## 系统要求

### 最低要求
- **操作系统**: Linux (推荐 Ubuntu 20.04+), macOS, Windows 10+
- **Python**: 3.9+
- **内存**: 512MB RAM
- **存储**: 1GB 可用空间
- **网络**: 稳定的互联网连接

### 推荐配置
- **CPU**: 2核心
- **内存**: 1GB RAM
- **存储**: 5GB SSD
- **网络**: 带宽 ≥ 10Mbps

### 外部依赖
- **GitHub Personal Access Token**: 具有Discussions读写权限
- **GLM-4.5 API密钥**: 智谱AI账户和API访问权限

## 部署方式对比

| 部署方式 | 适用场景 | 优点 | 缺点 |
|---------|---------|------|------|
| Docker Compose | 生产环境 | 环境隔离、易管理、可扩展 | 需要Docker知识 |
| systemd服务 | Linux服务器 | 系统集成好、自启动 | 仅限Linux |
| 开发模式 | 开发测试 | 简单快速、易调试 | 不适合生产 |
| Kubernetes | 大规模部署 | 高可用、自动伸缩 | 复杂度高 |

## 快速开始

### 1. 获取代码
```bash
git clone <repository-url>
cd github-discussions-analyzer
```

### 2. 配置环境变量
```bash
# 复制环境变量模板
cp env.example .env

# 编辑配置文件
nano .env
```

必需的环境变量：
```bash
# GitHub配置
GITHUB_TOKEN=ghp_xxxxxxxxxxxxxxxxxxxx
GITHUB_ORG=your-organization
GITHUB_REPO=your-repository

# GLM-4.5配置  
GLM_API_KEY=your-glm-api-key

# 调度配置
SCHEDULE_CRON=0 18 * * *  # 每天18:00执行
TIMEZONE=Asia/Shanghai
```

### 3. 选择部署方式

#### 方式一：Docker Compose（推荐）
```bash
# 使用部署脚本
chmod +x deploy/deploy.sh
./deploy/deploy.sh docker

# 或手动执行
docker-compose up -d
```

#### 方式二：systemd服务
```bash
./deploy/deploy.sh systemd
```

#### 方式三：开发模式
```bash
./deploy/deploy.sh dev
```

## 详细部署指南

### Docker Compose 部署

#### 准备工作
```bash
# 安装Docker和Docker Compose
curl -fsSL https://get.docker.com | sh
sudo usermod -aG docker $USER
sudo systemctl enable docker
sudo systemctl start docker

# 安装Docker Compose
sudo curl -L "https://github.com/docker/compose/releases/latest/download/docker-compose-$(uname -s)-$(uname -m)" -o /usr/local/bin/docker-compose
sudo chmod +x /usr/local/bin/docker-compose
```

#### 配置文件
创建 `docker-compose.override.yml` 进行自定义配置：
```yaml
version: '3.8'
services:
  github-analyzer:
    environment:
      - LOG_LEVEL=DEBUG
    volumes:
      - ./custom-config:/app/config:ro
    restart: unless-stopped
```

#### 部署步骤
```bash
# 1. 构建镜像
docker-compose build

# 2. 启动服务
docker-compose up -d

# 3. 查看状态
docker-compose ps

# 4. 查看日志
docker-compose logs -f

# 5. 停止服务
docker-compose down
```

#### 健康检查
```bash
# 检查容器状态
docker-compose ps

# 查看健康检查结果
docker inspect github-discussions-analyzer | grep Health -A 10
```

### systemd 服务部署

#### 适用场景
- Linux服务器环境
- 需要系统级服务管理
- 开机自启动需求

#### 部署步骤
```bash
# 1. 安装Python依赖
python3 -m pip install -r requirements.txt

# 2. 创建服务用户（可选）
sudo useradd -r -s /bin/false github-analyzer

# 3. 配置权限
sudo chown -R github-analyzer:github-analyzer /path/to/project

# 4. 创建systemd服务
sudo tee /etc/systemd/system/github-analyzer.service > /dev/null << 'EOF'
[Unit]
Description=GitHub Discussions 自动化分析服务
After=network.target

[Service]
Type=simple
User=github-analyzer
WorkingDirectory=/path/to/project
Environment=PYTHONPATH=/path/to/project
EnvironmentFile=/path/to/project/.env
ExecStart=/usr/bin/python3 /path/to/project/src/main.py
Restart=always
RestartSec=10
StandardOutput=journal
StandardError=journal

[Install]
WantedBy=multi-user.target
EOF

# 5. 启用并启动服务
sudo systemctl daemon-reload
sudo systemctl enable github-analyzer
sudo systemctl start github-analyzer

# 6. 检查状态
sudo systemctl status github-analyzer
```

#### 服务管理
```bash
# 启动服务
sudo systemctl start github-analyzer

# 停止服务
sudo systemctl stop github-analyzer

# 重启服务
sudo systemctl restart github-analyzer

# 查看日志
sudo journalctl -u github-analyzer -f

# 查看服务状态
sudo systemctl status github-analyzer
```

### 开发模式部署

#### 适用场景
- 开发和测试环境
- 快速验证功能
- 调试和问题排查

#### 部署步骤
```bash
# 1. 创建虚拟环境（推荐）
python3 -m venv venv
source venv/bin/activate  # Linux/macOS
# 或 venv\Scripts\activate  # Windows

# 2. 安装依赖
pip install -r requirements.txt

# 3. 配置环境变量
export PYTHONPATH=$(pwd)
source .env

# 4. 运行服务
python src/main.py
```

#### 调试模式
```bash
# 设置调试环境变量
export LOG_LEVEL=DEBUG
export DEBUG=true

# 运行服务
python src/main.py
```

### Kubernetes 部署

#### 适用场景
- 大规模生产环境
- 需要高可用性
- 容器编排需求

#### ConfigMap 配置
```yaml
apiVersion: v1
kind: ConfigMap
metadata:
  name: github-analyzer-config
data:
  config.yaml: |
    github:
      organization: "your-org"
      repository: "your-repo"
      discussion_category: "2 - 日结"
    
    glm:
      model: "glm-4-flash"
      temperature: 0.7
    
    scheduler:
      cron_expression: "0 18 * * *"
      timezone: "Asia/Shanghai"
```

#### Secret 配置
```yaml
apiVersion: v1
kind: Secret
metadata:
  name: github-analyzer-secrets
type: Opaque
stringData:
  GITHUB_TOKEN: "your-github-token"
  GLM_API_KEY: "your-glm-api-key"
```

#### Deployment 配置
```yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: github-analyzer
spec:
  replicas: 1
  selector:
    matchLabels:
      app: github-analyzer
  template:
    metadata:
      labels:
        app: github-analyzer
    spec:
      containers:
      - name: github-analyzer
        image: github-analyzer:latest
        envFrom:
        - secretRef:
            name: github-analyzer-secrets
        volumeMounts:
        - name: config
          mountPath: /app/config
        - name: logs
          mountPath: /app/logs
        resources:
          requests:
            memory: "256Mi"
            cpu: "250m"
          limits:
            memory: "512Mi"
            cpu: "500m"
      volumes:
      - name: config
        configMap:
          name: github-analyzer-config
      - name: logs
        emptyDir: {}
```

#### 部署命令
```bash
# 应用配置
kubectl apply -f k8s/configmap.yaml
kubectl apply -f k8s/secret.yaml
kubectl apply -f k8s/deployment.yaml

# 查看状态
kubectl get pods -l app=github-analyzer
kubectl logs -l app=github-analyzer -f
```

## 配置管理

### 环境变量优先级
1. 系统环境变量（最高优先级）
2. .env 文件
3. config.yaml 配置文件
4. 默认值（最低优先级）

### 配置文件结构
```yaml
# config/config.yaml
github:
  organization: "your-org"
  repository: "your-repo"
  discussion_category: "2 - 日结"
  timeout: 30

glm:
  model: "glm-4-flash"
  temperature: 0.7
  max_tokens: 2000

analysis:
  enable_deviation_analysis: true
  enable_clarity_analysis: true
  enable_consistency_analysis: true

scheduler:
  cron_expression: "0 18 * * *"
  timezone: "Asia/Shanghai"
  retry_attempts: 3

logging:
  level: "INFO"
  file_path: "logs/analyzer.log"
```

### 敏感信息管理
```bash
# 使用环境变量存储敏感信息
export GITHUB_TOKEN="ghp_xxxxxxxxxxxx"
export GLM_API_KEY="your-api-key"

# 或使用密钥管理工具
# HashiCorp Vault
vault kv put secret/github-analyzer github_token="..." glm_api_key="..."

# Kubernetes Secrets
kubectl create secret generic github-analyzer-secrets \
  --from-literal=GITHUB_TOKEN="..." \
  --from-literal=GLM_API_KEY="..."
```

## 监控和维护

### 日志管理
```bash
# 查看实时日志
tail -f logs/analyzer.log

# 日志轮转配置（logrotate）
sudo tee /etc/logrotate.d/github-analyzer > /dev/null << 'EOF'
/path/to/project/logs/*.log {
    daily
    rotate 30
    compress
    delaycompress
    missingok
    notifempty
    create 644 github-analyzer github-analyzer
}
EOF
```

### 健康检查
```bash
# 检查服务状态
curl -f http://localhost:8080/health || echo "Service unhealthy"

# 检查配置
python -c "from src.config import Config; Config().validate()"

# 检查连接
python -c "
import asyncio
from src.analyzers.daily_analyzer import DailyAnalyzer
from src.config import Config

async def test():
    analyzer = DailyAnalyzer(Config())
    result = await analyzer.test_connections()
    print(f'Connections: {result}')

asyncio.run(test())
"
```

### 备份策略
```bash
# 配置文件备份
cp -r config/ backup/config-$(date +%Y%m%d)/

# 日志备份
tar -czf backup/logs-$(date +%Y%m%d).tar.gz logs/

# 数据备份（如果有持久化数据）
tar -czf backup/data-$(date +%Y%m%d).tar.gz data/
```

### 性能监控
```bash
# 系统资源监控
htop
iostat -x 1
free -h

# Docker 资源监控
docker stats github-discussions-analyzer

# 应用级监控
python -c "
import psutil
import os

pid = os.getpid()
process = psutil.Process(pid)
print(f'CPU: {process.cpu_percent()}%')
print(f'Memory: {process.memory_info().rss / 1024 / 1024:.1f} MB')
"
```

## 故障排除

### 常见问题

#### 1. GitHub API 限制
```bash
# 检查API限制
curl -H "Authorization: token $GITHUB_TOKEN" \
  https://api.github.com/rate_limit

# 解决方案：
# - 增加请求间隔
# - 使用多个Token轮换
# - 升级GitHub账户
```

#### 2. GLM API 调用失败
```bash
# 检查API密钥
curl -H "Authorization: Bearer $GLM_API_KEY" \
  https://open.bigmodel.cn/api/paas/v4/models

# 解决方案：
# - 验证API密钥有效性
# - 检查账户余额
# - 确认网络连接
```

#### 3. 定时任务未执行
```bash
# 检查Cron表达式
python -c "
from croniter import croniter
from datetime import datetime
cron = croniter('0 18 * * *', datetime.now())
print(f'Next run: {cron.get_next(datetime)}')
"

# 检查时区设置
timedatectl status
```

#### 4. 内存不足
```bash
# 检查内存使用
free -h
ps aux --sort=-%mem | head

# 解决方案：
# - 增加系统内存
# - 优化代码内存使用
# - 设置内存限制
```

### 调试工具

#### 日志分析
```bash
# 错误日志统计
grep ERROR logs/analyzer.log | wc -l

# 性能分析
grep "processing time" logs/analyzer.log | \
  awk '{print $NF}' | \
  sort -n | \
  tail -10
```

#### 网络诊断
```bash
# 测试GitHub连接
curl -I https://api.github.com

# 测试GLM连接
curl -I https://open.bigmodel.cn

# DNS解析测试
nslookup api.github.com
nslookup open.bigmodel.cn
```

## 安全考虑

### 访问控制
- 使用最小权限原则
- 定期轮换API密钥
- 限制网络访问

### 数据保护
- 加密存储敏感配置
- 使用HTTPS通信
- 定期备份重要数据

### 审计日志
- 记录所有API调用
- 监控异常行为
- 保留审计日志

## 性能优化

### 系统级优化
```bash
# 增加文件描述符限制
echo "* soft nofile 65536" >> /etc/security/limits.conf
echo "* hard nofile 65536" >> /etc/security/limits.conf

# 优化网络参数
echo "net.core.somaxconn = 65535" >> /etc/sysctl.conf
sysctl -p
```

### 应用级优化
```yaml
# config.yaml
performance:
  max_concurrent_requests: 10
  request_pool_size: 20
  cache_enabled: true
  cache_ttl: 1800
```

### Docker 优化
```dockerfile
# 多阶段构建
FROM python:3.11-slim as builder
COPY requirements.txt .
RUN pip install --user --no-cache-dir -r requirements.txt

FROM python:3.11-slim
COPY --from=builder /root/.local /root/.local
# ... 其他配置
```

## 扩展和定制

### 添加新的分析类型
1. 在 `src/analyzers/` 目录下创建新的分析器
2. 在 `GLMClient` 中添加相应的分析方法
3. 更新配置文件支持新的分析类型

### 集成其他服务
- 添加Webhook支持
- 集成Slack/钉钉通知
- 连接数据库存储结果

### 自定义报告格式
- 修改 `generate_comprehensive_analysis` 方法
- 添加新的报告模板
- 支持多种输出格式（JSON、HTML等）

## 版本升级

### 升级步骤
```bash
# 1. 备份当前版本
cp -r . ../backup-$(date +%Y%m%d)

# 2. 拉取新版本
git pull origin main

# 3. 更新依赖
pip install -r requirements.txt --upgrade

# 4. 检查配置兼容性
python -c "from src.config import Config; Config().validate()"

# 5. 重启服务
./deploy/deploy.sh restart
```

### 回滚方案
```bash
# 停止当前服务
./deploy/deploy.sh stop

# 恢复备份
rm -rf ./*
cp -r ../backup-20240115/* .

# 重新启动
./deploy/deploy.sh start
```

## 支持和社区

### 获取帮助
- 查看GitHub Issues
- 阅读API文档
- 联系维护团队

### 贡献代码
- Fork项目仓库
- 创建功能分支
- 提交Pull Request

### 报告问题
- 提供详细的错误信息
- 包含复现步骤
- 附上相关日志
