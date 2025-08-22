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
from src.utils.logger import get_logger


class DailyAnalyzer:
    """日结分析器"""
    
    def __init__(self, config: Config):
        self.config = config
        self.logger = get_logger(__name__)
        
        # 初始化客户端
        self.github_client = GitHubClient(config.github)
        self.glm_client = GLMClient(config.glm)
        
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
            already_replied_count = 0
            discussion_details = []
            
            for i, result in enumerate(results):
                discussion = discussions[i]
                detail = {
                    'number': discussion.number,
                    'title': discussion.title,
                    'success': False,
                    'already_replied': False,
                    'new_comments_posted': 0,
                    'error': None
                }
                
                if isinstance(result, Exception):
                    error_msg = f"讨论 #{discussion.number} 分析失败: {str(result)}"
                    self.logger.error(error_msg)
                    analysis_summary['errors'].append(error_msg)
                    detail['error'] = str(result)
                elif isinstance(result, dict):
                    detail['success'] = result.get('success', False)
                    if result.get('success', False):
                        successful_analyses += 1
                        # 统计成功发布的评论数和已有回复数
                        analyses = result.get('analyses', [])
                        new_comments = 0
                        has_already_replied = False
                        
                        for analysis in analyses:
                            if analysis.get('success', False):
                                if analysis.get('already_replied', False):
                                    has_already_replied = True
                                else:
                                    new_comments += 1
                                    
                        detail['new_comments_posted'] = new_comments
                        detail['already_replied'] = has_already_replied
                        
                        if has_already_replied:
                            already_replied_count += 1
                        
                        total_comments_posted += new_comments
                    else:
                        analysis_summary['errors'].append(result.get('error', '未知错误'))
                        detail['error'] = result.get('error', '未知错误')
                        
                discussion_details.append(detail)
                        
            analysis_summary.update({
                'discussions_analyzed': successful_analyses,
                'comments_posted': total_comments_posted,
                'already_replied_count': already_replied_count,
                'discussion_details': discussion_details,
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
                result['error'] = '未能提取到有效的日结或计划内容'
                return result
                
            self.logger.debug(f"提取内容完成 - 日结: {len(daily_summary)} 字符, 计划: {len(daily_plan)} 字符")
            
            # 2. 周期计划已在extract_daily_content中提取（首楼内容）
            weekly_plan = content_data.get('weekly_plan', '')
            
            # 3. 根据提取到的内容分别执行相应的分析并发布到对应讨论
            analysis_results = []
            
            # 如果有日报内容，执行日报分析并发布到当前讨论（日报讨论）
            if daily_summary:
                self.logger.debug("执行日报内容分析")
                try:
                    # 为日报找到对应的日计划（应该是时间更早的日计划）
                    corresponding_plan = await self._find_corresponding_plan_for_report(
                        discussion.number, daily_summary
                    )
                    
                    daily_report_analysis = await self.glm_client.analyze_daily_report_content(
                        daily_summary=daily_summary,
                        daily_plan=corresponding_plan or daily_plan
                    )
                    if daily_report_analysis and not daily_report_analysis.startswith("## ❌"):
                        # 查找日报评论ID
                        daily_summary_comment_id = await self._find_content_comment_id(
                            discussion.number, 'daily_summary'
                        )
                        
                        # 检查是否已回复
                        already_replied = await self.github_client.check_already_replied(
                            discussion.number, daily_summary_comment_id, 'daily_report'
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
                            'already_replied': already_replied,
                            'discussion_number': discussion.number,
                            'length': len(daily_report_analysis),
                            'reply_to_comment_id': daily_summary_comment_id
                        })
                        if daily_summary_comment_id:
                            self.logger.info(f"日报分析完成并回复到日报评论楼层 #{discussion.number}: {'成功' if comment_success else '失败'}")
                        else:
                            self.logger.info(f"日报分析完成并发布到讨论 #{discussion.number}: {'成功' if comment_success else '失败'}")
                except Exception as e:
                    self.logger.error(f"日报分析失败: {e}")
                    analysis_results.append({
                        'type': '日报分析',
                        'success': False,
                        'error': str(e)
                    })
            
            # 如果有日计划内容，需要找到对应的周计划讨论并发布日计划分析
            if daily_plan:
                self.logger.debug("执行日计划内容分析")
                try:
                    daily_plan_analysis = await self.glm_client.analyze_daily_plan_content(
                        daily_plan=daily_plan,
                        weekly_plan=weekly_plan
                    )
                    if daily_plan_analysis and not daily_plan_analysis.startswith("## ❌"):
                        # 查找包含日计划的讨论（通常是周计划讨论）
                        plan_discussion_number = await self._find_plan_discussion(daily_plan)
                        if plan_discussion_number:
                            # 查找日计划评论ID
                            daily_plan_comment_id = await self._find_content_comment_id(
                                plan_discussion_number, 'daily_plan'
                            )
                            
                            # 检查是否已回复
                            already_replied = await self.github_client.check_already_replied(
                                plan_discussion_number, daily_plan_comment_id, 'daily_plan'
                            )
                            
                            # 发布日计划分析到日计划讨论，回复到日计划评论楼层
                            comment_success = await self.github_client.post_analysis_comment(
                                plan_discussion_number, 
                                daily_plan_analysis,
                                reply_to_comment_id=daily_plan_comment_id,
                                content_type='daily_plan'
                            )
                            analysis_results.append({
                                'type': '日计划分析',
                                'success': comment_success,
                                'already_replied': already_replied,
                                'discussion_number': plan_discussion_number,
                                'length': len(daily_plan_analysis),
                                'reply_to_comment_id': daily_plan_comment_id
                            })
                            if daily_plan_comment_id:
                                self.logger.info(f"日计划分析完成并回复到日计划评论楼层 #{plan_discussion_number}: {'成功' if comment_success else '失败'}")
                            else:
                                self.logger.info(f"日计划分析完成并发布到讨论 #{plan_discussion_number}: {'成功' if comment_success else '失败'}")
                        else:
                            # 如果找不到对应的日计划讨论，在当前讨论中查找日计划评论并回复
                            daily_plan_comment_id = await self._find_content_comment_id(
                                discussion.number, 'daily_plan'
                            )
                            
                            # 检查是否已回复
                            already_replied = await self.github_client.check_already_replied(
                                discussion.number, daily_plan_comment_id, 'daily_plan'
                            )
                            
                            comment_success = await self.github_client.post_analysis_comment(
                                discussion.number, 
                                daily_plan_analysis,
                                reply_to_comment_id=daily_plan_comment_id,
                                content_type='daily_plan'
                            )
                            analysis_results.append({
                                'type': '日计划分析',
                                'success': comment_success,
                                'already_replied': already_replied,
                                'discussion_number': discussion.number,
                                'length': len(daily_plan_analysis),
                                'reply_to_comment_id': daily_plan_comment_id,
                                'note': '未找到对应的日计划讨论，发布到当前讨论'
                            })
                            if daily_plan_comment_id:
                                self.logger.warning(f"未找到日计划讨论，日计划分析回复到当前讨论的日计划评论楼层 #{discussion.number}")
                            else:
                                self.logger.warning(f"未找到日计划讨论和日计划评论，日计划分析发布到当前讨论 #{discussion.number}")
                except Exception as e:
                    self.logger.error(f"日计划分析失败: {e}")
                    analysis_results.append({
                        'type': '日计划分析',
                        'success': False,
                        'error': str(e)
                    })
            
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
        优先基于评论内容识别，然后基于讨论标题和位置判断
        
        Args:
            discussion_number: 讨论编号
            content_type: 内容类型 ('daily_summary' 或 'daily_plan')
            
        Returns:
            Optional[str]: 评论ID，如果未找到则返回None
        """
        try:
            # 获取讨论信息
            discussions = await self.github_client.get_daily_discussions()
            current_discussion = None
            for disc in discussions:
                if disc.number == discussion_number:
                    current_discussion = disc
                    break
            
            if not current_discussion:
                self.logger.warning(f"未找到讨论#{discussion_number}")
                return None
            
            # 获取评论
            comments = await self.github_client.get_discussion_comments(discussion_number)
            
            if not comments:
                self.logger.warning(f"讨论#{discussion_number}没有评论")
                return None
            
            # 按时间排序评论，最新的在前（与extract_daily_content保持一致）
            comments.sort(key=lambda x: x.updated_at, reverse=True)
            
            # 第一步：基于标题进行精确匹配
            for comment in comments:
                # 跳过分析评论
                analysis_markers = [
                    '📋 日报分析', '📋 日计划分析', '## 📋 日报分析', '## 📋 日计划分析',
                    '日报分析', '日计划分析', '分析结果', '内容表述不清楚'
                ]
                if any(marker in comment.body for marker in analysis_markers):
                    continue
                
                # 检查评论标题
                first_line = comment.body.split('\n')[0].lower()
                
                # 根据标题匹配日计划
                if content_type == 'daily_plan' and '日计划' in first_line:
                    self.logger.info(f"基于标题找到日计划评论ID: {comment.id}")
                    return comment.id
                        
                # 根据标题匹配日报
                elif content_type == 'daily_summary' and ('日报' in first_line or '日结' in first_line):
                    self.logger.info(f"基于标题找到日报评论ID: {comment.id}")
                    return comment.id
            
            # 第二步：如果内容匹配失败，基于讨论标题和评论位置判断
            title_lower = current_discussion.title.lower()
            
            # 如果标题包含"日报"关键词，在最新排序中需要重新查找
            if '日报' in title_lower or '日结' in title_lower:
                # 在最新排序的评论中查找日报和日计划
                for comment in comments:
                    comment_body_lower = comment.body.lower()
                    
                    # 跳过分析评论
                    analysis_markers = [
                        '📋 日报分析', '📋 日计划分析', '## 📋 日报分析', '## 📋 日计划分析',
                        '日报分析', '日计划分析', '分析结果', '内容表述不清楚'
                    ]
                    if any(marker in comment.body for marker in analysis_markers):
                        continue
                    
                    if content_type == 'daily_summary':
                        daily_report_keywords = [
                            '日报', '日结', '今日完成', '今日工作', '工作总结', 
                            '完成情况', '今天完成', '今天做了', '进度', '遇到问题',
                            '今日进展', '工作内容'
                        ]
                        if any(keyword in comment_body_lower for keyword in daily_report_keywords):
                            self.logger.info(f"基于标题和内容匹配找到日报评论ID: {comment.id}")
                            return comment.id
                    elif content_type == 'daily_plan':
                        daily_plan_keywords = [
                            '日计划', '明日计划', '明天计划', '下一步', '待办',
                            '明日安排', '明天安排', '计划完成', '准备'
                        ]
                        if any(keyword in comment_body_lower for keyword in daily_plan_keywords):
                            self.logger.info(f"基于标题和内容匹配找到日计划评论ID: {comment.id}")
                            return comment.id
            
            # 如果标题包含"计划"关键词，在最新排序中需要重新查找
            elif '计划' in title_lower:
                # 在最新排序的评论中查找日报和日计划
                for comment in comments:
                    comment_body_lower = comment.body.lower()
                    
                    # 跳过分析评论
                    analysis_markers = [
                        '📋 日报分析', '📋 日计划分析', '## 📋 日报分析', '## 📋 日计划分析',
                        '日报分析', '日计划分析', '分析结果', '内容表述不清楚'
                    ]
                    if any(marker in comment.body for marker in analysis_markers):
                        continue
                    
                    if content_type == 'daily_plan':
                        daily_plan_keywords = [
                            '日计划', '明日计划', '明天计划', '下一步', '待办',
                            '明日安排', '明天安排', '计划完成', '准备'
                        ]
                        if any(keyword in comment_body_lower for keyword in daily_plan_keywords):
                            self.logger.info(f"基于标题和内容匹配找到日计划评论ID: {comment.id}")
                            return comment.id
                    elif content_type == 'daily_summary':
                        daily_report_keywords = [
                            '日报', '日结', '今日完成', '今日工作', '工作总结', 
                            '完成情况', '今天完成', '今天做了', '进度', '遇到问题',
                            '今日进展', '工作内容'
                        ]
                        if any(keyword in comment_body_lower for keyword in daily_report_keywords):
                            self.logger.info(f"基于标题和内容匹配找到日报评论ID: {comment.id}")
                            return comment.id
            
            # 第三步：默认兜底规则 - 遍历所有评论查找匹配内容
            else:
                # 过滤掉分析评论
                non_analysis_comments = []
                for comment in comments:
                    analysis_markers = [
                        '📋 日报分析', '📋 日计划分析', '## 📋 日报分析', '## 📋 日计划分析',
                        '日报分析', '日计划分析', '分析结果', '内容表述不清楚'
                    ]
                    if not any(marker in comment.body for marker in analysis_markers):
                        non_analysis_comments.append(comment)
                
                # 在非分析评论中查找
                for comment in non_analysis_comments:
                    comment_body_lower = comment.body.lower()
                    
                    if content_type == 'daily_plan':
                        plan_indicators = ['计划', '明日', '明天', '下一步', '待办', '准备', '安排']
                        if any(indicator in comment_body_lower for indicator in plan_indicators):
                            self.logger.info(f"兜底规则找到日计划评论ID: {comment.id}")
                            return comment.id
                    elif content_type == 'daily_summary':
                        report_indicators = ['完成', '今日', '今天', '总结', '进度', '工作', '任务']
                        if any(indicator in comment_body_lower for indicator in report_indicators):
                            self.logger.info(f"兜底规则找到日报评论ID: {comment.id}")
                            return comment.id
                        
            self.logger.warning(f"在讨论#{discussion_number}中未找到{content_type}类型的评论")
            return None
            
        except Exception as e:
            self.logger.error(f"查找评论ID时出错: {e}")
            return None
    
    async def _find_corresponding_plan_for_report(self, discussion_number: int, daily_summary: str) -> Optional[str]:
        """
        为日报找到对应的日计划内容
        根据时间顺序，日计划在前，日报在后，所以需要找到日报评论时间之前的最近一个日计划
        
        Args:
            discussion_number: 讨论编号
            daily_summary: 日报内容
            
        Returns:
            Optional[str]: 对应的日计划内容，如果没有找到则返回None
        """
        try:
            # 获取所有评论
            comments = await self.github_client.get_discussion_comments(discussion_number)
            if not comments:
                return None
            
            # 按时间正序排列（最早的在前）
            comments.sort(key=lambda x: x.updated_at)
            
            # 找到日报评论
            daily_summary_comment = None
            for comment in comments:
                # 跳过分析评论
                analysis_markers = [
                    '📋 日报分析', '📋 日计划分析', '## 📋 日报分析', '## 📋 日计划分析',
                    '日报分析', '日计划分析', '分析结果'
                ]
                if any(marker in comment.body for marker in analysis_markers):
                    continue
                    
                # 检查是否是当前日报评论（内容匹配）
                if comment.body.strip() == daily_summary.strip():
                    daily_summary_comment = comment
                    break
            
            if not daily_summary_comment:
                self.logger.debug("未找到对应的日报评论")
                return None
            
            corresponding_plan = None
            # 从日报评论之前的评论中查找最近的日计划（时间倒序查找，找最接近日报时间的）
            for comment in reversed([c for c in comments if c.updated_at < daily_summary_comment.updated_at]):
                # 跳过分析评论
                if any(marker in comment.body for marker in analysis_markers):
                    continue
                
                # 使用github_client的内容类型识别方法
                content_type = self.github_client.identify_content_type(comment.body)
                if content_type == 'daily_plan':
                    corresponding_plan = comment.body
                    self.logger.debug(f"找到对应的日计划评论，ID: {comment.id}")
                    break  # 找到最接近日报时间的日计划就停止
            
            return corresponding_plan
            
        except Exception as e:
            self.logger.error(f"查找对应日计划时出错: {e}")
            return None
    
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
