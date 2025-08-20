# 配置指南

本文档详细说明了GitHub Discussions自动化分析服务的所有配置选项。

## 配置文件结构

系统支持多种配置方式，按优先级从高到低：

1. **环境变量** - 最高优先级
2. **`.env` 文件** - 中等优先级  
3. **`config.yaml` 文件** - 低优先级
4. **默认值** - 最低优先级

## 环境变量配置

### 必需的环境变量

```bash
# GitHub 配置
GITHUB_TOKEN=ghp_xxxxxxxxxxxxxxxxxxxx    # GitHub Personal Access Token
GITHUB_ORG=your-organization            # GitHub组织名称
GITHUB_REPO=your-repository             # GitHub仓库名称

# GLM-4.5 配置
GLM_API_KEY=your-glm-api-key            # GLM-4.5 API密钥
```

### 可选的环境变量

```bash
# GitHub 配置
GITHUB_DISCUSSION_CATEGORY="2 - 日结"   # Discussion分类名称（默认）
GITHUB_API_BASE_URL=https://api.github.com  # GitHub API基础URL
GITHUB_TIMEOUT=30                       # API请求超时时间（秒）

# GLM-4.5 配置
GLM_BASE_URL=https://open.bigmodel.cn/api/paas/v4/  # GLM API基础URL
GLM_MODEL=glm-4-flash                   # 使用的模型名称
GLM_TEMPERATURE=0.7                     # 生成温度参数
GLM_MAX_TOKENS=2000                     # 最大生成token数
GLM_TOP_P=0.9                          # Top-p采样参数
GLM_TIMEOUT=60                          # API请求超时时间（秒）

# 调度配置
SCHEDULE_CRON="0 18 * * *"              # Cron表达式（每天18:00）
TIMEZONE=Asia/Shanghai                  # 时区设置
RETRY_ATTEMPTS=3                        # 失败重试次数
RETRY_DELAY=300                         # 重试延迟时间（秒）

# 分析功能开关
ENABLE_DEVIATION_ANALYSIS=true          # 启用偏离度分析
ENABLE_CLARITY_ANALYSIS=true            # 启用清晰度分析
ENABLE_CONSISTENCY_ANALYSIS=true        # 启用一致性分析

# 日志配置
LOG_LEVEL=INFO                          # 日志级别
LOG_FILE=logs/analyzer.log              # 日志文件路径
LOG_MAX_SIZE=10MB                       # 日志文件最大大小
LOG_BACKUP_COUNT=5                      # 日志备份文件数量

# 性能配置
MAX_CONCURRENT_REQUESTS=5               # 最大并发请求数
REQUEST_TIMEOUT=30                      # 请求超时时间（秒）
```

## YAML 配置文件

### 基本配置结构

```yaml
# config/config.yaml

# GitHub 配置
github:
  organization: "your-org"              # 必需：GitHub组织名
  repository: "your-repo"               # 必需：GitHub仓库名
  discussion_category: "2 - 日结"       # Discussion分类名称
  api_base_url: "https://api.github.com"  # GitHub API基础URL
  timeout: 30                           # API请求超时时间（秒）

# GLM-4.5 配置
glm:
  model: "glm-4-flash"                  # 模型名称
  base_url: "https://open.bigmodel.cn/api/paas/v4/"  # API基础URL
  temperature: 0.7                      # 生成温度参数 (0.0-1.0)
  max_tokens: 2000                      # 最大生成token数
  top_p: 0.9                           # Top-p采样参数 (0.0-1.0)
  timeout: 60                          # API请求超时时间（秒）

# 分析功能配置
analysis:
  enable_deviation_analysis: true       # 启用偏离度分析
  enable_clarity_analysis: true         # 启用清晰度分析
  enable_consistency_analysis: true     # 启用一致性分析
  
  # 分析阈值配置
  thresholds:
    deviation_warning: 0.3              # 偏离度警告阈值
    deviation_critical: 0.5             # 偏离度严重阈值
    clarity_minimum: 0.6                # 清晰度最低要求
    consistency_minimum: 0.7            # 一致性最低要求

# 定时任务配置
scheduler:
  cron_expression: "0 18 * * *"         # Cron表达式
  timezone: "Asia/Shanghai"             # 时区设置
  retry_attempts: 3                     # 失败重试次数
  retry_delay: 300                      # 重试延迟时间（秒）
  max_execution_time: 1800              # 最大执行时间（秒）

# 日志配置
logging:
  level: "INFO"                         # 日志级别
  format: "%(asctime)s - %(name)s - %(levelname)s - %(message)s"  # 日志格式
  file_path: "logs/analyzer.log"        # 日志文件路径
  max_size: "10MB"                      # 日志文件最大大小
  backup_count: 5                       # 备份文件数量

# 性能配置
performance:
  max_concurrent_requests: 5            # 最大并发请求数
  request_pool_size: 10                # 请求池大小
  cache_enabled: true                   # 启用缓存
  cache_ttl: 3600                      # 缓存过期时间（秒）

# 通知配置（可选）
notifications:
  enabled: false                        # 启用通知
  webhook_url: ""                       # Webhook URL
  email:
    enabled: false                      # 启用邮件通知
    smtp_server: ""                     # SMTP服务器
    smtp_port: 587                      # SMTP端口
    username: ""                        # 邮箱用户名
    password: ""                        # 邮箱密码
    recipients: []                      # 收件人列表
```

## 详细配置说明

### GitHub 配置

#### `github.organization`
- **类型**: 字符串
- **必需**: 是
- **说明**: GitHub组织名称
- **示例**: `"microsoft"`, `"google"`

#### `github.repository`
- **类型**: 字符串
- **必需**: 是
- **说明**: GitHub仓库名称
- **示例**: `"vscode"`, `"tensorflow"`

#### `github.discussion_category`
- **类型**: 字符串
- **默认值**: `"2 - 日结"`
- **说明**: 要分析的Discussion分类名称
- **注意**: 必须与GitHub Discussions中的分类名完全匹配

#### `github.token`
- **类型**: 字符串
- **必需**: 是（通过环境变量设置）
- **说明**: GitHub Personal Access Token
- **权限要求**:
  - `repo` - 访问私有仓库（如果需要）
  - `read:discussion` - 读取Discussions
  - `write:discussion` - 写入Discussions评论

#### `github.api_base_url`
- **类型**: 字符串
- **默认值**: `"https://api.github.com"`
- **说明**: GitHub API基础URL
- **用途**: 用于GitHub Enterprise Server

#### `github.timeout`
- **类型**: 整数
- **默认值**: `30`
- **单位**: 秒
- **说明**: GitHub API请求超时时间

### GLM-4.5 配置

#### `glm.api_key`
- **类型**: 字符串
- **必需**: 是（通过环境变量设置）
- **说明**: 智谱AI GLM-4.5 API密钥
- **获取方式**: 在智谱AI开放平台申请

#### `glm.model`
- **类型**: 字符串
- **默认值**: `"glm-4-flash"`
- **可选值**: 
  - `"glm-4-flash"` - 快速版本
  - `"glm-4"` - 标准版本
  - `"glm-4-plus"` - 增强版本
- **说明**: 使用的GLM模型版本

#### `glm.temperature`
- **类型**: 浮点数
- **范围**: 0.0 - 1.0
- **默认值**: `0.7`
- **说明**: 控制生成文本的随机性
  - 0.0 = 最确定性
  - 1.0 = 最随机性
  - 推荐值: 0.3-0.7

#### `glm.max_tokens`
- **类型**: 整数
- **默认值**: `2000`
- **说明**: 单次生成的最大token数
- **注意**: 过大可能导致成本增加

#### `glm.top_p`
- **类型**: 浮点数
- **范围**: 0.0 - 1.0
- **默认值**: `0.9`
- **说明**: Top-p采样参数，控制词汇选择范围

#### `glm.timeout`
- **类型**: 整数
- **默认值**: `60`
- **单位**: 秒
- **说明**: GLM API请求超时时间

### 分析功能配置

#### 功能开关
- `enable_deviation_analysis`: 启用工作偏离度分析
- `enable_clarity_analysis`: 启用内容清晰度分析
- `enable_consistency_analysis`: 启用计划一致性分析

#### 分析阈值
```yaml
thresholds:
  deviation_warning: 0.3        # 偏离度警告阈值（0-1）
  deviation_critical: 0.5       # 偏离度严重阈值（0-1）
  clarity_minimum: 0.6          # 清晰度最低要求（0-1）
  consistency_minimum: 0.7      # 一致性最低要求（0-1）
```

### 调度器配置

#### `scheduler.cron_expression`
- **类型**: 字符串
- **默认值**: `"0 18 * * *"`
- **说明**: Cron表达式，定义执行时间
- **格式**: `分 时 日 月 周`
- **示例**:
  - `"0 18 * * *"` - 每天18:00
  - `"0 9,18 * * *"` - 每天9:00和18:00
  - `"0 18 * * 1-5"` - 工作日18:00
  - `"30 17 * * *"` - 每天17:30

#### `scheduler.timezone`
- **类型**: 字符串
- **默认值**: `"Asia/Shanghai"`
- **说明**: 时区设置
- **常用值**:
  - `"UTC"` - 协调世界时
  - `"Asia/Shanghai"` - 中国标准时间
  - `"America/New_York"` - 美国东部时间
  - `"Europe/London"` - 英国时间

#### `scheduler.retry_attempts`
- **类型**: 整数
- **默认值**: `3`
- **说明**: 任务失败后的重试次数

#### `scheduler.retry_delay`
- **类型**: 整数
- **默认值**: `300`
- **单位**: 秒
- **说明**: 重试间隔时间

#### `scheduler.max_execution_time`
- **类型**: 整数
- **默认值**: `1800`
- **单位**: 秒
- **说明**: 单次任务最大执行时间

### 日志配置

#### `logging.level`
- **类型**: 字符串
- **默认值**: `"INFO"`
- **可选值**: `"DEBUG"`, `"INFO"`, `"WARNING"`, `"ERROR"`, `"CRITICAL"`
- **说明**: 日志记录级别

#### `logging.file_path`
- **类型**: 字符串
- **默认值**: `"logs/analyzer.log"`
- **说明**: 日志文件路径

#### `logging.max_size`
- **类型**: 字符串
- **默认值**: `"10MB"`
- **格式**: 数字+单位（KB, MB, GB）
- **说明**: 单个日志文件最大大小

#### `logging.backup_count`
- **类型**: 整数
- **默认值**: `5`
- **说明**: 保留的日志备份文件数量

### 性能配置

#### `performance.max_concurrent_requests`
- **类型**: 整数
- **默认值**: `5`
- **说明**: 最大并发API请求数
- **建议**: 根据API限制和服务器性能调整

#### `performance.request_pool_size`
- **类型**: 整数
- **默认值**: `10`
- **说明**: HTTP连接池大小

#### `performance.cache_enabled`
- **类型**: 布尔值
- **默认值**: `true`
- **说明**: 是否启用结果缓存

#### `performance.cache_ttl`
- **类型**: 整数
- **默认值**: `3600`
- **单位**: 秒
- **说明**: 缓存过期时间

### 通知配置

#### Webhook 通知
```yaml
notifications:
  enabled: true
  webhook_url: "https://hooks.slack.com/services/..."
```

#### 邮件通知
```yaml
notifications:
  email:
    enabled: true
    smtp_server: "smtp.gmail.com"
    smtp_port: 587
    username: "your-email@gmail.com"
    password: "your-app-password"
    recipients:
      - "admin@company.com"
      - "team@company.com"
```

## 配置验证

### 自动验证
服务启动时会自动验证配置：

```python
from src.config import Config

# 创建配置实例
config = Config()

# 验证配置
try:
    config.validate()
    print("配置验证通过")
except ValueError as e:
    print(f"配置错误: {e}")
```

### 手动验证
```bash
# 验证配置文件语法
python -c "
import yaml
with open('config/config.yaml') as f:
    yaml.safe_load(f)
print('YAML语法正确')
"

# 验证环境变量
python -c "
import os
required = ['GITHUB_TOKEN', 'GITHUB_ORG', 'GITHUB_REPO', 'GLM_API_KEY']
missing = [var for var in required if not os.getenv(var)]
if missing:
    print(f'缺少环境变量: {missing}')
else:
    print('环境变量配置完整')
"
```

## 配置示例

### 开发环境配置
```yaml
# config/config.dev.yaml
github:
  organization: "test-org"
  repository: "test-repo"
  
glm:
  temperature: 0.3  # 更确定的输出
  
scheduler:
  cron_expression: "*/5 * * * *"  # 每5分钟执行（测试用）
  
logging:
  level: "DEBUG"
  
performance:
  max_concurrent_requests: 2  # 降低并发
```

### 生产环境配置
```yaml
# config/config.prod.yaml
github:
  timeout: 60  # 增加超时时间
  
glm:
  temperature: 0.7
  max_tokens: 3000  # 增加token限制
  
scheduler:
  cron_expression: "0 18 * * *"
  retry_attempts: 5  # 增加重试次数
  
logging:
  level: "INFO"
  max_size: "50MB"  # 增加日志文件大小
  backup_count: 10  # 增加备份数量
  
performance:
  max_concurrent_requests: 10  # 增加并发
  cache_enabled: true
  
notifications:
  enabled: true
  webhook_url: "${SLACK_WEBHOOK_URL}"
```

### 高性能配置
```yaml
# config/config.performance.yaml
performance:
  max_concurrent_requests: 20
  request_pool_size: 50
  cache_enabled: true
  cache_ttl: 1800  # 30分钟缓存

glm:
  timeout: 120  # 增加超时时间
  
github:
  timeout: 90
  
logging:
  level: "WARNING"  # 减少日志输出
```

## 配置最佳实践

### 安全性
1. **敏感信息**: 始终通过环境变量设置API密钥
2. **权限最小化**: GitHub Token只授予必需权限
3. **定期轮换**: 定期更换API密钥
4. **访问控制**: 限制配置文件访问权限

```bash
# 设置配置文件权限
chmod 600 config/config.yaml
chmod 600 .env
```

### 可维护性
1. **环境分离**: 为不同环境使用不同配置文件
2. **文档化**: 为自定义配置添加注释
3. **版本控制**: 配置模板纳入版本控制
4. **备份**: 定期备份配置文件

### 性能优化
1. **合理设置并发数**: 根据API限制调整
2. **启用缓存**: 减少重复API调用
3. **调整超时时间**: 平衡响应速度和稳定性
4. **日志级别**: 生产环境使用INFO或WARNING级别

### 监控配置
```yaml
# 添加监控相关配置
monitoring:
  metrics_enabled: true
  metrics_port: 8080
  health_check_path: "/health"
  
alerts:
  error_threshold: 5  # 错误数阈值
  response_time_threshold: 30  # 响应时间阈值（秒）
```

## 故障排除

### 配置相关问题

#### 1. 配置文件未找到
```bash
# 检查文件路径
ls -la config/config.yaml

# 检查权限
ls -la config/
```

#### 2. YAML 语法错误
```bash
# 验证YAML语法
python -c "
import yaml
try:
    with open('config/config.yaml') as f:
        yaml.safe_load(f)
    print('YAML语法正确')
except yaml.YAMLError as e:
    print(f'YAML语法错误: {e}')
"
```

#### 3. 环境变量未生效
```bash
# 检查环境变量
env | grep GITHUB
env | grep GLM

# 检查.env文件加载
python -c "
from dotenv import load_dotenv
import os
load_dotenv()
print(f'GITHUB_TOKEN: {bool(os.getenv(\"GITHUB_TOKEN\"))}')
print(f'GLM_API_KEY: {bool(os.getenv(\"GLM_API_KEY\"))}')
"
```

#### 4. 时区问题
```bash
# 检查系统时区
timedatectl status

# 验证Python时区
python -c "
import pytz
from datetime import datetime
tz = pytz.timezone('Asia/Shanghai')
now = datetime.now(tz)
print(f'当前时间: {now}')
"
```

### 配置调试
```python
# 调试配置加载
from src.config import Config

config = Config()
summary = config.get_config_summary()
print(json.dumps(summary, indent=2, ensure_ascii=False))
```
