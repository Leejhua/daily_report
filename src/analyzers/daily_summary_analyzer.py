"""日报汇总分析器模块
负责收集、分析和汇总团队日报数据，生成管理层报告
"""

import logging
import asyncio
from datetime import date, datetime, timedelta
from typing import List, Dict, Any, Optional

from src.config import Config
from src.clients.github_client import GitHubClient, DiscussionData
from src.clients.glm_client import GLMClient
from src.clients.enhanced_glm_client import EnhancedGLMClient
from src.clients.feishu_client import FeishuClient
from src.models.data_models import (
    DailyReportData, UserDailySummary, TeamDailySummaryReport,
    DailySummaryAnalysisTask, TaskStatus, create_daily_summary_analysis_task
)
from src.utils.logger import get_logger


class DailySummaryAnalyzer:
    """日报汇总分析器"""
    
    def __init__(self, config: Config):
        self.config = config
        self.logger = get_logger(__name__)
        
        # 初始化客户端
        self.github_client = GitHubClient(config.github)
        self.glm_client = GLMClient(config.glm)
        self.enhanced_glm_client = EnhancedGLMClient(config.glm)
        
        # 初始化飞书客户端（用于发送汇总报告）
        if hasattr(config, 'feishu') and config.feishu:
            self.feishu_client = FeishuClient(config.feishu)
        else:
            self.feishu_client = None
            self.logger.warning("飞书配置未找到，将无法发送汇总报告")
        
        # 初始化数据管理器
        from ..storage.json_data_manager import JSONDataManager
        self.data_manager = JSONDataManager(data_dir='data')
        
    async def run_daily_summary_analysis(self, target_date: Optional[date] = None) -> Dict[str, Any]:
        """
        运行日报汇总分析任务
        
        Args:
            target_date: 目标分析日期，默认为今天
            
        Returns:
            Dict[str, Any]: 分析结果摘要
        """
        if target_date is None:
            # 默认分析今天的日报数据
            target_date = date.today()
            
        self.logger.info(f"开始执行 {target_date} 的日报汇总分析任务")
        
        # 创建分析任务
        task = create_daily_summary_analysis_task(target_date.isoformat())
        task.start()
        
        analysis_summary = {
            'task_id': task.task_id,
            'date': target_date.isoformat(),
            'start_time': datetime.now().isoformat(),
            'users_analyzed': 0,
            'reports_collected': 0,
            'report_generated': False,
            'notification_sent': False,
            'errors': [],
            'success': False
        }
        
        try:
            # 1. 收集当日所有用户的日报数据
            daily_reports = await self._collect_daily_reports(target_date)
            
            if not daily_reports:
                self.logger.info(f"{target_date} 没有找到任何日报数据")
                task.fail("没有找到任何日报数据")
                analysis_summary['success'] = True
                analysis_summary['end_time'] = datetime.now().isoformat()
                return analysis_summary
                
            self.logger.info(f"收集到 {len(daily_reports)} 份日报数据")
            analysis_summary['reports_collected'] = len(daily_reports)
            
            # 2. 并行分析每个用户的日报
            user_summaries = await self._analyze_user_reports(daily_reports)
            analysis_summary['users_analyzed'] = len(user_summaries)
            
            # 3. 生成团队汇总报告
            team_report = await self._generate_team_summary_report(
                target_date, daily_reports, user_summaries
            )
            
            if team_report:
                analysis_summary['report_generated'] = True
                task.complete(team_report)
                
                # 4. 发送汇总报告给管理层
                if self.feishu_client and self._should_send_notification():
                    notification_success = await self._send_summary_notification(team_report)
                    analysis_summary['notification_sent'] = notification_success
                    
                    if not notification_success:
                        analysis_summary['errors'].append('汇总报告发送失败')
                
                # 5. 保存汇总报告数据
                await self._save_summary_report(team_report)
                
                analysis_summary['success'] = True
                self.logger.info(f"日报汇总分析任务完成: {len(user_summaries)} 个用户分析完成")
            else:
                task.fail("生成团队汇总报告失败")
                analysis_summary['errors'].append('生成团队汇总报告失败')
                
        except Exception as e:
            error_msg = f"日报汇总分析任务执行失败: {str(e)}"
            self.logger.error(error_msg, exc_info=True)
            task.fail(error_msg)
            analysis_summary['errors'].append(error_msg)
            
        analysis_summary['end_time'] = datetime.now().isoformat()
        return analysis_summary
        
    async def _collect_daily_reports(self, target_date: date) -> List[DailyReportData]:
        """
        收集指定日期的所有用户日报数据
        
        Args:
            target_date: 目标日期
            
        Returns:
            List[DailyReportData]: 日报数据列表
        """
        self.logger.info(f"开始收集 {target_date} 的日报数据")
        
        daily_reports = []
        
        try:
            # 获取当日的所有讨论
            discussions = await self.github_client.get_daily_discussions(target_date)
            
            if not discussions:
                self.logger.info(f"{target_date} 没有找到任何讨论")
                return daily_reports
                
            self.logger.info(f"找到 {len(discussions)} 个讨论")
            
            # 并行处理所有讨论
            collection_tasks = []
            for discussion in discussions:
                task = self._extract_user_daily_report(discussion, target_date)
                collection_tasks.append(task)
                
            # 执行所有收集任务
            results = await asyncio.gather(*collection_tasks, return_exceptions=True)
            
            # 处理结果
            for i, result in enumerate(results):
                if isinstance(result, Exception):
                    self.logger.error(f"收集讨论 #{discussions[i].number} 的日报数据失败: {str(result)}")
                elif result:
                    daily_reports.append(result)
                    
            self.logger.info(f"成功收集到 {len(daily_reports)} 份日报数据")
            
        except Exception as e:
            self.logger.error(f"收集日报数据时出错: {str(e)}", exc_info=True)
            
        return daily_reports
        
    async def _extract_user_daily_report(self, discussion: DiscussionData, 
                                       target_date: date) -> Optional[DailyReportData]:
        """
        从讨论中提取用户的日报数据
        
        Args:
            discussion: 讨论数据
            target_date: 目标日期
            
        Returns:
            Optional[DailyReportData]: 日报数据，如果没有找到则返回None
        """
        try:
            # 提取讨论中的日报和计划内容
            content_data = await self.github_client.extract_daily_content(discussion)
            
            daily_summary = content_data.get('daily_summary', '')
            daily_plan = content_data.get('daily_plan', '')
            
            # 如果没有日报内容，跳过
            if not daily_summary or not daily_summary.strip():
                return None
                
            # 验证是否为日报内容
            content_type = self.github_client.identify_content_type(daily_summary)
            if content_type != 'daily_report':
                return None
                
            # 从讨论标题或内容中提取用户信息
            user_info = await self._extract_user_info(discussion)
            
            if not user_info:
                self.logger.warning(f"无法从讨论 #{discussion.number} 中提取用户信息")
                return None
                
            return DailyReportData(
                user_id=user_info['user_id'],
                username=user_info['username'],
                date=target_date.isoformat(),
                plan_content=daily_plan,
                report_content=daily_summary,
                discussion_number=discussion.number
            )
            
        except Exception as e:
            self.logger.error(f"提取讨论 #{discussion.number} 的日报数据时出错: {str(e)}")
            return None
            
    async def _extract_user_info(self, discussion: DiscussionData) -> Optional[Dict[str, str]]:
        """
        从讨论中提取用户信息
        
        Args:
            discussion: 讨论数据
            
        Returns:
            Optional[Dict[str, str]]: 包含user_id和username的字典
        """
        try:
            # 验证输入数据
            if not discussion:
                self.logger.error("讨论数据为空")
                return None
                
            # 安全获取标题
            title = getattr(discussion, 'title', '') or ''
            author_data = getattr(discussion, 'author', '') or ''
            
            # 处理author字段，可能是字符串或字典
            if isinstance(author_data, dict):
                author = author_data.get('login', '') or author_data.get('name', '')
            else:
                author = str(author_data) if author_data else ''
            
            # 从讨论标题中提取用户名（假设格式为："用户名 - 日期" 或包含用户名）
            # 尝试从标题中提取用户名
            # 常见格式："张三 - 2024-01-15"、"张三的日报"、"张三 日报" 等
            import re
            
            # 匹配用户名模式
            patterns = [
                r'^([^\-\s]+)\s*[-\s]',  # "张三 - " 或 "张三 "
                r'^([^\s]+)的?日报',      # "张三日报" 或 "张三的日报"
                r'^([^\s]+)\s+\d{4}',    # "张三 2024"
                r'^([^\s]+)',           # 第一个词作为用户名
            ]
            
            username = None
            if title:
                for pattern in patterns:
                    match = re.match(pattern, title)
                    if match:
                        username = match.group(1).strip()
                        break
                    
            if not username:
                # 如果无法从标题提取，使用讨论作者信息
                username = author if author else 'unknown'
                
            # 生成用户ID（可以是GitHub用户名或其他唯一标识）
            user_id = author if author else username.lower()
            
            # 验证结果
            if not username or not user_id:
                self.logger.warning(f"无法提取有效的用户信息，标题: {title}, 作者: {author}")
                return None
            
            return {
                'user_id': user_id,
                'username': username
            }
            
        except Exception as e:
            self.logger.error(f"提取用户信息时出错: {str(e)}")
            self.logger.error(f"讨论数据类型: {type(discussion)}")
            if hasattr(discussion, '__dict__'):
                self.logger.error(f"讨论数据内容: {discussion.__dict__}")
            return None
            
    async def _analyze_user_reports(self, daily_reports: List[DailyReportData]) -> List[UserDailySummary]:
        """
        分析用户日报数据
        
        Args:
            daily_reports: 日报数据列表
            
        Returns:
            List[UserDailySummary]: 用户日报汇总列表
        """
        self.logger.info(f"开始分析 {len(daily_reports)} 份用户日报")
        
        user_summaries = []
        
        # 并行分析所有用户日报
        analysis_tasks = []
        for report in daily_reports:
            task = self._analyze_single_user_report(report)
            analysis_tasks.append(task)
            
        # 执行所有分析任务
        results = await asyncio.gather(*analysis_tasks, return_exceptions=True)
        
        # 处理结果
        for i, result in enumerate(results):
            if isinstance(result, Exception):
                self.logger.error(f"分析用户 {daily_reports[i].username} 的日报失败: {str(result)}")
            elif result:
                user_summaries.append(result)
                
        self.logger.info(f"成功分析 {len(user_summaries)} 份用户日报")
        return user_summaries
        
    async def _analyze_single_user_report(self, report: DailyReportData) -> Optional[UserDailySummary]:
        """
        分析单个用户的日报
        
        Args:
            report: 日报数据
            
        Returns:
            Optional[UserDailySummary]: 用户日报汇总
        """
        try:
            self.logger.debug(f"开始分析用户 {report.username} 的日报")
            
            # 使用GLM进行偏离度和完成度分析
            analysis_result = await self.enhanced_glm_client.analyze_daily_report_with_plan(
                daily_summary=report.report_content,
                daily_plan=report.plan_content
            )
            
            if not analysis_result:
                self.logger.warning(f"用户 {report.username} 的日报分析失败")
                return None
                
            # 提取分析结果
            deviation_score = analysis_result.get('deviation_score', 0.0)
            completion_rate = analysis_result.get('completion_rate', 0.0)
            analysis_summary = analysis_result.get('summary', '')
            
            # 生成GLM洞察
            glm_insights = await self._generate_user_insights(
                report, deviation_score, completion_rate, analysis_summary
            )
            
            return UserDailySummary(
                user_id=report.user_id,
                username=report.username,
                date=report.date,
                plan_content=report.plan_content,
                report_content=report.report_content,
                deviation_score=deviation_score,
                completion_rate=completion_rate,
                analysis_summary=analysis_summary,
                glm_insights=glm_insights
            )
            
        except Exception as e:
            self.logger.error(f"分析用户 {report.username} 的日报时出错: {str(e)}")
            return None
            
    async def _generate_user_insights(self, report: DailyReportData, 
                                     deviation_score: float, completion_rate: float,
                                     analysis_summary: str) -> str:
        """
        生成用户洞察
        
        Args:
            report: 日报数据
            deviation_score: 偏离度分数
            completion_rate: 完成率
            analysis_summary: 分析摘要
            
        Returns:
            str: 用户洞察
        """
        try:
            prompt = f"""
请基于以下用户日报数据生成简洁的洞察分析：

用户：{report.username}
日期：{report.date}
偏离度：{deviation_score}
完成率：{completion_rate}

日计划：
{report.plan_content}

日报：
{report.report_content}

分析摘要：
{analysis_summary}

请生成一段简洁的洞察，包括：
1. 工作表现评价
2. 主要亮点或问题
3. 改进建议（如有必要）

要求：
- 控制在100字以内
- 语言简洁专业
- 突出关键信息
"""
            
            insights = await self.glm_client.generate_text(prompt)
            return insights if insights else "暂无特殊洞察"
            
        except Exception as e:
            self.logger.error(f"生成用户洞察时出错: {str(e)}")
            return "洞察生成失败"
            
    async def _generate_team_summary_report(self, target_date: date, 
                                          daily_reports: List[DailyReportData],
                                          user_summaries: List[UserDailySummary]) -> Optional[TeamDailySummaryReport]:
        """
        生成团队汇总报告
        
        Args:
            target_date: 目标日期
            daily_reports: 日报数据列表
            user_summaries: 用户汇总列表
            
        Returns:
            Optional[TeamDailySummaryReport]: 团队汇总报告
        """
        try:
            self.logger.info(f"开始生成 {target_date} 的团队汇总报告")
            
            # 计算统计数据
            total_users = len(set(report.user_id for report in daily_reports))
            submitted_reports = len(daily_reports)
            submission_rate = submitted_reports / total_users if total_users > 0 else 0.0
            
            # 计算平均分数
            if user_summaries:
                avg_deviation = sum(s.deviation_score for s in user_summaries) / len(user_summaries)
                avg_completion = sum(s.completion_rate for s in user_summaries) / len(user_summaries)
            else:
                avg_deviation = 0.0
                avg_completion = 0.0
                
            # 生成团队洞察
            team_insights = await self._generate_team_insights(target_date)
            
            # 生成改进建议
            recommendations = await self._generate_team_recommendations(
                user_summaries, avg_deviation, avg_completion, submission_rate
            )
            
            return TeamDailySummaryReport(
                date=target_date.isoformat(),
                total_users=total_users,
                submitted_reports=submitted_reports,
                submission_rate=submission_rate,
                average_deviation_score=avg_deviation,
                average_completion_rate=avg_completion,
                user_summaries=user_summaries,
                team_insights=team_insights,
                recommendations=recommendations
            )
            
        except Exception as e:
            self.logger.error(f"生成团队汇总报告时出错: {str(e)}")
            return None
            
    async def _generate_team_insights(self, target_date: date) -> str:
        """
        生成团队洞察
        
        Args:
            target_date: 目标日期
            
        Returns:
            str: 团队洞察
        """
        try:
            # 获取配置中的提示词
            team_insights_prompt = self.config.daily_summary_analysis.glm_enhancement.team_insights_prompt
            
            # 重新收集原始日报数据
            daily_reports = await self._collect_daily_reports(target_date)
            
            if not daily_reports:
                return "暂无日报数据可供分析"
            
            # 构建原始日报内容
            original_reports_data = f"日报汇总（{target_date}）\n\n"
            
            for report in daily_reports:
                original_reports_data += f"**{report.user_id}**\n"
                
                if report.plan_content and report.plan_content.strip():
                    original_reports_data += f"日计划：\n{report.plan_content}\n\n"
                
                if report.report_content and report.report_content.strip():
                    original_reports_data += f"日报：\n{report.report_content}\n\n"
                
                original_reports_data += "---\n\n"
            
            # 使用配置中的提示词和原始数据
            full_prompt = f"{team_insights_prompt}\n\n{original_reports_data}"
            
            insights = await self.glm_client.generate_text(full_prompt)
            return insights if insights else "团队整体表现正常，无特殊异常。"
            
        except Exception as e:
            self.logger.error(f"生成团队洞察时出错: {str(e)}")
            return "团队洞察生成失败"
            
    async def _generate_team_recommendations(self, user_summaries: List[UserDailySummary],
                                           avg_deviation: float, avg_completion: float,
                                           submission_rate: float) -> List[str]:
        """
        生成团队改进建议
        
        Args:
            user_summaries: 用户汇总列表
            avg_deviation: 平均偏离度
            avg_completion: 平均完成率
            submission_rate: 提交率
            
        Returns:
            List[str]: 改进建议列表
        """
        recommendations = []
        
        try:
            # 基于数据生成建议
            if submission_rate < 0.8:
                recommendations.append(f"日报提交率偏低({submission_rate:.1%})，建议加强日报提交管理")
                
            if avg_deviation > 0.7:
                recommendations.append(f"团队平均偏离度较高({avg_deviation:.2f})，建议优化计划制定和执行")
                
            if avg_completion < 0.6:
                recommendations.append(f"团队平均完成率偏低({avg_completion:.1%})，建议评估任务难度和资源配置")
                
            # 识别需要关注的个人
            high_deviation_users = [s for s in user_summaries if s.deviation_score > 0.8]
            if high_deviation_users:
                usernames = [s.username for s in high_deviation_users[:3]]
                recommendations.append(f"关注高偏离度用户：{', '.join(usernames)} 等")
                
            low_completion_users = [s for s in user_summaries if s.completion_rate < 0.4]
            if low_completion_users:
                usernames = [s.username for s in low_completion_users[:3]]
                recommendations.append(f"关注低完成率用户：{', '.join(usernames)} 等")
                
            # 如果没有明显问题，给出积极建议
            if not recommendations:
                recommendations.append("团队整体表现良好，建议保持当前工作节奏")
                
        except Exception as e:
            self.logger.error(f"生成团队建议时出错: {str(e)}")
            recommendations.append("建议生成失败，请人工分析")
            
        return recommendations
        
    def _should_send_notification(self) -> bool:
        """
        判断是否应该发送通知
        
        Returns:
            bool: 是否发送通知
        """
        # 检查配置中的通知设置
        if not hasattr(self.config, 'daily_summary_analysis'):
            return False
            
        daily_config = self.config.daily_summary_analysis
        notification_config = daily_config.get('notification', {})
        
        return notification_config.get('enabled', False)
        
    async def _send_summary_notification(self, report: TeamDailySummaryReport) -> bool:
        """
        发送汇总报告通知
        
        Args:
            report: 团队汇总报告
            
        Returns:
            bool: 发送是否成功
        """
        try:
            if not self.feishu_client:
                self.logger.warning("飞书客户端未初始化，无法发送通知")
                return False
                
            # 构建通知消息
            message = self._format_summary_message(report)
            
            # 获取接收者列表
            recipients = self._get_notification_recipients()
            
            if not recipients:
                self.logger.warning("没有配置通知接收者")
                return False
                
            # 发送通知
            success_count = 0
            for recipient in recipients:
                try:
                    success = await self.feishu_client.send_private_message(
                        user_id=recipient,
                        message=message
                    )
                    if success:
                        success_count += 1
                        self.logger.info(f"成功发送汇总报告给 {recipient}")
                    else:
                        self.logger.error(f"发送汇总报告给 {recipient} 失败")
                except Exception as e:
                    self.logger.error(f"发送汇总报告给 {recipient} 时出错: {str(e)}")
                    
            return success_count > 0
            
        except Exception as e:
            self.logger.error(f"发送汇总报告通知时出错: {str(e)}")
            return False
            
    def _format_summary_message(self, report: TeamDailySummaryReport) -> str:
        """
        格式化汇总报告消息
        
        Args:
            report: 团队汇总报告
            
        Returns:
            str: 格式化的消息
        """
        # 只返回LLM生成的团队洞察内容，不拼接其他数据
        return report.team_insights
        
    def _get_notification_recipients(self) -> List[str]:
        """
        获取通知接收者列表
        
        Returns:
            List[str]: 接收者用户ID列表
        """
        try:
            if not hasattr(self.config, 'daily_summary_analysis'):
                return []
                
            daily_config = self.config.daily_summary_analysis
            notification_config = daily_config.notification
            
            # 直接从notification配置中获取recipients
            recipients = notification_config.recipients if hasattr(notification_config, 'recipients') else []
            
            if not recipients:
                self.logger.warning("日报汇总通知接收者列表为空，请检查配置文件中的daily_summary_analysis.notification.recipients")
            
            return recipients
            
        except Exception as e:
            self.logger.error(f"获取通知接收者时出错: {str(e)}")
            return []
            
    async def _save_summary_report(self, report: TeamDailySummaryReport) -> bool:
        """
        保存汇总报告数据
        
        Args:
            report: 团队汇总报告
            
        Returns:
            bool: 保存是否成功
        """
        try:
            # 保存到数据管理器
            report_data = report.to_dict()
            filename = f"daily_summary_{report.date}.json"
            
            success = await self.data_manager.save_data(
                filename, report_data, 'daily_summaries'
            )
            
            if success:
                self.logger.info(f"汇总报告已保存: {filename}")
            else:
                self.logger.error(f"保存汇总报告失败: {filename}")
                
            return success
            
        except Exception as e:
            self.logger.error(f"保存汇总报告时出错: {str(e)}")
            return False