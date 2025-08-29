#!/usr/bin/env python3
"""
真实端到端测试脚本
测试完整流程：Mock数据 → GLM分析 → 偏离检测 → 飞书通知
"""

import asyncio
import json
import time
import logging
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, List, Any, Optional
import sys
import os

# 添加项目根目录到Python路径
sys.path.insert(0, str(Path(__file__).parent.parent))

from src.config import Config
from src.clients.enhanced_glm_client import EnhancedGLMClient
from src.clients.feishu_client import FeishuClient
from src.models.data_models import DeviationAnalysisResult
from src.utils.logger import get_logger
from tests.mock_data_generator import MockDataGenerator

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = get_logger(__name__)

class RealE2ETestRunner:
    """真实端到端测试运行器"""
    
    def __init__(self):
        self.config = None
        self.glm_client = None
        self.feishu_client = None
        self.test_results = []
        self.start_time = None
        self.end_time = None
        
    async def initialize(self) -> bool:
        """初始化测试环境"""
        try:
            logger.info("🚀 初始化真实端到端测试环境")
            
            # 加载配置
            self.config = Config()
            if not self.config:
                logger.error("配置加载失败")
                return False
            
            # 初始化GLM客户端
            if not self.config.glm.api_key:
                logger.error("GLM API密钥未配置")
                return False
                
            self.glm_client = EnhancedGLMClient(self.config.glm)
            
            # 测试GLM连接
            logger.info("测试GLM API连接...")
            if not await self.glm_client.test_connection():
                logger.error("GLM API连接测试失败")
                return False
            logger.info("✅ GLM API连接正常")
            
            # 初始化飞书客户端
            if hasattr(self.config, 'feishu') and getattr(self.config.feishu, 'enabled', False):
                try:
                    from src.clients.enhanced_feishu_client import EnhancedFeishuClient, FeishuConfig, FeishuClientWrapper
                    
                    # 创建飞书配置
                    feishu_config = FeishuConfig(
                        app_id=self.config.feishu.api.app_id,
                        app_secret=self.config.feishu.api.app_secret,
                        base_url=self.config.feishu.api.base_url,
                        timeout=self.config.feishu.api.timeout,
                        max_retries=self.config.feishu.api.max_retries,
                        retry_delay=self.config.feishu.api.retry_delay
                    )
                    
                    # 创建增强飞书客户端
                    enhanced_client = EnhancedFeishuClient(feishu_config)
                    
                    # 使用包装器保持接口兼容性
                    self.feishu_client = FeishuClientWrapper(
                        enhanced_client, 
                        self.config.feishu.api.default_chat_id
                    )
                    
                    # 测试飞书连接
                    logger.info("测试飞书连接...")
                    if enhanced_client.test_connection():
                        logger.info("✅ 飞书连接正常")
                    else:
                        logger.warning("⚠️ 飞书连接测试失败，将跳过飞书通知测试")
                        self.feishu_client = None
                        
                except Exception as e:
                    logger.error(f"飞书客户端初始化失败: {e}")
                    self.feishu_client = None
            else:
                logger.info("飞书功能未启用")
                self.feishu_client = None
                
            return True
            
        except Exception as e:
            logger.error(f"初始化失败: {e}")
            return False
    
    def generate_test_data(self) -> List[Dict[str, Any]]:
        """生成测试数据"""
        generator = MockDataGenerator()
        
        # 生成连续偏离场景的测试数据
        results = generator.generate_continuous_deviation_scenario(
            user_id="test_user_001",
            deviation_days=3,
            severity="significant"
        )
        
        # 转换为字典格式
        mock_data = [result.to_dict() for result in results]
        
        return mock_data
    
    async def run_glm_analysis(self, test_case: Dict[str, Any]) -> Dict[str, Any]:
        """运行GLM分析"""
        user_id = test_case.get('user_id', 'test_user')
        
        logger.info(f"🤖 开始GLM分析 - 用户: {user_id}")
        
        start_time = time.time()
        
        try:
            # 从测试数据中提取计划和总结
            # 这里我们模拟一个简单的计划和总结
            daily_plan = "完成项目开发任务，包括代码编写、测试和文档更新"
            daily_summary = f"用户{user_id}的工作总结，偏离评分: {test_case.get('score', 5)}"
            
            # 调用GLM API进行分析
            weekly_plan = "本周计划：完成项目核心功能开发，包括用户认证、数据管理和API接口实现"
            result = await self.glm_client.analyze_deviation_with_structured_output(
                daily_plan=daily_plan,
                daily_summary=daily_summary,
                user_id=user_id,
                weekly_plan=weekly_plan
            )
            
            end_time = time.time()
            analysis_time = end_time - start_time
            
            if result.success:
                logger.info(f"✅ GLM分析成功 - 耗时: {analysis_time:.2f}秒")
                
                # 从structured_data中提取信息
                structured_data = result.structured_data
                deviation_score = structured_data.get('score', 0.0)
                completion_rate = structured_data.get('completion_rate', 0.0)
                is_deviation = structured_data.get('is_deviation', False)
                
                logger.info(f"📊 偏离度分数: {deviation_score}")
                logger.info(f"📝 分析摘要: {result.text_analysis[:100]}...")
                
                return {
                    'success': True,
                    'analysis_time': analysis_time,
                    'deviation_score': deviation_score,
                    'completion_rate': completion_rate,
                    'is_deviation': is_deviation,
                    'text_analysis': result.text_analysis,
                    'structured_data': {
                        'deviation_reasons': structured_data.get('deviation_reasons', []),
                        'additional_work': structured_data.get('additional_work', []),
                        'suggestions': structured_data.get('suggestions', [])
                    },
                    'confidence': structured_data.get('confidence', 0.0),
                    'api_calls': 2  # 双次对话
                }
            else:
                logger.error(f"❌ GLM分析失败: {result.error_message}")
                return {
                    'success': False,
                    'analysis_time': analysis_time,
                    'error': result.error_message
                }
                
        except Exception as e:
            end_time = time.time()
            analysis_time = end_time - start_time
            logger.error(f"❌ GLM分析异常: {e}")
            return {
                'success': False,
                'analysis_time': analysis_time,
                'error': str(e)
            }
    
    async def send_feishu_notification(self, test_case: Dict[str, Any], 
                                     glm_result: Dict[str, Any]) -> Dict[str, Any]:
        """发送飞书通知"""
        if not self.feishu_client:
            logger.info("⏭️ 跳过飞书通知测试（飞书客户端未配置）")
            return {'success': False, 'reason': 'feishu_not_configured'}
        
        user_id = test_case.get('user_id', 'test_user')
        
        logger.info(f"📱 发送飞书通知 - 用户: {user_id}")
        
        start_time = time.time()
        
        try:
            # 构建通知内容
            if glm_result['success'] and glm_result.get('is_deviation', False):
                report_content = f"""
📊 工作偏离预警通知

**用户:** {user_id}
**偏离度分数:** {glm_result.get('deviation_score', 'N/A')}
**完成率:** {glm_result.get('completion_rate', 'N/A')}
**分析时间:** {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}

**GLM分析结果:**
{glm_result.get('text_analysis', '无分析内容')[:500]}...

**改进建议:**
{', '.join(glm_result.get('structured_data', {}).get('suggestions', []))}
"""
                
                # 发送通知到默认群聊
                success = self.feishu_client.send_message(report_content)
                
                end_time = time.time()
                notification_time = end_time - start_time
                
                if success:
                    logger.info(f"✅ 飞书通知发送成功 - 耗时: {notification_time:.2f}秒")
                    return {
                        'success': True,
                        'notification_time': notification_time,
                        'message_type': 'text'
                    }
                else:
                    logger.error("❌ 飞书通知发送失败")
                    return {
                        'success': False,
                        'notification_time': notification_time,
                        'error': 'send_failed'
                    }
            else:
                logger.info("ℹ️ 无偏离情况，跳过飞书通知")
                return {
                    'success': True,
                    'notification_time': 0.0,
                    'reason': 'no_deviation'
                }
                
        except Exception as e:
            end_time = time.time()
            notification_time = end_time - start_time
            logger.error(f"❌ 飞书通知异常: {e}")
            return {
                'success': False,
                'notification_time': notification_time,
                'error': str(e)
            }
    
    async def run_single_test(self, test_case: Dict[str, Any]) -> Dict[str, Any]:
        """运行单个测试用例"""
        user_id = test_case.get('user_id', 'test_user')
        expected_score = test_case.get('score', 5.0)
        
        logger.info(f"\n🧪 开始测试用例: 用户 {user_id}")
        logger.info("=" * 60)
        
        test_start_time = time.time()
        
        # 步骤1: GLM分析
        glm_result = await self.run_glm_analysis(test_case)
        
        # 步骤2: 飞书通知
        feishu_result = await self.send_feishu_notification(test_case, glm_result)
        
        test_end_time = time.time()
        total_time = test_end_time - test_start_time
        
        # 验证结果
        actual_score = glm_result.get('deviation_score', 0.0) if glm_result['success'] else None
        
        score_accuracy = None
        if actual_score is not None:
            score_diff = abs(actual_score - expected_score)
            score_accuracy = max(0, 1 - (score_diff / 10.0))  # 10分制下的准确度
        
        # 汇总测试结果
        test_result = {
            'test_case': test_case,
            'total_time': total_time,
            'glm_result': glm_result,
            'feishu_result': feishu_result,
            'validation': {
                'expected_score': expected_score,
                'actual_score': actual_score,
                'score_accuracy': score_accuracy,
                'glm_success': glm_result['success'],
                'feishu_success': feishu_result['success']
            },
            'timestamp': datetime.now().isoformat()
        }
        
        logger.info(f"✅ 测试用例完成 - 总耗时: {total_time:.2f}秒")
        if actual_score is not None:
            logger.info(f"📊 偏离度分数: 预期={expected_score}, 实际={actual_score:.2f}, 准确度={score_accuracy:.2%}")
        
        return test_result
    
    async def run_all_tests(self) -> Dict[str, Any]:
        """运行所有测试"""
        logger.info("\n🚀 开始真实端到端测试")
        logger.info("=" * 80)
        
        self.start_time = time.time()
        
        # 生成测试数据
        test_data = self.generate_test_data()
        
        # 运行所有测试
        for test_case in test_data:
            test_result = await self.run_single_test(test_case)
            self.test_results.append(test_result)
        
        self.end_time = time.time()
        total_test_time = self.end_time - self.start_time
        
        # 生成测试报告
        report = self.generate_test_report(total_test_time)
        
        logger.info("\n🎉 所有测试完成")
        logger.info("=" * 80)
        
        return report
    
    def generate_test_report(self, total_time: float) -> Dict[str, Any]:
        """生成测试报告"""
        logger.info("📋 生成测试报告")
        
        # 统计数据
        total_tests = len(self.test_results)
        glm_success_count = sum(1 for r in self.test_results if r['glm_result']['success'])
        feishu_success_count = sum(1 for r in self.test_results if r['feishu_result']['success'])
        
        # GLM分析时间统计
        glm_times = [r['glm_result']['analysis_time'] for r in self.test_results if r['glm_result']['success']]
        avg_glm_time = sum(glm_times) / len(glm_times) if glm_times else 0
        
        # 准确度统计
        accuracies = [r['validation']['score_accuracy'] for r in self.test_results if r['validation']['score_accuracy'] is not None]
        avg_accuracy = sum(accuracies) / len(accuracies) if accuracies else 0
        
        # 详细结果
        detailed_results = []
        for result in self.test_results:
            detailed_results.append({
                'scenario': result['test_case'].get('scenario_name', 'unknown'),
                'user_id': result['test_case']['user_id'],
                'total_time': f"{result['total_time']:.2f}s",
                'glm_analysis_time': f"{result['glm_result'].get('analysis_time', 0):.2f}s",
                'glm_success': result['glm_result']['success'],
                'feishu_success': result['feishu_result']['success'],
                'expected_score': result['validation']['expected_score'],
                'actual_score': result['validation']['actual_score'],
                'score_accuracy': f"{result['validation']['score_accuracy']:.2%}" if result['validation']['score_accuracy'] else 'N/A',
                'deviation_detected': result['glm_result'].get('is_deviation', False)
            })
        
        report = {
            'test_summary': {
                'total_tests': total_tests,
                'total_time': f"{total_time:.2f}s",
                'glm_success_rate': f"{glm_success_count/total_tests:.2%}",
                'feishu_success_rate': f"{feishu_success_count/total_tests:.2%}",
                'avg_glm_analysis_time': f"{avg_glm_time:.2f}s",
                'avg_score_accuracy': f"{avg_accuracy:.2%}",
                'test_timestamp': datetime.now().isoformat()
            },
            'detailed_results': detailed_results,
            'raw_results': self.test_results
        }
        
        return report
    
    def save_report(self, report: Dict[str, Any], filename: str = None) -> str:
        """保存测试报告"""
        if filename is None:
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            filename = f"real_e2e_test_report_{timestamp}.json"
        
        report_path = Path(__file__).parent / filename
        
        with open(report_path, 'w', encoding='utf-8') as f:
            json.dump(report, f, ensure_ascii=False, indent=2)
        
        logger.info(f"📄 测试报告已保存: {report_path}")
        return str(report_path)
    
    def print_summary(self, report: Dict[str, Any]):
        """打印测试摘要"""
        summary = report['test_summary']
        
        print("\n" + "=" * 80)
        print("🎯 真实端到端测试报告摘要")
        print("=" * 80)
        print(f"📊 测试总数: {summary['total_tests']}")
        print(f"⏱️ 总耗时: {summary['total_time']}")
        print(f"🤖 GLM成功率: {summary['glm_success_rate']}")
        print(f"📱 飞书成功率: {summary['feishu_success_rate']}")
        print(f"⚡ 平均GLM分析时间: {summary['avg_glm_analysis_time']}")
        print(f"🎯 平均分数准确度: {summary['avg_score_accuracy']}")
        print(f"🕐 测试时间: {summary['test_timestamp']}")
        
        print("\n📋 详细结果:")
        print("-" * 80)
        for result in report['detailed_results']:
            print(f"场景: {result['scenario']} | GLM: {result['glm_analysis_time']} | 准确度: {result['score_accuracy']} | 偏离: {result['deviation_detected']}")
        
        print("=" * 80)


async def main():
    """主函数"""
    runner = RealE2ETestRunner()
    
    try:
        # 初始化
        if not await runner.initialize():
            logger.error("❌ 初始化失败，测试终止")
            return
        
        # 运行测试
        report = await runner.run_all_tests()
        
        # 保存和显示报告
        report_path = runner.save_report(report)
        runner.print_summary(report)
        
        logger.info(f"\n✅ 真实端到端测试完成！报告已保存至: {report_path}")
        
    except KeyboardInterrupt:
        logger.info("\n⏹️ 测试被用户中断")
    except Exception as e:
        logger.error(f"\n❌ 测试执行异常: {e}")
        raise


if __name__ == "__main__":
    asyncio.run(main())