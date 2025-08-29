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
        self.glm_client = GLMClient(config.glm) if hasattr(config, 'glm') else None
        self.logger = get_logger(__name__)
    
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
        reasons_text = "\n  - ".join(data.deviation_reasons) if data.deviation_reasons else "暂无明确原因"
        suggestions_text = "\n".join(data.suggestions) if data.suggestions else "暂无具体建议"
        
        return f"""# 📊 工作状态预警汇报

**预警时间**：{data.timestamp}
**预警类型**：连续偏离检测
**相关人员**：@{data.user_name}

## 📈 偏离趋势分析
- **连续偏离天数**：{data.continuous_days}天
- **平均偏离度**：{data.avg_deviation_score:.1f}/10
- **影响程度**：{data.impact_level}
- **主要偏离原因**：
  - {reasons_text}

## 💡 改进建议
{suggestions_text}

## 📊 关键指标
- 平均完成率：{data.avg_completion_rate*100:.1f}%
- 趋势分析：{data.trend_analysis}

---
*本报告由 GitHub Discussions 自动化分析服务生成*"""
    
    def _generate_detailed_report(self, data: ReportData) -> str:
        """
        生成详细型汇报
        
        Args:
            data: 汇报数据
        
        Returns:
            详细型汇报内容
        """
        # 生成偏离情况表格
        table_rows = []
        for i, analysis in enumerate(data.analyses):
            date = analysis.get('analysis_date', f'第{i+1}天')
            score = analysis.get('deviation_score', 0)
            completion = analysis.get('completion_rate', 0) * 100
            reasons = ', '.join(analysis.get('deviation_reasons', [])[:2])  # 只显示前2个原因
            if not reasons:
                reasons = '无明确原因'
            
            table_rows.append(f"| {date} | {score:.1f} | {completion:.1f}% | {reasons} |")
        
        deviation_table = "\n".join(table_rows)
        
        # 生成原因分析
        reasons_analysis = self._generate_reasons_analysis(data.deviation_reasons)
        
        # 生成建议
        short_term_suggestions = "\n".join([f"- {s}" for s in data.suggestions[:3]])
        long_term_suggestions = "\n".join([f"- {s}" for s in data.suggestions[3:]])
        
        if not short_term_suggestions:
            short_term_suggestions = "- 建议加强日常工作计划的制定和执行"
        if not long_term_suggestions:
            long_term_suggestions = "- 建议建立更完善的工作流程和监控机制"
        
        return f"""# 🚨 工作执行偏离预警报告

## 基本信息
- **报告生成时间**：{data.timestamp}
- **分析周期**：最近{data.continuous_days}个工作日
- **预警级别**：{data.impact_level}
- **相关人员**：@{data.user_name}

## 偏离情况统计
| 日期 | 偏离度评分 | 完成率 | 主要偏离原因 |
|------|------------|--------|-------------|
{deviation_table}

## 趋势分析
### 📊 偏离度变化趋势
{data.trend_analysis}

### 🎯 完成率统计
- 平均完成率：{data.avg_completion_rate*100:.1f}%
- 最低完成率：{data.min_deviation_score*10:.1f}%
- 完成率趋势：{'持续偏低' if data.avg_completion_rate < 0.7 else '基本正常'}

## 深度分析
### 🔍 偏离原因分析
{reasons_analysis}

### ⚡ 影响因素识别
连续{data.continuous_days}天的偏离表明存在系统性问题，需要从根本上分析和解决。

## 改进建议
### 🎯 短期改进措施
{short_term_suggestions}

### 📈 长期优化方向
{long_term_suggestions}

## 统计摘要
- **总分析天数**：{data.continuous_days}天
- **平均偏离度**：{data.avg_deviation_score:.1f}/10
- **最高偏离度**：{data.max_deviation_score:.1f}/10
- **最低偏离度**：{data.min_deviation_score:.1f}/10

---
*本报告由 GitHub Discussions 自动化分析服务生成*"""
    
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
        
        return f"""# 📋 工作状态监控卡片

> 🚨 **检测到连续工作偏离情况**

## 📊 关键指标
```
偏离天数: {data.continuous_days}天
平均偏离度: {data.avg_deviation_score:.1f}/10
影响程度: {data.impact_level}
完成率: {data.avg_completion_rate*100:.1f}%
```

## 🎯 核心问题
{core_issues}

## 💡 快速建议
{quick_suggestions}

## 👤 需要关注
@{data.user_name}

## 📈 趋势
{data.trend_analysis}

---
📅 {data.timestamp} | 🤖 自动生成"""
    
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