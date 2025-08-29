"""增强版GLM客户端
支持双次对话获取结构化数据
"""

import json
import logging
import asyncio
from typing import Optional, Dict, Any, Tuple
from dataclasses import dataclass
from datetime import datetime

from zhipuai import ZhipuAI
from zhipuai.core._errors import APIStatusError, APITimeoutError

from src.config import GLMConfig
from .langfuse_client import langfuse_client
from ..models.data_models import DeviationAnalysisResult
from ..utils.logger import get_logger


@dataclass
class DualConversationResult:
    """双次对话结果"""
    text_analysis: str
    structured_data: Dict[str, Any]
    success: bool
    error_message: Optional[str] = None


class EnhancedGLMClient:
    """增强版GLM客户端，支持双次对话"""
    
    def __init__(self, config: GLMConfig):
        self.config = config
        self.logger = get_logger(__name__)
        
        try:
            # 初始化智谱AI客户端
            self.client = ZhipuAI(
                api_key=config.api_key,
                base_url=config.base_url
            )
            
            self.logger.info("增强版GLM客户端初始化成功")
            
        except Exception as e:
            self.logger.error(f"增强版GLM客户端初始化失败: {e}")
            raise
    
    def _get_prompt_from_langfuse(self, prompt_name: str, variables: Dict[str, Any]) -> Optional[Dict[str, str]]:
        """从Langfuse获取提示词"""
        if not langfuse_client.is_available():
            return None
        
        return langfuse_client.get_prompt(prompt_name, variables)
    
    async def analyze_deviation_with_structured_output(self, 
                                                     daily_summary: str, 
                                                     daily_plan: str,
                                                     user_id: str,
                                                     weekly_plan: Optional[str] = None,
                                                     discussion_number: Optional[int] = None) -> DualConversationResult:
        """使用双次对话分析偏离情况并获取结构化数据"""
        self.logger.info(f"开始双次对话偏离分析 - 用户: {user_id}")
        
        try:
            # 第一次对话：获取文本分析
            text_analysis = await self._first_conversation_text_analysis(
                daily_summary, daily_plan, user_id, weekly_plan
            )
            
            if not text_analysis:
                return DualConversationResult(
                    text_analysis="",
                    structured_data={},
                    success=False,
                    error_message="第一次对话失败"
                )
            
            # 第二次对话：在同一上下文中获取结构化数据
            structured_data = await self._second_conversation_structured_data(
                daily_summary, daily_plan, text_analysis, user_id, weekly_plan
            )
            
            if not structured_data:
                return DualConversationResult(
                    text_analysis=text_analysis,
                    structured_data={},
                    success=False,
                    error_message="第二次对话失败"
                )
            
            # 创建DeviationAnalysisResult对象
            deviation_result = self._create_deviation_analysis_result(
                structured_data, text_analysis, user_id, discussion_number
            )
            
            return DualConversationResult(
                text_analysis=text_analysis,
                structured_data=deviation_result.to_dict(),
                success=True
            )
            
        except Exception as e:
            self.logger.error(f"双次对话分析失败: {e}")
            return DualConversationResult(
                text_analysis="",
                structured_data={},
                success=False,
                error_message=str(e)
            )
    
    async def _first_conversation_text_analysis(self, 
                                              daily_summary: str, 
                                              daily_plan: str,
                                              user_id: str,
                                              weekly_plan: Optional[str] = None) -> Optional[str]:
        """第一次对话：生成文本分析报告"""
        self.logger.info(f"执行第一次对话 - 文本分析 - 用户: {user_id}")
        
        # 准备模板变量
        variables = {
            'daily_summary': daily_summary if daily_summary and daily_summary.strip() else '未提供日报内容',
            'daily_plan': daily_plan if daily_plan and daily_plan.strip() else '未提供日计划内容',
            'weekly_plan': weekly_plan if weekly_plan and weekly_plan.strip() else '未提供周计划内容',
            'user_id': user_id,
            'analysis_date': datetime.now().strftime('%Y-%m-%d'),
            'analysis_time': datetime.now().strftime('%H:%M:%S')
        }
        
        # 尝试从Langfuse获取提示词
        prompts = self._get_prompt_from_langfuse('deviation_analysis_text', variables)
        
        if prompts and prompts.get('user_prompt') and prompts['user_prompt'].strip():
            system_prompt = prompts['system_prompt']
            user_prompt = prompts['user_prompt']
            self.logger.info("使用Langfuse提示词进行文本分析")
        else:
            # 降级到硬编码提示词
            system_prompt = """
【角色】工作偏离度分析专家
【任务】深度分析日报与日计划的偏离情况，提供详细的文本分析报告

【分析维度】
1. 工作完成情况评估
2. 计划执行偏离度分析
3. 周计划一致性分析
4. 额外工作识别
5. 问题原因分析
6. 改进建议提供

【输出要求】
- 提供详细的文本分析报告
- 分析要客观、具体、有建设性
- 重点关注偏离原因和改进方向
- 特别关注日计划与周计划的一致性
- 语言要专业但易懂
"""
            
            user_prompt = f"""
【用户ID】{user_id}
【分析日期】{variables['analysis_date']}

【周计划】
{variables['weekly_plan']}

【日计划】
{variables['daily_plan']}

【日报】
{variables['daily_summary']}

请对以上内容进行深度偏离分析，提供详细的文本分析报告。重点分析：
1. 实际工作与计划的匹配程度
2. 偏离的具体表现和程度
3. 日计划与周计划的一致性分析
4. 偏离的可能原因
5. 额外工作的合理性
6. 具体的改进建议
"""
            self.logger.info("使用降级提示词进行文本分析")
        
        try:
            response = await self._call_glm_api(
                system_prompt=system_prompt,
                user_prompt=user_prompt,
                temperature=0.3
            )
            
            return response
            
        except Exception as e:
            self.logger.error(f"第一次对话失败: {e}")
            return None
    
    async def _second_conversation_structured_data(self, 
                                                 daily_summary: str, 
                                                 daily_plan: str,
                                                 text_analysis: str,
                                                 user_id: str,
                                                 weekly_plan: Optional[str] = None) -> Optional[Dict[str, Any]]:
        """第二次对话：在同一上下文中获取结构化数据"""
        self.logger.info(f"执行第二次对话 - 结构化数据 - 用户: {user_id}")
        
        # 构建包含上下文的系统提示词
        system_prompt = """
【角色】数据结构化专家
【任务】基于之前的分析结果，提供精确的结构化数据

【要求】
- 基于之前的文本分析，提供对应的结构化数据
- 确保数据的一致性和准确性
- 严格按照JSON格式输出
- 数值要准确反映分析结果

【输出格式】
必须输出有效的JSON格式，包含以下字段：
{
  "score": 偏离度评分(0-10，数字),
  "completion_rate": 完成率(0-1，数字),
  "deviation_reasons": ["偏离原因1", "偏离原因2"],
  "additional_work": ["额外工作1", "额外工作2"],
  "suggestions": ["改进建议1", "改进建议2"],
  "summary": "简要总结",
  "confidence": 置信度(0-1，数字)
}
"""
        
        weekly_plan_info = f"周计划: {weekly_plan if weekly_plan and weekly_plan.strip() else '未提供周计划内容'}" if weekly_plan else "周计划: 未提供周计划内容"
        
        user_prompt = f"""
【上下文信息】
用户ID: {user_id}
{weekly_plan_info}
日计划: {daily_plan}
日报: {daily_summary}

【之前的文本分析结果】
{text_analysis}

【任务】
基于以上文本分析结果，请提供对应的结构化JSON数据。确保：
1. 偏离度评分要准确反映分析中的偏离程度（包括与周计划的偏离）
2. 完成率要基于实际完成情况
3. 偏离原因要与文本分析一致（包括周计划一致性问题）
4. 改进建议要具体可行
5. 置信度要反映分析的可靠程度

请直接输出JSON格式的结构化数据，不要包含任何其他文字说明。
"""
        
        try:
            response = await self._call_glm_api(
                system_prompt=system_prompt,
                user_prompt=user_prompt,
                temperature=0.1  # 降低温度以获得更稳定的结构化输出
            )
            
            # 尝试解析JSON
            try:
                # 清理响应内容，移除可能的markdown标记
                cleaned_response = response.strip()
                if cleaned_response.startswith('```json'):
                    cleaned_response = cleaned_response[7:]
                if cleaned_response.endswith('```'):
                    cleaned_response = cleaned_response[:-3]
                cleaned_response = cleaned_response.strip()
                
                structured_data = json.loads(cleaned_response)
                
                # 验证必要字段
                required_fields = ['score', 'completion_rate', 'deviation_reasons', 
                                 'additional_work', 'suggestions', 'summary', 'confidence']
                
                for field in required_fields:
                    if field not in structured_data:
                        self.logger.warning(f"缺少必要字段: {field}")
                        structured_data[field] = self._get_default_value(field)
                
                # 数据类型验证和修正
                structured_data = self._validate_and_fix_data_types(structured_data)
                
                return structured_data
                
            except json.JSONDecodeError as e:
                self.logger.error(f"JSON解析失败: {e}")
                self.logger.error(f"原始响应: {response}")
                
                # 尝试从文本中提取结构化信息
                return self._extract_structured_data_from_text(response, text_analysis)
                
        except Exception as e:
            self.logger.error(f"第二次对话失败: {e}")
            return None
    
    def _get_default_value(self, field: str) -> Any:
        """获取字段的默认值"""
        defaults = {
            'score': 5.0,
            'completion_rate': 0.5,
            'deviation_reasons': ['分析数据不完整'],
            'additional_work': [],
            'suggestions': ['建议提供更详细的信息'],
            'summary': '分析结果不完整',
            'confidence': 0.3
        }
        return defaults.get(field, None)
    
    def _validate_and_fix_data_types(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """验证和修正数据类型"""
        try:
            # 确保score是float类型，范围0-10
            if 'score' in data:
                data['score'] = max(0.0, min(10.0, float(data['score'])))
            
            # 确保completion_rate是float类型，范围0-1
            if 'completion_rate' in data:
                data['completion_rate'] = max(0.0, min(1.0, float(data['completion_rate'])))
            
            # 确保confidence是float类型，范围0-1
            if 'confidence' in data:
                data['confidence'] = max(0.0, min(1.0, float(data['confidence'])))
            
            # 确保列表字段是列表类型
            list_fields = ['deviation_reasons', 'additional_work', 'suggestions']
            for field in list_fields:
                if field in data and not isinstance(data[field], list):
                    if isinstance(data[field], str):
                        data[field] = [data[field]]
                    else:
                        data[field] = []
            
            # 确保summary是字符串类型
            if 'summary' in data and not isinstance(data['summary'], str):
                data['summary'] = str(data['summary'])
            
            return data
            
        except Exception as e:
            self.logger.error(f"数据类型验证失败: {e}")
            return data
    
    def _extract_structured_data_from_text(self, response: str, text_analysis: str) -> Dict[str, Any]:
        """从文本中提取结构化数据（备用方案）"""
        self.logger.info("尝试从文本中提取结构化数据")
        
        # 基于文本分析的简单启发式提取
        try:
            # 默认值
            structured_data = {
                'score': 5.0,
                'completion_rate': 0.5,
                'deviation_reasons': ['分析结果解析失败'],
                'additional_work': [],
                'suggestions': ['建议重新分析'],
                'summary': '数据提取失败',
                'confidence': 0.2
            }
            
            # 简单的关键词分析来估算分数
            text_lower = text_analysis.lower()
            
            # 偏离度评分启发式
            if any(word in text_lower for word in ['严重偏离', '完全偏离', '重大偏离']):
                structured_data['score'] = 8.5
            elif any(word in text_lower for word in ['明显偏离', '较大偏离']):
                structured_data['score'] = 7.0
            elif any(word in text_lower for word in ['轻微偏离', '小幅偏离']):
                structured_data['score'] = 4.0
            elif any(word in text_lower for word in ['基本符合', '按计划执行']):
                structured_data['score'] = 2.0
            
            # 完成率启发式
            if any(word in text_lower for word in ['完全完成', '全部完成']):
                structured_data['completion_rate'] = 1.0
            elif any(word in text_lower for word in ['大部分完成', '基本完成']):
                structured_data['completion_rate'] = 0.8
            elif any(word in text_lower for word in ['部分完成', '一半完成']):
                structured_data['completion_rate'] = 0.5
            elif any(word in text_lower for word in ['少量完成', '未完成']):
                structured_data['completion_rate'] = 0.2
            
            return structured_data
            
        except Exception as e:
            self.logger.error(f"文本提取失败: {e}")
            return {
                'score': 5.0,
                'completion_rate': 0.5,
                'deviation_reasons': ['提取失败'],
                'additional_work': [],
                'suggestions': ['请重新分析'],
                'summary': '提取失败',
                'confidence': 0.1
            }
    
    def _create_deviation_analysis_result(self, 
                                        structured_data: Dict[str, Any],
                                        text_analysis: str,
                                        user_id: str,
                                        discussion_number: Optional[int]) -> DeviationAnalysisResult:
        """创建偏离分析结果对象"""
        try:
            # 判断是否偏离（分数大于5.0认为是偏离）
            is_deviation = structured_data.get('score', 0) > 5.0
            
            return DeviationAnalysisResult(
                user_id=user_id,
                analysis_date=datetime.now().strftime('%Y-%m-%d'),
                discussion_number=discussion_number,
                score=structured_data.get('score', 5.0),
                completion_rate=structured_data.get('completion_rate', 0.5),
                deviation_reasons=structured_data.get('deviation_reasons', []),
                additional_work=structured_data.get('additional_work', []),
                suggestions=structured_data.get('suggestions', []),
                summary=structured_data.get('summary', ''),
                confidence=structured_data.get('confidence', 0.5),
                is_deviation=is_deviation,
                raw_analysis_text=text_analysis
            )
            
        except Exception as e:
            self.logger.error(f"创建偏离分析结果失败: {e}")
            # 返回默认结果
            return DeviationAnalysisResult(
                user_id=user_id,
                analysis_date=datetime.now().strftime('%Y-%m-%d'),
                discussion_number=discussion_number,
                score=5.0,
                completion_rate=0.5,
                deviation_reasons=['分析失败'],
                additional_work=[],
                suggestions=['请重新分析'],
                summary='分析失败',
                confidence=0.1,
                is_deviation=False,
                raw_analysis_text=text_analysis or '分析失败'
            )
    
    async def _call_glm_api(self, system_prompt: str, user_prompt: str, temperature: Optional[float] = None) -> str:
        """调用GLM API"""
        if temperature is None:
            temperature = self.config.temperature
        
        # 处理Langfuse返回的空system_prompt情况
        # 如果system_prompt为空或只包含空白字符，使用默认的system_prompt
        if not system_prompt or not system_prompt.strip():
            system_prompt = "你是一个专业的工作分析助手，请根据用户的要求进行分析。"
            self.logger.info("使用默认system_prompt，因为原system_prompt为空")
        
        # 确保user_prompt不为空
        if not user_prompt or not user_prompt.strip():
            raise ValueError("user_prompt不能为空")
            
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
        """测试GLM API连接"""
        try:
            test_response = await self._call_glm_api(
                system_prompt="你是一个测试助手。",
                user_prompt="请回复'连接测试成功'。",
                temperature=0.1
            )
            
            self.logger.info("增强版GLM API连接测试成功")
            return True
            
        except Exception as e:
            self.logger.error(f"增强版GLM API连接测试失败: {e}")
            return False