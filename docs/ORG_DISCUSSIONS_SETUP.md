# 组织级别Discussions设置指南

本指南专门针对使用**组织级别GitHub Discussions**的配置和设置。

## 📋 组织级别 vs 仓库级别

### 组织级别Discussions
- **URL格式**: `https://github.com/orgs/YOUR_ORG/discussions`
- **特点**: 整个组织共享，跨仓库协作
- **适用场景**: 团队日报、组织公告、跨项目讨论

### 仓库级别Discussions  
- **URL格式**: `https://github.com/YOUR_ORG/YOUR_REPO/discussions`
- **特点**: 特定仓库内的讨论
- **适用场景**: 项目相关的技术讨论、问题追踪

## 🔧 配置组织级别Discussions

### 1. 环境变量配置 (.env文件)

```bash
# GitHub配置
GITHUB_TOKEN=your_github_personal_access_token_here
GITHUB_ORG=your_organization_name
GITHUB_REPO=  # 组织级别时留空
USE_ORG_DISCUSSIONS=true  # 设置为true使用组织级别

# GLM-4.5配置
GLM_API_KEY=your_glm_api_key_here

# 其他配置...
SCHEDULE_CRON=0 18 * * *
TIMEZONE=Asia/Shanghai
LOG_LEVEL=INFO
```

### 2. YAML配置文件 (config/config.yaml)

```yaml
github:
  organization: "your-org-name"     # 您的GitHub组织名
  repository: ""                    # 组织级别时留空
  discussion_category: "2 - 日结"   # Discussion分类名称
  use_org_discussions: true         # 启用组织级别
  timeout: 30

glm:
  model: "glm-4-flash"
  temperature: 0.7

# 其他配置...
```

## 🔑 GitHub Token权限要求

对于组织级别的Discussions，Token需要以下权限：

### 必需权限
- ✅ `read:org` - 读取组织信息
- ✅ `read:discussion` - 读取讨论
- ✅ `write:discussion` - 写入讨论评论

### 可选权限
- `repo` - 如果组织有私有仓库且需要访问

### 获取Token步骤
1. GitHub → Settings → Developer settings → Personal access tokens
2. Generate new token (classic)
3. 选择上述权限
4. 复制生成的token (格式: `ghp_xxxxxxxxxxxx`)

## 📍 确认您的组织Discussions

### 1. 检查组织Discussions是否启用
访问: `https://github.com/orgs/YOUR_ORG/discussions`

如果看到404错误，说明：
- 组织未启用Discussions功能
- 您没有访问权限
- 组织名称不正确

### 2. 确认"2 - 日结"分类存在
在组织Discussions页面检查是否有"2 - 日结"分类。

如果没有，需要：
1. 联系组织管理员创建分类
2. 或者修改配置中的 `discussion_category` 为实际存在的分类名

### 3. 记录测试用的Discussion编号
找到几个现有的Discussion编号（如 #123, #124）用于测试。

## 🧪 测试组织级别配置

### 1. 基础连接测试
```bash
python scripts/test_service.py --test connections
```

### 2. 探索组织Discussions结构
```bash
python scripts/explore_discussions.py categories
```

### 3. 测试特定讨论解析
```bash
python scripts/test_daily_structure.py discuss 讨论编号
```

### 4. 完整测试
```bash
python scripts/full_test.py
```

## 🔍 常见问题排查

### Q: 提示"未找到组织"
**A**: 检查：
- 组织名称是否正确（区分大小写）
- Token是否有 `read:org` 权限
- 您是否是组织成员

### Q: 提示"无法访问Discussions"
**A**: 检查：
- 组织是否启用了Discussions功能
- 您的Token是否有 `read:discussion` 权限
- 组织Discussions是否设置为公开

### Q: 找不到"2 - 日结"分类
**A**: 
1. 访问组织Discussions页面确认分类名称
2. 修改配置文件中的 `discussion_category`
3. 或联系管理员创建该分类

### Q: 无法发布评论
**A**: 检查：
- Token是否有 `write:discussion` 权限
- 您是否有在该讨论中评论的权限
- 讨论是否已锁定

## 📝 配置示例

### 完整的 .env 配置示例
```bash
# GitHub配置 - 组织级别
GITHUB_TOKEN=ghp_1234567890abcdefghijklmnopqrstuvwxyz
GITHUB_ORG=my-company
GITHUB_REPO=
USE_ORG_DISCUSSIONS=true

# GLM-4.5配置
GLM_API_KEY=sk-1234567890abcdefghijk
GLM_BASE_URL=https://open.bigmodel.cn/api/paas/v4/

# 调度配置
SCHEDULE_CRON=0 18 * * *
TIMEZONE=Asia/Shanghai

# 分析功能
ENABLE_DEVIATION_ANALYSIS=true
ENABLE_CLARITY_ANALYSIS=true
ENABLE_CONSISTENCY_ANALYSIS=true

# 日志配置
LOG_LEVEL=INFO
LOG_FILE=logs/analyzer.log
```

## 🚀 启动服务

配置完成后：

1. **验证配置**:
   ```bash
   python scripts/full_test.py
   ```

2. **测试分析预览**:
   ```bash
   python scripts/manual_analysis.py discuss 讨论编号 --preview
   ```

3. **启动定时服务**:
   ```bash
   python src/main.py
   ```

4. **Docker部署**:
   ```bash
   docker-compose up -d
   ```

## 💡 最佳实践

### 权限管理
- 使用专门的机器人账号创建Token
- 定期轮换API密钥
- 限制Token权限范围

### 分类管理
- 与团队确认统一的分类命名
- 建立清晰的内容组织规范
- 定期清理过期讨论

### 监控运维
- 定期检查API调用限制
- 监控分析结果质量
- 备份重要的分析数据

通过以上配置，您就可以在组织级别使用GitHub Discussions自动化分析服务了！
