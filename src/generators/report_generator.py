#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
智能汇报生成模块

功能：
- 支持多种汇报格式（简洁型、详细型、卡片型）
- 包含偏离分析、趋势统计和改进建议
- 自动生成连续偏离预警汇报
"""

import asyncio
import json
from datetime import datetime, timedelta
from typing import List, Dict, Any, Optional
from dataclasses import dataclass

from src.utils.logger import get_logger
from src.models.data_models import DeviationAnalysisResult
from src.clients.glm_client import GLMClient
from src.config import Config


@dataclass
class ReportData:
    """汇报数据结构"""
    user_name: str
    analyses: List[Dict[str, Any]]
    continuous_days: int
    avg_deviation_score: float
    avg_completion_rate: float
    max_deviation_score: float
    min_deviation_score: float
    deviation_reasons: List[str]
    suggestions: List[str]
    trend_analysis: str
    impact_level: str
    timestamp: str


class ReportGenerator:
    """智能汇报生成器"""
    
    def __init__(self, config: Config):
        self.config = config
        # 只有当GLM配置存在且API密钥已配置时才初始化GLMClient
        if hasattr(config, 'glm') and config.glm.api_key and config.glm.api_key.strip():
            try:
                self.glm_client = GLMClient(config.glm)
                self.logger = get_logger(__name__)
                self.logger.info("GLM客户端初始化成功")
            except Exception as e:
                self.glm_client = None
                self.logger = get_logger(__name__)
                self.logger.warning(f"GLM客户端初始化失败: {e}，将使用传统报告生成")
        else:
            self.glm_client = None
            self.logger = get_logger(__name__)
            self.logger.info("GLM API密钥未配置，将使用传统报告生成")
    
    async def generate_deviation_report(self, user_name: str, analyses: List[Dict[str, Any]], 
                                      format_type: str = "detailed") -> Dict[str, Any]:
        """
        生成偏离汇报
        
        Args:
            user_name: 用户名
            analyses: 分析结果列表
            format_type: 汇报格式类型 (simple/detailed/card)
        
        Returns:
            包含success和content字段的字典
        """
        try:
            if not analyses:
                self.logger.warning(f"用户 {user_name} 没有分析数据，无法生成汇报")
                return {"success": False, "content": "", "error": "没有分析数据"}
            
            # 聚合分析数据
            report_data = self._aggregate_analysis_data(user_name, analyses)
            
            # 根据格式类型生成报告
            content = ""
            if format_type == "simple":
                content = self._generate_simple_report(report_data)
            elif format_type == "detailed":
                content = self._generate_detailed_report(report_data)
            elif format_type == "card":
                content = self._generate_card_report(report_data)
            else:
                self.logger.warning(f"未知的汇报格式类型: {format_type}，使用详细型格式")
                content = self._generate_detailed_report(report_data)
            
            return {"success": True, "content": content, "format_type": format_type}
            
        except Exception as e:
            self.logger.error(f"生成汇报失败: {e}")
            return {"success": False, "content": "", "error": str(e)}
    
    def _aggregate_analysis_data(self, user_name: str, analyses: List[Dict[str, Any]]) -> ReportData:
        """
        聚合分析数据
        
        Args:
            user_name: 用户名
            analyses: 分析结果列表
        
        Returns:
            聚合后的汇报数据
        """
        if not analyses:
            raise ValueError("分析数据不能为空")
        
        # 计算统计数据
        deviation_scores = [a.get('deviation_score', 0) for a in analyses]
        completion_rates = [a.get('completion_rate', 0) for a in analyses]
        
        avg_deviation_score = sum(deviation_scores) / len(deviation_scores)
        avg_completion_rate = sum(completion_rates) / len(completion_rates)
        max_deviation_score = max(deviation_scores)
        min_deviation_score = min(deviation_scores)
        
        # 收集偏离原因和建议
        all_reasons = []
        all_suggestions = []
        
        for analysis in analyses:
            reasons = analysis.get('deviation_reasons', [])
            suggestions = analysis.get('suggestions', [])
            
            if isinstance(reasons, list):
                all_reasons.extend(reasons)
            if isinstance(suggestions, list):
                all_suggestions.extend(suggestions)
        
        # 去重并保持顺序
        unique_reasons = list(dict.fromkeys(all_reasons))
        unique_suggestions = list(dict.fromkeys(all_suggestions))
        
        # 生成趋势分析
        trend_analysis = self._analyze_trend(deviation_scores)
        
        # 确定影响程度
        impact_level = self._determine_impact_level(avg_deviation_score, len(analyses))
        
        return ReportData(
            user_name=user_name,
            analyses=analyses,
            continuous_days=len(analyses),
            avg_deviation_score=avg_deviation_score,
            avg_completion_rate=avg_completion_rate,
            max_deviation_score=max_deviation_score,
            min_deviation_score=min_deviation_score,
            deviation_reasons=unique_reasons[:5],  # 最多显示5个原因
            suggestions=unique_suggestions[:5],    # 最多显示5个建议
            trend_analysis=trend_analysis,
            impact_level=impact_level,
            timestamp=datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        )
    
    def _analyze_trend(self, scores: List[float]) -> str:
        """
        分析偏离度趋势
        
        Args:
            scores: 偏离度评分列表
        
        Returns:
            趋势分析文本
        """
        if len(scores) < 2:
            return "数据不足，无法分析趋势"
        
        # 计算趋势
        if scores[-1] > scores[0]:
            if scores[-1] - scores[0] > 1.0:
                return "偏离度呈明显上升趋势，情况正在恶化"
            else:
                return "偏离度略有上升，需要关注"
        elif scores[-1] < scores[0]:
            if scores[0] - scores[-1] > 1.0:
                return "偏离度呈下降趋势，情况有所改善"
            else:
                return "偏离度略有下降，但仍需持续关注"
        else:
            return "偏离度保持稳定，但持续偏离需要重视"
    
    def _determine_impact_level(self, avg_score: float, days: int) -> str:
        """
        确定影响程度
        
        Args:
            avg_score: 平均偏离度评分
            days: 连续天数
        
        Returns:
            影响程度描述
        """
        if avg_score >= 7.0 or days >= 5:
            return "高风险"
        elif avg_score >= 5.0 or days >= 3:
            return "中风险"
        else:
            return "低风险"
    
    def _generate_simple_report(self, data: ReportData) -> str:
        """
        生成简洁型汇报
        
        Args:
            data: 汇报数据
        
        Returns:
            简洁型汇报内容
        """
        reasons_text = "\n• ".join(data.deviation_reasons[:3]) if data.deviation_reasons else "暂无明确原因"
        suggestions_text = "\n• ".join(data.suggestions[:3]) if data.suggestions else "暂无具体建议"
        
        return f"""📊 **工作状态预警通知**

**相关人员**：@{data.user_name}
**预警时间**：{data.timestamp}
**影响程度**：{data.impact_level}

**核心问题**：
• {reasons_text}

**改进建议**：
• {suggestions_text}

**关键数据**：连续{data.continuous_days}天偏离，平均完成率{data.avg_completion_rate*100:.0f}%

{data.trend_analysis}，请及时关注并采取改进措施。"""
    
    def _generate_detailed_report(self, data: ReportData) -> str:
        """
        生成详细型汇报
        
        Args:
            data: 汇报数据
        
        Returns:
            详细型汇报内容
        """
        # 生成核心问题列表
        core_issues = "\n• ".join(data.deviation_reasons[:3]) if data.deviation_reasons else "工作执行与计划存在偏差"
        
        # 生成改进建议
        suggestions_list = "\n• ".join(data.suggestions[:4]) if data.suggestions else "建议重新评估工作计划和优先级"
        
        return f"""🚨 **工作执行偏离详细报告**

**相关人员**：@{data.user_name}
**报告时间**：{data.timestamp}
**预警级别**：{data.impact_level}
**分析周期**：最近{data.continuous_days}个工作日

**偏离情况概述**：
连续{data.continuous_days}天出现工作偏离，平均完成率{data.avg_completion_rate*100:.0f}%，{data.trend_analysis}。

**核心问题**：
• {core_issues}

**改进建议**：
• {suggestions_list}

**风险提示**：
连续偏离表明存在系统性问题，建议管理层重点关注并制定针对性改进措施。如不及时处理，可能影响整体项目进度和团队效率。

**后续跟进**：
建议在3个工作日内制定改进计划，并在一周内开始实施相关措施。"""
    
    def _generate_card_report(self, data: ReportData) -> str:
        """
        生成卡片型汇报
        
        Args:
            data: 汇报数据
        
        Returns:
            卡片型汇报内容
        """
        core_issues = "\n".join([f"• {reason}" for reason in data.deviation_reasons[:3]])
        if not core_issues:
            core_issues = "• 工作执行与计划存在偏差"
        
        quick_suggestions = "\n".join([f"• {suggestion}" for suggestion in data.suggestions[:3]])
        if not quick_suggestions:
            quick_suggestions = "• 重新评估工作计划和优先级"
        
        return f"""📋 **工作状态监控提醒**

🚨 检测到连续工作偏离情况

**关键信息**：
偏离天数：{data.continuous_days}天 | 影响程度：{data.impact_level} | 完成率：{data.avg_completion_rate*100:.0f}%

**核心问题**：
{core_issues}

**快速建议**：
{quick_suggestions}

**需要关注**：@{data.user_name}

**趋势分析**：{data.trend_analysis}

{data.timestamp}"""
    
    def _generate_reasons_analysis(self, reasons: List[str]) -> str:
        """
        生成偏离原因分析
        
        Args:
            reasons: 偏离原因列表
        
        Returns:
            原因分析文本
        """
        if not reasons:
            return "暂未识别到明确的偏离原因，建议进一步分析工作流程和执行情况。"
        
        analysis_parts = []
        for i, reason in enumerate(reasons, 1):
            analysis_parts.append(f"{i}. **{reason}**：这是导致工作偏离的重要因素之一")
        
        return "\n".join(analysis_parts)
    
    def _generate_personal_report(self, data: ReportData) -> str:
        """
        生成个人类型报告
        
        Args:
            data: 汇报数据
        
        Returns:
            个人报告内容
        """
        # 生成核心问题列表
        core_issues = "\n• ".join(data.deviation_reasons[:3]) if data.deviation_reasons else "工作执行与计划存在偏差"
        
        # 生成改进建议
        suggestions_list = "\n• ".join(data.suggestions[:4]) if data.suggestions else "建议重新评估工作计划和优先级"
        
        return f"""🚨 **工作执行偏离详细报告**

**相关人员**：@{data.user_name}
**报告时间**：{data.timestamp}
**预警级别**：{data.impact_level}
**分析周期**：最近{data.continuous_days}个工作日

**偏离情况概述**：
连续{data.continuous_days}天出现工作偏离，平均完成率{data.avg_completion_rate*100:.0f}%，{data.trend_analysis}。

**核心问题**：
• {core_issues}

**改进建议**：
• {suggestions_list}

**风险提示**：
连续偏离表明存在系统性问题，建议管理层重点关注并制定针对性改进措施。如不及时处理，可能影响整体项目进度和团队效率。

**后续跟进**：
建议在3个工作日内制定改进计划，并在一周内开始实施相关措施。"""
    
    def _generate_management_report(self, data: ReportData) -> str:
        """
        生成管理层类型报告
        
        Args:
            data: 汇报数据
        
        Returns:
            管理层报告内容
        """
        # 生成核心问题列表（更简洁）
        core_issues = "\n• ".join(data.deviation_reasons[:2]) if data.deviation_reasons else "团队成员工作执行偏离"
        
        # 生成管理建议（更关注资源配置和团队管理）
        management_suggestions = []
        if data.suggestions:
            for suggestion in data.suggestions[:3]:
                if "会议" in suggestion:
                    management_suggestions.append("优化会议安排，减少不必要的会议冲突")
                elif "出差" in suggestion:
                    management_suggestions.append("完善出差支持流程，提供必要的远程工作工具")
                elif "事故" in suggestion:
                    management_suggestions.append("建立应急响应机制，减少突发事件对正常工作的影响")
                else:
                    management_suggestions.append(suggestion)
        
        if not management_suggestions:
            management_suggestions = ["重新评估团队资源配置", "优化工作流程和任务分配"]
        
        suggestions_text = "\n• ".join(management_suggestions[:3])
        
        return f"""📊 **团队工作状态管理报告**

**团队成员**：@{data.user_name}
**报告时间**：{data.timestamp}
**风险等级**：{data.impact_level}
**监控周期**：{data.continuous_days}个工作日

**状态概览**：
团队成员连续{data.continuous_days}天工作偏离，平均完成率{data.avg_completion_rate*100:.0f}%，{data.trend_analysis}。

**主要影响因素**：
• {core_issues}

**管理建议**：
• {suggestions_text}

**资源需求评估**：
当前偏离情况可能需要额外的管理支持和资源调配。建议评估团队工作负荷分配，必要时进行任务重新分配或增加支持资源。

**管理行动**：
建议管理层在2个工作日内与相关人员沟通，了解具体困难并提供必要支持。同时评估是否需要调整项目时间线或资源配置。"""
    
    async def generate_batch_reports(self, users_data: Dict[str, List[Dict[str, Any]]], 
                                   format_type: str = "detailed") -> Dict[str, str]:
        """
        批量生成多个用户的偏离汇报
        
        Args:
            users_data: 用户数据字典，key为用户名，value为分析结果列表
            format_type: 汇报格式类型
        
        Returns:
            用户汇报字典，key为用户名，value为汇报内容
        """
        reports = {}
        
        for user_name, analyses in users_data.items():
            try:
                report = await self.generate_deviation_report(user_name, analyses, format_type)
                reports[user_name] = report
                self.logger.info(f"成功生成用户 {user_name} 的偏离汇报")
            except Exception as e:
                self.logger.error(f"生成用户 {user_name} 的偏离汇报失败: {e}")
                reports[user_name] = f"汇报生成失败: {str(e)}"
        
        return reports
    
    def generate_llm_report(self, user_name: str, analyses: List[Dict[str, Any]], 
                                 report_type: str = "personal") -> Dict[str, Any]:
        """
        使用LLM动态生成个性化报告内容
        
        Args:
            user_name: 用户名
            analyses: 分析结果列表
            report_type: 报告类型 (personal/management)
        
        Returns:
            包含success和content字段的字典
        """
        try:
            if not analyses:
                self.logger.warning(f"用户 {user_name} 没有分析数据，无法生成LLM报告")
                return {"success": False, "content": "", "error": "没有分析数据"}
            
            if not self.glm_client:
                self.logger.warning("GLM客户端未配置，降级到传统报告生成")
                report_data = self._aggregate_analysis_data(user_name, analyses)
                if report_type == "management":
                    traditional_content = self._generate_management_report(report_data)
                else:
                    traditional_content = self._generate_personal_report(report_data)
                return {"success": True, "content": traditional_content, "format_type": "traditional"}
            
            # 聚合分析数据
            report_data = self._aggregate_analysis_data(user_name, analyses)
            
            # 构建LLM提示词
            system_prompt, user_prompt = self._build_llm_prompts(report_data, report_type)
            
            # 调用LLM生成报告
            llm_content = self.glm_client._call_glm_api_sync(
                system_prompt=system_prompt,
                user_prompt=user_prompt,
                temperature=0.7
            )
            
            self.logger.info(f"成功使用LLM生成用户 {user_name} 的{report_type}报告")
            return {"success": True, "content": llm_content, "format_type": "llm_generated"}
            
        except Exception as e:
            self.logger.error(f"LLM报告生成失败: {e}，降级到传统报告")
            # 降级到传统报告生成
            report_data = self._aggregate_analysis_data(user_name, analyses)
            if report_type == "management":
                traditional_content = self._generate_management_report(report_data)
            else:
                traditional_content = self._generate_personal_report(report_data)
            return {"success": True, "content": traditional_content, "format_type": "traditional"}
    
    def _build_llm_prompts(self, report_data: ReportData, report_type: str) -> tuple[str, str]:
        """
        构建LLM提示词
        
        Args:
            report_data: 汇报数据
            report_type: 报告类型 (personal/management)
        
        Returns:
            (system_prompt, user_prompt) 元组
        """
        if report_type == "management":
            system_prompt = """
你是一位高效的管理层助理，专门为管理者提供简洁的团队状态摘要。

核心要求：
1. 内容必须控制在150字以内
2. 聚焦管理决策：风险等级、影响范围、需要的管理行动
3. 使用管理层语言：数据驱动、结果导向、行动明确
4. 格式简洁：关键信息+风险评估+管理建议

禁止：
- 详细的技术细节或个人情感描述
- 超过150字的内容
- 重复或冗余信息
"""
            
            user_prompt = f"""
团队成员：{report_data.user_name}
偏离状况：连续{report_data.continuous_days}天，完成率{report_data.avg_completion_rate*100:.0f}%
影响等级：{report_data.impact_level}
主要原因：{', '.join(report_data.deviation_reasons[:2])}

请生成150字以内的管理层通知，包含：
1. 风险评估（1句话）
2. 业务影响（1句话）
3. 管理行动建议（1-2句话）

格式要求：简洁、数据化、行动导向。
"""
        else:  # personal
            system_prompt = """
你是一位温暖的工作效率顾问，帮助个人改善工作状态。

核心要求：
1. 内容必须控制在200字以内
2. 语调温暖鼓励，避免批评或指责
3. 提供2-3个具体可行的改进建议
4. 关注个人成长和能力提升

禁止：
- 超过200字的内容
- 过于详细的分析或重复信息
- 消极或批评性语言
"""
            
            user_prompt = f"""
{report_data.user_name}，你好！

最近状况：连续{report_data.continuous_days}天工作偏离，完成率{report_data.avg_completion_rate*100:.0f}%
主要困难：{', '.join(report_data.deviation_reasons[:2])}
趋势：{report_data.trend_analysis}

请生成200字以内的个人改进建议，包含：
1. 理解和鼓励（1句话）
2. 2-3个具体改进方法
3. 积极的结尾鼓励

语调要温暖、具体、可操作。
"""
        
        return system_prompt, user_prompt
    
    async def enhance_report_with_ai(self, basic_report: str, user_name: str) -> str:
        """
        使用AI增强汇报内容
        
        Args:
            basic_report: 基础汇报内容
            user_name: 用户名
        
        Returns:
            AI增强后的汇报内容
        """
        if not self.glm_client:
            self.logger.warning("GLM客户端未配置，跳过AI增强")
            return basic_report
        
        try:
            enhancement_prompt = f"""
请基于以下工作偏离汇报，提供更深入的分析和建议：

{basic_report}

请从以下角度进行增强：
1. 深层原因分析
2. 具体可执行的改进措施
3. 预防类似问题的长期策略
4. 时间管理和优先级建议

请保持原有格式，在相应部分添加更详细的内容。
"""
            
            enhanced_content = await self.glm_client._call_glm_api(
                system_prompt="你是一位专业的工作效率分析师，擅长分析工作偏离问题并提供实用建议。",
                user_prompt=enhancement_prompt,
                temperature=0.7
            )
            
            self.logger.info(f"成功使用AI增强用户 {user_name} 的汇报")
            return enhanced_content
            
        except Exception as e:
            self.logger.error(f"AI增强汇报失败: {e}")
            return basic_report