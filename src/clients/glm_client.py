"""
GLM-4.5模型客户端模块
负责与智谱AI GLM-4.5模型的交互
"""

import logging
import asyncio
import json
from typing import Dict, Any, Optional, List
from dataclasses import dataclass

from zhipuai import ZhipuAI
from zhipuai.core._errors import APIStatusError, APITimeoutError

from src.config import GLMConfig


@dataclass
class AnalysisPrompt:
    """分析提示词模板"""
    system_prompt: str
    user_prompt: str
    temperature: float = 0.7
    max_tokens: int = 2000


class GLMClient:
    """GLM-4.5客户端"""
    
    def __init__(self, config: GLMConfig):
        self.config = config
        self.logger = logging.getLogger(__name__)
        
        try:
            # 初始化智谱AI客户端
            self.client = ZhipuAI(
                api_key=config.api_key,
                base_url=config.base_url
            )
            
            self.logger.info("GLM-4.5客户端初始化成功")
            
        except Exception as e:
            self.logger.error(f"GLM-4.5客户端初始化失败: {e}")
            raise
            
    async def analyze_work_deviation(self, daily_summary: str, daily_plan: str) -> Dict[str, Any]:
        """
        分析工作偏离度
        
        Args:
            daily_summary: 日结内容
            daily_plan: 日计划内容
            
        Returns:
            Dict[str, Any]: 偏离度分析结果
        """
        self.logger.info("正在进行工作偏离度分析...")
        
        system_prompt = """你是一位专业的工作效率分析师。请分析用户的日报内容与日计划之间的偏离程度。

背景信息：
- 日报通常包含：当日完成的工作、进度情况、遇到的问题
- 日计划是之前制定的当日工作安排
- 需要评估实际执行与计划的符合程度

分析要求：
1. 对比日报中的实际完成工作与日计划的匹配度
2. 识别未完成的计划项目，分析可能原因（如遇到技术问题、临时任务等）
3. 发现额外完成的工作内容，评估其重要性
4. 评估偏离的合理性（如问题解决、优先级调整等）
5. 提供0-10分的偏离度评分（0分表示完全按计划执行，10分表示完全偏离计划）

请以JSON格式返回分析结果，包含以下字段：
- score: 偏离度评分(0-10)
- completion_rate: 计划完成率(0-1)
- deviation_reasons: 偏离原因列表
- additional_work: 额外完成的工作
- suggestions: 改进建议
- summary: 简要总结"""

        user_prompt = f"""请分析以下日报与日计划的偏离程度：

**日计划内容：**
{daily_plan if daily_plan.strip() else '未提供日计划内容'}

**日报内容：**
{daily_summary if daily_summary.strip() else '未提供日报内容'}

请按照要求进行详细分析，特别关注：
1. 计划中的任务是否完成
2. 遇到的问题是否影响了计划执行
3. 额外工作是否合理且重要
4. 整体工作效率和时间分配"""

        try:
            response = await self._call_glm_api(
                system_prompt=system_prompt,
                user_prompt=user_prompt,
                temperature=0.3  # 使用较低温度确保结果一致性
            )
            
            # 尝试解析JSON响应
            try:
                result = json.loads(response)
                self.logger.info("工作偏离度分析完成")
                return result
            except json.JSONDecodeError:
                # 如果无法解析JSON，返回包装的文本结果
                return {
                    'score': 5.0,
                    'completion_rate': 0.5,
                    'deviation_reasons': ['无法解析详细原因'],
                    'additional_work': [],
                    'suggestions': ['建议提供更清晰的计划和总结'],
                    'summary': response,
                    'raw_response': response
                }
                
        except Exception as e:
            self.logger.error(f"工作偏离度分析失败: {e}")
            return {
                'score': 0.0,
                'completion_rate': 0.0,
                'deviation_reasons': [f'分析失败: {str(e)}'],
                'additional_work': [],
                'suggestions': ['请检查输入内容并重试'],
                'summary': f'分析失败: {str(e)}',
                'error': str(e)
            }
    
    async def analyze_daily_report_content(self, daily_summary: str, daily_plan: str) -> str:
        """
        分析日报内容，重点关注工作完成情况和偏离分析
        
        Args:
            daily_summary: 日结内容
            daily_plan: 日计划内容
            
        Returns:
            str: 日报分析结果
        """
        self.logger.info("正在进行日报内容分析...")
        
        system_prompt = """你是一位专业的日报分析专家。请对用户的日报进行精准分析。

回复格式要求：
内容表述不清楚的地方：
如何澄清不清楚的内容：
当天工作是否偏离了日计划（若未偏离则不需要）：

分析要求：
1. 严格按照上述格式组织回复内容，每个部分只写一次
2. 避免重复表述相同的问题
3. 如果某个部分没有问题，写"无"
4. 保持简洁，不要展开详细说明
5. 每个问题点用一句话概括"""
        
        user_prompt = f"""请分析以下日报内容：

**日计划内容（参考）：**
{daily_plan if daily_plan and daily_plan.strip() else '未提供日计划内容'}

**日报内容：**
{daily_summary if daily_summary.strip() else '未提供日报内容'}

请按照指定格式进行分析和回复。"""
        
        try:
            response = await self._call_glm_api(
                system_prompt=system_prompt,
                user_prompt=user_prompt,
                temperature=0.3
            )
            
            return f"## 📊 日报分析\n\n{response}"
            
        except Exception as e:
            self.logger.error(f"日报分析失败: {e}")
            return f"## ❌ 日报分析失败\n\n错误信息: {str(e)}"
    
    async def analyze_daily_plan_content(self, daily_plan: str, weekly_plan: str) -> str:
        """
        分析日计划内容，重点关注计划合理性和与周计划的一致性
        
        Args:
            daily_plan: 日计划内容
            weekly_plan: 周计划内容
            
        Returns:
            str: 日计划分析结果
        """
        self.logger.info("正在进行日计划内容分析...")
        
        system_prompt = """你是一位专业的计划管理专家。请对用户的日计划进行精准分析。

分析要求：
1. 重点审核"目标内容"是否明确，若缺失则指出需要补充的信息
2. 当计划内容与既定方向出现偏差时提供提醒

注意：
- 避免冗长的分析，重点关注目标不明确或偏离方向的问题
- 如果计划目标明确且方向正确，无需详细说明
- 使用简洁、专业的语言"""
        
        user_prompt = f"""请分析以下日计划内容：

**周计划内容（参考）：**
{weekly_plan if weekly_plan and weekly_plan.strip() else '未提供周计划内容'}

**日计划内容：**
{daily_plan if daily_plan.strip() else '未提供日计划内容'}

请重点关注：
- "目标内容"是否明确
- 计划内容是否与既定方向出现偏差"""
        
        try:
            response = await self._call_glm_api(
                system_prompt=system_prompt,
                user_prompt=user_prompt,
                temperature=0.3
            )
            
            return f"## 📋 日计划分析\n\n{response}"
            
        except Exception as e:
            self.logger.error(f"日计划分析失败: {e}")
            return f"## ❌ 日计划分析失败\n\n错误信息: {str(e)}"
                
        except Exception as e:
            self.logger.error(f"工作偏离度分析失败: {e}")
            return {
                'score': 0.0,
                'completion_rate': 0.0,
                'deviation_reasons': [f'分析失败: {str(e)}'],
                'additional_work': [],
                'suggestions': ['请检查网络连接和API配置'],
                'summary': '分析失败',
                'error': str(e)
            }
            
    async def analyze_content_clarity(self, daily_summary: str) -> Dict[str, Any]:
        """
        分析内容清晰度
        
        Args:
            daily_summary: 日结内容
            
        Returns:
            Dict[str, Any]: 清晰度分析结果
        """
        self.logger.info("正在进行内容清晰度分析...")
        
        system_prompt = """你是一位专业的技术写作和沟通专家。请分析用户日报内容的清晰度、完整性和准确性。

分析维度：
1. 描述的具体性：是否包含具体的任务、进度、时间、结果
2. 表达的准确性：术语使用是否准确，逻辑是否清晰
3. 内容的完整性：是否包含工作内容、进度情况、遇到问题等关键信息
4. 可理解性：他人（如团队成员、领导）是否能够理解工作内容和成果
5. 专业性：是否符合工作日报的专业标准
6. 问题描述：遇到的问题是否描述清楚，是否提及解决方案

请以JSON格式返回分析结果，包含以下字段：
- clarity_score: 清晰度评分(0-10)
- specificity_score: 具体性评分(0-10)
- completeness_score: 完整性评分(0-10)
- unclear_parts: 不清晰的部分列表
- missing_info: 可能缺失的信息
- improvement_suggestions: 改进建议
- summary: 总体评价"""

        user_prompt = f"""请分析以下日报内容的清晰度：

**日报内容：**
{daily_summary if daily_summary.strip() else '未提供日报内容'}

请按照要求进行详细分析，特别关注：
1. 工作内容是否具体明确
2. 进度描述是否量化清晰
3. 遇到的问题是否详细说明
4. 是否便于他人理解和跟进"""

        try:
            response = await self._call_glm_api(
                system_prompt=system_prompt,
                user_prompt=user_prompt,
                temperature=0.3
            )
            
            try:
                result = json.loads(response)
                self.logger.info("内容清晰度分析完成")
                return result
            except json.JSONDecodeError:
                return {
                    'clarity_score': 5.0,
                    'specificity_score': 5.0,
                    'completeness_score': 5.0,
                    'unclear_parts': ['无法解析详细分析'],
                    'missing_info': ['分析结果解析失败'],
                    'improvement_suggestions': ['建议重新分析'],
                    'summary': response,
                    'raw_response': response
                }
                
        except Exception as e:
            self.logger.error(f"内容清晰度分析失败: {e}")
            return {
                'clarity_score': 0.0,
                'specificity_score': 0.0,
                'completeness_score': 0.0,
                'unclear_parts': [f'分析失败: {str(e)}'],
                'missing_info': ['分析过程中发生错误'],
                'improvement_suggestions': ['请检查网络连接和API配置'],
                'summary': '分析失败',
                'error': str(e)
            }
            
    async def analyze_plan_consistency(self, daily_plan: str, weekly_plan: str) -> Dict[str, Any]:
        """
        分析计划一致性
        
        Args:
            daily_plan: 日计划内容
            weekly_plan: 周期计划内容
            
        Returns:
            Dict[str, Any]: 一致性分析结果
        """
        self.logger.info("正在进行计划一致性分析...")
        
        system_prompt = """你是一位专业的项目管理和规划专家。请分析日计划与周期计划之间的一致性。

分析要点：
1. 目标对齐：日计划是否支持周期计划的目标
2. 优先级一致：重要任务的优先级是否匹配
3. 资源分配：时间和精力分配是否合理
4. 进度协调：日计划是否有助于周期计划的按时完成
5. 策略连贯：执行策略是否保持一致

请以JSON格式返回分析结果，包含以下字段：
- consistency_score: 一致性评分(0-10)
- alignment_level: 目标对齐程度(0-10)
- priority_match: 优先级匹配度(0-10)
- inconsistencies: 不一致的地方
- alignment_strengths: 对齐的优势
- recommendations: 改进建议
- summary: 一致性总结"""

        user_prompt = f"""请分析以下日计划与周期计划的一致性：

**周期计划（参考）：**
{weekly_plan if weekly_plan and weekly_plan.strip() else '未提供周期计划内容'}

**日计划：**
{daily_plan if daily_plan.strip() else '未提供日计划内容'}

请按照要求进行详细分析。"""

        try:
            response = await self._call_glm_api(
                system_prompt=system_prompt,
                user_prompt=user_prompt,
                temperature=0.3
            )
            
            try:
                result = json.loads(response)
                self.logger.info("计划一致性分析完成")
                return result
            except json.JSONDecodeError:
                return {
                    'consistency_score': 5.0,
                    'alignment_level': 5.0,
                    'priority_match': 5.0,
                    'inconsistencies': ['无法解析详细分析'],
                    'alignment_strengths': ['分析结果解析失败'],
                    'recommendations': ['建议重新分析'],
                    'summary': response,
                    'raw_response': response
                }
                
        except Exception as e:
            self.logger.error(f"计划一致性分析失败: {e}")
            return {
                'consistency_score': 0.0,
                'alignment_level': 0.0,
                'priority_match': 0.0,
                'inconsistencies': [f'分析失败: {str(e)}'],
                'alignment_strengths': [],
                'recommendations': ['请检查网络连接和API配置'],
                'summary': '分析失败',
                'error': str(e)
            }
            
    async def _call_glm_api(self, system_prompt: str, user_prompt: str, temperature: Optional[float] = None) -> str:
        """
        调用GLM API
        
        Args:
            system_prompt: 系统提示词
            user_prompt: 用户提示词
            temperature: 温度参数
            
        Returns:
            str: API响应内容
        """
        if temperature is None:
            temperature = self.config.temperature
            
        try:
            response = self.client.chat.completions.create(
                model=self.config.model,
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_prompt}
                ],
                temperature=temperature,
                max_tokens=self.config.max_tokens,
                top_p=self.config.top_p
            )
            
            return response.choices[0].message.content
            
        except APITimeoutError as e:
            self.logger.error(f"GLM API调用超时: {e}")
            raise
        except APIStatusError as e:
            self.logger.error(f"GLM API调用错误: {e}")
            raise
        except Exception as e:
            self.logger.error(f"GLM API调用失败: {e}")
            raise
            
    async def test_connection(self) -> bool:
        """
        测试GLM API连接
        
        Returns:
            bool: 连接是否成功
        """
        try:
            test_response = await self._call_glm_api(
                system_prompt="你是一个测试助手。",
                user_prompt="请回复'连接测试成功'。",
                temperature=0.1
            )
            
            self.logger.info("GLM API连接测试成功")
            return True
            
        except Exception as e:
            self.logger.error(f"GLM API连接测试失败: {e}")
            return False
            
    async def generate_comprehensive_analysis(self, 
                                            daily_summary: str, 
                                            daily_plan: str, 
                                            weekly_plan: str = "") -> str:
        """
        生成简化的综合分析报告
        
        Args:
            daily_summary: 日结内容
            daily_plan: 日计划内容
            weekly_plan: 周期计划内容
            
        Returns:
            str: 简化的分析报告
        """
        self.logger.info("正在生成综合分析报告...")
        
        if not daily_summary and not daily_plan:
            return "## ⚠️ 分析失败\n\n无足够内容进行分析，请确保提供了日结或日计划内容。"
            
        try:
            # 使用简化的分析逻辑
            report = await self._generate_simple_analysis(daily_summary, daily_plan, weekly_plan)
            
            self.logger.info("综合分析报告生成完成")
            return report
            
        except Exception as e:
            self.logger.error(f"生成综合分析报告失败: {e}")
            return f"## ❌ 分析报告生成失败\n\n错误信息: {str(e)}"
            
    async def _generate_simple_analysis(self, daily_summary: str, daily_plan: str, weekly_plan: str) -> str:
        """
        生成简化的分析报告，包含四个要点：
        1. 哪些内容不清楚
        2. 如何澄清
        3. 工作是否偏离
        4. 日计划是否偏离周计划
        """
        system_prompt = """你是一位专业的工作分析师。请对用户的日结、日计划和周计划进行简洁分析，回答以下四个问题：

1. 哪些内容表述不清楚？
2. 如何澄清这些不清楚的内容？
3. 当天工作是否偏离了日计划？
4. 日计划是否偏离了周计划？

请用简洁明了的语言回答，重点关注计划的一致性和执行情况。"""
        
        user_prompt = f"""请分析以下内容：

**周期计划（参考）：**
{weekly_plan if weekly_plan and weekly_plan.strip() else '未提供周期计划内容'}

**日计划内容：**
{daily_plan if daily_plan.strip() else '未提供日计划内容'}

**日结内容：**
{daily_summary if daily_summary.strip() else '未提供日结内容'}

请简洁回答上述四个问题，特别关注：
- 日计划与周计划的目标是否一致
- 日计划的优先级是否合理
- 实际工作与日计划的偏离情况"""
        
        try:
            response = await self._call_glm_api(
                system_prompt=system_prompt,
                user_prompt=user_prompt,
                temperature=0.3
            )
            
            return f"## 📋 工作分析\n\n{response}"
            
        except Exception as e:
            self.logger.error(f"简化分析失败: {e}")
            return f"## ❌ 分析失败\n\n{str(e)}"
            
    def _generate_markdown_report(self, results: List[Any], daily_summary: str, daily_plan: str, weekly_plan: str) -> str:
        """生成Markdown格式的分析报告"""
        from datetime import datetime
        
        report_lines = [
            f"## 📊 每日工作分析报告 - {datetime.now().strftime('%Y-%m-%d')}",
            ""
        ]
        
        # 处理偏离度分析结果
        if len(results) > 0 and isinstance(results[0], dict) and 'score' in results[0]:
            deviation_result = results[0]
            report_lines.extend([
                "### 🎯 工作偏离度评估",
                f"**评分**: {deviation_result.get('score', 0):.1f}/10",
                f"**计划完成率**: {deviation_result.get('completion_rate', 0)*100:.1f}%",
                ""
            ])
            
            if deviation_result.get('deviation_reasons'):
                report_lines.append("**偏离原因:**")
                for reason in deviation_result['deviation_reasons'][:3]:  # 最多显示3个
                    report_lines.append(f"- {reason}")
                report_lines.append("")
                
            if deviation_result.get('suggestions'):
                report_lines.append("**改进建议:**")
                for suggestion in deviation_result['suggestions'][:2]:  # 最多显示2个
                    report_lines.append(f"- 💡 {suggestion}")
                report_lines.append("")
                
        # 处理清晰度分析结果
        clarity_index = 1 if len(results) > 1 else 0
        if len(results) > clarity_index and isinstance(results[clarity_index], dict):
            clarity_result = results[clarity_index]
            if 'clarity_score' in clarity_result:
                report_lines.extend([
                    "### 📝 内容清晰度分析",
                    f"**清晰度评分**: {clarity_result.get('clarity_score', 0):.1f}/10",
                    f"**具体性评分**: {clarity_result.get('specificity_score', 0):.1f}/10",
                    f"**完整性评分**: {clarity_result.get('completeness_score', 0):.1f}/10",
                    ""
                ])
                
                if clarity_result.get('improvement_suggestions'):
                    report_lines.append("**改进建议:**")
                    for suggestion in clarity_result['improvement_suggestions'][:2]:
                        report_lines.append(f"- 💡 {suggestion}")
                    report_lines.append("")
                    
        # 处理一致性分析结果
        consistency_index = 2 if len(results) > 2 else (1 if len(results) > 1 and weekly_plan else -1)
        if consistency_index >= 0 and len(results) > consistency_index and isinstance(results[consistency_index], dict):
            consistency_result = results[consistency_index]
            if 'consistency_score' in consistency_result:
                report_lines.extend([
                    "### 🔄 计划一致性分析",
                    f"**一致性评分**: {consistency_result.get('consistency_score', 0):.1f}/10",
                    f"**目标对齐度**: {consistency_result.get('alignment_level', 0):.1f}/10",
                    ""
                ])
                
                if consistency_result.get('recommendations'):
                    report_lines.append("**优化建议:**")
                    for rec in consistency_result['recommendations'][:2]:
                        report_lines.append(f"- 💡 {rec}")
                    report_lines.append("")
                    
        # 添加数据摘要
        report_lines.extend([
            "---",
            "### 📋 数据摘要",
            f"- 日结内容长度: {len(daily_summary)} 字符" if daily_summary else "- 日结内容: 未提供",
            f"- 日计划长度: {len(daily_plan)} 字符" if daily_plan else "- 日计划: 未提供",
            f"- 周期计划长度: {len(weekly_plan)} 字符" if weekly_plan else "- 周期计划: 未提供",
            ""
        ])
        
        return "\n".join(report_lines)
