"""
配置管理模块
负责加载和管理所有配置参数
"""

import os
import yaml
from pathlib import Path
from typing import Dict, Any, Optional, Union, List
from dataclasses import dataclass, field
from dotenv import load_dotenv


@dataclass
class GitHubConfig:
    """GitHub配置"""
    token: str
    organization: str
    repository: str = ""  # 组织级别Discussions时可为空
    discussion_category: str = "2 - 日结"
    api_base_url: str = "https://api.github.com"
    timeout: int = 30
    use_org_discussions: bool = True  # 是否使用组织级别的Discussions


@dataclass
class GLMConfig:
    """GLM-4.5配置"""
    api_key: str
    model: str = "glm-4-flash"
    base_url: str = "https://open.bigmodel.cn/api/paas/v4/"
    temperature: float = 0.7
    max_tokens: int = 2000
    top_p: float = 0.9
    timeout: int = 60


@dataclass
class AnalysisThresholds:
    """分析阈值配置"""
    deviation_warning: float = 0.3
    deviation_critical: float = 0.5
    clarity_minimum: float = 0.6
    consistency_minimum: float = 0.7


@dataclass
class AnalysisConfig:
    """分析功能配置"""
    enable_deviation_analysis: bool = True
    enable_clarity_analysis: bool = True
    enable_consistency_analysis: bool = True
    continuous_threshold: int = 3
    thresholds: AnalysisThresholds = field(default_factory=AnalysisThresholds)


@dataclass
class SchedulerConfig:
    """调度器配置"""
    cron_expression: str = "0 13 * * *"
    timezone: str = "Asia/Shanghai"
    retry_attempts: int = 3
    retry_delay: int = 300
    max_execution_time: int = 1800


@dataclass
class LoggingConfig:
    """日志配置"""
    level: str = "INFO"
    format: str = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
    file_path: str = "logs/analyzer.log"
    max_size: str = "10MB"
    backup_count: int = 5


@dataclass
class PerformanceConfig:
    """性能配置"""
    max_concurrent_requests: int = 5
    request_pool_size: int = 10
    cache_enabled: bool = True
    cache_ttl: int = 3600


@dataclass
class FeishuApiConfig:
    """飞书API配置"""
    enabled: bool = True
    app_id: str = ""
    app_secret: str = ""
    base_url: str = "https://open.feishu.cn"
    default_chat_id: str = ""
    timeout: int = 30
    max_retries: int = 3
    retry_delay: float = 1.0


@dataclass
class FeishuWebhookConfig:
    """飞书Webhook配置"""
    enabled: bool = False
    url: str = ""


@dataclass
class FeishuConfig:
    """飞书配置"""
    enabled: bool = False
    api: FeishuApiConfig = field(default_factory=FeishuApiConfig)
    webhook: FeishuWebhookConfig = field(default_factory=FeishuWebhookConfig)
    mapping_file: str = "feishu_mapping.json"
    message_type: str = "rich_text"


@dataclass
class ManagementNotificationConfig:
    """管理层通知配置"""
    enabled: bool = False
    user_ids: list = field(default_factory=list)
    notification_type: str = "private_chat"  # private_chat 或 group_chat


@dataclass
class WeeklyDataCollectionConfig:
    """周报数据收集配置"""
    days_to_collect: int = 7
    include_weekends: bool = False
    min_records_required: int = 3


@dataclass
class WeeklyReportGenerationConfig:
    """周报生成配置"""
    include_achievements: bool = True
    include_issues: bool = True
    include_suggestions: bool = True
    include_trends: bool = True
    max_achievements: int = 5
    max_issues: int = 5
    max_suggestions: int = 3


@dataclass
class WeeklyGLMEnhancementConfig:
    """周报GLM增强配置"""
    enabled: bool = True
    personal_prompt: str = "基于员工一周的工作数据，生成个人周报总结，包含成就、问题和建议"
    management_prompt: str = "基于团队一周的工作数据，生成管理层周报，重点关注团队表现和趋势"
    max_tokens: int = 1500
    temperature: float = 0.7


@dataclass
class WeeklyDeliveryConfig:
    """周报发送配置"""
    send_to_individuals: bool = True
    send_to_management: bool = True
    management_user_ids: list = field(default_factory=list)
    message_format: str = "rich_text"
    include_charts: bool = False


@dataclass
class WeeklyReportsConfig:
    """周报配置"""
    enabled: bool = True
    execution_hour: int = 17
    execution_day: int = 5  # 1-7，1为周一，5为周五
    data_collection: WeeklyDataCollectionConfig = field(default_factory=WeeklyDataCollectionConfig)
    report_generation: WeeklyReportGenerationConfig = field(default_factory=WeeklyReportGenerationConfig)
    glm_enhancement: WeeklyGLMEnhancementConfig = field(default_factory=WeeklyGLMEnhancementConfig)
    delivery: WeeklyDeliveryConfig = field(default_factory=WeeklyDeliveryConfig)


@dataclass
class DailyContentCheckConfig:
    """日报/日计划内容检查配置"""
    enabled: bool = True
    content_check_cron: Union[str, List[str]] = field(default_factory=lambda: ["0 12 * * *", "0 19 * * *"])  # 内容检查时间，支持单个或多个时间点
    analysis_cron: Union[str, List[str]] = field(default_factory=lambda: ["0 13 * * *", "0 20 * * *"])      # 日常分析时间，支持单个或多个时间点
    check_date_offset: int = 0              # 检查日期偏移
    morning_check_hour: int = 9             # 上午检查时间
    afternoon_check_hour: int = 14          # 下午检查时间
    evening_check_hour: int = 18            # 晚上检查时间
    weekend_check_enabled: bool = False     # 是否在周末检查
    retry_attempts: int = 3                 # 重试次数
    retry_delay: int = 300                  # 重试延迟
    max_execution_time: int = 600           # 最大执行时间
    reminder_enabled: bool = True           # 启用提醒功能
    duplicate_prevention_hours: int = 4     # 防重复提醒时间
    batch_check_enabled: bool = True        # 启用批量检查
    summary_report_enabled: bool = True     # 启用检查结果摘要报告


@dataclass
class NotificationConfig:
    """通知配置"""
    enabled: bool = False
    webhook_url: str = ""
    email_enabled: bool = False
    smtp_server: str = ""
    smtp_port: int = 587
    username: str = ""
    password: str = ""
    recipients: list = field(default_factory=list)


@dataclass
class DailySummaryScheduleConfig:
    """日报汇总调度配置"""
    enabled: bool = True
    cron_expression: str = "0 9 * * *"  # 每天上午9点执行
    timezone: str = "Asia/Shanghai"
    retry_attempts: int = 3
    retry_delay: int = 300
    max_execution_time: int = 1800


@dataclass
class DailySummaryDataCollectionConfig:
    """日报汇总数据收集配置"""
    target_date_offset: int = -1  # 分析前一天的数据
    include_weekends: bool = False
    min_reports_required: int = 1
    max_reports_per_user: int = 1
    content_validation_enabled: bool = True


@dataclass
class DailySummaryAnalysisConfig:
    """日报汇总分析配置"""
    deviation_analysis_enabled: bool = True
    completion_analysis_enabled: bool = True
    trend_analysis_enabled: bool = True
    performance_scoring_enabled: bool = True
    team_insights_enabled: bool = True
    individual_insights_enabled: bool = True


@dataclass
class DailySummaryGLMEnhancementConfig:
    """日报汇总GLM增强配置"""
    enabled: bool = True
    user_analysis_prompt: str = "基于用户的日报和日计划，分析工作偏离度、完成率，并提供简洁的洞察和建议"
    team_insights_prompt: str = "基于团队日报数据，生成团队整体表现洞察，包括趋势分析和改进建议"
    recommendations_prompt: str = "基于团队表现数据，生成具体的管理建议和改进措施"
    max_tokens: int = 1500
    temperature: float = 0.7
    timeout: int = 60


@dataclass
class DailySummaryNotificationConfig:
    """日报汇总通知配置"""
    enabled: bool = True
    recipients: List[str] = field(default_factory=list)
    notification_type: str = "private_chat"  # private_chat 或 group_chat
    message_format: str = "rich_text"
    include_individual_summaries: bool = True
    include_team_insights: bool = True
    include_recommendations: bool = True
    max_users_in_summary: int = 10
    
    def get(self, key: str, default=None):
        """字典式访问方法"""
        return getattr(self, key, default)


@dataclass
class DailySummaryExecutionConfig:
    """日报汇总执行控制配置"""
    parallel_analysis_enabled: bool = True
    max_concurrent_users: int = 5
    batch_size: int = 10
    error_tolerance_rate: float = 0.2  # 允许20%的用户分析失败
    skip_on_no_data: bool = True
    save_intermediate_results: bool = True


@dataclass
class DailySummaryConfig:
    """日报汇总分析功能配置"""
    enabled: bool = True
    schedule: DailySummaryScheduleConfig = field(default_factory=DailySummaryScheduleConfig)
    data_collection: DailySummaryDataCollectionConfig = field(default_factory=DailySummaryDataCollectionConfig)
    analysis: DailySummaryAnalysisConfig = field(default_factory=DailySummaryAnalysisConfig)
    glm_enhancement: DailySummaryGLMEnhancementConfig = field(default_factory=DailySummaryGLMEnhancementConfig)
    notification: DailySummaryNotificationConfig = field(default_factory=DailySummaryNotificationConfig)
    execution: DailySummaryExecutionConfig = field(default_factory=DailySummaryExecutionConfig)
    
    def get(self, key: str, default=None):
        """字典式访问方法"""
        return getattr(self, key, default)


class Config:
    """主配置类"""
    
    def __init__(self, config_path: Optional[str] = None):
        # 加载环境变量
        load_dotenv()
        
        # 设置配置文件路径
        if config_path is None:
            config_path = Path(__file__).parent.parent / "config" / "config.yaml"
        
        self.config_path = Path(config_path)
        self._config_data = {}
        
        # 加载配置
        self._load_config()
        self._init_configs()
        
    def _load_config(self):
        """加载YAML配置文件"""
        if self.config_path.exists():
            with open(self.config_path, 'r', encoding='utf-8') as f:
                self._config_data = yaml.safe_load(f) or {}
        else:
            # 如果配置文件不存在，使用默认配置
            self._config_data = {}
            
    def _init_configs(self):
        """初始化各个配置对象"""
        # GitHub配置
        github_config = self._config_data.get('github', {})
        self.github = GitHubConfig(
            token=self._get_env_or_config('GITHUB_TOKEN', github_config.get('token', '')),
            organization=self._get_env_or_config('GITHUB_ORG', github_config.get('organization', '')),
            repository=self._get_env_or_config('GITHUB_REPO', github_config.get('repository', '')),
            discussion_category=github_config.get('discussion_category', '2 - 日结'),
            api_base_url=github_config.get('api_base_url', 'https://api.github.com'),
            timeout=github_config.get('timeout', 30),
            use_org_discussions=self._get_bool_env_or_config('USE_ORG_DISCUSSIONS', github_config.get('use_org_discussions', True))
        )
        
        # GLM配置
        glm_config = self._config_data.get('glm', {})
        self.glm = GLMConfig(
            api_key=self._get_env_or_config('GLM_API_KEY', glm_config.get('api_key', '')),
            model=glm_config.get('model', 'glm-4-flash'),
            base_url=self._get_env_or_config('GLM_BASE_URL', glm_config.get('base_url', 'https://open.bigmodel.cn/api/paas/v4/')),
            temperature=glm_config.get('temperature', 0.7),
            max_tokens=glm_config.get('max_tokens', 2000),
            top_p=glm_config.get('top_p', 0.9),
            timeout=glm_config.get('timeout', 60)
        )
        
        # 分析配置
        analysis_config = self._config_data.get('analysis', {})
        thresholds_config = analysis_config.get('thresholds', {})
        
        self.analysis = AnalysisConfig(
            enable_deviation_analysis=self._get_bool_env_or_config('ENABLE_DEVIATION_ANALYSIS', analysis_config.get('enable_deviation_analysis', True)),
            enable_clarity_analysis=self._get_bool_env_or_config('ENABLE_CLARITY_ANALYSIS', analysis_config.get('enable_clarity_analysis', True)),
            enable_consistency_analysis=self._get_bool_env_or_config('ENABLE_CONSISTENCY_ANALYSIS', analysis_config.get('enable_consistency_analysis', True)),
            continuous_threshold=int(self._get_env_or_config('CONTINUOUS_THRESHOLD', analysis_config.get('continuous_threshold', 3))),
            thresholds=AnalysisThresholds(
                deviation_warning=thresholds_config.get('deviation_warning', 0.3),
                deviation_critical=thresholds_config.get('deviation_critical', 0.5),
                clarity_minimum=thresholds_config.get('clarity_minimum', 0.6),
                consistency_minimum=thresholds_config.get('consistency_minimum', 0.7)
            )
        )
        
        # 调度器配置
        scheduler_config = self._config_data.get('scheduler', {})
        self.scheduler = SchedulerConfig(
            cron_expression=self._get_env_or_config('SCHEDULE_CRON', scheduler_config.get('cron_expression', '0 18 * * *')),
            timezone=self._get_env_or_config('TIMEZONE', scheduler_config.get('timezone', 'Asia/Shanghai')),
            retry_attempts=int(self._get_env_or_config('RETRY_ATTEMPTS', scheduler_config.get('retry_attempts', 3))),
            retry_delay=int(self._get_env_or_config('RETRY_DELAY', scheduler_config.get('retry_delay', 300))),
            max_execution_time=scheduler_config.get('max_execution_time', 1800)
        )
        
        # 日志配置
        logging_config = self._config_data.get('logging', {})
        self.logging = LoggingConfig(
            level=self._get_env_or_config('LOG_LEVEL', logging_config.get('level', 'INFO')),
            format=logging_config.get('format', '%(asctime)s - %(name)s - %(levelname)s - %(message)s'),
            file_path=self._get_env_or_config('LOG_FILE', logging_config.get('file_path', 'logs/analyzer.log')),
            max_size=self._get_env_or_config('LOG_MAX_SIZE', logging_config.get('max_size', '10MB')),
            backup_count=int(self._get_env_or_config('LOG_BACKUP_COUNT', logging_config.get('backup_count', 5)))
        )
        
        # 性能配置
        performance_config = self._config_data.get('performance', {})
        self.performance = PerformanceConfig(
            max_concurrent_requests=int(self._get_env_or_config('MAX_CONCURRENT_REQUESTS', performance_config.get('max_concurrent_requests', 5))),
            request_pool_size=performance_config.get('request_pool_size', 10),
            cache_enabled=performance_config.get('cache_enabled', True),
            cache_ttl=performance_config.get('cache_ttl', 3600)
        )
        
        # 飞书配置
        feishu_config = self._config_data.get('feishu', {})
        feishu_api_config = feishu_config.get('api', {})
        feishu_webhook_config = feishu_config.get('webhook', {})
        
        self.feishu = FeishuConfig(
            enabled=self._get_bool_env_or_config('FEISHU_ENABLED', feishu_config.get('enabled', False)),
            api=FeishuApiConfig(
                enabled=feishu_api_config.get('enabled', True),
                app_id=self._get_env_or_config('FEISHU_APP_ID', feishu_api_config.get('app_id', '')),
                app_secret=self._get_env_or_config('FEISHU_APP_SECRET', feishu_api_config.get('app_secret', '')),
                base_url=feishu_api_config.get('base_url', 'https://open.feishu.cn'),
                default_chat_id=self._get_env_or_config('FEISHU_DEFAULT_CHAT_ID', feishu_api_config.get('default_chat_id', '')),
                timeout=feishu_api_config.get('timeout', 30),
                max_retries=feishu_api_config.get('max_retries', 3),
                retry_delay=feishu_api_config.get('retry_delay', 1.0)
            ),
            webhook=FeishuWebhookConfig(
                enabled=feishu_webhook_config.get('enabled', False),
                url=self._get_env_or_config('FEISHU_WEBHOOK_URL', feishu_webhook_config.get('url', ''))
            ),
            mapping_file=feishu_config.get('mapping_file', 'feishu_mapping.json'),
            message_type=feishu_config.get('message_type', 'rich_text')
        )
        
        # 管理层通知配置
        management_config = self._config_data.get('management_notification', {})
        self.management_notification = ManagementNotificationConfig(
            enabled=management_config.get('enabled', False),
            user_ids=management_config.get('user_ids', []),
            notification_type=management_config.get('notification_type', 'private_chat')
        )
        
        # 周报配置
        weekly_config = self._config_data.get('weekly_reports', {})
        data_collection_config = weekly_config.get('data_collection', {})
        report_generation_config = weekly_config.get('report_generation', {})
        glm_enhancement_config = weekly_config.get('glm_enhancement', {})
        delivery_config = weekly_config.get('delivery', {})
        
        self.weekly_reports = WeeklyReportsConfig(
            enabled=self._get_bool_env_or_config('WEEKLY_REPORTS_ENABLED', weekly_config.get('enabled', True)),
            execution_hour=int(self._get_env_or_config('WEEKLY_EXECUTION_HOUR', weekly_config.get('execution_hour', 17))),
            execution_day=int(self._get_env_or_config('WEEKLY_EXECUTION_DAY', weekly_config.get('execution_day', 5))),
            data_collection=WeeklyDataCollectionConfig(
                days_to_collect=data_collection_config.get('days_to_collect', 7),
                include_weekends=data_collection_config.get('include_weekends', False),
                min_records_required=data_collection_config.get('min_records_required', 3)
            ),
            report_generation=WeeklyReportGenerationConfig(
                include_achievements=report_generation_config.get('include_achievements', True),
                include_issues=report_generation_config.get('include_issues', True),
                include_suggestions=report_generation_config.get('include_suggestions', True),
                include_trends=report_generation_config.get('include_trends', True),
                max_achievements=report_generation_config.get('max_achievements', 5),
                max_issues=report_generation_config.get('max_issues', 5),
                max_suggestions=report_generation_config.get('max_suggestions', 3)
            ),
            glm_enhancement=WeeklyGLMEnhancementConfig(
                enabled=glm_enhancement_config.get('enabled', True),
                personal_prompt=glm_enhancement_config.get('personal_prompt', '基于员工一周的工作数据，生成个人周报总结，包含成就、问题和建议'),
                management_prompt=glm_enhancement_config.get('management_prompt', '基于团队一周的工作数据，生成管理层周报，重点关注团队表现和趋势'),
                max_tokens=glm_enhancement_config.get('max_tokens', 1500),
                temperature=glm_enhancement_config.get('temperature', 0.7)
            ),
            delivery=WeeklyDeliveryConfig(
                send_to_individuals=delivery_config.get('send_to_individuals', True),
                send_to_management=delivery_config.get('send_to_management', True),
                management_user_ids=delivery_config.get('management_user_ids', []),
                message_format=delivery_config.get('message_format', 'rich_text'),
                include_charts=delivery_config.get('include_charts', False)
            )
        )
        
        # 日报内容检查配置
        daily_content_check_config = self._config_data.get('daily_content_check', {})
        # 确保从配置文件获取cron表达式，如果配置文件中没有则抛出异常
        content_check_cron = daily_content_check_config.get('content_check_cron')
        if not content_check_cron:
            raise ValueError("daily_content_check.content_check_cron 配置项缺失")
        analysis_cron = daily_content_check_config.get('analysis_cron')
        if not analysis_cron:
            raise ValueError("daily_content_check.analysis_cron 配置项缺失")
            
        self.daily_content_check = DailyContentCheckConfig(
            enabled=self._get_bool_env_or_config('DAILY_CONTENT_CHECK_ENABLED', daily_content_check_config.get('enabled', True)),
            content_check_cron=self._get_cron_list_env_or_config('CONTENT_CHECK_CRON', content_check_cron),
            analysis_cron=self._get_cron_list_env_or_config('ANALYSIS_CRON', analysis_cron),
            check_date_offset=daily_content_check_config.get('check_date_offset', 0),
            morning_check_hour=daily_content_check_config.get('morning_check_hour', 9),
            afternoon_check_hour=daily_content_check_config.get('afternoon_check_hour', 14),
            evening_check_hour=daily_content_check_config.get('evening_check_hour', 18),
            weekend_check_enabled=daily_content_check_config.get('weekend_check_enabled', False),
            retry_attempts=daily_content_check_config.get('retry_attempts', 3),
            retry_delay=daily_content_check_config.get('retry_delay', 300),
            max_execution_time=daily_content_check_config.get('max_execution_time', 600),
            reminder_enabled=daily_content_check_config.get('reminder_enabled', True),
            duplicate_prevention_hours=daily_content_check_config.get('duplicate_prevention_hours', 4),
            batch_check_enabled=daily_content_check_config.get('batch_check_enabled', True),
            summary_report_enabled=daily_content_check_config.get('summary_report_enabled', True)
        )
        
        # 通知配置
        notifications_config = self._config_data.get('notifications', {})
        email_config = notifications_config.get('email', {})
        
        self.notifications = NotificationConfig(
            enabled=notifications_config.get('enabled', False),
            webhook_url=notifications_config.get('webhook_url', ''),
            email_enabled=email_config.get('enabled', False),
            smtp_server=email_config.get('smtp_server', ''),
            smtp_port=email_config.get('smtp_port', 587),
            username=email_config.get('username', ''),
            password=email_config.get('password', ''),
            recipients=email_config.get('recipients', [])
        )
        
        # 日报汇总分析配置
        daily_summary_config = self._config_data.get('daily_summary_analysis', {})
        schedule_config = daily_summary_config.get('schedule', {})
        data_collection_config = daily_summary_config.get('data_collection', {})
        analysis_config = daily_summary_config.get('analysis', {})
        glm_enhancement_config = daily_summary_config.get('glm_enhancement', {})
        notification_config = daily_summary_config.get('notification', {})
        execution_config = daily_summary_config.get('execution', {})
        
        self.daily_summary_analysis = DailySummaryConfig(
            enabled=self._get_bool_env_or_config('DAILY_SUMMARY_ENABLED', daily_summary_config.get('enabled', True)),
            schedule=DailySummaryScheduleConfig(
                enabled=schedule_config.get('enabled', True),
                cron_expression=self._get_env_or_config('DAILY_SUMMARY_CRON', schedule_config.get('cron_expression', '0 9 * * *')),
                timezone=schedule_config.get('timezone', 'Asia/Shanghai'),
                retry_attempts=schedule_config.get('retry_attempts', 3),
                retry_delay=schedule_config.get('retry_delay', 300),
                max_execution_time=schedule_config.get('max_execution_time', 1800)
            ),
            data_collection=DailySummaryDataCollectionConfig(
                target_date_offset=data_collection_config.get('target_date_offset', -1),
                include_weekends=data_collection_config.get('include_weekends', False),
                min_reports_required=data_collection_config.get('min_reports_required', 1),
                max_reports_per_user=data_collection_config.get('max_reports_per_user', 1),
                content_validation_enabled=data_collection_config.get('content_validation_enabled', True)
            ),
            analysis=DailySummaryAnalysisConfig(
                deviation_analysis_enabled=analysis_config.get('deviation_analysis_enabled', True),
                completion_analysis_enabled=analysis_config.get('completion_analysis_enabled', True),
                trend_analysis_enabled=analysis_config.get('trend_analysis_enabled', True),
                performance_scoring_enabled=analysis_config.get('performance_scoring_enabled', True),
                team_insights_enabled=analysis_config.get('team_insights_enabled', True),
                individual_insights_enabled=analysis_config.get('individual_insights_enabled', True)
            ),
            glm_enhancement=DailySummaryGLMEnhancementConfig(
                enabled=glm_enhancement_config.get('enabled', True),
                user_analysis_prompt=glm_enhancement_config.get('user_analysis_prompt', '基于用户的日报和日计划，分析工作偏离度、完成率，并提供简洁的洞察和建议'),
                team_insights_prompt=glm_enhancement_config.get('team_insights_prompt', '基于团队日报数据，生成团队整体表现洞察，包括趋势分析和改进建议'),
                recommendations_prompt=glm_enhancement_config.get('recommendations_prompt', '基于团队表现数据，生成具体的管理建议和改进措施'),
                max_tokens=glm_enhancement_config.get('max_tokens', 1500),
                temperature=glm_enhancement_config.get('temperature', 0.7),
                timeout=glm_enhancement_config.get('timeout', 60)
            ),
            notification=DailySummaryNotificationConfig(
                enabled=notification_config.get('enabled', True),
                recipients=notification_config.get('recipients', []),
                notification_type=notification_config.get('notification_type', 'private_chat'),
                message_format=notification_config.get('message_format', 'rich_text'),
                include_individual_summaries=notification_config.get('include_individual_summaries', True),
                include_team_insights=notification_config.get('include_team_insights', True),
                include_recommendations=notification_config.get('include_recommendations', True),
                max_users_in_summary=notification_config.get('max_users_in_summary', 10)
            ),
            execution=DailySummaryExecutionConfig(
                parallel_analysis_enabled=execution_config.get('parallel_analysis_enabled', True),
                max_concurrent_users=execution_config.get('max_concurrent_users', 5),
                batch_size=execution_config.get('batch_size', 10),
                error_tolerance_rate=execution_config.get('error_tolerance_rate', 0.2),
                skip_on_no_data=execution_config.get('skip_on_no_data', True),
                save_intermediate_results=execution_config.get('save_intermediate_results', True)
            )
        )
        
    def _get_env_or_config(self, env_key: str, config_value: Any) -> str:
        """优先从环境变量获取值，否则使用配置文件值"""
        return os.getenv(env_key, config_value)
        
    def _get_bool_env_or_config(self, env_key: str, config_value: bool) -> bool:
        """获取布尔值配置"""
        env_value = os.getenv(env_key)
        if env_value is not None:
            return env_value.lower() in ('true', '1', 'yes', 'on')
        return config_value
        
    def _get_cron_list_env_or_config(self, env_key: str, config_value: Union[str, List[str]]) -> Union[str, List[str]]:
        """获取cron表达式列表配置，支持环境变量中的逗号分隔格式"""
        env_value = os.getenv(env_key)
        if env_value is not None:
            # 如果环境变量包含逗号，则分割为列表
            if ',' in env_value:
                return [cron.strip() for cron in env_value.split(',')]
            else:
                return env_value
        return config_value
        
    def validate(self) -> bool:
        """验证配置的有效性"""
        errors = []
        
        # 验证必需的配置项
        if not self.github.token:
            errors.append("GitHub token未配置")
        if not self.github.organization:
            errors.append("GitHub组织名未配置")
        if not self.github.use_org_discussions and not self.github.repository:
            errors.append("仓库级别Discussions需要配置仓库名")
        if not self.glm.api_key:
            errors.append("GLM API密钥未配置")
            
        if errors:
            raise ValueError(f"配置验证失败: {', '.join(errors)}")
            
        return True
        
    def get_config_summary(self) -> Dict[str, Any]:
        """获取配置摘要（隐藏敏感信息）"""
        return {
            'github': {
                'organization': self.github.organization,
                'repository': self.github.repository,
                'discussion_category': self.github.discussion_category,
                'token_configured': bool(self.github.token)
            },
            'glm': {
                'model': self.glm.model,
                'base_url': self.glm.base_url,
                'api_key_configured': bool(self.glm.api_key)
            },
            'analysis': {
                'deviation_analysis': self.analysis.enable_deviation_analysis,
                'clarity_analysis': self.analysis.enable_clarity_analysis,
                'consistency_analysis': self.analysis.enable_consistency_analysis
            },
            'scheduler': {
                'cron_expression': self.scheduler.cron_expression,
                'timezone': self.scheduler.timezone
            },
            'weekly_reports': {
                'enabled': self.weekly_reports.enabled,
                'execution_time': f'周{self.weekly_reports.execution_day} {self.weekly_reports.execution_hour}:00',
                'glm_enhancement_enabled': self.weekly_reports.glm_enhancement.enabled,
                'send_to_individuals': self.weekly_reports.delivery.send_to_individuals,
                'send_to_management': self.weekly_reports.delivery.send_to_management
            }
        }
