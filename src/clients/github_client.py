"""
GitHub API客户端模块
负责与GitHub Discussions API的交互
"""

import logging
import asyncio
from datetime import datetime, date, timezone
from typing import List, Dict, Any, Optional, Tuple
from dataclasses import dataclass

import requests
from github import Github, GithubException
from github.RepositoryDiscussion import RepositoryDiscussion
from github.RepositoryDiscussionComment import RepositoryDiscussionComment

from src.config import GitHubConfig


@dataclass
class DiscussionData:
    """Discussion数据模型"""
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


@dataclass
class CommentData:
    """评论数据模型"""
    id: str
    body: str
    author: str
    created_at: datetime
    updated_at: datetime


class GitHubClient:
    """GitHub API客户端"""
    
    def __init__(self, config: GitHubConfig):
        self.config = config
        self.logger = logging.getLogger(__name__)
        
        # 初始化GitHub客户端
        try:
            self.github = Github(
                login_or_token=config.token,
                base_url=config.api_base_url,
                timeout=config.timeout
            )
            
            if config.use_org_discussions:
                # 使用组织级别的Discussions
                self.org = self.github.get_organization(config.organization)
                self.repo = None  # 组织级别不需要repo对象
                self.logger.info(f"GitHub客户端初始化成功 (组织级别): {config.organization}")
            else:
                # 使用仓库级别的Discussions
                repo_full_name = f"{config.organization}/{config.repository}"
                self.repo = self.github.get_repo(repo_full_name)
                self.org = None
                self.logger.info(f"GitHub客户端初始化成功 (仓库级别): {repo_full_name}")
            
        except Exception as e:
            self.logger.error(f"GitHub客户端初始化失败: {e}")
            raise
            
    async def get_daily_discussions(self, target_date: Optional[date] = None) -> List[DiscussionData]:
        """
        获取指定日期的"日结"分类讨论
        
        Args:
            target_date: 目标日期，默认为今天
            
        Returns:
            List[DiscussionData]: 讨论列表
        """
        if target_date is None:
            target_date = date.today()
            
        self.logger.info(f"正在获取 {target_date} 的日结讨论...")
        
        try:
            # 根据配置获取discussions
            if self.config.use_org_discussions:
                # 组织级别的Discussions - 使用REST API
                discussions = await self._get_org_discussions()
            else:
                # 仓库级别的Discussions - 使用REST API
                discussions = await self._get_repo_discussions()
                
            daily_discussions = []
            
            for discussion in discussions:
                # 过滤指定分类的讨论
                if discussion.category.name != self.config.discussion_category:
                    continue
                    
                # 检查更新时间是否在目标日期
                updated_date = discussion.updated_at.date()
                if updated_date != target_date:
                    continue
                    
                # 转换为DiscussionData对象
                discussion_data = DiscussionData(
                    id=str(discussion.id),
                    number=discussion.number,
                    title=discussion.title,
                    body=discussion.body or "",
                    author=discussion.user.login,
                    created_at=discussion.created_at,
                    updated_at=discussion.updated_at,
                    category=discussion.category.name,
                    url=discussion.html_url,
                    comments_count=discussion.comments
                )
                
                daily_discussions.append(discussion_data)
                
            self.logger.info(f"找到 {len(daily_discussions)} 个相关讨论")
            return daily_discussions
            
        except GithubException as e:
            self.logger.error(f"获取讨论失败: {e}")
            raise
        except Exception as e:
            self.logger.error(f"获取讨论时发生未知错误: {e}")
            raise
            
    async def get_discussion_comments(self, discussion_number: int) -> List[CommentData]:
        """
        获取指定讨论的所有评论
        
        Args:
            discussion_number: 讨论编号
            
        Returns:
            List[CommentData]: 评论列表
        """
        self.logger.debug(f"正在获取讨论 #{discussion_number} 的评论...")
        
        try:
            # 根据配置获取discussion
            if self.config.use_org_discussions:
                # 组织级别需要遍历找到对应的discussion
                discussions = self.org.get_discussions()
                discussion = None
                for disc in discussions:
                    if disc.number == discussion_number:
                        discussion = disc
                        break
                if not discussion:
                    raise Exception(f"未找到讨论 #{discussion_number}")
            else:
                # 仓库级别需要遍历找到对应的discussion
                discussions = await self._get_repo_discussions()
                discussion = None
                for disc in discussions:
                    if disc.number == discussion_number:
                        discussion = disc
                        break
                if not discussion:
                    raise Exception(f"未找到讨论 #{discussion_number}")
                
            # 获取评论
            if self.config.use_org_discussions:
                comments = discussion.get_comments()
            else:
                # 仓库级别通过REST API获取评论
                comments = await self._get_repo_discussion_comments(discussion_number)
            
            comment_list = []
            for comment in comments:
                comment_data = CommentData(
                    id=str(comment.id),
                    body=comment.body,
                    author=comment.user.login,
                    created_at=comment.created_at,
                    updated_at=comment.updated_at
                )
                comment_list.append(comment_data)
                
            self.logger.debug(f"获取到 {len(comment_list)} 条评论")
            return comment_list
            
        except GithubException as e:
            self.logger.error(f"获取评论失败: {e}")
            raise
            
    async def check_already_replied(self, discussion_number: int, reply_to_comment_id: Optional[str] = None, content_type: Optional[str] = None) -> bool:
        """
        检查是否已经回复过指定评论或讨论
        
        Args:
            discussion_number: 讨论编号
            reply_to_comment_id: 要检查的评论ID（可选，如果为None则检查讨论的顶级评论）
            content_type: 内容类型（可选，'daily_report'或'daily_plan'，用于区分不同类型的分析）
            
        Returns:
            bool: 如果已经回复过返回True，否则返回False
        """
        try:
            # 获取结构化的评论数据（包括顶级评论和按父评论分组的回复）
            structured_comments = await self._get_all_comments_with_replies(discussion_number)
            
            # 根据内容类型定义不同的分析评论特征标识
            if content_type == 'daily_report':
                analysis_markers = [
                    "## 📊 日报分析",
                    "## 📋 日报分析",  # 兼容不同的图标
                    "### 🎯 总体评估",
                    "### 📈 完成情况分析",
                    "### 💡 改进建议"
                ]
            elif content_type == 'daily_plan':
                analysis_markers = [
                    "## 📋 日计划分析",
                    "### 🎯 计划评估",
                    "### 📊 任务分析",
                    "### 💡 优化建议"
                ]
            else:
                # 如果没有指定内容类型，使用通用的分析评论标识
                analysis_markers = [
                    "本分析由GLM-4.5自动生成",
                    "## 📊 日报分析",
                    "## 📋 日计划分析",
                    "### 🎯 总体评估",
                    "### 📈 完成情况分析",
                    "### 💡 改进建议"
                ]
            
            if reply_to_comment_id is None:
                # 检查顶级评论中是否存在指定类型的分析评论
                for comment in structured_comments['top_level']:
                    comment_body = comment.body.strip()
                    is_analysis_comment = any(marker in comment_body for marker in analysis_markers)
                    if is_analysis_comment:
                        content_desc = f"{content_type}" if content_type else "分析"
                        self.logger.info(f"讨论 #{discussion_number} 已存在顶级{content_desc}评论，跳过重复发布")
                        return True
            else:
                # 检查指定评论的回复中是否存在指定类型的分析评论
                if reply_to_comment_id in structured_comments['replies']:
                    for reply in structured_comments['replies'][reply_to_comment_id]:
                        reply_body = reply.body.strip()
                        is_analysis_comment = any(marker in reply_body for marker in analysis_markers)
                        if is_analysis_comment:
                            content_desc = f"{content_type}" if content_type else "分析"
                            self.logger.info(f"讨论 #{discussion_number} 的评论 {reply_to_comment_id} 已存在{content_desc}回复，跳过重复发布")
                            return True
                else:
                    self.logger.debug(f"评论 {reply_to_comment_id} 暂无回复")
            
            return False
            
        except Exception as e:
            self.logger.error(f"检查重复回复时发生错误: {e}")
            # 发生错误时，为了安全起见，假设没有回复过
            return False
    
    async def post_analysis_comment(self, discussion_number: int, analysis_content: str, reply_to_comment_id: Optional[str] = None, content_type: Optional[str] = None) -> bool:
        """
        在指定讨论下发布分析评论
        
        Args:
            discussion_number: 讨论编号
            analysis_content: 分析内容（Markdown格式）
            reply_to_comment_id: 要回复的评论ID（可选）
            content_type: 内容类型（可选，'daily_report'或'daily_plan'，用于区分不同类型的分析）
            
        Returns:
            bool: 是否成功发布
        """
        content_desc = f"{content_type}" if content_type else "分析"
        self.logger.info(f"正在向讨论 #{discussion_number} 发布{content_desc}评论...")
        
        try:
            # 检查是否已经回复过指定类型的分析
            if await self.check_already_replied(discussion_number, reply_to_comment_id, content_type):
                self.logger.info(f"讨论 #{discussion_number} 已存在{content_desc}评论，跳过发布")
                return True  # 返回True表示不需要重复发布
            
            # 添加分析时间戳
            timestamp = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S UTC")
            full_content = f"{analysis_content}\n\n---\n*本分析由GLM-4.5自动生成 | 生成时间: {timestamp}*"
            
            # 统一使用REST API发布评论（避免PyGithub的get_discussions参数问题）
            if self.config.use_org_discussions:
                # 组织级别使用REST API发布评论
                return await self._post_org_discussion_comment(discussion_number, full_content, reply_to_comment_id)
            else:
                # 仓库级别使用REST API发布评论
                return await self._post_repo_discussion_comment(discussion_number, full_content, reply_to_comment_id)
            
        except GithubException as e:
            self.logger.error(f"发布评论失败: {e}")
            return False
        except Exception as e:
            self.logger.error(f"发布评论时发生未知错误: {e}")
            return False
            
    async def extract_daily_content(self, discussion: DiscussionData) -> Dict[str, str]:
        """
        从讨论评论中提取最新的日结和计划内容
        注意：首楼是周期计划，日计划和日报在评论中轮流出现
        
        Args:
            discussion: 讨论数据
            
        Returns:
            Dict[str, str]: 包含'daily_summary'、'daily_plan'和'weekly_plan'的字典
        """
        self.logger.debug(f"正在解析讨论 #{discussion.number} 的内容...")
        
        result = {
            'daily_summary': '',
            'daily_plan': '',
            'weekly_plan': discussion.body or '',  # 首楼作为周期计划
            'original_content': discussion.body
        }
        
        try:
            # 获取讨论的所有评论
            comments = await self.get_discussion_comments(discussion.number)
            
            if not comments:
                self.logger.debug("讨论没有评论，仅使用首楼内容")
                return result
            
            # 按时间排序评论，最新的在前
            comments.sort(key=lambda x: x.updated_at, reverse=True)
            
            # 分析最近的评论，寻找日报和日计划
            daily_summary_found = False
            daily_plan_found = False
            
            for comment in comments:
                if daily_summary_found and daily_plan_found:
                    break
                    
                comment_content = comment.body.lower()
                
                # 跳过分析评论（包含分析标记的评论）
                analysis_markers = [
                    '📋 日报分析', '📋 日计划分析', '## 📋 日报分析', '## 📋 日计划分析',
                    '日报分析', '日计划分析', '分析结果', '内容表述不清楚', '如何澄清这些不清楚的内容'
                ]
                
                if any(marker in comment.body for marker in analysis_markers):
                    self.logger.debug(f"跳过分析评论，评论ID: {comment.id}")
                    continue
                
                # 识别日报关键词
                daily_report_keywords = [
                    '日报', '日结', '今日完成', '今日工作', '工作总结', 
                    '完成情况', '今天完成', '今天做了', '进度', '遇到问题',
                    '今日进展', '工作内容'
                ]
                
                # 识别日计划关键词  
                daily_plan_keywords = [
                    '日计划', '明日计划', '明天计划', '下一步', '待办',
                    '明日安排', '明天安排', '计划完成', '准备'
                ]
                
                # 检查是否是日报
                if not daily_summary_found and any(keyword in comment_content for keyword in daily_report_keywords):
                    result['daily_summary'] = comment.body
                    daily_summary_found = True
                    self.logger.debug(f"找到日报内容，评论ID: {comment.id}")
                    continue
                
                # 检查是否是日计划
                if not daily_plan_found and any(keyword in comment_content for keyword in daily_plan_keywords):
                    result['daily_plan'] = comment.body
                    daily_plan_found = True
                    self.logger.debug(f"找到日计划内容，评论ID: {comment.id}")
                    continue
                
                # 如果评论内容较长且包含工作相关词汇，可能是日报
                if not daily_summary_found and len(comment.body) > 50:
                    work_keywords = ['完成', '开发', '测试', '修复', '问题', '功能', '任务', '会议']
                    if sum(1 for keyword in work_keywords if keyword in comment_content) >= 2:
                        result['daily_summary'] = comment.body
                        daily_summary_found = True
                        self.logger.debug(f"根据内容特征识别为日报，评论ID: {comment.id}")
            
            # 记录提取结果
            self.logger.debug(f"内容提取完成 - 周期计划: {len(result['weekly_plan'])} 字符, "
                            f"日报: {len(result['daily_summary'])} 字符, "
                            f"日计划: {len(result['daily_plan'])} 字符")
            
            return result
            
        except Exception as e:
            self.logger.error(f"提取内容时出错: {e}")
            # 出错时返回基本结果
            return result
            
    def identify_content_type(self, content: str) -> str:
        """
        识别内容类型：日报、日计划或周计划
        
        Args:
            content: 要识别的内容
            
        Returns:
            str: 'daily_report', 'daily_plan', 'weekly_plan', 或 'unknown'
        """
        if not content or not content.strip():
            return 'unknown'
            
        content_lower = content.lower()
        
        # 强日报关键词（明确表示日报的词汇）
        strong_daily_report_keywords = [
            '日报', '日结', '今日完成', '今日工作', '工作总结', 
            '完成情况', '今天完成', '今天做了', '今日进展', '工作内容',
            '今日总结', '当日工作', '本日完成'
        ]
        
        # 强日计划关键词（明确表示日计划的词汇）
        strong_daily_plan_keywords = [
            '日计划', '明日计划', '明天计划', '明日安排', '明天安排',
            '明日工作', '明天工作', '下一步计划', '明日目标', '明天目标'
        ]
        
        # 弱日报关键词（可能表示日报的词汇）
        weak_daily_report_keywords = [
            '进度', '遇到问题', '解决', '处理', '完成', '开发', '测试', 
            '修复', '问题', '功能', '任务', '会议', '学习', '研究'
        ]
        
        # 弱日计划关键词（可能表示日计划的词汇）
        weak_daily_plan_keywords = [
            '下一步', '待办', '准备', '计划', '安排', '目标', '任务',
            '继续', '开始', '进行', '实现', '完善', '优化'
        ]
        
        # 周计划关键词
        weekly_plan_keywords = [
            '周计划', '本周', '周期计划', '周安排', '周目标',
            '本周计划', '这周', '周工作', '本周任务', '周期目标'
        ]
        
        # 计算强关键词得分
        strong_daily_report_score = sum(2 for keyword in strong_daily_report_keywords if keyword in content_lower)
        strong_daily_plan_score = sum(2 for keyword in strong_daily_plan_keywords if keyword in content_lower)
        
        # 计算弱关键词得分
        weak_daily_report_score = sum(1 for keyword in weak_daily_report_keywords if keyword in content_lower)
        weak_daily_plan_score = sum(1 for keyword in weak_daily_plan_keywords if keyword in content_lower)
        
        # 计算周计划得分
        weekly_plan_score = sum(2 for keyword in weekly_plan_keywords if keyword in content_lower)
        
        # 综合得分
        daily_report_total = strong_daily_report_score + weak_daily_report_score
        daily_plan_total = strong_daily_plan_score + weak_daily_plan_score
        
        # 内容长度和结构特征分析
        content_length = len(content)
        lines = content.split('\n')
        line_count = len([line for line in lines if line.strip()])
        
        # 日报通常较长，包含详细的工作内容
        if content_length > 100 and line_count > 3:
            daily_report_total += 1
            
        # 日计划通常较短，条目化
        if content_length < 200 and ('1.' in content or '2.' in content or '-' in content):
            daily_plan_total += 1
            
        # 时间特征分析
        time_indicators = {
            'past': ['完成了', '做了', '处理了', '解决了', '学习了', '参加了'],
            'future': ['计划', '准备', '将要', '打算', '预计', '安排']
        }
        
        past_score = sum(1 for indicator in time_indicators['past'] if indicator in content_lower)
        future_score = sum(1 for indicator in time_indicators['future'] if indicator in content_lower)
        
        # 过去时态倾向于日报
        if past_score > future_score:
            daily_report_total += 1
        # 将来时态倾向于日计划
        elif future_score > past_score:
            daily_plan_total += 1
            
        # 决策逻辑
        max_score = max(daily_report_total, daily_plan_total, weekly_plan_score)
        
        # 如果有强关键词，优先考虑
        if strong_daily_report_score > 0 and strong_daily_report_score >= strong_daily_plan_score:
            return 'daily_report'
        elif strong_daily_plan_score > 0 and strong_daily_plan_score > strong_daily_report_score:
            return 'daily_plan'
        elif weekly_plan_score > 0:
            return 'weekly_plan'
            
        # 如果没有强关键词，根据综合得分判断
        if max_score == 0:
            return 'unknown'
        elif daily_report_total == max_score and daily_report_total > 0:
            return 'daily_report'
        elif daily_plan_total == max_score and daily_plan_total > 0:
            return 'daily_plan'
        elif weekly_plan_score == max_score:
            return 'weekly_plan'
        else:
            return 'unknown'
        
    async def get_thread_first_post(self, discussion_number: int) -> Optional[str]:
        """
        获取讨论串的首楼内容（通常包含周期计划）
        
        Args:
            discussion_number: 讨论编号
            
        Returns:
            Optional[str]: 首楼内容，如果获取失败则返回None
        """
        try:
            # 根据配置获取discussion
            if self.config.use_org_discussions:
                # 组织级别需要遍历找到对应的discussion
                discussions = self.org.get_discussions()
                discussion = None
                for disc in discussions:
                    if disc.number == discussion_number:
                        discussion = disc
                        break
                if not discussion:
                    return None
            else:
                discussion = self.repo.get_discussion(discussion_number)
            return discussion.body
        except Exception as e:
            self.logger.error(f"获取首楼内容失败: {e}")
            return None
            
    async def check_api_rate_limit(self) -> Dict[str, Any]:
        """
        检查API速率限制状态
        
        Returns:
            Dict[str, Any]: 速率限制信息
        """
        try:
            rate_limit = self.github.get_rate_limit()
            return {
                'core': {
                    'remaining': rate_limit.core.remaining,
                    'limit': rate_limit.core.limit,
                    'reset': rate_limit.core.reset
                },
                'search': {
                    'remaining': rate_limit.search.remaining,
                    'limit': rate_limit.search.limit,
                    'reset': rate_limit.search.reset
                }
            }
        except Exception as e:
            self.logger.error(f"检查速率限制失败: {e}")
            return {}
            
    async def test_connection(self) -> bool:
        """
        测试GitHub连接
        
        Returns:
            bool: 连接是否成功
        """
        try:
            # 根据配置测试连接
            if self.config.use_org_discussions:
                # 测试组织连接
                org_info = self.org.login
                self.logger.info(f"GitHub连接测试成功 (组织): {org_info}")
            else:
                # 测试仓库连接
                repo_info = self.repo
                self.logger.info(f"GitHub连接测试成功 (仓库): {repo_info.full_name}")
            return True
        except Exception as e:
            self.logger.error(f"GitHub连接测试失败: {e}")
            return False
    
    async def _get_org_discussions(self):
        """
        使用REST API获取组织级别的Discussions（支持分页）
        
        Returns:
            List: 讨论列表
        """
        try:
            # 使用GitHub REST API获取组织讨论
            headers = {
                'Authorization': f'token {self.config.token}',
                'Accept': 'application/vnd.github.v3+json',
                'X-GitHub-Api-Version': '2022-11-28'
            }
            
            all_discussions_data = []
            page = 1
            per_page = 100  # 每页最多100个
            
            while True:
                url = f"{self.config.api_base_url}/orgs/{self.config.organization}/discussions"
                params = {
                    'page': page,
                    'per_page': per_page
                }
                
                self.logger.debug(f"获取第 {page} 页组织讨论，每页 {per_page} 个")
                response = requests.get(url, headers=headers, params=params, timeout=self.config.timeout)
                response.raise_for_status()
                
                discussions_data = response.json()
                
                if not discussions_data:  # 没有更多数据
                    break
                    
                all_discussions_data.extend(discussions_data)
                
                # 如果返回的数据少于per_page，说明是最后一页
                if len(discussions_data) < per_page:
                    break
                    
                page += 1
            
            self.logger.info(f"总共获取到 {len(all_discussions_data)} 个组织讨论")
            discussions_data = all_discussions_data
            
            # 创建模拟的discussion对象列表
            discussions = []
            for disc_data in discussions_data:
                # 创建一个简单的对象来模拟PyGithub的Discussion对象
                class MockDiscussion:
                    def __init__(self, data):
                        self.id = data['id']
                        self.number = data['number']
                        self.title = data['title']
                        self.body = data.get('body', '')
                        self.created_at = datetime.fromisoformat(data['created_at'].replace('Z', '+00:00'))
                        self.updated_at = datetime.fromisoformat(data['updated_at'].replace('Z', '+00:00'))
                        self.url = data['html_url']
                        self.html_url = data['html_url']  # 添加html_url属性
                        self.comments = data.get('comments', 0)  # 修正属性名
                        self.comments_count = data.get('comments', 0)
                        
                        # 模拟category对象
                        class MockCategory:
                            def __init__(self, name):
                                self.name = name
                        self.category = MockCategory(data.get('category', {}).get('name', ''))
                        
                        # 模拟user对象
                        class MockUser:
                            def __init__(self, login):
                                self.login = login
                        self.user = MockUser(data.get('user', {}).get('login', ''))
                        self.author = self.user.login  # 添加author属性
                
                discussions.append(MockDiscussion(disc_data))
            
            return discussions
            
        except Exception as e:
             self.logger.error(f"获取组织讨论失败: {e}")
             # 如果REST API失败，返回空列表
             return []
    
    async def _get_repo_discussions(self):
        """
        使用REST API获取仓库级别的Discussions（支持分页）
        
        Returns:
            List: 讨论列表
        """
        try:
            # 使用GitHub REST API获取仓库讨论
            headers = {
                'Authorization': f'token {self.config.token}',
                'Accept': 'application/vnd.github.v3+json',
                'X-GitHub-Api-Version': '2022-11-28'
            }
            
            all_discussions_data = []
            page = 1
            per_page = 100  # 每页最多100个
            
            while True:
                url = f"{self.config.api_base_url}/repos/{self.config.organization}/{self.config.repository}/discussions"
                params = {
                    'page': page,
                    'per_page': per_page
                }
                
                self.logger.debug(f"获取第 {page} 页讨论，每页 {per_page} 个")
                response = requests.get(url, headers=headers, params=params, timeout=self.config.timeout)
                response.raise_for_status()
                
                discussions_data = response.json()
                
                if not discussions_data:  # 没有更多数据
                    break
                    
                all_discussions_data.extend(discussions_data)
                
                # 如果返回的数据少于per_page，说明是最后一页
                if len(discussions_data) < per_page:
                    break
                    
                page += 1
            
            self.logger.info(f"总共获取到 {len(all_discussions_data)} 个讨论")
            discussions_data = all_discussions_data
            
            # 创建模拟的discussion对象列表
            discussions = []
            for disc_data in discussions_data:
                # 创建一个简单的对象来模拟PyGithub的Discussion对象
                class MockDiscussion:
                    def __init__(self, data):
                        self.id = data['id']
                        self.number = data['number']
                        self.title = data['title']
                        self.body = data.get('body', '')
                        self.created_at = datetime.fromisoformat(data['created_at'].replace('Z', '+00:00'))
                        self.updated_at = datetime.fromisoformat(data['updated_at'].replace('Z', '+00:00'))
                        self.url = data['html_url']
                        self.html_url = data['html_url']  # 添加html_url属性
                        self.comments = data.get('comments', 0)  # 修正属性名
                        self.comments_count = data.get('comments', 0)
                        
                        # 模拟category对象
                        class MockCategory:
                            def __init__(self, name):
                                self.name = name
                        self.category = MockCategory(data.get('category', {}).get('name', ''))
                        
                        # 模拟user对象
                        class MockUser:
                            def __init__(self, login):
                                self.login = login
                        self.user = MockUser(data.get('user', {}).get('login', ''))
                        self.author = self.user.login  # 添加author属性
                    
                    def get_comments(self):
                        """模拟获取评论的方法"""
                        # 这里返回空列表，因为我们需要通过REST API单独获取评论
                        # 实际的评论获取会在get_discussion_comments方法中处理
                        return []
                
                discussions.append(MockDiscussion(disc_data))
            
            return discussions
            
        except Exception as e:
            self.logger.error(f"获取仓库讨论失败: {e}")
            # 如果REST API失败，返回空列表
            return []
    
    async def _get_repo_discussion_comments(self, discussion_number: int):
        """通过GraphQL API获取仓库讨论的评论"""
        try:
            # 使用GraphQL查询获取讨论评论
            comments_query = """
            query($owner: String!, $name: String!, $number: Int!) {
                repository(owner: $owner, name: $name) {
                    discussion(number: $number) {
                        comments(first: 100) {
                            nodes {
                                id
                                body
                                createdAt
                                updatedAt
                                author {
                                    login
                                }
                                replies(first: 50) {
                                    nodes {
                                        id
                                        body
                                        createdAt
                                        updatedAt
                                        author {
                                            login
                                        }
                                    }
                                }
                            }
                        }
                    }
                }
            }
            """
            
            query_variables = {
                "owner": self.config.organization,
                "name": self.config.repository,
                "number": discussion_number
            }
            
            headers = {
                "Authorization": f"Bearer {self.config.token}",
                "Content-Type": "application/json"
            }
            
            response = requests.post(
                "https://api.github.com/graphql",
                headers=headers,
                json={"query": comments_query, "variables": query_variables},
                timeout=self.config.timeout
            )
            response.raise_for_status()
            
            result = response.json()
            self.logger.debug(f"GraphQL查询结果: {result}")
            
            if "errors" in result:
                self.logger.error(f"GraphQL查询错误: {result['errors']}")
                return []
                
            data = result.get("data", {})
            repository = data.get("repository")
            if not repository:
                self.logger.error(f"未找到仓库 {self.config.organization}/{self.config.repository}")
                return []
                
            discussion = repository.get("discussion")
            if discussion is None:
                self.logger.error(f"未找到讨论 #{discussion_number}，可能讨论不存在或无权限访问")
                return []
            
            comments_data = discussion["comments"]["nodes"]
            
            # 创建模拟的comment对象列表，包括顶级评论和所有回复
            comments = []
            
            # 定义MockComment类
            class MockComment:
                def __init__(self, data):
                    self.id = data['id']
                    self.body = data['body']
                    self.created_at = datetime.fromisoformat(data['createdAt'].replace('Z', '+00:00'))
                    self.updated_at = datetime.fromisoformat(data['updatedAt'].replace('Z', '+00:00'))
                    
                    # 模拟user对象
                    class MockUser:
                        def __init__(self, login):
                            self.login = login
                    self.user = MockUser(data.get('author', {}).get('login', '') if data.get('author') else '')
            
            for comment_data in comments_data:
                # 只添加顶级评论，不添加回复
                # 这样确保_find_content_comment_id只会返回顶级评论的ID
                # 避免"Parent comment is already in a thread"错误
                comments.append(MockComment(comment_data))
            
            return comments
            
        except Exception as e:
            self.logger.error(f"获取仓库讨论评论失败: {e}")
            return []
    
    async def _get_all_comments_with_replies(self, discussion_number: int) -> Dict[str, Any]:
        """获取讨论的所有评论，包括顶级评论和按父评论分组的回复"""
        try:
            # 使用修改后的GraphQL查询获取评论和回复
            comments_query = """
            query($owner: String!, $name: String!, $number: Int!) {
                repository(owner: $owner, name: $name) {
                    discussion(number: $number) {
                        comments(first: 100) {
                            nodes {
                                id
                                body
                                createdAt
                                updatedAt
                                author {
                                    login
                                }
                                replies(first: 50) {
                                    nodes {
                                        id
                                        body
                                        createdAt
                                        updatedAt
                                        author {
                                            login
                                        }
                                    }
                                }
                            }
                        }
                    }
                }
            }
            """
            
            query_variables = {
                "owner": self.config.organization,
                "name": self.config.repository,
                "number": discussion_number
            }
            
            headers = {
                "Authorization": f"Bearer {self.config.token}",
                "Content-Type": "application/json"
            }
            
            response = requests.post(
                "https://api.github.com/graphql",
                headers=headers,
                json={"query": comments_query, "variables": query_variables},
                timeout=self.config.timeout
            )
            response.raise_for_status()
            
            result = response.json()
            
            if "errors" in result:
                self.logger.error(f"GraphQL查询错误: {result['errors']}")
                return {"top_level": [], "replies": {}}
                
            data = result.get("data", {})
            repository = data.get("repository")
            if not repository:
                self.logger.error(f"未找到仓库 {self.config.organization}/{self.config.repository}")
                return {"top_level": [], "replies": {}}
                
            discussion = repository.get("discussion")
            if discussion is None:
                self.logger.error(f"未找到讨论 #{discussion_number}，可能讨论不存在或无权限访问")
                return {"top_level": [], "replies": {}}
            
            comments_data = discussion["comments"]["nodes"]
            
            # 定义MockComment类
            class MockComment:
                def __init__(self, data):
                    self.id = data['id']
                    self.body = data['body']
                    self.created_at = datetime.fromisoformat(data['createdAt'].replace('Z', '+00:00'))
                    self.updated_at = datetime.fromisoformat(data['updatedAt'].replace('Z', '+00:00'))
                    
                    # 模拟user对象
                    class MockUser:
                        def __init__(self, login):
                            self.login = login
                    self.user = MockUser(data.get('author', {}).get('login', '') if data.get('author') else '')
            
            # 分离顶级评论和回复
            top_level_comments = []
            replies_by_parent = {}
            
            for comment_data in comments_data:
                # 添加顶级评论
                top_level_comment = MockComment(comment_data)
                top_level_comments.append(top_level_comment)
                
                # 添加该评论的所有回复
                if 'replies' in comment_data and comment_data['replies']:
                    parent_id = comment_data['id']
                    replies_by_parent[parent_id] = []
                    for reply_data in comment_data['replies']['nodes']:
                        reply_comment = MockComment(reply_data)
                        replies_by_parent[parent_id].append(reply_comment)
            
            return {
                "top_level": top_level_comments,
                "replies": replies_by_parent
            }
            
        except Exception as e:
            self.logger.error(f"获取结构化评论数据失败: {e}")
            return {"top_level": [], "replies": {}}
    
    async def _post_repo_discussion_comment(self, discussion_number: int, content: str, reply_to_comment_id: Optional[str] = None) -> bool:
        """通过GraphQL API在仓库讨论下发布评论或回复指定评论"""
        try:
            # 首先获取讨论的node ID和最新评论
            discussion_query = """
            query($owner: String!, $name: String!, $number: Int!) {
                repository(owner: $owner, name: $name) {
                    discussion(number: $number) {
                        id
                        comments(last: 1) {
                            nodes {
                                id
                                body
                                author {
                                    login
                                }
                            }
                        }
                    }
                }
            }
            """
            
            query_variables = {
                "owner": self.config.organization,
                "name": self.config.repository,
                "number": discussion_number
            }
            
            headers = {
                "Authorization": f"Bearer {self.config.token}",
                "Content-Type": "application/json"
            }
            
            response = requests.post(
                "https://api.github.com/graphql",
                headers=headers,
                json={"query": discussion_query, "variables": query_variables},
                timeout=self.config.timeout
            )
            response.raise_for_status()
            
            result = response.json()
            if "errors" in result:
                self.logger.error(f"获取讨论信息失败: {result['errors']}")
                return False
                
            discussion_data = result["data"]["repository"]["discussion"]
            if not discussion_data:
                self.logger.error(f"未找到讨论 #{discussion_number}")
                return False
                
            discussion_id = discussion_data["id"]
            comments = discussion_data["comments"]["nodes"]
            
            # 准备评论mutation
            comment_mutation = """
            mutation($discussionId: ID!, $body: String!, $replyToId: ID) {
                addDiscussionComment(input: {
                    discussionId: $discussionId,
                    body: $body,
                    replyToId: $replyToId
                }) {
                    clientMutationId
                    comment {
                        id
                        body
                    }
                }
            }
            """
            
            mutation_variables = {
                "discussionId": discussion_id,
                "body": content
            }
            
            # 如果指定了要回复的评论ID，则回复该评论；否则创建顶级评论
            if reply_to_comment_id:
                mutation_variables["replyToId"] = reply_to_comment_id
                self.logger.info(f"回复指定评论 {reply_to_comment_id}")
            else:
                self.logger.info("创建新的顶级评论")
            
            response = requests.post(
                "https://api.github.com/graphql",
                headers=headers,
                json={"query": comment_mutation, "variables": mutation_variables},
                timeout=self.config.timeout
            )
            response.raise_for_status()
            
            result = response.json()
            if "errors" in result:
                self.logger.error(f"GraphQL mutation错误: {result['errors']}")
                return False
                
            if result.get("data", {}).get("addDiscussionComment", {}).get("comment"):
                comment_id = result["data"]["addDiscussionComment"]["comment"]["id"]
                self.logger.info(f"分析评论发布成功，评论ID: {comment_id}")
                return True
            else:
                self.logger.error("评论发布失败，未返回评论数据")
                return False
            
        except Exception as e:
            self.logger.error(f"发布仓库讨论评论失败: {e}")
            return False
    
    async def _post_org_discussion_comment(self, discussion_number: int, content: str, reply_to_comment_id: Optional[str] = None) -> bool:
        """通过GraphQL API在组织讨论下发布评论或回复指定评论"""
        try:
            # 首先获取讨论的node ID和最新评论
            discussion_query = """
            query($org: String!, $number: Int!) {
                organization(login: $org) {
                    discussion(number: $number) {
                        id
                        comments(last: 1) {
                            nodes {
                                id
                                body
                                author {
                                    login
                                }
                            }
                        }
                    }
                }
            }
            """
            
            query_variables = {
                "org": self.config.organization,
                "number": discussion_number
            }
            
            headers = {
                "Authorization": f"Bearer {self.config.token}",
                "Content-Type": "application/json"
            }
            
            response = requests.post(
                "https://api.github.com/graphql",
                headers=headers,
                json={"query": discussion_query, "variables": query_variables},
                timeout=self.config.timeout
            )
            response.raise_for_status()
            
            result = response.json()
            if "errors" in result:
                self.logger.error(f"获取组织讨论信息失败: {result['errors']}")
                return False
                
            discussion_data = result["data"]["organization"]["discussion"]
            if not discussion_data:
                self.logger.error(f"未找到组织讨论 #{discussion_number}")
                return False
                
            discussion_id = discussion_data["id"]
            comments = discussion_data["comments"]["nodes"]
            
            # 准备评论mutation
            comment_mutation = """
            mutation($discussionId: ID!, $body: String!, $replyToId: ID) {
                addDiscussionComment(input: {
                    discussionId: $discussionId,
                    body: $body,
                    replyToId: $replyToId
                }) {
                    clientMutationId
                    comment {
                        id
                        body
                    }
                }
            }
            """
            
            mutation_variables = {
                "discussionId": discussion_id,
                "body": content
            }
            
            # 如果指定了要回复的评论ID，则回复该评论；否则根据现有评论决定
            if reply_to_comment_id:
                mutation_variables["replyToId"] = reply_to_comment_id
                self.logger.info(f"回复指定的组织讨论评论 {reply_to_comment_id}")
            elif comments:
                latest_comment = comments[0]
                mutation_variables["replyToId"] = latest_comment["id"]
                self.logger.info(f"回复最新的组织讨论评论 {latest_comment['id']} (作者: {latest_comment.get('author', {}).get('login', '未知')})")
            else:
                self.logger.info("组织讨论中暂无评论，将创建新的顶级评论")
            
            response = requests.post(
                "https://api.github.com/graphql",
                headers=headers,
                json={"query": comment_mutation, "variables": mutation_variables},
                timeout=self.config.timeout
            )
            response.raise_for_status()
            
            result = response.json()
            if "errors" in result:
                self.logger.error(f"组织讨论GraphQL mutation错误: {result['errors']}")
                return False
                
            if result.get("data", {}).get("addDiscussionComment", {}).get("comment"):
                comment_id = result["data"]["addDiscussionComment"]["comment"]["id"]
                self.logger.info(f"组织讨论分析评论发布成功，评论ID: {comment_id}")
                return True
            else:
                self.logger.error("组织讨论评论发布失败，未返回评论数据")
                return False
            
        except Exception as e:
            self.logger.error(f"发布组织讨论评论失败: {e}")
            return False
