"""
GLM-4.5模型客户端模块
负责与智谱AI GLM-4.5模型的交互
"""

import logging
import asyncio
from typing import Optional, Dict, Any
from dataclasses import dataclass
from datetime import datetime

from zhipuai import ZhipuAI
from zhipuai.core._errors import APIStatusError, APITimeoutError

from src.config import GLMConfig
from .langfuse_client import langfuse_client


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
    
    def _get_prompt_from_langfuse(self, prompt_name: str, variables: Dict[str, Any]) -> Optional[Dict[str, str]]:
        """从Langfuse获取提示词"""
        if not langfuse_client.is_available():
            return None
        
        return langfuse_client.get_prompt(prompt_name, variables)
    
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
        
        # 准备模板变量
        variables = {
            'daily_summary': daily_summary if daily_summary and daily_summary.strip() else '未提供日报内容',
            'daily_plan': daily_plan if daily_plan and daily_plan.strip() else '未提供日计划内容',
            'analysis_date': datetime.now().strftime('%Y-%m-%d'),
            'analysis_time': datetime.now().strftime('%H:%M:%S')
        }
        
        # 尝试从Langfuse获取提示词
        prompts = self._get_prompt_from_langfuse('daily_report_analysis', variables)
        
        if prompts:
            # 使用Langfuse提示词
            system_prompt = prompts['system_prompt']
            user_prompt = prompts['user_prompt']
            self.logger.info("使用Langfuse提示词进行日报分析")
        else:
            # 降级到硬编码提示词
            system_prompt = """
【角色】日报审核助手
【任务】分析日报内容，指出不清晰之处，并判断工作是否偏离当天计划

【分析要求】
1. 必须输出【内容问题】：指出日报中表述不清晰、缺乏具体细节的地方
2. 选择性输出【偏离判断】：只有当实际工作与计划存在明显偏离时才输出此部分

【输出格式】
- 始终输出【内容问题】部分
- 只有在存在明显偏离时才输出【偏离判断】部分
- 如果工作基本按计划执行，则不输出【偏离判断】部分

【内容问题】
- [直接指出不清晰的具体问题]
- [直接指出不清晰的具体问题]
...

【偏离判断】（仅在存在明显偏离时输出）
[分析偏离情况]
"""
            
            user_prompt = f"""
【日计划】
{variables['daily_plan']}

【日报】
{variables['daily_summary']}

分析指示：
1. 必须输出【内容问题】部分
2. 评估是否存在明显偏离：
   - 如果工作基本按计划执行，则只输出【内容问题】部分，不要输出【偏离判断】部分
   - 如果存在明显偏离，则同时输出【内容问题】和【偏离判断】两个部分"""
            self.logger.info("使用降级提示词进行日报分析")
        
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
    
    async def analyze_daily_plan_content(self, daily_plan: str, weekly_plan: str = "") -> str:
        """
        分析日计划内容，重点关注计划合理性和与周计划的一致性
        
        Args:
            daily_plan: 日计划内容
            weekly_plan: 周计划内容
            
        Returns:
            str: 日计划分析结果
        """
        self.logger.info("正在进行日计划内容分析...")
        
        # 准备模板变量
        variables = {
            'daily_plan': daily_plan if daily_plan.strip() else '未提供日计划内容',
            'weekly_plan': weekly_plan if weekly_plan.strip() else '未提供周计划内容',
            'analysis_date': datetime.now().strftime('%Y-%m-%d'),
            'analysis_time': datetime.now().strftime('%H:%M:%S')
        }
        
        # 尝试从Langfuse获取提示词
        prompts = self._get_prompt_from_langfuse('daily_plan_analysis', variables)
        
        if prompts:
            # 使用Langfuse提示词
            system_prompt = prompts['system_prompt']
            user_prompt = prompts['user_prompt']
            self.logger.info("使用Langfuse提示词进行日计划分析")
        else:
            # 降级到硬编码提示词
            system_prompt = """
【角色】计划管理助手
【任务】分析日计划内容，指出目标不明确之处

【分析要求】
1. 必须输出【目标明确性】：指出日计划中目标不够明确、缺乏具体细节的地方
2. 严格禁止输出任何关于方向一致性的内容

【输出格式】
- 只输出【目标明确性】部分
- 禁止输出任何关于方向、一致性、偏离的内容
- 分析完目标明确性后立即结束

【目标明确性】
- [直接指出不明确的具体问题]
- [直接指出不明确的具体问题]
...

【严格禁令】：绝对不要输出任何关于方向一致性、偏离判断、与周计划关系的内容！分析完目标明确性后立即停止！
"""
            
            user_prompt = f"""
【日计划】
{variables['daily_plan']}

分析要求：
1. 只分析【目标明确性】：直接指出每个任务缺乏具体细节的地方
2. 分析完目标明确性后立即结束
3. 严格禁止：不要提及任何关于方向、一致性、偏离、周计划关系的内容

输出格式：
【目标明确性】
- [直接指出不明确的具体问题]
- [直接指出不明确的具体问题]

注意：分析完目标明确性后立即停止，不要添加任何其他内容！"""
            self.logger.info("使用降级提示词进行日计划分析")
        
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
