"""
数据模型定义
定义系统中使用的各种数据结构
"""

from datetime import datetime, date
from typing import List, Dict, Any, Optional, Union
from dataclasses import dataclass, field
from enum import Enum


class AnalysisType(Enum):
    """分析类型枚举"""
    DEVIATION = "deviation"          # 偏离度分析
    CLARITY = "clarity"             # 清晰度分析
    CONSISTENCY = "consistency"     # 一致性分析


class TaskStatus(Enum):
    """任务状态枚举"""
    PENDING = "pending"             # 待处理
    RUNNING = "running"             # 运行中
    COMPLETED = "completed"         # 已完成
    FAILED = "failed"               # 失败
    CANCELLED = "cancelled"         # 已取消


@dataclass
class DiscussionMetadata:
    """Discussion元数据"""
    id: str
    number: int
    title: str
    author: str
    created_at: datetime
    updated_at: datetime
    category: str
    url: str
    comments_count: int
    
    def to_dict(self) -> Dict[str, Any]:
        """转换为字典"""
        return {
            'id': self.id,
            'number': self.number,
            'title': self.title,
            'author': self.author,
            'created_at': self.created_at.isoformat(),
            'updated_at': self.updated_at.isoformat(),
            'category': self.category,
            'url': self.url,
            'comments_count': self.comments_count
        }


@dataclass
class ContentExtraction:
    """内容提取结果"""
    daily_summary: str = ""         # 日结内容
    daily_plan: str = ""            # 日计划内容
    weekly_plan: str = ""           # 周期计划内容
    original_content: str = ""      # 原始内容
    extraction_confidence: float = 0.0  # 提取置信度
    
    def is_valid(self) -> bool:
        """检查提取结果是否有效"""
        return bool(self.daily_summary.strip() or self.daily_plan.strip())
        
    def get_summary(self) -> Dict[str, Any]:
        """获取提取摘要"""
        return {
            'has_daily_summary': bool(self.daily_summary.strip()),
            'has_daily_plan': bool(self.daily_plan.strip()),
            'has_weekly_plan': bool(self.weekly_plan.strip()),
            'daily_summary_length': len(self.daily_summary),
            'daily_plan_length': len(self.daily_plan),
            'weekly_plan_length': len(self.weekly_plan),
            'extraction_confidence': self.extraction_confidence
        }


@dataclass
class DeviationAnalysisResult:
    """偏离度分析结果"""
    score: float                    # 偏离度评分 (0-10)
    completion_rate: float          # 完成率 (0-1)
    deviation_reasons: List[str]    # 偏离原因
    additional_work: List[str]      # 额外工作
    suggestions: List[str]          # 改进建议
    summary: str                    # 总结
    confidence: float = 0.0         # 分析置信度
    
    # V2.0 新增字段
    user_id: str = ""               # 用户ID
    analysis_date: str = ""         # 分析日期 (YYYY-MM-DD)
    discussion_number: int = 0      # Discussion编号
    is_deviation: bool = False      # 是否存在偏离
    raw_analysis_text: str = ""     # 原始分析文本
    content_type: str = ""          # 内容类型 (daily_report, daily_plan, weekly_plan)
    original_content: str = ""      # 原始内容
    
    def get_grade(self) -> str:
        """获取评级"""
        if self.score <= 2:
            return "优秀"
        elif self.score <= 4:
            return "良好"
        elif self.score <= 6:
            return "一般"
        elif self.score <= 8:
            return "需改进"
        else:
            return "较差"
    
    def to_dict(self) -> Dict[str, Any]:
        """转换为字典格式，用于JSON存储"""
        return {
            'score': self.score,
            'completion_rate': self.completion_rate,
            'deviation_reasons': self.deviation_reasons,
            'additional_work': self.additional_work,
            'suggestions': self.suggestions,
            'summary': self.summary,
            'confidence': self.confidence,
            'user_id': self.user_id,
            'analysis_date': self.analysis_date,
            'discussion_number': self.discussion_number,
            'is_deviation': self.is_deviation,
            'raw_analysis_text': self.raw_analysis_text,
            'content_type': self.content_type,
            'original_content': self.original_content,
            'grade': self.get_grade()
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'DeviationAnalysisResult':
        """从字典创建实例"""
        return cls(
            score=data.get('score', 0.0),
            completion_rate=data.get('completion_rate', 0.0),
            deviation_reasons=data.get('deviation_reasons', []),
            additional_work=data.get('additional_work', []),
            suggestions=data.get('suggestions', []),
            summary=data.get('summary', ''),
            confidence=data.get('confidence', 0.0),
            user_id=data.get('user_id', ''),
            analysis_date=data.get('analysis_date', ''),
            discussion_number=data.get('discussion_number', 0),
            is_deviation=data.get('is_deviation', False),
            raw_analysis_text=data.get('raw_analysis_text', ''),
            content_type=data.get('content_type', ''),
            original_content=data.get('original_content', '')
        )


@dataclass
class ClarityAnalysisResult:
    """清晰度分析结果"""
    clarity_score: float            # 清晰度评分 (0-10)
    specificity_score: float        # 具体性评分 (0-10)
    completeness_score: float       # 完整性评分 (0-10)
    unclear_parts: List[str]        # 不清晰的部分
    missing_info: List[str]         # 缺失信息
    improvement_suggestions: List[str]  # 改进建议
    summary: str                    # 总结
    confidence: float = 0.0         # 分析置信度
    
    def get_overall_score(self) -> float:
        """获取总体评分"""
        return (self.clarity_score + self.specificity_score + self.completeness_score) / 3


@dataclass
class ConsistencyAnalysisResult:
    """一致性分析结果"""
    consistency_score: float        # 一致性评分 (0-10)
    alignment_level: float          # 对齐程度 (0-10)
    priority_match: float           # 优先级匹配度 (0-10)
    inconsistencies: List[str]      # 不一致的地方
    alignment_strengths: List[str]  # 对齐优势
    recommendations: List[str]      # 改进建议
    summary: str                    # 总结
    confidence: float = 0.0         # 分析置信度


@dataclass
class ComprehensiveAnalysisResult:
    """综合分析结果"""
    discussion_metadata: DiscussionMetadata
    content_extraction: ContentExtraction
    deviation_analysis: Optional[DeviationAnalysisResult] = None
    clarity_analysis: Optional[ClarityAnalysisResult] = None
    consistency_analysis: Optional[ConsistencyAnalysisResult] = None
    analysis_timestamp: datetime = field(default_factory=datetime.now)
    processing_time: float = 0.0    # 处理时间（秒）
    
    def get_overall_summary(self) -> Dict[str, Any]:
        """获取总体摘要"""
        summary = {
            'discussion_number': self.discussion_metadata.number,
            'discussion_title': self.discussion_metadata.title,
            'analysis_timestamp': self.analysis_timestamp.isoformat(),
            'processing_time': self.processing_time,
            'analyses_performed': []
        }
        
        if self.deviation_analysis:
            summary['analyses_performed'].append('deviation')
            summary['deviation_score'] = self.deviation_analysis.score
            summary['completion_rate'] = self.deviation_analysis.completion_rate
            
        if self.clarity_analysis:
            summary['analyses_performed'].append('clarity')
            summary['clarity_score'] = self.clarity_analysis.get_overall_score()
            
        if self.consistency_analysis:
            summary['analyses_performed'].append('consistency')
            summary['consistency_score'] = self.consistency_analysis.consistency_score
            
        return summary


@dataclass
class AnalysisTask:
    """分析任务"""
    task_id: str
    discussion_number: int
    analysis_types: List[AnalysisType]
    status: TaskStatus = TaskStatus.PENDING
    created_at: datetime = field(default_factory=datetime.now)
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    result: Optional[ComprehensiveAnalysisResult] = None
    error_message: Optional[str] = None
    retry_count: int = 0
    
    def start(self):
        """开始任务"""
        self.status = TaskStatus.RUNNING
        self.started_at = datetime.now()
        
    def complete(self, result: ComprehensiveAnalysisResult):
        """完成任务"""
        self.status = TaskStatus.COMPLETED
        self.completed_at = datetime.now()
        self.result = result
        
    def fail(self, error_message: str):
        """任务失败"""
        self.status = TaskStatus.FAILED
        self.completed_at = datetime.now()
        self.error_message = error_message
        
    def cancel(self):
        """取消任务"""
        self.status = TaskStatus.CANCELLED
        self.completed_at = datetime.now()
        
    def get_duration(self) -> Optional[float]:
        """获取任务持续时间（秒）"""
        if self.started_at and self.completed_at:
            return (self.completed_at - self.started_at).total_seconds()
        return None


@dataclass
class DailyAnalysisSummary:
    """每日分析摘要"""
    date: date
    total_discussions: int
    analyzed_discussions: int
    successful_analyses: int
    failed_analyses: int
    comments_posted: int
    total_processing_time: float
    start_time: datetime
    end_time: Optional[datetime] = None
    errors: List[str] = field(default_factory=list)
    
    def get_success_rate(self) -> float:
        """获取成功率"""
        if self.analyzed_discussions == 0:
            return 0.0
        return self.successful_analyses / self.analyzed_discussions
        
    def get_comment_rate(self) -> float:
        """获取评论发布率"""
        if self.successful_analyses == 0:
            return 0.0
        return self.comments_posted / self.successful_analyses
        
    def to_dict(self) -> Dict[str, Any]:
        """转换为字典"""
        return {
            'date': self.date.isoformat(),
            'total_discussions': self.total_discussions,
            'analyzed_discussions': self.analyzed_discussions,
            'successful_analyses': self.successful_analyses,
            'failed_analyses': self.failed_analyses,
            'comments_posted': self.comments_posted,
            'success_rate': self.get_success_rate(),
            'comment_rate': self.get_comment_rate(),
            'total_processing_time': self.total_processing_time,
            'start_time': self.start_time.isoformat(),
            'end_time': self.end_time.isoformat() if self.end_time else None,
            'error_count': len(self.errors)
        }


@dataclass
class SystemStatus:
    """系统状态"""
    is_running: bool
    current_task: Optional[str]
    next_scheduled_run: Optional[datetime]
    last_successful_run: Optional[datetime]
    github_connection_ok: bool
    glm_connection_ok: bool
    total_analyses_today: int
    failed_analyses_today: int
    uptime_seconds: float
    
    def is_healthy(self) -> bool:
        """检查系统是否健康"""
        return (
            self.is_running and
            self.github_connection_ok and
            self.glm_connection_ok
        )
        
    def to_dict(self) -> Dict[str, Any]:
        """转换为字典"""
        return {
            'is_running': self.is_running,
            'is_healthy': self.is_healthy(),
            'current_task': self.current_task,
            'next_scheduled_run': self.next_scheduled_run.isoformat() if self.next_scheduled_run else None,
            'last_successful_run': self.last_successful_run.isoformat() if self.last_successful_run else None,
            'connections': {
                'github': self.github_connection_ok,
                'glm': self.glm_connection_ok
            },
            'statistics': {
                'total_analyses_today': self.total_analyses_today,
                'failed_analyses_today': self.failed_analyses_today,
                'success_rate_today': (
                    (self.total_analyses_today - self.failed_analyses_today) / self.total_analyses_today
                    if self.total_analyses_today > 0 else 0
                )
            },
            'uptime_seconds': self.uptime_seconds
        }


@dataclass
class ContinuousDeviationRecord:
    """连续偏离记录"""
    user_id: str
    start_date: str                 # 开始日期 (YYYY-MM-DD)
    end_date: Optional[str] = None  # 结束日期 (YYYY-MM-DD)
    deviation_count: int = 0        # 连续偏离次数
    deviation_dates: List[str] = field(default_factory=list)  # 偏离日期列表
    is_active: bool = True          # 是否仍在连续偏离中
    report_generated: bool = False  # 是否已生成汇报
    created_at: str = field(default_factory=lambda: datetime.now().isoformat())
    
    def to_dict(self) -> Dict[str, Any]:
        """转换为字典格式"""
        return {
            'user_id': self.user_id,
            'start_date': self.start_date,
            'end_date': self.end_date,
            'deviation_count': self.deviation_count,
            'deviation_dates': self.deviation_dates,
            'is_active': self.is_active,
            'report_generated': self.report_generated,
            'created_at': self.created_at
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'ContinuousDeviationRecord':
        """从字典创建实例"""
        return cls(
            user_id=data.get('user_id', ''),
            start_date=data.get('start_date', ''),
            end_date=data.get('end_date'),
            deviation_count=data.get('deviation_count', 0),
            deviation_dates=data.get('deviation_dates', []),
            is_active=data.get('is_active', True),
            report_generated=data.get('report_generated', False),
            created_at=data.get('created_at', datetime.now().isoformat())
        )


@dataclass
class DeviationReport:
    """偏离汇报"""
    user_id: str
    report_type: str                # 汇报类型: 'concise', 'detailed', 'card'
    title: str                      # 汇报标题
    content: str                    # 汇报内容
    deviation_period: str           # 偏离周期描述
    analysis_results: List[Dict[str, Any]]  # 相关分析结果
    generated_at: str = field(default_factory=lambda: datetime.now().isoformat())
    sent_to_feishu: bool = False    # 是否已发送到飞书
    
    def to_dict(self) -> Dict[str, Any]:
        """转换为字典格式"""
        return {
            'user_id': self.user_id,
            'report_type': self.report_type,
            'title': self.title,
            'content': self.content,
            'deviation_period': self.deviation_period,
            'analysis_results': self.analysis_results,
            'generated_at': self.generated_at,
            'sent_to_feishu': self.sent_to_feishu
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'DeviationReport':
        """从字典创建实例"""
        return cls(
            user_id=data.get('user_id', ''),
            report_type=data.get('report_type', 'concise'),
            title=data.get('title', ''),
            content=data.get('content', ''),
            deviation_period=data.get('deviation_period', ''),
            analysis_results=data.get('analysis_results', []),
            generated_at=data.get('generated_at', datetime.now().isoformat()),
            sent_to_feishu=data.get('sent_to_feishu', False)
        )


@dataclass
class DailyReportData:
    """日报数据"""
    user_id: str
    username: str
    date: str  # YYYY-MM-DD
    plan_content: str
    report_content: str
    discussion_number: int
    created_at: datetime = field(default_factory=datetime.now)
    
    def to_dict(self) -> Dict[str, Any]:
        """转换为字典"""
        return {
            'user_id': self.user_id,
            'username': self.username,
            'date': self.date,
            'plan_content': self.plan_content,
            'report_content': self.report_content,
            'discussion_number': self.discussion_number,
            'created_at': self.created_at.isoformat()
        }


@dataclass
class UserDailySummary:
    """用户日报汇总"""
    user_id: str
    username: str
    date: str  # YYYY-MM-DD
    plan_content: str
    report_content: str
    deviation_score: float
    completion_rate: float
    analysis_summary: str
    glm_insights: str
    
    def to_dict(self) -> Dict[str, Any]:
        """转换为字典"""
        return {
            'user_id': self.user_id,
            'username': self.username,
            'date': self.date,
            'plan_content': self.plan_content,
            'report_content': self.report_content,
            'deviation_score': self.deviation_score,
            'completion_rate': self.completion_rate,
            'analysis_summary': self.analysis_summary,
            'glm_insights': self.glm_insights
        }


@dataclass
class TeamDailySummaryReport:
    """团队日报汇总报告"""
    date: str  # YYYY-MM-DD
    total_users: int
    submitted_reports: int
    submission_rate: float
    average_deviation_score: float
    average_completion_rate: float
    user_summaries: List[UserDailySummary]
    team_insights: str
    recommendations: List[str]
    overview_summary: str = ""
    key_insights: List[str] = field(default_factory=list)
    management_recommendations: str = ""
    glm_enhanced_summary: str = ""
    team_performance_metrics: Dict[str, Any] = field(default_factory=dict)
    generated_at: datetime = field(default_factory=datetime.now)
    
    def to_dict(self) -> Dict[str, Any]:
        """转换为字典"""
        return {
            'date': self.date,
            'total_users': self.total_users,
            'submitted_reports': self.submitted_reports,
            'submission_rate': self.submission_rate,
            'average_deviation_score': self.average_deviation_score,
            'average_completion_rate': self.average_completion_rate,
            'user_summaries': [summary.to_dict() for summary in self.user_summaries],
            'team_insights': self.team_insights,
            'recommendations': self.recommendations,
            'generated_at': self.generated_at.isoformat()
        }


@dataclass
class DailySummaryAnalysisTask:
    """日报汇总分析任务"""
    task_id: str
    date: str  # YYYY-MM-DD
    status: TaskStatus = TaskStatus.PENDING
    created_at: datetime = field(default_factory=datetime.now)
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    report: Optional[TeamDailySummaryReport] = None
    error_message: Optional[str] = None
    retry_count: int = 0
    
    def start(self):
        """开始任务"""
        self.status = TaskStatus.RUNNING
        self.started_at = datetime.now()
        
    def complete(self, report: TeamDailySummaryReport):
        """完成任务"""
        self.status = TaskStatus.COMPLETED
        self.completed_at = datetime.now()
        self.report = report
        
    def fail(self, error_message: str):
        """任务失败"""
        self.status = TaskStatus.FAILED
        self.completed_at = datetime.now()
        self.error_message = error_message
        
    def get_duration(self) -> Optional[float]:
        """获取任务持续时间（秒）"""
        if self.started_at and self.completed_at:
            return (self.completed_at - self.started_at).total_seconds()
        return None


# 工厂函数
def create_analysis_task(discussion_number: int, 
                        analysis_types: Optional[List[AnalysisType]] = None) -> AnalysisTask:
    """创建分析任务"""
    if analysis_types is None:
        analysis_types = [AnalysisType.DEVIATION, AnalysisType.CLARITY, AnalysisType.CONSISTENCY]
        
    task_id = f"task_{discussion_number}_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
    
    return AnalysisTask(
        task_id=task_id,
        discussion_number=discussion_number,
        analysis_types=analysis_types
    )


def create_daily_summary(date_obj: date) -> DailyAnalysisSummary:
    """创建每日摘要"""
    return DailyAnalysisSummary(
        date=date_obj,
        total_discussions=0,
        analyzed_discussions=0,
        successful_analyses=0,
        failed_analyses=0,
        comments_posted=0,
        total_processing_time=0.0,
        start_time=datetime.now()
    )


def create_daily_summary_analysis_task(date_str: str) -> DailySummaryAnalysisTask:
    """创建日报汇总分析任务"""
    task_id = f"daily_summary_{date_str}_{datetime.now().strftime('%H%M%S')}"
    
    return DailySummaryAnalysisTask(
        task_id=task_id,
        date=date_str
    )
