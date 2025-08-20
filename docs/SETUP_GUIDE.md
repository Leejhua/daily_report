# 设置指南

本指南将帮助您获取必要的API密钥和配置信息，以便运行GitHub Discussions自动化分析服务。

## 🔑 获取GitHub Personal Access Token

### 1. 访问GitHub设置页面
1. 登录您的GitHub账户
2. 点击右上角头像 → **Settings**
3. 在左侧菜单中找到 **Developer settings**
4. 点击 **Personal access tokens** → **Tokens (classic)**

### 2. 创建新Token
1. 点击 **Generate new token** → **Generate new token (classic)**
2. 填写Token描述，例如："GitHub Discussions Analyzer"
3. 设置过期时间（建议选择90天或自定义）

### 3. 选择权限范围
**必需权限**：
- ✅ `repo` - 完整的仓库访问权限（如果仓库是私有的）
- ✅ `read:discussion` - 读取讨论权限
- ✅ `write:discussion` - 写入讨论权限

**可选权限**：
- `read:org` - 读取组织信息（如果需要）

### 4. 生成并保存Token
1. 点击 **Generate token**
2. **重要**：立即复制Token（格式：`ghp_xxxxxxxxxxxxxxxxxxxx`）
3. Token只显示一次，请妥善保存

## 🤖 获取GLM-4.5 API密钥

### 1. 注册智谱AI账户
1. 访问 [智谱AI开放平台](https://open.bigmodel.cn/)
2. 点击右上角 **登录/注册**
3. 使用手机号或邮箱注册账户

### 2. 实名认证
1. 登录后进入控制台
2. 完成实名认证（个人或企业）
3. 认证通过后可以使用API服务

### 3. 获取API密钥
1. 进入 **API管理** → **API Keys**
2. 点击 **创建新的API Key**
3. 输入密钥名称，例如："Discussions Analyzer"
4. 复制生成的API密钥（格式类似：`sk-xxxxxxxxxxxxxxxx`）

### 4. 充值余额（如需要）
1. 进入 **账户管理** → **余额管理**
2. 根据需要充值（GLM-4-flash模型相对便宜）
3. 查看计费标准和余额情况

## 📋 找到您的GitHub组织和仓库信息

### 1. 确认组织名称
- 访问您的GitHub组织页面
- URL格式：`https://github.com/YOUR_ORG_NAME`
- 组织名称就是URL中的 `YOUR_ORG_NAME` 部分

### 2. 确认仓库名称
- 访问包含Discussions的仓库
- URL格式：`https://github.com/YOUR_ORG/YOUR_REPO`
- 仓库名称就是URL中的 `YOUR_REPO` 部分

### 3. 验证Discussions功能
1. 确认仓库已启用Discussions功能
2. 访问 `https://github.com/YOUR_ORG/YOUR_REPO/discussions`
3. 确认存在"2 - 日结"分类
4. 记录几个现有Discussion的编号（用于测试）

## 🔧 创建配置文件

### 1. 创建环境变量文件
在项目根目录创建 `.env` 文件：

```bash
# GitHub配置
GITHUB_TOKEN=ghp_your_github_token_here
GITHUB_ORG=your_organization_name
GITHUB_REPO=your_repository_name

# GLM-4.5配置
GLM_API_KEY=your_glm_api_key_here

# 调度配置（可选）
SCHEDULE_CRON=0 18 * * *
TIMEZONE=Asia/Shanghai

# 日志配置（可选）
LOG_LEVEL=INFO
```

### 2. 创建YAML配置文件（可选）
复制并编辑配置文件：

```bash
cp config/config.yaml.example config/config.yaml
```

编辑 `config/config.yaml`，调整以下关键配置：

```yaml
github:
  organization: "your-org-name"
  repository: "your-repo-name"
  discussion_category: "2 - 日结"

glm:
  model: "glm-4-flash"
  temperature: 0.7

scheduler:
  cron_expression: "0 18 * * *"
  timezone: "Asia/Shanghai"
```

## ✅ 验证配置

### 1. 运行配置测试
```bash
python scripts/full_test.py
```

### 2. 快速连接测试
```bash
python scripts/test_service.py --test connections
```

### 3. 测试Discussion结构
```bash
python scripts/test_daily_structure.py recent
```

## 🔒 安全注意事项

### API密钥安全
1. **不要**将API密钥提交到版本控制系统
2. **不要**在代码中硬编码API密钥
3. **定期轮换**API密钥
4. **限制权限**，只授予必需的最小权限

### 文件权限设置
```bash
# 设置配置文件权限（仅所有者可读写）
chmod 600 .env
chmod 600 config/config.yaml
```

### Token权限最小化
- 只为Token授予必需的权限
- 定期检查和更新Token权限
- 监控Token使用情况

## 🆘 常见问题

### Q: GitHub Token权限不足
**A**: 确保Token包含以下权限：
- `repo`（私有仓库）或 `public_repo`（公开仓库）
- `read:discussion`
- `write:discussion`

### Q: GLM API调用失败
**A**: 检查以下项目：
- API密钥是否正确
- 账户余额是否充足
- 网络连接是否正常
- API调用频率是否超限

### Q: 找不到"2 - 日结"分类
**A**: 确认：
- 仓库已启用Discussions功能
- 分类名称完全匹配（包括空格和标点）
- 您有访问该分类的权限

### Q: Discussion内容解析错误
**A**: 检查：
- Discussion是否有评论
- 评论内容是否包含关键词
- 日期过滤是否正确

## 📞 获取帮助

如果遇到问题：

1. **查看日志**：检查 `logs/analyzer.log` 文件
2. **运行测试**：使用 `scripts/full_test.py` 诊断问题
3. **检查配置**：确认所有配置项正确填写
4. **网络连接**：确认可以访问GitHub和GLM API

## 🚀 下一步

配置完成后：

1. 运行完整测试：`python scripts/full_test.py`
2. 测试分析预览：`python scripts/test_daily_structure.py preview 讨论编号`
3. 启动服务：`python src/main.py`
4. 查看定时任务：服务将按配置的时间自动运行
