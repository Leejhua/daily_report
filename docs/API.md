# API 文档

GitHub Discussions 自动化分析服务内部API接口文档。

## 核心类接口

### GitHubClient

GitHub API客户端，负责与GitHub Discussions的交互。

#### 初始化
```python
from src.clients.github_client import GitHubClient
from src.config import GitHubConfig

config = GitHubConfig(
    token="your_token",
    organization="your_org",
    repository="your_repo"
)
client = GitHubClient(config)
```

#### 主要方法

##### `get_daily_discussions(target_date=None)`
获取指定日期的"日结"分类讨论。

**参数:**
- `target_date` (Optional[date]): 目标日期，默认为今天

**返回:**
- `List[DiscussionData]`: 讨论列表

**示例:**
```python
from datetime import date
discussions = await client.get_daily_discussions(date(2024, 1, 15))
```

##### `get_discussion_comments(discussion_number)`
获取指定讨论的所有评论。

**参数:**
- `discussion_number` (int): 讨论编号

**返回:**
- `List[CommentData]`: 评论列表

##### `post_analysis_comment(discussion_number, analysis_content)`
在指定讨论下发布分析评论。

**参数:**
- `discussion_number` (int): 讨论编号
- `analysis_content` (str): 分析内容（Markdown格式）

**返回:**
- `bool`: 是否成功发布

##### `extract_daily_content(discussion)`
从讨论内容中提取日结和计划内容。

**参数:**
- `discussion` (DiscussionData): 讨论数据

**返回:**
- `Dict[str, str]`: 包含'daily_summary'和'daily_plan'的字典

### GLMClient

GLM-4.5模型客户端，负责内容分析。

#### 初始化
```python
from src.clients.glm_client import GLMClient
from src.config import GLMConfig

config = GLMConfig(
    api_key="your_api_key",
    model="glm-4-flash"
)
client = GLMClient(config)
```

#### 主要方法

##### `analyze_work_deviation(daily_summary, daily_plan)`
分析工作偏离度。

**参数:**
- `daily_summary` (str): 日结内容
- `daily_plan` (str): 日计划内容

**返回:**
- `Dict[str, Any]`: 偏离度分析结果

**返回格式:**
```json
{
    "score": 5.5,
    "completion_rate": 0.8,
    "deviation_reasons": ["临时会议占用时间"],
    "additional_work": ["处理紧急bug"],
    "suggestions": ["建议预留缓冲时间"],
    "summary": "整体执行良好，有少量偏离"
}
```

##### `analyze_content_clarity(daily_summary)`
分析内容清晰度。

**参数:**
- `daily_summary` (str): 日结内容

**返回:**
- `Dict[str, Any]`: 清晰度分析结果

**返回格式:**
```json
{
    "clarity_score": 7.5,
    "specificity_score": 8.0,
    "completeness_score": 6.5,
    "unclear_parts": ["性能优化部分描述模糊"],
    "missing_info": ["缺少具体的性能指标"],
    "improvement_suggestions": ["建议补充具体数据"],
    "summary": "总体清晰，部分细节需完善"
}
```

##### `analyze_plan_consistency(daily_plan, weekly_plan)`
分析计划一致性。

**参数:**
- `daily_plan` (str): 日计划内容
- `weekly_plan` (str): 周期计划内容

**返回:**
- `Dict[str, Any]`: 一致性分析结果

##### `generate_comprehensive_analysis(daily_summary, daily_plan, weekly_plan="")`
生成综合分析报告。

**参数:**
- `daily_summary` (str): 日结内容
- `daily_plan` (str): 日计划内容
- `weekly_plan` (str): 周期计划内容

**返回:**
- `str`: Markdown格式的综合分析报告

### DailyAnalyzer

日结分析器，协调整个分析流程。

#### 初始化
```python
from src.analyzers.daily_analyzer import DailyAnalyzer
from src.config import Config

config = Config()
analyzer = DailyAnalyzer(config)
```

#### 主要方法

##### `run_daily_analysis(target_date=None)`
运行每日分析任务。

**参数:**
- `target_date` (Optional[date]): 目标分析日期，默认为今天

**返回:**
- `Dict[str, Any]`: 分析结果摘要

**返回格式:**
```json
{
    "date": "2024-01-15",
    "start_time": "2024-01-15T18:00:00",
    "discussions_analyzed": 3,
    "comments_posted": 3,
    "errors": [],
    "success": true,
    "end_time": "2024-01-15T18:05:30"
}
```

##### `analyze_specific_discussion(discussion_number)`
分析指定的讨论。

**参数:**
- `discussion_number` (int): 讨论编号

**返回:**
- `Dict[str, Any]`: 分析结果

##### `test_connections()`
测试所有外部连接。

**返回:**
- `Dict[str, bool]`: 连接测试结果

**返回格式:**
```json
{
    "github": true,
    "glm": true,
    "overall": true
}
```

##### `get_analysis_preview(discussion_number)`
获取分析预览（不发布评论）。

**参数:**
- `discussion_number` (int): 讨论编号

**返回:**
- `Dict[str, Any]`: 分析预览结果

### AnalysisScheduler

定时任务调度器。

#### 初始化
```python
from src.scheduler import AnalysisScheduler
from src.config import Config

config = Config()
scheduler = AnalysisScheduler(config)
```

#### 主要方法

##### `start()`
启动调度器。

##### `stop()`
停止调度器。

##### `run_once()`
手动执行一次分析任务（用于测试）。

##### `get_status()`
获取调度器状态。

**返回:**
- `Dict[str, Any]`: 调度器状态

**返回格式:**
```json
{
    "running": true,
    "cron_expression": "0 18 * * *",
    "timezone": "Asia/Shanghai",
    "next_run_time": "2024-01-16T18:00:00+08:00",
    "current_task_running": false,
    "last_run_time": "2024-01-15T18:00:00+08:00"
}
```

## 数据模型

### DiscussionData
讨论数据模型。

```python
@dataclass
class DiscussionData:
    id: str
    number: int
    title: str
    body: str
    author: str
    created_at: datetime
    updated_at: datetime
    category: str
    url: str
    comments_count: int
```

### CommentData
评论数据模型。

```python
@dataclass
class CommentData:
    id: str
    body: str
    author: str
    created_at: datetime
    updated_at: datetime
```

### ComprehensiveAnalysisResult
综合分析结果模型。

```python
@dataclass
class ComprehensiveAnalysisResult:
    discussion_metadata: DiscussionMetadata
    content_extraction: ContentExtraction
    deviation_analysis: Optional[DeviationAnalysisResult]
    clarity_analysis: Optional[ClarityAnalysisResult]
    consistency_analysis: Optional[ConsistencyAnalysisResult]
    analysis_timestamp: datetime
    processing_time: float
```

## 错误处理

### 常见异常

#### `GithubException`
GitHub API相关异常。

**处理方式:**
```python
from github import GithubException

try:
    discussions = await client.get_daily_discussions()
except GithubException as e:
    logger.error(f"GitHub API错误: {e}")
    # 处理错误逻辑
```

#### `APIError`
GLM API相关异常。

**处理方式:**
```python
from zhipuai.core._errors import APIError

try:
    result = await client.analyze_work_deviation(summary, plan)
except APIError as e:
    logger.error(f"GLM API错误: {e}")
    # 处理错误逻辑
```

#### `ConfigurationError`
配置相关异常。

**处理方式:**
```python
try:
    config = Config()
    config.validate()
except ValueError as e:
    logger.error(f"配置错误: {e}")
    # 处理错误逻辑
```

## 使用示例

### 完整的分析流程

```python
import asyncio
from src.config import Config
from src.analyzers.daily_analyzer import DailyAnalyzer

async def main():
    # 初始化配置
    config = Config()
    
    # 创建分析器
    analyzer = DailyAnalyzer(config)
    
    # 测试连接
    connections = await analyzer.test_connections()
    if not connections['overall']:
        print("连接测试失败")
        return
    
    # 运行分析
    result = await analyzer.run_daily_analysis()
    print(f"分析完成: {result}")

if __name__ == "__main__":
    asyncio.run(main())
```

### 分析特定讨论

```python
async def analyze_discussion(discussion_number: int):
    config = Config()
    analyzer = DailyAnalyzer(config)
    
    # 获取预览
    preview = await analyzer.get_analysis_preview(discussion_number)
    print(f"分析预览: {preview['analysis_report']}")
    
    # 执行完整分析
    result = await analyzer.analyze_specific_discussion(discussion_number)
    print(f"分析结果: {result}")

# 分析讨论 #123
asyncio.run(analyze_discussion(123))
```

### 自定义分析

```python
from src.clients.github_client import GitHubClient
from src.clients.glm_client import GLMClient

async def custom_analysis():
    github_config = GitHubConfig(token="...", organization="...", repository="...")
    glm_config = GLMConfig(api_key="...")
    
    github_client = GitHubClient(github_config)
    glm_client = GLMClient(glm_config)
    
    # 获取讨论
    discussions = await github_client.get_daily_discussions()
    
    for discussion in discussions:
        # 提取内容
        content = await github_client.extract_daily_content(discussion)
        
        # 分析偏离度
        deviation = await glm_client.analyze_work_deviation(
            content['daily_summary'],
            content['daily_plan']
        )
        
        print(f"讨论 #{discussion.number} 偏离度: {deviation['score']}")

asyncio.run(custom_analysis())
```

## 性能优化

### 并发控制
系统内置了并发控制机制，可通过配置文件调整：

```yaml
performance:
  max_concurrent_requests: 5
  request_pool_size: 10
```

### 缓存机制
支持结果缓存，减少重复API调用：

```yaml
performance:
  cache_enabled: true
  cache_ttl: 3600  # 1小时
```

### 速率限制
内置速率限制，避免API调用过于频繁：

```python
from src.utils.helpers import rate_limit

@rate_limit(calls_per_second=2.0)
async def api_call():
    # API调用逻辑
    pass
```

## 监控和调试

### 日志级别
- `DEBUG`: 详细的调试信息
- `INFO`: 一般运行信息  
- `WARNING`: 警告信息
- `ERROR`: 错误信息
- `CRITICAL`: 严重错误

### 性能指标
系统会自动记录以下指标：
- API调用响应时间
- 分析处理时间
- 成功/失败率
- 内存使用情况

### 健康检查
```python
async def health_check():
    analyzer = DailyAnalyzer(Config())
    connections = await analyzer.test_connections()
    return connections['overall']
```
