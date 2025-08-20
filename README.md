# GitHub Discussions 自动化分析服务

基于GLM-4.5模型的GitHub Discussions内容自动化分析系统，专门用于分析"日结"分类中的工作总结和计划内容。

## 功能特性

### 🕒 定时自动执行
- 支持每日固定时间点自动触发
- 基于Cron表达式的灵活调度配置
- 自动重试机制和错误恢复

### 🔍 GitHub Discussions集成
- 自动访问指定GitHub组织的Discussions
- 专门读取"2 - 日结"分类内容
- 智能识别当日更新的内容
- 支持周期计划（首楼）+ 日计划/日报（评论）结构

### 🤖 GLM-4.5智能分析
- **工作偏离度评估**：对比实际完成工作与预设计划的偏离程度
- **内容完整性分析**：评估日结描述的清晰度、准确性和完整性
- **计划一致性分析**：检查日计划与周期计划的一致性

### 📝 自动化评论发布
- 将分析结果自动发布为Discussion评论
- 结构化的分析报告格式
- 支持Markdown格式的详细反馈

## 技术架构

```
├── src/
│   ├── main.py              # 主程序入口
│   ├── config.py            # 配置管理
│   ├── scheduler.py         # 定时任务调度器
│   ├── clients/
│   │   ├── github_client.py # GitHub API客户端
│   │   └── glm_client.py    # GLM-4.5模型客户端
│   ├── analyzers/
│   │   ├── deviation_analyzer.py    # 偏离度分析器
│   │   ├── clarity_analyzer.py      # 清晰度分析器
│   │   └── consistency_analyzer.py  # 一致性分析器
│   ├── models/
│   │   └── data_models.py   # 数据模型定义
│   └── utils/
│       ├── logger.py        # 日志工具
│       └── helpers.py       # 辅助工具
├── config/
│   ├── config.yaml          # 主配置文件
│   └── prompts/             # GLM提示词模板
├── logs/                    # 日志文件目录
├── requirements.txt         # Python依赖
├── Dockerfile              # Docker容器配置
├── docker-compose.yml      # Docker Compose配置
└── deploy/                 # 部署脚本
```

## 快速开始

### 环境要求
- Python 3.9+
- GitHub Personal Access Token (具有Discussions读写权限)
- GLM-4.5 API密钥

### 安装步骤

1. **克隆项目**
```bash
git clone <repository-url>
cd github-discussions-analyzer
```

2. **安装依赖**
```bash
pip install -r requirements.txt
```

3. **配置环境变量**
```bash
cp env.example .env
# 编辑.env文件，填入必要的API密钥和配置
```

4. **配置服务参数**
```bash
cp config/config.yaml.example config/config.yaml
# 编辑config.yaml，设置GitHub组织、仓库等信息
```

5. **测试配置**
```bash
python scripts/test_service.py --test connections
```

6. **测试日报结构解析**
```bash
# 测试最近的讨论结构
python scripts/test_daily_structure.py recent

# 测试特定讨论
python scripts/test_daily_structure.py discuss 讨论编号
```

7. **运行服务**
```bash
python src/main.py
```

### Docker部署

```bash
# 构建镜像
docker-compose build

# 启动服务
docker-compose up -d
```

## 配置说明

### 环境变量 (.env)
```env
# GitHub配置
GITHUB_TOKEN=your_github_token_here
GITHUB_ORG=your_organization_name
GITHUB_REPO=your_repository_name

# GLM-4.5配置
GLM_API_KEY=your_glm_api_key_here
GLM_BASE_URL=https://open.bigmodel.cn/api/paas/v4/

# 调度配置
SCHEDULE_CRON=0 18 * * *  # 每天18:00执行
TIMEZONE=Asia/Shanghai

# 日志配置
LOG_LEVEL=INFO
LOG_FILE=logs/analyzer.log
```

### 主配置文件 (config/config.yaml)
```yaml
github:
  organization: "your-org"
  repository: "your-repo"
  discussion_category: "2 - 日结"
  
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
  retry_delay: 300  # 5分钟
```

## 分析功能详解

### 1. 工作偏离度评估
- 自动提取"日结"和"计划"内容
- 使用GLM-4.5模型分析完成度和偏离度
- 生成量化评分和详细说明

### 2. 内容清晰度分析
- 评估描述的具体性和准确性
- 识别模糊或不完整的表述
- 提供改进建议

### 3. 计划一致性分析
- 对比日计划与周期计划的一致性
- 检测计划偏离和调整合理性
- 评估计划执行的连贯性

## 输出示例

服务将在对应的Discussion下自动发布如下格式的分析评论：

```markdown
## 📊 每日工作分析报告 - 2024-01-15

### 🎯 工作偏离度评估
**评分**: 8.5/10
- ✅ 主要计划任务完成度: 85%
- ⚠️ 偏离项目: 临时会议占用2小时
- 💡 建议: 建议预留缓冲时间处理突发事务

### 📝 内容清晰度分析
**评分**: 7.5/10
- ✅ 技术实现描述详细
- ⚠️ 需要改进: "优化了性能"表述过于笼统
- 💡 建议: 补充具体的性能指标和优化方法

### 🔄 计划一致性分析
**评分**: 9.0/10
- ✅ 与周计划高度一致
- ✅ 优先级安排合理
- 💡 建议: 保持当前计划执行节奏

---
*本分析由GLM-4.5自动生成 | 生成时间: 2024-01-15 18:00:00*
```

## 监控与日志

### 日志级别
- `DEBUG`: 详细的调试信息
- `INFO`: 一般运行信息
- `WARNING`: 警告信息
- `ERROR`: 错误信息
- `CRITICAL`: 严重错误

### 监控指标
- 任务执行成功率
- API调用响应时间
- 分析准确性指标
- 系统资源使用情况

## 故障排除

### 常见问题

1. **GitHub API限制**
   - 检查Token权限
   - 确认API调用频率限制
   - 查看网络连接状态

2. **GLM-4.5调用失败**
   - 验证API密钥有效性
   - 检查余额和配额
   - 确认请求格式正确

3. **定时任务未执行**
   - 检查Cron表达式格式
   - 确认时区设置
   - 查看系统时间同步

### 日志查看
```bash
# 查看实时日志
tail -f logs/analyzer.log

# 查看错误日志
grep ERROR logs/analyzer.log

# 查看今日日志
grep "$(date +%Y-%m-%d)" logs/analyzer.log
```

## 贡献指南

欢迎提交Issue和Pull Request来改进这个项目。

## 许可证

本项目采用MIT许可证。

## 联系方式

如有问题或建议，请通过以下方式联系：
- 提交GitHub Issue
- 发送邮件至项目维护者
