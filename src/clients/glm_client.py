"""
GLM-4.5模型客户端模块
负责与智谱AI GLM-4.5模型的交互
"""

import logging
import asyncio
from typing import Optional
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
        
        system_prompt = """请分析下面的日报内容：

找出写得不清晰的地方，直接给点评，像同事读日报时随手批注。

在点评里顺带给出修改或补充建议。

对照日计划，如果日报里遗漏或没做到，就顺手指出来；如果没有偏离，不要提偏离。

输出风格要自然，像人说话，不要列表化或过度格式化。"""
        
        user_prompt = f"""日计划：{daily_plan if daily_plan and daily_plan.strip() else '未提供日计划内容'}

日报：{daily_summary if daily_summary.strip() else '未提供日报内容'}"""
        
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
