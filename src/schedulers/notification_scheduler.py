import asyncio
import logging
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any
from pathlib import Path
import json
import threading
import time

from ..trackers.deviation_tracker import DeviationTracker
from ..generators.report_generator import ReportGenerator
from ..clients.feishu_client import FeishuClient
from ..clients.enhanced_feishu_client import EnhancedFeishuClient, FeishuConfig, FeishuClientWrapper
from ..storage.json_data_manager import JSONDataManager

logger = logging.getLogger(__name__)

class NotificationScheduler:
    """通知调度器
    
    整合偏离检测和通知发送，支持定时检查和即时通知，防重复通知机制。
    """
    
    def __init__(self, config: Dict[str, Any], use_llm_reports: bool = True):
        """初始化通知调度器
        
        Args:
            config: 配置字典，包含偏离检测、汇报生成和飞书通知配置
            use_llm_reports: 是否使用LLM生成报告
        """
        self.config = config
        self.deviation_config = config.get('deviation_tracking', {})
        self.report_config = config.get('report', {})
        self.feishu_config = config.get('feishu', {})
        
        # 初始化组件
        storage_config = config.get('storage', {})
        self.data_manager = JSONDataManager(
            data_dir=storage_config.get('base_dir', 'data'),
            backup_enabled=storage_config.get('backup_enabled', True),
            cache_enabled=storage_config.get('cache_enabled', True),
            max_cache_size=storage_config.get('max_cache_size', 1000)
        )
        self.deviation_tracker = DeviationTracker(self.data_manager, self.deviation_config)
        self.report_generator = ReportGenerator(self.report_config)
        self.feishu_client = self._initialize_feishu_client()
        
        # 通知状态管理
        self.notification_history_file = config.get('storage', {}).get('base_dir', 'data') + '/notification_history.json'
        self.notification_history = self._load_notification_history()
        
        # 调度器状态
        self.is_running = False
        self.scheduler_thread = None
        
        # 配置参数
        self.check_interval = self.deviation_config.get('check_interval_minutes', 60) * 60  # 转换为秒
        self.notification_hours = self.feishu_config.get('notification_hours', [9, 14, 18])
        self.weekend_notifications = self.feishu_config.get('weekend_notifications', False)
        self.duplicate_prevention_hours = self.feishu_config.get('duplicate_prevention_hours', 4)
        self.use_llm_reports = use_llm_reports
    
    def _initialize_feishu_client(self):
        """初始化飞书客户端
        
        根据配置选择使用API模式或Webhook模式
        
        Returns:
            飞书客户端实例或None
        """
        if not self.feishu_config.get('enabled', False):
            return None
        
        try:
            # 检查是否启用API模式
            api_config = self.feishu_config.get('api', {})
            if api_config.get('enabled', False):
                # 使用增强版API客户端
                import os
                
                app_id = api_config.get('app_id') or os.getenv('FEISHU_APP_ID')
                app_secret = api_config.get('app_secret') or os.getenv('FEISHU_APP_SECRET')
                
                if not app_id or not app_secret:
                    logger.warning("飞书API配置不完整，app_id或app_secret缺失")
                    return None
                
                feishu_config = FeishuConfig(
                    app_id=app_id,
                    app_secret=app_secret,
                    base_url=api_config.get('base_url', 'https://open.feishu.cn'),
                    timeout=api_config.get('timeout', 30),
                    max_retries=api_config.get('max_retries', 3),
                    retry_delay=api_config.get('retry_delay', 1.0)
                )
                
                enhanced_client = EnhancedFeishuClient(feishu_config)
                default_chat_id = api_config.get('default_chat_id') or os.getenv('FEISHU_DEFAULT_CHAT_ID')
                
                # 使用包装器保持接口兼容性
                wrapper_client = FeishuClientWrapper(enhanced_client, default_chat_id)
                
                # 测试连接
                if enhanced_client.test_connection():
                    logger.info("飞书API客户端初始化成功")
                    return wrapper_client
                else:
                    logger.error("飞书API连接测试失败")
                    return None
            
            # 检查是否启用Webhook模式
            webhook_config = self.feishu_config.get('webhook', {})
            if webhook_config.get('enabled', False):
                # 使用传统Webhook客户端
                logger.info("使用飞书Webhook模式")
                return FeishuClient(self.feishu_config)
            
            logger.warning("飞书配置中未启用API或Webhook模式")
            return None
            
        except Exception as e:
            logger.error(f"初始化飞书客户端失败: {e}")
            return None
        
    def _load_notification_history(self) -> Dict[str, Any]:
        """加载通知历史记录
        
        Returns:
            通知历史记录字典
        """
        try:
            history_path = Path(self.notification_history_file)
            if history_path.exists():
                with open(history_path, 'r', encoding='utf-8') as f:
                    return json.load(f)
            else:
                return {'notifications': [], 'last_cleanup': None}
        except Exception as e:
            logger.error(f"加载通知历史记录失败: {e}")
            return {'notifications': [], 'last_cleanup': None}
    
    def _save_notification_history(self):
        """保存通知历史记录"""
        try:
            history_path = Path(self.notification_history_file)
            history_path.parent.mkdir(parents=True, exist_ok=True)
            
            with open(history_path, 'w', encoding='utf-8') as f:
                json.dump(self.notification_history, f, ensure_ascii=False, indent=2)
        except Exception as e:
            logger.error(f"保存通知历史记录失败: {e}")
    
    def _is_duplicate_notification(self, user: str, deviation_type: str) -> bool:
        """检查是否为重复通知
        
        Args:
            user: 用户名
            deviation_type: 偏离类型
            
        Returns:
            是否为重复通知
        """
        current_time = datetime.now()
        cutoff_time = current_time - timedelta(hours=self.duplicate_prevention_hours)
        
        for notification in self.notification_history.get('notifications', []):
            if (notification.get('user') == user and 
                notification.get('type') == deviation_type and
                datetime.fromisoformat(notification.get('timestamp', '')) > cutoff_time):
                return True
        
        return False
    
    def _record_notification(self, user: str, deviation_type: str, success: bool, details: Dict[str, Any] = None):
        """记录通知发送情况
        
        Args:
            user: 用户名
            deviation_type: 偏离类型
            success: 发送是否成功
            details: 详细信息
        """
        notification_record = {
            'timestamp': datetime.now().isoformat(),
            'user': user,
            'type': deviation_type,
            'success': success,
            'details': details or {}
        }
        
        if 'notifications' not in self.notification_history:
            self.notification_history['notifications'] = []
        
        self.notification_history['notifications'].append(notification_record)
        
        # 清理旧记录（保留最近30天）
        self._cleanup_old_notifications()
        
        # 保存历史记录
        self._save_notification_history()
    
    def _cleanup_old_notifications(self):
        """清理旧的通知记录"""
        cutoff_time = datetime.now() - timedelta(days=30)
        
        if 'notifications' in self.notification_history:
            self.notification_history['notifications'] = [
                n for n in self.notification_history['notifications']
                if datetime.fromisoformat(n.get('timestamp', '')) > cutoff_time
            ]
        
        self.notification_history['last_cleanup'] = datetime.now().isoformat()
    
    def _should_send_notification_now(self) -> bool:
        """判断当前时间是否应该发送通知
        
        Returns:
            是否应该发送通知
        """
        now = datetime.now()
        
        # 检查是否为周末
        if not self.weekend_notifications and now.weekday() >= 5:  # 5=Saturday, 6=Sunday
            return False
        
        # 检查是否在通知时间范围内
        current_hour = now.hour
        return current_hour in self.notification_hours
    
    def check_and_notify(self) -> Dict[str, Any]:
        """检查偏离情况并发送通知
        
        Returns:
            检查和通知结果
        """
        result = {
            'timestamp': datetime.now().isoformat(),
            'checked_users': [],
            'notifications_sent': [],
            'errors': []
        }
        
        try:
            # 获取所有存在连续偏离的用户
            continuous_deviations = self.deviation_tracker.get_all_continuous_deviations()
            
            if not continuous_deviations:
                logger.info("未发现连续偏离情况")
                return result
            
            logger.info(f"发现 {len(continuous_deviations)} 个连续偏离情况")
            
            for deviation in continuous_deviations:
                user = deviation.get('user')
                deviation_type = deviation.get('type', 'continuous_deviation')
                
                result['checked_users'].append(user)
                
                try:
                    # 检查是否为重复通知
                    if self._is_duplicate_notification(user, deviation_type):
                        logger.info(f"跳过重复通知: {user} - {deviation_type}")
                        continue
                    
                    # 检查是否应该在当前时间发送通知
                    if not self._should_send_notification_now():
                        logger.info(f"当前时间不适合发送通知: {datetime.now().hour}")
                        continue
                    
                    # 生成汇报 - 优先使用LLM生成
                    if self.use_llm_reports:
                        try:
                            report_result = self.report_generator.generate_llm_report(
                                user, deviation, report_type='personal'
                            )
                            logger.info(f"使用LLM生成报告: {user}")
                        except Exception as e:
                            logger.warning(f"LLM报告生成失败，降级使用传统模板: {user} - {e}")
                            report_result = self.report_generator.generate_deviation_report(
                                user, deviation, format_type='detailed'
                            )
                    else:
                        report_result = self.report_generator.generate_deviation_report(
                            user, deviation, format_type='detailed'
                        )
                    
                    if not report_result.get('success'):
                        error_msg = f"生成汇报失败: {user} - {report_result.get('error', 'Unknown error')}"
                        logger.error(error_msg)
                        result['errors'].append(error_msg)
                        continue
                    
                    # 发送飞书通知
                    if self.feishu_client:
                        notification_success = self._send_feishu_notification(
                            user, report_result, deviation
                        )
                        
                        # 记录通知发送情况
                        self._record_notification(
                            user, deviation_type, notification_success,
                            {'report_type': 'detailed', 'deviation_days': deviation.get('consecutive_days', 0)}
                        )
                        
                        if notification_success:
                            result['notifications_sent'].append({
                                'user': user,
                                'type': deviation_type,
                                'method': 'feishu'
                            })
                        else:
                            result['errors'].append(f"飞书通知发送失败: {user}")
                    else:
                        logger.warning("飞书客户端未配置，跳过通知发送")
                        
                except Exception as e:
                    error_msg = f"处理用户 {user} 的偏离通知时发生错误: {e}"
                    logger.error(error_msg)
                    result['errors'].append(error_msg)
            
        except Exception as e:
            error_msg = f"检查偏离情况时发生错误: {e}"
            logger.error(error_msg)
            result['errors'].append(error_msg)
        
        return result
    
    def _format_personal_message(self, report_content: str, user: str, deviation: Dict[str, Any]) -> str:
        """格式化适合个人私聊的消息内容
        
        Args:
            report_content: 原始报告内容（可能是LLM生成的）
            user: 用户名
            deviation: 偏离信息
            
        Returns:
            格式化后的个人消息
        """
        # 如果report_content已经是LLM生成的个性化内容，直接使用
        if report_content and len(report_content.strip()) > 100:  # 假设LLM生成的内容较长
            return report_content
        try:
            # 提取关键信息
            consecutive_days = deviation.get('consecutive_days', 0)
            has_deviation = deviation.get('has_continuous_deviation', True)
            
            if not has_deviation:
                return f"Hi {user}，今天的工作状态很好，继续保持！💪"
            
            # 构建亲切的个人消息（传统模板）
            message_lines = [
                f"Hi {user}，",
                f"最近几天的工作似乎有些偏离计划，我想和你聊聊。😊",
                "",
                "🤔 我注意到的情况：",
                "看起来你的工作进度和原定计划有些差距，这很正常，每个人都会遇到这种情况。",
                "",
                "💡 一些小建议：",
                "• 不妨重新看看你的任务清单，哪些是真正紧急重要的？",
                "• 如果遇到了什么困难或阻碍，别憋着，找同事或领导聊聊",
                "• 适当调整一下工作节奏，有时候慢一点反而能走得更稳",
                "• 记得给自己留点喘息的空间，别把自己逼得太紧",
                "",
                "🌟 记住：",
                "每个人都有状态起伏的时候，关键是及时调整。你一直都很努力，相信你能很快找回节奏！",
                "",
                "有什么需要帮助的，随时找我聊！加油！💪"
            ]
            
            return '\n'.join(message_lines)
            
        except Exception as e:
            logger.error(f"格式化个人消息时发生错误: {e}")
            # 如果格式化失败，返回简化版本
            return f"Hi {user}，工作状态需要关注，有什么困难记得及时沟通哦！😊"
    
    def _format_management_message(self, user: str, deviation: Dict[str, Any]) -> str:
        """
        格式化管理层通知消息
        
        Args:
            user: 用户名
            deviation: 偏离信息
            
        Returns:
            格式化后的管理层消息内容
        """
        try:
            consecutive_days = deviation.get('consecutive_days', 0)
            
            # 构建简洁的管理层消息
            message_lines = [
                f"📋 团队状态提醒",
                "",
                f"团队成员 {user} 近期工作进度出现偏离，已持续{consecutive_days}天。",
                "",
                "🎯 管理建议：",
                "• 安排一对一沟通，了解具体困难和阻碍",
                "• 评估当前任务分配是否合理，必要时进行调整",
                "• 考虑提供额外的资源支持或技术指导",
                "• 关注团队成员的工作负荷和心理状态",
                "",
                "💡 关注要点：",
                "持续的工作偏离可能影响项目进度和团队士气，建议及时介入并提供必要支持。",
                "",
                "建议在2个工作日内与该成员进行深度沟通。"
            ]
            
            return "\n".join(message_lines)
            
        except Exception as e:
            logger.error(f"格式化管理层消息失败: {e}")
            return f"团队成员 {user} 工作状态需要关注，建议及时沟通了解情况。"
    
    def _send_feishu_notification(self, user: str, report_result: Dict[str, Any], 
                                 deviation: Dict[str, Any]) -> bool:
        """发送飞书通知
        
        Args:
            user: 用户名
            report_result: 汇报生成结果
            deviation: 偏离信息
            
        Returns:
            发送是否成功
        """
        try:
            report_content = report_result.get('content', '')
            report_data = report_result.get('data', {})
            
            # 加载用户映射配置
            user_mapping = {}
            try:
                import json
                with open('feishu_mapping.json', 'r', encoding='utf-8') as f:
                    mapping_config = json.load(f)
                    user_mapping = mapping_config.get('user_mapping', {})
            except Exception as e:
                logger.warning(f"加载用户映射配置失败: {e}")
            
            # 获取用户的飞书ID
            feishu_user_id = user_mapping.get(user)
            if not feishu_user_id:
                logger.warning(f"未找到用户 {user} 的飞书映射，跳过个人通知")
                return False
            
            # 使用enhanced_feishu_client发送个人私聊通知
            personal_success = False
            if hasattr(self.feishu_client, 'client'):
                try:
                    # 格式化适合个人私聊的消息内容
                    personal_message = self._format_personal_message(report_content, user, deviation)
                    
                    # 发送个人消息
                    personal_success = self.feishu_client.client.send_text_message(
                        receive_id=feishu_user_id,
                        text=personal_message,
                        receive_id_type='open_id'
                    )
                    
                    if personal_success:
                        logger.info(f"飞书个人通知发送成功: {user} ({feishu_user_id})")
                    else:
                        logger.error(f"飞书个人通知发送失败: {user} ({feishu_user_id})")
                        
                except Exception as e:
                    logger.error(f"发送个人通知时发生错误: {e}")
                    personal_success = False
            else:
                logger.warning("enhanced_feishu_client未配置，无法发送个人通知")
            
            # 发送管理层通知
            management_success = True  # 默认为成功，如果未配置管理层通知
            if hasattr(self.feishu_client, 'send_management_notification'):
                try:
                    # 生成管理层通知内容 - 优先使用LLM
                    if self.use_llm_reports:
                        try:
                            mgmt_report = self.report_generator.generate_llm_report(
                                user, deviation, report_type='management'
                            )
                            if mgmt_report.get('success'):
                                management_message = mgmt_report.get('content', '')
                                logger.info(f"使用LLM生成管理层报告: {user}")
                            else:
                                management_message = self._format_management_message(user, deviation)
                        except Exception as e:
                            logger.warning(f"LLM管理层报告生成失败，使用传统模板: {user} - {e}")
                            management_message = self._format_management_message(user, deviation)
                    else:
                        management_message = self._format_management_message(user, deviation)
                    
                    management_success = self.feishu_client.send_management_notification(management_message)
                    if management_success:
                        logger.info(f"管理层通知发送成功: {user}")
                    else:
                        logger.warning(f"管理层通知发送失败: {user}")
                except Exception as e:
                    logger.error(f"发送管理层通知时发生错误: {e}")
                    management_success = False
            
            # 个人通知成功就认为整体成功
            return personal_success
            
        except Exception as e:
            logger.error(f"发送飞书通知时发生错误: {e}")
            return False
    
    def start_scheduler(self):
        """启动定时调度器"""
        if self.is_running:
            logger.warning("调度器已在运行中")
            return
        
        self.is_running = True
        self.scheduler_thread = threading.Thread(target=self._scheduler_loop, daemon=True)
        self.scheduler_thread.start()
        logger.info(f"通知调度器已启动，检查间隔: {self.check_interval}秒")
    
    def stop_scheduler(self):
        """停止定时调度器"""
        self.is_running = False
        if self.scheduler_thread:
            self.scheduler_thread.join(timeout=5)
        logger.info("通知调度器已停止")
    
    def _scheduler_loop(self):
        """调度器主循环"""
        while self.is_running:
            try:
                logger.debug("执行定时偏离检查")
                result = self.check_and_notify()
                
                if result.get('notifications_sent'):
                    logger.info(f"本次检查发送了 {len(result['notifications_sent'])} 个通知")
                
                if result.get('errors'):
                    logger.warning(f"本次检查发生了 {len(result['errors'])} 个错误")
                
            except Exception as e:
                logger.error(f"调度器循环中发生错误: {e}")
            
            # 等待下次检查
            time.sleep(self.check_interval)
    
    def manual_check(self, user: str = None) -> Dict[str, Any]:
        """手动触发检查
        
        Args:
            user: 指定用户，如果为None则检查所有用户
            
        Returns:
            检查结果
        """
        logger.info(f"手动触发偏离检查: {user or '所有用户'}")
        
        if user:
            # 检查指定用户
            try:
                deviation = self.deviation_tracker.check_continuous_deviation(user, None)
                if deviation:
                    # 生成汇报并发送通知 - 优先使用LLM
                    if self.use_llm_reports:
                        try:
                            report_result = self.report_generator.generate_llm_report(
                                user, deviation, report_type='personal'
                            )
                            logger.info(f"手动检查使用LLM生成报告: {user}")
                        except Exception as e:
                            logger.warning(f"手动检查LLM报告生成失败，降级使用传统模板: {user} - {e}")
                            report_result = self.report_generator.generate_deviation_report(
                                user, deviation, format_type='detailed'
                            )
                    else:
                        report_result = self.report_generator.generate_deviation_report(
                            user, deviation, format_type='detailed'
                        )
                    
                    if report_result.get('success') and self.feishu_client:
                        success = self._send_feishu_notification(user, report_result, deviation)
                        return {
                            'user': user,
                            'deviation_found': True,
                            'notification_sent': success,
                            'report': report_result
                        }
                    
                return {
                    'user': user,
                    'deviation_found': bool(deviation),
                    'notification_sent': False
                }
            except Exception as e:
                return {
                    'user': user,
                    'error': str(e)
                }
        else:
            # 检查所有用户
            return self.check_and_notify()
    
    def get_notification_stats(self) -> Dict[str, Any]:
        """获取通知统计信息
        
        Returns:
            通知统计信息
        """
        notifications = self.notification_history.get('notifications', [])
        
        # 统计最近7天的通知
        recent_cutoff = datetime.now() - timedelta(days=7)
        recent_notifications = [
            n for n in notifications
            if datetime.fromisoformat(n.get('timestamp', '')) > recent_cutoff
        ]
        
        # 按用户统计
        user_stats = {}
        for notification in recent_notifications:
            user = notification.get('user')
            if user not in user_stats:
                user_stats[user] = {'total': 0, 'success': 0, 'failed': 0}
            
            user_stats[user]['total'] += 1
            if notification.get('success'):
                user_stats[user]['success'] += 1
            else:
                user_stats[user]['failed'] += 1
        
        return {
            'total_notifications': len(notifications),
            'recent_notifications': len(recent_notifications),
            'user_stats': user_stats,
            'scheduler_running': self.is_running,
            'last_cleanup': self.notification_history.get('last_cleanup'),
            'config': {
                'check_interval_minutes': self.check_interval // 60,
                'notification_hours': self.notification_hours,
                'weekend_notifications': self.weekend_notifications,
                'duplicate_prevention_hours': self.duplicate_prevention_hours
            }
        }