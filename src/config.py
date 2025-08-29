"""
配置管理模块
负责加载和管理所有配置参数
"""

import os
import yaml
from pathlib import Path
from typing import Dict, Any, Optional
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
    thresholds: AnalysisThresholds = field(default_factory=AnalysisThresholds)


@dataclass
class SchedulerConfig:
    """调度器配置"""
    cron_expression: str = "0 18 * * *"
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
        
    def _get_env_or_config(self, env_key: str, config_value: Any) -> str:
        """优先从环境变量获取值，否则使用配置文件值"""
        return os.getenv(env_key, config_value)
        
    def _get_bool_env_or_config(self, env_key: str, config_value: bool) -> bool:
        """获取布尔值配置"""
        env_value = os.getenv(env_key)
        if env_value is not None:
            return env_value.lower() in ('true', '1', 'yes', 'on')
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
            }
        }
