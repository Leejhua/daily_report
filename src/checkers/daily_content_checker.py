from datetime import datetime, timedelta
from typing import List, Dict, Optional, Set
import json
import os
from dataclasses import dataclass

from ..clients.github_client import GitHubClient
from ..clients.feishu_client import FeishuClient
from ..config import Config
from ..utils.logger import setup_logging, get_logger


@dataclass
class CheckResult:
    """检测结果数据类"""
    user: str
    date: str
    has_daily_plan: bool
    has_daily_report: bool
    missing_content: List[str]


class DailyContentChecker:
    """日计划/日报检测器"""
    
    def __init__(self, config: Config):
        self.config = config
        self.logger = get_logger(__name__)
        
        # 初始化GitHub客户端
        self.github_client = GitHubClient(config.github)
        
        # 初始化飞书客户端
        self.feishu_client = FeishuClient(config.feishu)
        
        # 防重复提醒记录文件
        self.reminder_history_file = "reminder_history.json"
        self.reminder_history = self._load_reminder_history()
        
        # 日计划/日报关键词
        self.daily_plan_keywords = ["计划", "plan", "今日计划", "工作计划"]
        self.daily_report_keywords = ["日报", "report", "今日总结", "工作总结", "日结"]
    
    def _load_reminder_history(self) -> Dict:
        """加载提醒历史记录"""
        if os.path.exists(self.reminder_history_file):
            try:
                with open(self.reminder_history_file, 'r', encoding='utf-8') as f:
                    return json.load(f)
            except Exception as e:
                self.logger.warning(f"加载提醒历史记录失败: {e}")
        return {}
    
    def _save_reminder_history(self):
        """保存提醒历史记录"""
        try:
            with open(self.reminder_history_file, 'w', encoding='utf-8') as f:
                json.dump(self.reminder_history, f, ensure_ascii=False, indent=2)
        except Exception as e:
            self.logger.error(f"保存提醒历史记录失败: {e}")
    
    def _should_send_reminder(self, user: str, date: str, content_type: str) -> bool:
        """检查是否应该发送提醒（防重复提醒）"""
        key = f"{user}_{date}_{content_type}"
        last_reminder = self.reminder_history.get(key)
        
        if not last_reminder:
            return True
        
        # 如果距离上次提醒超过4小时，可以再次提醒
        last_time = datetime.fromisoformat(last_reminder)
        now = datetime.now()
        return (now - last_time).total_seconds() > 4 * 3600
    
    def _record_reminder(self, user: str, date: str, content_type: str):
        """记录提醒发送时间"""
        key = f"{user}_{date}_{content_type}"
        self.reminder_history[key] = datetime.now().isoformat()
        self._save_reminder_history()
    
    def _get_content_types_to_check(self, check_time: Optional[datetime] = None) -> List[str]:
        """根据时间段确定应该检查的内容类型
        
        Args:
            check_time: 检查时间，如果为None则使用当前时间
            
        Returns:
            应该检查的内容类型列表，可能包含 'daily_plan' 和/或 'daily_report'
        """
        if check_time is None:
            check_time = datetime.now()
        
        hour = check_time.hour
        
        # 早上（0-12点）：只检查日计划
        if 0 <= hour <= 12:
            return ['daily_plan']
        # 下午到晚上（13-24点）：检查日计划和日报
        else:
            return ['daily_plan', 'daily_report']
    
    def _identify_content_type(self, content: str) -> Set[str]:
        """识别内容类型（日计划或日报）"""
        content_lower = content.lower()
        content_types = set()
        
        # 获取内容的前几行，用于检查标题
        lines = content.strip().split('\n')
        first_lines = '\n'.join(lines[:3]).lower()  # 检查前3行
        
        # 优先检查标题或开头是否明确指示内容类型
        title_plan_keywords = ["# 日计划", "##日计划", "日计划:", "日计划：", "今日计划", "工作计划"]
        title_report_keywords = ["# 日报", "##日报", "日报:", "日报：", "今日总结", "工作总结", "日结"]
        
        # 检查标题中的关键词（优先级高）
        title_has_plan = any(keyword in first_lines for keyword in title_plan_keywords)
        title_has_report = any(keyword in first_lines for keyword in title_report_keywords)
        
        # 如果标题明确指示了类型，优先使用标题判断
        if title_has_plan and not title_has_report:
            content_types.add("daily_plan")
        elif title_has_report and not title_has_plan:
            content_types.add("daily_report")
        elif title_has_plan and title_has_report:
            # 如果标题同时包含两种类型，都添加
            content_types.add("daily_plan")
            content_types.add("daily_report")
        else:
            # 如果标题没有明确指示，则检查整个内容
            if any(keyword in content_lower for keyword in self.daily_plan_keywords):
                content_types.add("daily_plan")
            
            if any(keyword in content_lower for keyword in self.daily_report_keywords):
                content_types.add("daily_report")
        
        return content_types
    
    async def check_user_daily_content(self, user: str, date: str, check_time: Optional[datetime] = None) -> CheckResult:
        """检查指定用户在指定日期的日计划/日报提交情况
        
        Args:
            user: 用户名
            date: 检查日期（格式：YYYY-MM-DD）
            check_time: 检查时间，用于确定应该检查的内容类型
        """
        # 确定应该检查的内容类型
        content_types_to_check = self._get_content_types_to_check(check_time)
        
        check_plan = 'daily_plan' in content_types_to_check
        check_report = 'daily_report' in content_types_to_check
        
        content_desc = []
        if check_plan:
            content_desc.append("日计划")
        if check_report:
            content_desc.append("日报")
        
        self.logger.info(f"检查用户 {user} 在 {date} 的{'/'.join(content_desc)}")
        
        has_daily_plan = False
        has_daily_report = False
        
        try:
            # 将字符串日期转换为date对象
            from datetime import datetime
            target_date = datetime.strptime(date, '%Y-%m-%d').date()
            
            # 获取指定日期的讨论
            discussions = await self.github_client.get_daily_discussions(target_date)
            
            for discussion in discussions:
                # 检查讨论作者和日期（不区分大小写）
                if (discussion.author.lower() == user.lower() and 
                    discussion.created_at.date() == target_date):
                    content_types = self._identify_content_type(discussion.body)
                    if 'daily_plan' in content_types:
                        has_daily_plan = True
                    if 'daily_report' in content_types:
                        has_daily_report = True
                
                # 检查讨论中的评论
                comments = await self.github_client.get_discussion_comments(discussion.number)
                for comment in comments:
                    # 检查评论作者和日期
                    if (comment.author.lower() == user.lower() and 
                        comment.created_at.date() == target_date):
                        content_types = self._identify_content_type(comment.body)
                        if 'daily_plan' in content_types:
                            has_daily_plan = True
                        if 'daily_report' in content_types:
                            has_daily_report = True
        
        except Exception as e:
            self.logger.error(f"检查用户 {user} 日计划/日报时出错: {e}")
        
        # 根据时间段确定缺失的内容类型
        missing_content = []
        if check_plan and not has_daily_plan:
            missing_content.append("日计划")
        if check_report and not has_daily_report:
            missing_content.append("日报")
        
        return CheckResult(
            user=user,
            date=date,
            has_daily_plan=has_daily_plan,
            has_daily_report=has_daily_report,
            missing_content=missing_content
        )
    
    def get_users_to_check(self) -> List[str]:
        """获取需要检查的用户列表"""
        # 从配置文件或飞书映射文件中获取用户列表
        users = []
        
        # 尝试从飞书映射文件获取用户列表
        mapping_file = "feishu_mapping.json"
        if os.path.exists(mapping_file):
            try:
                with open(mapping_file, 'r', encoding='utf-8') as f:
                    mapping = json.load(f)
                    users = list(mapping.get('user_mapping', {}).keys())
            except Exception as e:
                self.logger.warning(f"读取用户映射文件失败: {e}")
        
        # 如果没有从映射文件获取到用户，使用默认配置
        if not users:
            users = getattr(self.config, 'check_users', ['leejhua', 'example_user'])
        
        self.logger.info(f"需要检查的用户列表: {users}")
        return users
    
    def generate_reminder_message(self, user: str, missing_content: List[str], date: str) -> str:
        """生成提醒消息内容"""
        if not missing_content:
            return ""
        
        content_str = "、".join(missing_content)
        message = f"📝 提醒：{user}，您还没有提交 {date} 的{content_str}，请及时补充。\n\n"
        message += "💡 提交方式：在GitHub Discussions的'日结'分类中发布或评论您的日计划/日报内容。"
        
        return message
    
    def send_reminder(self, user: str, message: str, missing_content: List[str], date: str) -> bool:
        """发送提醒消息到飞书"""
        try:
            # 过滤掉已在4小时内发送过提醒的内容类型
            content_to_send = []
            for content_type in missing_content:
                content_key = "daily_plan" if content_type == "日计划" else "daily_report"
                if self._should_send_reminder(user, date, content_key):
                    content_to_send.append(content_type)
                else:
                    self.logger.info(f"用户 {user} 的 {content_type} 提醒已在4小时内发送过，跳过")
            
            # 如果没有需要发送的内容，返回True（不算失败）
            if not content_to_send:
                self.logger.info(f"用户 {user} 的所有提醒都已在4小时内发送过，无需重复发送")
                return True
            
            # 重新生成只包含需要发送内容的消息
            actual_message = self.generate_reminder_message(user, content_to_send, date)
            if not actual_message:
                return True
            
            # 发送飞书消息
            success = self.feishu_client._send_private_message(user, actual_message)
            
            if success:
                # 记录提醒发送时间（只记录实际发送的内容类型）
                for content_type in content_to_send:
                    content_key = "daily_plan" if content_type == "日计划" else "daily_report"
                    self._record_reminder(user, date, content_key)
                
                self.logger.info(f"成功向用户 {user} 发送提醒消息（内容：{', '.join(content_to_send)}）")
                return True
            else:
                self.logger.error(f"向用户 {user} 发送提醒消息失败")
                return False
        
        except Exception as e:
            self.logger.error(f"发送提醒消息时出错: {e}")
            return False
    
    async def check_and_remind_all_users(self, date: Optional[str] = None, check_time: Optional[datetime] = None) -> Dict[str, CheckResult]:
        """检查所有用户并发送提醒
        
        Args:
            date: 检查日期，如果为None则使用当前日期
            check_time: 检查时间，用于确定应该检查的内容类型
        """
        if not date:
            date = datetime.now().strftime('%Y-%m-%d')
        
        if check_time is None:
            check_time = datetime.now()
        
        # 确定检查的内容类型用于日志
        content_types_to_check = self._get_content_types_to_check(check_time)
        check_desc = []
        if 'daily_plan' in content_types_to_check:
            check_desc.append("日计划")
        if 'daily_report' in content_types_to_check:
            check_desc.append("日报")
        
        self.logger.info(f"开始检查所有用户在 {date} 的{'/'.join(check_desc)}提交情况（检查时间：{check_time.strftime('%H:%M')}）")
        
        users = self.get_users_to_check()
        results = {}
        
        for user in users:
            try:
                # 检查用户的日计划/日报提交情况
                result = await self.check_user_daily_content(user, date, check_time)
                results[user] = result
                
                # 如果有缺失内容，发送提醒
                if result.missing_content:
                    message = self.generate_reminder_message(user, result.missing_content, date)
                    if message:
                        self.send_reminder(user, message, result.missing_content, date)
                else:
                    self.logger.info(f"用户 {user} 已完成当日的日计划和日报")
            
            except Exception as e:
                self.logger.error(f"处理用户 {user} 时出错: {e}")
        
        return results
    
    def get_summary_report(self, results: Dict[str, CheckResult]) -> str:
        """生成检查结果摘要报告"""
        total_users = len(results)
        complete_users = sum(1 for result in results.values() if not result.missing_content)
        missing_plan_users = sum(1 for result in results.values() if "日计划" in result.missing_content)
        missing_report_users = sum(1 for result in results.values() if "日报" in result.missing_content)
        
        summary = f"📊 日计划/日报检查摘要\n\n"
        summary += f"总用户数: {total_users}\n"
        summary += f"已完成用户数: {complete_users}\n"
        summary += f"缺少日计划用户数: {missing_plan_users}\n"
        summary += f"缺少日报用户数: {missing_report_users}\n\n"
        
        summary += "详细情况:\n"
        for user, result in results.items():
            status = "✅ 已完成" if not result.missing_content else f"❌ 缺少: {', '.join(result.missing_content)}"
            summary += f"- {user}: {status}\n"
        
        return summary