#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
周报汇总器模块
负责收集和汇总本周的工作数据，生成周报统计信息
"""

import asyncio
import logging
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple
from dataclasses import dataclass
from collections import defaultdict

from .storage.json_data_manager import JSONDataManager
from .models.data_models import DeviationAnalysisResult


@dataclass
class UserWeeklyData:
    """用户周报数据结构"""
    user_id: str
    week_id: str
    total_reports: int
    deviation_count: int
    avg_score: float
    daily_summaries: List[str]
    daily_plans: List[str]
    weekly_plans: List[str]
    work_completion_rate: float
    key_achievements: List[str]
    identified_issues: List[str]
    analysis_results: List[DeviationAnalysisResult]


@dataclass
class WeeklySummaryRecord:
    """周报汇总记录"""
    week_id: str
    start_date: str
    end_date: str
    created_at: datetime
    status: str  # 'pending', 'processing', 'completed', 'failed'
    user_count: int
    total_reports: int
    error_message: Optional[str] = None


class WeeklyReportSummarizer:
    """周报汇总器"""
    
    def __init__(self, data_manager: JSONDataManager):
        self.data_manager = data_manager
        self.logger = logging.getLogger(__name__)
        
    def get_week_date_range(self, target_date: Optional[datetime] = None) -> Tuple[str, str]:
        """获取指定日期所在周的日期范围（周一到周五）
        
        Args:
            target_date: 目标日期，默认为当前日期
            
        Returns:
            Tuple[str, str]: (start_date, end_date) 格式为 YYYY-MM-DD
        """
        if target_date is None:
            target_date = datetime.now()
            
        # 获取周一（weekday() 返回 0-6，0为周一）
        days_since_monday = target_date.weekday()
        monday = target_date - timedelta(days=days_since_monday)
        
        # 获取周五
        friday = monday + timedelta(days=4)
        
        return monday.strftime('%Y-%m-%d'), friday.strftime('%Y-%m-%d')
    
    def get_week_id(self, target_date: Optional[datetime] = None) -> str:
        """获取周ID（格式：YYYY-WW）
        
        Args:
            target_date: 目标日期，默认为当前日期
            
        Returns:
            str: 周ID
        """
        if target_date is None:
            target_date = datetime.now()
            
        year, week, _ = target_date.isocalendar()
        return f"{year}-W{week:02d}"
    
    async def collect_weekly_data(self, start_date: str, end_date: str) -> Dict[str, UserWeeklyData]:
        """收集指定周的所有用户数据
        
        Args:
            start_date: 开始日期 (YYYY-MM-DD)
            end_date: 结束日期 (YYYY-MM-DD)
            
        Returns:
            Dict[str, UserWeeklyData]: 按用户ID组织的周报数据
        """
        self.logger.info(f"开始收集周报数据: {start_date} 到 {end_date}")
        
        # 获取日期范围内的所有分析结果
        all_results = await self._get_analysis_results_in_range(start_date, end_date)
        
        # 按用户组织数据
        user_data = defaultdict(lambda: {
            'analysis_results': [],
            'daily_summaries': [],
            'daily_plans': [],
            'weekly_plans': []
        })
        
        for result in all_results:
            user_id = result.user_id
            user_data[user_id]['analysis_results'].append(result)
            
            # 提取不同类型的内容
            if result.content_type == 'daily_report':
                user_data[user_id]['daily_summaries'].append(result.original_content)
            elif result.content_type == 'daily_plan':
                user_data[user_id]['daily_plans'].append(result.original_content)
            elif result.content_type == 'weekly_plan':
                user_data[user_id]['weekly_plans'].append(result.original_content)
        
        # 生成UserWeeklyData对象
        week_id = self.get_week_id(datetime.strptime(start_date, '%Y-%m-%d'))
        weekly_data = {}
        
        for user_id, data in user_data.items():
            analysis_results = data['analysis_results']
            
            # 计算统计指标
            total_reports = len(analysis_results)
            deviation_count = sum(1 for r in analysis_results if r.is_deviation)
            avg_score = sum(r.score for r in analysis_results) / total_reports if total_reports > 0 else 0
            
            # 计算工作完成率（基于偏离度的反向指标）
            work_completion_rate = max(0, (avg_score - 5) / 5) if avg_score > 0 else 0
            
            # 提取关键成就和问题
            key_achievements = self._extract_achievements(analysis_results)
            identified_issues = self._extract_issues(analysis_results)
            
            weekly_data[user_id] = UserWeeklyData(
                user_id=user_id,
                week_id=week_id,
                total_reports=total_reports,
                deviation_count=deviation_count,
                avg_score=avg_score,
                daily_summaries=data['daily_summaries'],
                daily_plans=data['daily_plans'],
                weekly_plans=data['weekly_plans'],
                work_completion_rate=work_completion_rate,
                key_achievements=key_achievements,
                identified_issues=identified_issues,
                analysis_results=analysis_results
            )
        
        self.logger.info(f"收集完成，共 {len(weekly_data)} 个用户的数据")
        return weekly_data
    
    async def _get_analysis_results_in_range(self, start_date: str, end_date: str) -> List[DeviationAnalysisResult]:
        """获取日期范围内的所有分析结果
        
        Args:
            start_date: 开始日期
            end_date: 结束日期
            
        Returns:
            List[DeviationAnalysisResult]: 分析结果列表
        """
        results = []
        current_date = datetime.strptime(start_date, '%Y-%m-%d')
        end_date_obj = datetime.strptime(end_date, '%Y-%m-%d')
        
        while current_date <= end_date_obj:
            date_str = current_date.strftime('%Y-%m-%d')
            
            try:
                # 获取当天的所有分析结果
                daily_results = await self.data_manager.get_analysis_results_by_date(date_str)
                results.extend(daily_results)
            except Exception as e:
                self.logger.warning(f"获取 {date_str} 的数据时出错: {e}")
            
            current_date += timedelta(days=1)
        
        return results
    
    def _extract_achievements(self, analysis_results: List[DeviationAnalysisResult]) -> List[str]:
        """从分析结果中提取关键成就
        
        Args:
            analysis_results: 分析结果列表
            
        Returns:
            List[str]: 关键成就列表
        """
        achievements = []
        
        for result in analysis_results:
            # 从高分结果中提取成就
            if result.score >= 8.0 and not result.is_deviation:
                # 提取原始内容中的关键信息
                content = result.original_content
                if content and len(content) > 20:
                    # 简单的关键词提取（可以后续优化）
                    if any(keyword in content for keyword in ['完成', '实现', '成功', '达成', '解决']):
                        # 截取前100个字符作为成就描述
                        achievement = content[:100] + '...' if len(content) > 100 else content
                        achievements.append(achievement)
        
        return achievements[:5]  # 最多返回5个关键成就
    
    def _extract_issues(self, analysis_results: List[DeviationAnalysisResult]) -> List[str]:
        """从分析结果中提取识别的问题
        
        Args:
            analysis_results: 分析结果列表
            
        Returns:
            List[str]: 问题列表
        """
        issues = []
        
        for result in analysis_results:
            # 从偏离结果中提取问题
            if result.is_deviation and result.deviation_reasons:
                issues.extend(result.deviation_reasons)
        
        # 去重并限制数量
        unique_issues = list(set(issues))
        return unique_issues[:10]  # 最多返回10个问题
    
    async def save_weekly_summary(self, week_id: str, start_date: str, end_date: str, 
                                user_data: Dict[str, UserWeeklyData], status: str = 'completed') -> bool:
        """保存周报汇总记录
        
        Args:
            week_id: 周ID
            start_date: 开始日期
            end_date: 结束日期
            user_data: 用户数据
            status: 状态
            
        Returns:
            bool: 保存是否成功
        """
        try:
            summary_record = WeeklySummaryRecord(
                week_id=week_id,
                start_date=start_date,
                end_date=end_date,
                created_at=datetime.now(),
                status=status,
                user_count=len(user_data),
                total_reports=sum(data.total_reports for data in user_data.values())
            )
            
            # 保存汇总记录
            await self.data_manager.save_weekly_summary(summary_record)
            
            # 保存用户数据
            for user_id, data in user_data.items():
                await self.data_manager.save_user_weekly_data(data)
            
            self.logger.info(f"周报汇总记录保存成功: {week_id}")
            return True
            
        except Exception as e:
            self.logger.error(f"保存周报汇总记录失败: {e}")
            return False
    
    async def get_weekly_summary(self, week_id: str) -> Optional[WeeklySummaryRecord]:
        """获取周报汇总记录
        
        Args:
            week_id: 周ID
            
        Returns:
            Optional[WeeklySummaryRecord]: 汇总记录
        """
        try:
            return await self.data_manager.get_weekly_summary(week_id)
        except Exception as e:
            self.logger.error(f"获取周报汇总记录失败: {e}")
            return None
    
    async def process_weekly_summary(self, target_date: Optional[datetime] = None) -> Optional[Dict[str, UserWeeklyData]]:
        """处理周报汇总的完整流程
        
        Args:
            target_date: 目标日期，默认为当前日期
            
        Returns:
            Optional[Dict[str, UserWeeklyData]]: 处理成功返回用户数据，失败返回None
        """
        try:
            # 获取日期范围
            start_date, end_date = self.get_week_date_range(target_date)
            week_id = self.get_week_id(target_date)
            
            self.logger.info(f"开始处理周报汇总: {week_id} ({start_date} 到 {end_date})")
            
            # 检查是否已经处理过
            existing_summary = await self.get_weekly_summary(week_id)
            if existing_summary and existing_summary.status == 'completed':
                self.logger.info(f"周报 {week_id} 已经处理完成，跳过")
                return None
            
            # 收集数据
            user_data = await self.collect_weekly_data(start_date, end_date)
            
            if not user_data:
                self.logger.warning(f"周报 {week_id} 没有找到任何数据")
                return None
            
            # 保存汇总记录
            success = await self.save_weekly_summary(week_id, start_date, end_date, user_data)
            
            if success:
                self.logger.info(f"周报汇总处理完成: {week_id}")
                return user_data
            else:
                self.logger.error(f"周报汇总保存失败: {week_id}")
                return None
                
        except Exception as e:
            self.logger.error(f"处理周报汇总时出错: {e}")
            return None
    
    async def generate_and_send_weekly_reports(self, target_date: Optional[datetime] = None) -> bool:
        """生成并发送周报（调度器接口）
        
        Args:
            target_date: 目标日期，默认为当前日期
            
        Returns:
            bool: 是否成功
        """
        try:
            self.logger.info("开始生成和发送周报")
            
            # 处理周报汇总
            user_data = await self.process_weekly_summary(target_date)
            
            if user_data:
                self.logger.info(f"周报生成成功，包含 {len(user_data)} 个用户的数据")
                # TODO: 这里可以添加发送逻辑，比如发送到飞书等
                return True
            else:
                self.logger.warning("没有生成周报数据")
                return False
                
        except Exception as e:
            self.logger.error(f"生成和发送周报失败: {e}")
            return False