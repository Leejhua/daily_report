"""
日结分析器模块
负责执行每日分析任务的核心逻辑
"""

import logging
import asyncio
from datetime import date, datetime
from typing import List, Dict, Any, Optional

from src.config import Config
from src.clients.github_client import GitHubClient, DiscussionData
from src.clients.glm_client import GLMClient
from src.clients.enhanced_glm_client import EnhancedGLMClient
from src.trackers.deviation_tracker import DeviationTracker
from src.models.data_models import DeviationAnalysisResult
from src.utils.logger import get_logger


class DailyAnalyzer:
    """日结分析器"""
    
    def __init__(self, config: Config):
        self.config = config
        self.logger = get_logger(__name__)
        
        # 初始化客户端
        self.github_client = GitHubClient(config.github)
        self.glm_client = GLMClient(config.glm)
        self.enhanced_glm_client = EnhancedGLMClient(config.glm)
        
        # 初始化数据管理器和偏离跟踪器
        from ..storage.json_data_manager import JSONDataManager
        self.data_manager = JSONDataManager(data_dir='data')
        self.deviation_tracker = DeviationTracker(self.data_manager, {})
        
    async def run_daily_analysis(self, target_date: Optional[date] = None) -> Dict[str, Any]:
        """
        运行每日分析任务
        
        Args:
            target_date: 目标分析日期，默认为今天
            
        Returns:
            Dict[str, Any]: 分析结果摘要
        """
        if target_date is None:
            target_date = date.today()
            
        self.logger.info(f"开始执行 {target_date} 的日结分析任务")
        
        analysis_summary = {
            'date': target_date.isoformat(),
            'start_time': datetime.now().isoformat(),
            'discussions_analyzed': 0,
            'comments_posted': 0,
            'errors': [],
            'success': False
        }
        
        try:
            # 1. 获取当日的"日结"讨论
            discussions = await self.github_client.get_daily_discussions(target_date)
            
            if not discussions:
                self.logger.info(f"{target_date} 没有找到需要分析的讨论")
                analysis_summary['success'] = True
                return analysis_summary
                
            self.logger.info(f"找到 {len(discussions)} 个需要分析的讨论")
            
            # 2. 并行分析所有讨论
            analysis_tasks = []
            for discussion in discussions:
                task = self._analyze_single_discussion(discussion)
                analysis_tasks.append(task)
                
            # 执行所有分析任务
            results = await asyncio.gather(*analysis_tasks, return_exceptions=True)
            
            # 3. 统计结果
            successful_analyses = 0
            total_comments_posted = 0
            
            for i, result in enumerate(results):
                if isinstance(result, Exception):
                    error_msg = f"讨论 #{discussions[i].number} 分析失败: {str(result)}"
                    self.logger.error(error_msg)
                    analysis_summary['errors'].append(error_msg)
                elif isinstance(result, dict):
                    if result.get('success', False):
                        successful_analyses += 1
                        # 统计成功发布的评论数
                        analyses = result.get('analyses', [])
                        successful_comments = sum(1 for analysis in analyses if analysis.get('success', False))
                        total_comments_posted += successful_comments
                    else:
                        analysis_summary['errors'].append(result.get('error', '未知错误'))
                        
            analysis_summary.update({
                'discussions_analyzed': successful_analyses,
                'comments_posted': total_comments_posted,
                'success': successful_analyses > 0,
                'end_time': datetime.now().isoformat()
            })
            
            self.logger.info(f"分析任务完成: {successful_analyses}/{len(discussions)} 个讨论分析成功，{total_comments_posted} 条评论已发布")
            
        except Exception as e:
            error_msg = f"分析任务执行失败: {str(e)}"
            self.logger.error(error_msg, exc_info=True)
            analysis_summary['errors'].append(error_msg)
            analysis_summary['end_time'] = datetime.now().isoformat()
            
        return analysis_summary
        
    async def _analyze_single_discussion(self, discussion: DiscussionData) -> Dict[str, Any]:
        """
        分析单个讨论
        
        Args:
            discussion: 讨论数据
            
        Returns:
            Dict[str, Any]: 分析结果
        """
        self.logger.info(f"开始分析讨论 #{discussion.number}: {discussion.title}")
        
        result = {
            'discussion_number': discussion.number,
            'discussion_title': discussion.title,
            'success': False,
            'comment_posted': False,
            'error': None
        }
        
        try:
            # 1. 提取日结和计划内容
            content_data = await self.github_client.extract_daily_content(discussion)
            
            daily_summary = content_data.get('daily_summary', '')
            daily_plan = content_data.get('daily_plan', '')
            
            if not daily_summary and not daily_plan:
                result.update({
                    'success': True,
                    'analyses': [],
                    'successful_count': 0,
                    'failed_count': 0,
                    'note': '没有日结或计划内容，跳过分析'
                })
                self.logger.info(f"讨论 #{discussion.number} 没有日结或计划内容，跳过分析")
                return result
                
            self.logger.debug(f"提取内容完成 - 日结: {len(daily_summary)} 字符, 计划: {len(daily_plan)} 字符")
            
            # 2. 周期计划已在extract_daily_content中提取（首楼内容）
            weekly_plan = content_data.get('weekly_plan', '')
            
            # 3. 根据提取到的内容分别执行相应的分析并发布到对应讨论
            analysis_results = []
            
            # 如果有日报内容，执行日报分析并发布到当前讨论（日报讨论）
            if daily_summary and daily_summary.strip():
                # 进一步验证是否真的是日报内容
                content_type = self.github_client.identify_content_type(daily_summary)
                if content_type == 'daily_report':
                    self.logger.debug("执行日报内容分析")
                    try:
                        # 为日报分析找到对应的当天计划，而不是使用最新计划
                        corresponding_plan, corresponding_plan_comment_id = await self._find_corresponding_daily_plan(
                            discussion, daily_summary
                        )
                        
                        # 执行传统日报分析
                        daily_report_analysis = await self.glm_client.analyze_daily_report_content(
                            daily_summary=daily_summary,
                            daily_plan=corresponding_plan
                        )
                        
                        # 执行偏离分析
                        deviation_result = await self._perform_deviation_analysis(
                            discussion.number, daily_summary, daily_plan, weekly_plan
                        )
                        
                        if daily_report_analysis and not daily_report_analysis.startswith("## ❌"):
                            # 查找日报评论ID
                            daily_summary_comment_id = await self._find_content_comment_id(
                                discussion.number, 'daily_summary'
                            )
                            
                            # 发布日报分析到当前讨论，回复到日报评论楼层
                            comment_success = await self.github_client.post_analysis_comment(
                                discussion.number, 
                                daily_report_analysis,
                                reply_to_comment_id=daily_summary_comment_id,
                                content_type='daily_report'
                            )
                            analysis_results.append({
                                'type': '日报分析',
                                'success': comment_success,
                                'discussion_number': discussion.number,
                                'length': len(daily_report_analysis),
                                'reply_to_comment_id': daily_summary_comment_id,
                                'deviation_analysis': deviation_result
                            })
                            if daily_summary_comment_id:
                                self.logger.info(f"日报分析完成并回复到日报评论楼层 #{discussion.number}: {'成功' if comment_success else '失败'}")
                            else:
                                self.logger.info(f"日报分析完成并发布到讨论 #{discussion.number}: {'成功' if comment_success else '失败'}")
                                
                            # 记录偏离分析结果
                            if deviation_result and deviation_result.get('success'):
                                deviation_score = deviation_result.get('deviation_score', 'N/A')
                                self.logger.info(f"偏离分析完成 #{discussion.number}: 偏离度 {deviation_score}")
                    except Exception as e:
                        self.logger.error(f"日报分析失败: {e}")
                        analysis_results.append({
                            'type': '日报分析',
                            'success': False,
                            'error': str(e)
                        })
                else:
                    self.logger.info(f"提取的内容不是日报类型（识别为: {content_type}），跳过日报分析")
            
            # 如果有日计划内容，需要找到对应的周计划讨论并发布日计划分析
            if daily_plan and daily_plan.strip():
                # 进一步验证是否真的是日计划内容
                content_type = self.github_client.identify_content_type(daily_plan)
                if content_type == 'daily_plan':
                    self.logger.debug("执行日计划内容分析")
                    try:
                        daily_plan_analysis = await self.glm_client.analyze_daily_plan_content(
                            daily_plan=daily_plan,
                            weekly_plan=weekly_plan
                        )
                        if daily_plan_analysis and not daily_plan_analysis.startswith("## ❌"):
                            # 如果有对应的日计划评论ID，使用它；否则查找最新的日计划评论ID
                            if 'corresponding_plan_comment_id' in locals() and corresponding_plan_comment_id:
                                daily_plan_comment_id = corresponding_plan_comment_id
                                self.logger.info(f"使用对应的日计划评论ID: {daily_plan_comment_id}")
                            else:
                                daily_plan_comment_id = await self._find_content_comment_id(
                                    discussion.number, 'daily_plan'
                                )
                                self.logger.info(f"使用最新的日计划评论ID: {daily_plan_comment_id}")
                            
                            comment_success = await self.github_client.post_analysis_comment(
                                discussion.number, 
                                daily_plan_analysis,
                                reply_to_comment_id=daily_plan_comment_id,
                                content_type='daily_plan'
                            )
                            analysis_results.append({
                                'type': '日计划分析',
                                'success': comment_success,
                                'discussion_number': discussion.number,
                                'length': len(daily_plan_analysis),
                                'reply_to_comment_id': daily_plan_comment_id
                            })
                            if daily_plan_comment_id:
                                self.logger.info(f"日计划分析完成并回复到日计划评论楼层 #{discussion.number}: {'成功' if comment_success else '失败'}")
                            else:
                                self.logger.info(f"日计划分析完成并发布到讨论 #{discussion.number}: {'成功' if comment_success else '失败'}")
                    except Exception as e:
                        self.logger.error(f"日计划分析失败: {e}")
                        analysis_results.append({
                            'type': '日计划分析',
                            'success': False,
                            'error': str(e)
                        })
                else:
                    self.logger.info(f"提取的内容不是日计划类型（识别为: {content_type}），跳过日计划分析")
            
            # 如果日计划分析失败或没有找到合适的发布位置，记录详细信息
            if daily_plan and not any(r.get('type') == '日计划分析' and r.get('success', False) for r in analysis_results):
                self.logger.warning(f"日计划分析未能成功发布到合适位置，讨论 #{discussion.number}")
                # 可以考虑发送通知或记录到特定位置
                analysis_results.append({
                    'type': '日计划分析状态',
                    'success': False,
                    'note': '日计划内容存在但未能找到合适的发布位置',
                    'discussion_number': discussion.number
                })
            
            # 统计分析结果
            successful_analyses = [r for r in analysis_results if r.get('success', False)]
            failed_analyses = [r for r in analysis_results if not r.get('success', False)]
            
            if successful_analyses:
                result.update({
                    'success': True,
                    'analyses': analysis_results,
                    'successful_count': len(successful_analyses),
                    'failed_count': len(failed_analyses)
                })
                analysis_types = [r['type'] for r in successful_analyses]
                self.logger.info(f"完成分析类型: {', '.join(analysis_types)}")
            else:
                result['error'] = '所有分析都失败了'
                result['analyses'] = analysis_results
                
            # 更新日志信息
            if successful_analyses:
                success_info = ', '.join([f"{r['type']}(#{r['discussion_number']})" for r in successful_analyses])
                self.logger.info(f"讨论 #{discussion.number} 分析完成: {success_info}")
            else:
                self.logger.warning(f"讨论 #{discussion.number} 所有分析都失败了")

        except Exception as e:
            error_msg = f"分析讨论 #{discussion.number} 时出错: {str(e)}"
            self.logger.error(error_msg, exc_info=True)
            result['error'] = error_msg
            
        return result
        
    async def _find_content_comment_id(self, discussion_number: int, content_type: str) -> Optional[str]:
        """
        在讨论中查找特定类型内容的评论ID
        使用与extract_daily_content相同的逻辑，确保找到最新的匹配内容
        
        Args:
            discussion_number: 讨论编号
            content_type: 内容类型 ('daily_summary' 或 'daily_plan')
            
        Returns:
            Optional[str]: 评论ID，如果未找到则返回None
        """
        try:
            # 获取评论
            comments = await self.github_client.get_discussion_comments(discussion_number)
            
            if not comments:
                self.logger.warning(f"讨论#{discussion_number}没有评论")
                return None
            
            # 按时间排序评论，最新的在前（与extract_daily_content保持一致）
            comments.sort(key=lambda x: x.updated_at, reverse=True)
            
            # 跳过分析评论（与extract_daily_content使用相同的标记）
            analysis_markers = [
                '📋 日报分析', '📋 日计划分析', '## 📋 日报分析', '## 📋 日计划分析',
                '日报分析', '日计划分析', '分析结果', '内容表述不清楚', '如何澄清这些不清楚的内容',
                '## 📊', '## ✅', '## ❌', 'AI分析'
            ]
            
            # 映射内容类型（与extract_daily_content保持一致）
            expected_type = {
                'daily_summary': 'daily_report',
                'daily_plan': 'daily_plan'
            }.get(content_type)
            
            if not expected_type:
                self.logger.warning(f"未知的内容类型: {content_type}")
                return None
            
            # 使用与extract_daily_content完全相同的逻辑
            for comment in comments:
                # 跳过分析评论
                if any(marker in comment.body for marker in analysis_markers):
                    self.logger.debug(f"跳过分析评论，评论ID: {comment.id}")
                    continue
                
                # 使用内容识别方法判断内容类型（与extract_daily_content保持一致）
                identified_type = self.github_client.identify_content_type(comment.body)
                
                # 如果找到匹配的内容类型，立即返回（与extract_daily_content保持一致）
                if identified_type == expected_type:
                    self.logger.info(f"通过内容识别找到{content_type}评论ID: {comment.id}")
                    return comment.id
                
                # 如果内容识别不确定，回退到关键词匹配（与extract_daily_content保持一致）
                if identified_type == 'unknown':
                    comment_content = comment.body.lower()
                    
                    if content_type == 'daily_summary':
                        # 识别日报关键词（与extract_daily_content保持一致）
                        daily_report_keywords = [
                            '日报', '日结', '今日完成', '今日工作', '工作总结', 
                            '完成情况', '今天完成', '今天做了', '进度', '遇到问题',
                            '今日进展', '工作内容'
                        ]
                        
                        if any(keyword in comment_content for keyword in daily_report_keywords):
                            self.logger.info(f"通过关键词找到日报评论ID: {comment.id}")
                            return comment.id
                    
                    elif content_type == 'daily_plan':
                        # 识别日计划关键词（与extract_daily_content保持一致）
                        daily_plan_keywords = [
                            '日计划', '明日计划', '明天计划', '下一步', '待办',
                            '明日安排', '明天安排', '计划完成', '准备'
                        ]
                        
                        if any(keyword in comment_content for keyword in daily_plan_keywords):
                            self.logger.info(f"通过关键词找到日计划评论ID: {comment.id}")
                            return comment.id
                    
                    # 如果是日报且评论内容较长且包含工作相关词汇（与extract_daily_content保持一致）
                    if content_type == 'daily_summary' and len(comment.body) > 50:
                        work_keywords = ['完成', '开发', '测试', '修复', '问题', '功能', '任务', '会议']
                        if sum(1 for keyword in work_keywords if keyword in comment_content) >= 2:
                            self.logger.info(f"根据内容特征识别为日报评论ID: {comment.id}")
                            return comment.id
            
            self.logger.warning(f"在讨论#{discussion_number}中未找到{content_type}类型的评论")
            return None
                    

            
        except Exception as e:
            self.logger.error(f"查找评论ID时出错: {e}")
            return None
    
    async def _find_corresponding_daily_plan(self, discussion: 'DiscussionData', daily_summary: str) -> tuple[str, Optional[str]]:
        """
        为日报分析找到对应的当天计划内容和评论ID
        优先使用最新的日计划评论，确保与extract_daily_content方法的逻辑一致
        
        Args:
            discussion: 讨论数据
            daily_summary: 日报内容
            
        Returns:
            tuple[str, Optional[str]]: (对应的日计划内容, 评论ID)，如果找不到则返回('', None)
        """
        try:
            # 直接使用extract_daily_content获取最新的日计划内容和ID
            content_data = await self.github_client.extract_daily_content(discussion)
            daily_plan = content_data.get('daily_plan', '')
            
            if daily_plan:
                # 获取最新的日计划评论ID
                daily_plan_comment_id = await self._find_content_comment_id(discussion.number, 'daily_plan')
                if daily_plan_comment_id:
                    self.logger.info(f"找到最新的日计划，评论ID: {daily_plan_comment_id}")
                    return daily_plan, daily_plan_comment_id
            
            self.logger.warning("未找到日计划内容")
            return '', None
            

            
        except Exception as e:
            self.logger.error(f"查找对应日计划时出错: {e}")
            return '', None
    
    async def _find_latest_daily_plan(self, discussion: 'DiscussionData') -> str:
        """
        查找最新的日计划内容作为备选
        
        Args:
            discussion: 讨论数据
            
        Returns:
            str: 最新的日计划内容，如果找不到则返回空字符串
        """
        try:
            content_data = await self.github_client.extract_daily_content(discussion)
            return content_data.get('daily_plan', '')
        except Exception as e:
            self.logger.error(f"查找最新日计划时出错: {e}")
            return ''
    
    async def _find_plan_discussion(self, daily_plan: str) -> Optional[int]:
        """
        查找包含日计划的讨论编号
        优先查找周计划讨论，然后查找包含相似日计划内容的讨论
        
        Args:
            daily_plan: 日计划内容
            
        Returns:
            Optional[int]: 讨论编号，如果找不到则返回None
        """
        try:
            # 获取最近的讨论列表
            discussions = await self.github_client.get_daily_discussions()
            
            # 按时间排序，最新的在前
            discussions.sort(key=lambda x: x.updated_at, reverse=True)
            
            # 第一步：优先查找周计划讨论（通常包含日计划）
            weekly_plan_discussions = []
            for discussion in discussions:
                title_lower = discussion.title.lower()
                # 检查是否为周计划讨论
                if any(keyword in title_lower for keyword in ['周计划', 'weekly', '本周', '这周']):
                    weekly_plan_discussions.append(discussion)
                    self.logger.debug(f"发现周计划讨论 #{discussion.number}: {discussion.title}")
            
            # 在周计划讨论中查找包含日计划的评论
            for discussion in weekly_plan_discussions:
                try:
                    comments = await self.github_client.get_discussion_comments(discussion.number)
                    
                    # 检查评论中是否包含相似的日计划内容
                    for comment in comments:
                        if self._is_similar_plan_content(daily_plan, comment.body):
                            self.logger.info(f"在周计划讨论中找到匹配的日计划 #{discussion.number}: {discussion.title}")
                            return discussion.number
                        
                        # 检查评论是否包含日计划特征
                        comment_lower = comment.body.lower()
                        plan_indicators = ['日计划', '明日计划', '明天计划', '下一步', '待办', '明日安排']
                        if any(indicator in comment_lower for indicator in plan_indicators):
                            # 进一步检查内容相似性
                            if self._is_similar_plan_content(daily_plan, comment.body):
                                self.logger.info(f"基于日计划特征找到匹配讨论 #{discussion.number}: {discussion.title}")
                                return discussion.number
                except Exception as e:
                    self.logger.warning(f"检查周计划讨论 #{discussion.number} 时出错: {e}")
                    continue
            
            # 第二步：如果在周计划讨论中未找到，查找其他包含计划关键词的讨论
            plan_discussions = []
            for discussion in discussions:
                title_lower = discussion.title.lower()
                # 检查是否包含计划相关关键词（但不是周计划）
                if any(keyword in title_lower for keyword in ['计划', 'plan']) and not any(keyword in title_lower for keyword in ['周计划', 'weekly', '本周', '这周']):
                    plan_discussions.append(discussion)
            
            # 在计划讨论中查找匹配内容
            for discussion in plan_discussions:
                try:
                    comments = await self.github_client.get_discussion_comments(discussion.number)
                    
                    for comment in comments:
                        if self._is_similar_plan_content(daily_plan, comment.body):
                            self.logger.info(f"在计划讨论中找到匹配的日计划 #{discussion.number}: {discussion.title}")
                            return discussion.number
                except Exception as e:
                    self.logger.warning(f"检查计划讨论 #{discussion.number} 时出错: {e}")
                    continue
            
            # 第三步：最后兜底，在所有讨论中查找包含相似日计划内容的讨论
            self.logger.debug("在专门的计划讨论中未找到匹配，开始全局搜索")
            for discussion in discussions[:10]:  # 限制搜索最近10个讨论，避免性能问题
                try:
                    comments = await self.github_client.get_discussion_comments(discussion.number)
                    
                    for comment in comments:
                        # 使用更严格的相似性检查
                        if self._is_similar_plan_content(daily_plan, comment.body):
                            self.logger.info(f"全局搜索找到包含日计划的讨论 #{discussion.number}: {discussion.title}")
                            return discussion.number
                except Exception as e:
                    self.logger.warning(f"全局搜索讨论 #{discussion.number} 时出错: {e}")
                    continue
            
            self.logger.warning("未找到包含日计划的讨论")
            return None
            
        except Exception as e:
            self.logger.error(f"查找日计划讨论时出错: {e}")
            return None
    
    def _is_similar_plan_content(self, plan1: str, plan2: str) -> bool:
        """
        判断两个计划内容是否相似
        
        Args:
            plan1: 第一个计划内容
            plan2: 第二个计划内容
            
        Returns:
            bool: 是否相似
        """
        if not plan1 or not plan2:
            return False
            
        # 提取关键词进行匹配
        plan1_words = set(plan1.replace('\n', ' ').split())
        plan2_words = set(plan2.replace('\n', ' ').split())
        
        # 计算交集比例
        if len(plan1_words) == 0 or len(plan2_words) == 0:
            return False
            
        intersection = plan1_words.intersection(plan2_words)
        similarity = len(intersection) / min(len(plan1_words), len(plan2_words))
        
        # 如果相似度超过30%，认为是相似内容
        return similarity > 0.3
    
    async def _perform_deviation_analysis(self, discussion_number: int, daily_summary: str, 
                                        daily_plan: str, weekly_plan: str) -> Dict[str, Any]:
        """
        执行偏离分析
        
        Args:
            discussion_number: 讨论编号
            daily_summary: 日报内容
            daily_plan: 日计划内容
            weekly_plan: 周计划内容
            
        Returns:
            Dict[str, Any]: 偏离分析结果
        """
        try:
            self.logger.debug(f"开始执行偏离分析 #{discussion_number}")
            
            # 获取用户ID（从讨论作者获取）
            discussions = await self.github_client.get_daily_discussions()
            user_id = None
            for disc in discussions:
                if disc.number == discussion_number:
                    user_id = disc.author
                    break
            
            if not user_id:
                self.logger.warning(f"无法获取讨论 #{discussion_number} 的作者信息")
                return {'success': False, 'error': '无法获取用户信息'}
            
            # 使用增强版GLM客户端进行偏离分析
            deviation_analysis_result = await self.enhanced_glm_client.analyze_deviation_with_structured_output(
                daily_summary=daily_summary,
                daily_plan=daily_plan,
                user_id=user_id,
                weekly_plan=weekly_plan,
                discussion_number=discussion_number
            )
            
            if not deviation_analysis_result:
                self.logger.warning(f"偏离分析返回空结果 #{discussion_number}")
                return {'success': False, 'error': '偏离分析返回空结果'}
            
            # 从structured_data中创建DeviationAnalysisResult对象
            if hasattr(deviation_analysis_result, 'structured_data') and deviation_analysis_result.structured_data:
                from ..models.data_models import DeviationAnalysisResult
                
                # 创建DeviationAnalysisResult对象用于记录
                deviation_result_obj = DeviationAnalysisResult(
                    user_id=user_id,
                    analysis_date=date.today().strftime('%Y-%m-%d'),
                    discussion_number=discussion_number,
                    score=deviation_analysis_result.structured_data.get('score', 0.0),
                    completion_rate=deviation_analysis_result.structured_data.get('completion_rate', 0.0),
                    deviation_reasons=deviation_analysis_result.structured_data.get('deviation_reasons', []),
                    additional_work=deviation_analysis_result.structured_data.get('additional_work', []),
                    suggestions=deviation_analysis_result.structured_data.get('suggestions', []),
                    summary=deviation_analysis_result.structured_data.get('summary', ''),
                    confidence=deviation_analysis_result.structured_data.get('confidence', 0.0),
                    is_deviation=deviation_analysis_result.structured_data.get('is_deviation', False)
                )
                
                # 记录分析结果到偏离跟踪器
                self.deviation_tracker.record_analysis_result(deviation_result_obj)
            
            # 检查连续偏离
            continuous_deviation = self.deviation_tracker.check_continuous_deviation(
                user_id, date.today().strftime('%Y-%m-%d')
            )
            
            # 从structured_data中获取偏离分析数据
            structured_data = deviation_analysis_result.structured_data if hasattr(deviation_analysis_result, 'structured_data') else {}
            
            result = {
                'success': True,
                'user_id': user_id,
                'deviation_score': structured_data.get('score', 0.0),
                'completion_rate': structured_data.get('completion_rate', 0.0),
                'is_deviation': structured_data.get('is_deviation', False),
                'deviation_reasons': structured_data.get('deviation_reasons', []),
                'continuous_deviation': continuous_deviation
            }
            
            # 如果存在连续偏离，记录预警
            if continuous_deviation and continuous_deviation.get('has_continuous_deviation', False):
                self.deviation_tracker.record_continuous_deviation_alert(
                    user_id, date.today().strftime('%Y-%m-%d'), continuous_deviation
                )
                self.logger.warning(f"用户 {user_id} 存在连续偏离: {continuous_deviation.get('consecutive_days', 0)} 天")
            
            return result
            
        except Exception as e:
            self.logger.error(f"偏离分析失败 #{discussion_number}: {e}", exc_info=True)
            return {
                'success': False,
                'error': str(e)
            }
    
    async def get_deviation_summary(self, user_id: Optional[str] = None, days: int = 7) -> Dict[str, Any]:
        """
        获取偏离分析摘要
        
        Args:
            user_id: 用户ID，如果为None则获取所有用户
            days: 查询天数
            
        Returns:
            Dict[str, Any]: 偏离摘要
        """
        try:
            if user_id:
                # 获取特定用户的偏离摘要
                user_summary = self.deviation_tracker.get_user_deviation_summary(user_id, days)
                return {
                    'success': True,
                    'user_id': user_id,
                    'summary': user_summary
                }
            else:
                # 获取所有存在连续偏离的用户
                continuous_deviation_users = self.deviation_tracker.get_users_with_continuous_deviation()
                return {
                    'success': True,
                    'continuous_deviation_users': continuous_deviation_users
                }
                
        except Exception as e:
            self.logger.error(f"获取偏离摘要失败: {e}", exc_info=True)
            return {
                'success': False,
                'error': str(e)
            }
        
    async def analyze_specific_discussion(self, discussion_number: int) -> Dict[str, Any]:
        """
        分析指定的讨论（用于测试或手动触发）
        
        Args:
            discussion_number: 讨论编号
            
        Returns:
            Dict[str, Any]: 分析结果
        """
        self.logger.info(f"开始分析指定讨论 #{discussion_number}")
        
        try:
            # 获取讨论数据
            discussions = await self.github_client.get_daily_discussions()
            target_discussion = None
            
            for discussion in discussions:
                if discussion.number == discussion_number:
                    target_discussion = discussion
                    break
                    
            if not target_discussion:
                return {
                    'success': False,
                    'error': f'未找到讨论 #{discussion_number} 或该讨论不在"日结"分类中'
                }
                
            # 执行分析
            result = await self._analyze_single_discussion(target_discussion)
            return result
            
        except Exception as e:
            error_msg = f"分析指定讨论失败: {str(e)}"
            self.logger.error(error_msg, exc_info=True)
            return {
                'success': False,
                'error': error_msg
            }
            
    async def test_connections(self) -> Dict[str, bool]:
        """
        测试所有外部连接
        
        Returns:
            Dict[str, bool]: 连接测试结果
        """
        self.logger.info("开始测试外部连接...")
        
        # 并行测试所有连接
        github_task = self.github_client.test_connection()
        glm_task = self.glm_client.test_connection()
        
        github_ok, glm_ok = await asyncio.gather(
            github_task, glm_task, return_exceptions=True
        )
        
        # 处理异常结果
        if isinstance(github_ok, Exception):
            self.logger.error(f"GitHub连接测试异常: {github_ok}")
            github_ok = False
            
        if isinstance(glm_ok, Exception):
            self.logger.error(f"GLM连接测试异常: {glm_ok}")
            glm_ok = False
            
        results = {
            'github': bool(github_ok),
            'glm': bool(glm_ok),
            'overall': bool(github_ok) and bool(glm_ok)
        }
        
        self.logger.info(f"连接测试结果: {results}")
        return results
        
    async def get_analysis_preview(self, discussion_number: int) -> Dict[str, Any]:
        """
        获取分析预览（不发布评论）
        
        Args:
            discussion_number: 讨论编号
            
        Returns:
            Dict[str, Any]: 分析预览结果
        """
        self.logger.info(f"生成讨论 #{discussion_number} 的分析预览")
        
        try:
            # 获取讨论数据
            discussions = await self.github_client.get_daily_discussions()
            target_discussion = None
            
            for discussion in discussions:
                if discussion.number == discussion_number:
                    target_discussion = discussion
                    break
                    
            if not target_discussion:
                return {
                    'success': False,
                    'error': f'未找到讨论 #{discussion_number}'
                }
                
            # 提取内容
            content_data = await self.github_client.extract_daily_content(target_discussion)
            daily_summary = content_data.get('daily_summary', '')
            daily_plan = content_data.get('daily_plan', '')
            
            # 获取周期计划
            weekly_plan = await self.github_client.get_thread_first_post(discussion_number) or ""
            
            # 生成分析报告（但不发布）
            analysis_parts = []
            
            if daily_summary:
                daily_report_analysis = await self.glm_client.analyze_daily_report_content(
                    daily_summary=daily_summary,
                    daily_plan=daily_plan
                )
                if daily_report_analysis:
                    analysis_parts.append(daily_report_analysis)
            
            if daily_plan:
                daily_plan_analysis = await self.glm_client.analyze_daily_plan_content(
                    daily_plan=daily_plan,
                    weekly_plan=weekly_plan
                )
                if daily_plan_analysis:
                    analysis_parts.append(daily_plan_analysis)
            
            analysis_report = "\n\n---\n\n".join(analysis_parts) if analysis_parts else "暂无分析内容"
            
            return {
                'success': True,
                'discussion_title': target_discussion.title,
                'daily_summary': daily_summary,
                'daily_plan': daily_plan,
                'weekly_plan': weekly_plan[:500] + '...' if len(weekly_plan) > 500 else weekly_plan,
                'analysis_report': analysis_report,
                'report_length': len(analysis_report)
            }
            
        except Exception as e:
            error_msg = f"生成分析预览失败: {str(e)}"
            self.logger.error(error_msg, exc_info=True)
            return {
                'success': False,
                'error': error_msg
            }
