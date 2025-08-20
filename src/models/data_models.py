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
