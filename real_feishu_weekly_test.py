#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
真实飞书周报测试脚本
使用真实配置发送飞书消息
"""

import asyncio
import json
import logging
import os
from datetime import datetime, timedelta
from typing import Dict, Any

from src.clients.feishu_client import FeishuClient
from src.generators.report_generator import ReportGenerator
from src.storage.json_data_manager import JSONDataManager
from src.weekly_summarizer import WeeklyReportSummarizer
from src.weekly_summarizer import UserWeeklyData
from src.models.data_models import DeviationAnalysisResult
from src.clients.glm_client import GLMClient

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

class RealFeishuWeeklyTester:
    """真实飞书周报测试器"""
    
    def __init__(self):
        """初始化测试器"""
        self.feishu_client = None
        self.report_generator = None
        self.data_manager = None
        self.weekly_summarizer = None
        
    def _init_components(self):
        """初始化各个组件"""
        try:
            # 初始化数据管理器
            self.data_manager = JSONDataManager("data")
            logger.info("✅ 数据管理器初始化成功")
            
            # 初始化GLM客户端
            from src.config import Config
            config = Config()
            self.glm_client = GLMClient(config.glm)
            logger.info("✅ GLM客户端初始化成功")
            
            # 初始化周报汇总器
            self.weekly_summarizer = WeeklyReportSummarizer(self.data_manager)
            logger.info("✅ 周报汇总器初始化成功")
            
            # 初始化报告生成器
            self.report_generator = ReportGenerator(config)
            logger.info("✅ 报告生成器初始化成功")
            
            # 初始化飞书客户端
            self._init_feishu_client()
            
            return True
            
        except Exception as e:
            logger.error(f"❌ 组件初始化失败: {e}")
            return False
    
    def _init_feishu_client(self):
        """初始化飞书客户端"""
        try:
            # 构建飞书配置
            feishu_config = {
                'webhook_url': os.getenv('FEISHU_WEBHOOK_URL', 'https://open.feishu.cn/open-apis/bot/v2/hook/test'),
                'mapping_file': 'feishu_mapping.json',
                'timeout': 30,
                'retry_count': 3,
                'api': {
                    'app_id': os.getenv('FEISHU_APP_ID', 'cli_test'),
                    'app_secret': os.getenv('FEISHU_APP_SECRET', 'test_secret'),
                    'base_url': 'https://open.feishu.cn/open-apis',
                    'timeout': 30,
                    'max_retries': 3,
                    'retry_delay': 1
                },
                'management': {
                    'enabled': True,
                    'user_ids': ['goudaren0528', 'Leejhua']  # 使用真实用户ID
                }
            }
            
            self.feishu_client = FeishuClient(config=feishu_config)
            logger.info("✅ 飞书客户端初始化成功")
            
            # 检查用户映射
            mapping_stats = self._check_user_mapping()
            logger.info(f"📊 用户映射统计: {mapping_stats}")
            
        except Exception as e:
            logger.error(f"❌ 飞书客户端初始化失败: {e}")
            raise
    
    def _check_user_mapping(self) -> Dict[str, Any]:
        """检查用户映射配置"""
        try:
            mapping_file = 'feishu_mapping.json'
            if os.path.exists(mapping_file):
                with open(mapping_file, 'r', encoding='utf-8') as f:
                    mapping_data = json.load(f)
                
                user_mapping = mapping_data.get('user_mapping', {})
                return {
                    'total_mappings': len(user_mapping),
                    'mapped_users': list(user_mapping.keys()),
                    'mapping_file_exists': True
                }
            else:
                return {
                    'total_mappings': 0,
                    'mapped_users': [],
                    'mapping_file_exists': False
                }
                
        except Exception as e:
            logger.error(f"检查用户映射失败: {e}")
            return {
                'total_mappings': 0,
                'mapped_users': [],
                'mapping_file_exists': False,
                'error': str(e)
            }
    
    def _create_test_weekly_data(self, user_id: str = "测试用户") -> UserWeeklyData:
        """创建测试周报数据"""
        end_date = datetime.now()
        start_date = end_date - timedelta(days=7)
        
        # 创建模拟的分析结果
        analysis_results = [
            DeviationAnalysisResult(
                score=2.5,
                completion_rate=0.85,
                deviation_reasons=["部分任务延期", "优先级调整"],
                additional_work=["紧急需求处理"],
                suggestions=["优化时间管理", "提前沟通变更"],
                summary="整体执行良好，存在小幅偏离",
                confidence=0.8,
                user_id=user_id,
                analysis_date=(end_date - timedelta(days=1)).strftime('%Y-%m-%d'),
                discussion_number=123,
                is_deviation=True,
                content_type='daily_report',
                original_content='完成用户登录功能开发，包括前端页面设计和后端API实现'
            ),
            DeviationAnalysisResult(
                score=1.8,
                completion_rate=0.92,
                deviation_reasons=["计划外优化工作"],
                additional_work=["代码重构", "性能优化"],
                suggestions=["合理安排优化时间"],
                summary="执行效果优秀，略有额外工作",
                confidence=0.9,
                user_id=user_id,
                analysis_date=(end_date - timedelta(days=2)).strftime('%Y-%m-%d'),
                discussion_number=124,
                is_deviation=False,
                content_type='daily_report',
                original_content='修复数据库连接问题，优化查询性能'
            )
        ]
        
        # 创建UserWeeklyData对象
        weekly_data = UserWeeklyData(
            user_id=user_id,
            week_id=f"{end_date.year}-W{end_date.isocalendar()[1]:02d}",
            total_reports=len(analysis_results),
            deviation_count=0,
            avg_score=8.15,
            daily_summaries=[
                '完成用户登录功能开发，包括前端页面设计和后端API实现',
                '修复数据库连接问题，优化查询性能'
            ],
            daily_plans=[
                '今日计划：完成用户认证模块测试',
                '今日计划：优化系统性能'
            ],
            weekly_plans=[
                '本周计划：完成用户管理模块开发'
            ],
            work_completion_rate=0.85,
            key_achievements=[
                '成功实现用户登录功能',
                '解决了数据库性能问题'
            ],
            identified_issues=[
                '需要进一步优化前端响应速度'
            ],
            analysis_results=analysis_results
        )
        
        return weekly_data
    
    async def test_employee_report(self) -> bool:
        """测试员工周报发送"""
        try:
            logger.info("\n" + "="*50)
            logger.info("测试员工周报发送")
            logger.info("="*50)
            
            # 创建测试数据
            test_user = "goudaren0528"  # 使用映射文件中的真实用户
            weekly_data = self._create_test_weekly_data(test_user)
            
            # 生成周报
            logger.info(f"为用户 {test_user} 生成周报...")
            report_content = await self.report_generator.generate_weekly_report(
                weekly_data=weekly_data,
                report_type='personal'
            )
            
            logger.info(f"✅ 周报生成成功，内容长度: {len(report_content)} 字符")
            logger.info(f"📄 周报内容预览:\n{report_content[:200]}...")
            
            # 发送周报
            logger.info(f"发送员工周报给用户: {test_user}")
            success = self.feishu_client.send_weekly_report(
                report_content=report_content,
                report_type="employee",
                users=[test_user]
            )
            
            if success:
                logger.info("✅ 员工周报发送成功")
                return True
            else:
                logger.error("❌ 员工周报发送失败")
                return False
                
        except Exception as e:
            logger.error(f"❌ 员工周报测试异常: {e}")
            return False
    
    async def test_management_report(self) -> bool:
        """测试管理层周报发送"""
        try:
            logger.info("\n" + "="*50)
            logger.info("测试管理层周报发送")
            logger.info("="*50)
            
            # 创建团队汇总数据
            team_data = self._create_test_weekly_data("团队汇总")
            
            # 生成管理层周报
            logger.info("生成管理层周报...")
            report_content = await self.report_generator.generate_weekly_report(
                weekly_data=team_data,
                report_type='management'
            )
            
            logger.info(f"✅ 管理层周报生成成功，内容长度: {len(report_content)} 字符")
            logger.info(f"📄 周报内容预览:\n{report_content[:200]}...")
            
            # 发送管理层周报
            logger.info("发送管理层周报...")
            success = self.feishu_client.send_weekly_report(
                report_content=report_content,
                report_type="management"
            )
            
            if success:
                logger.info("✅ 管理层周报发送成功")
                return True
            else:
                logger.error("❌ 管理层周报发送失败")
                return False
                
        except Exception as e:
            logger.error(f"❌ 管理层周报测试异常: {e}")
            return False
    
    async def test_webhook_message(self) -> bool:
        """测试webhook消息发送"""
        try:
            logger.info("\n" + "="*50)
            logger.info("测试Webhook消息发送")
            logger.info("="*50)
            
            # 创建测试周报内容
            test_content = f"""
📊 **飞书Webhook测试周报**

📅 **测试时间**: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}

## 🎯 测试目的
验证飞书Webhook消息发送功能

## ✅ 测试内容
- Webhook URL配置
- 消息格式化
- 群聊消息发送

## 📈 模拟数据
- 本周提交: 15次
- 代码行数: +254 -46
- PR合并: 3个
- 问题解决: 2个

## 📝 说明
这是一条通过Webhook发送的测试消息。如果您在飞书群聊中收到这条消息，说明Webhook集成功能正常。

---
⏰ 发送时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
            """
            
            # 发送到群聊
            logger.info("发送Webhook消息到群聊...")
            success = self.feishu_client.send_weekly_report(
                report_content=test_content,
                report_type="employee"  # 不指定users，会发送到群聊
            )
            
            if success:
                logger.info("✅ Webhook消息发送成功")
                return True
            else:
                logger.error("❌ Webhook消息发送失败")
                return False
                
        except Exception as e:
            logger.error(f"❌ Webhook消息测试异常: {e}")
            return False
    
    async def run_all_tests(self):
        """运行所有测试"""
        logger.info("🚀 开始飞书周报真实测试")
        logger.info("="*60)
        
        # 初始化组件
        if not self._init_components():
            logger.error("❌ 组件初始化失败，测试终止")
            return
        
        # 运行测试
        results = {
            'employee_report': False,
            'management_report': False,
            'webhook_message': False
        }
        
        # 测试员工周报
        results['employee_report'] = await self.test_employee_report()
        
        # 测试管理层周报
        results['management_report'] = await self.test_management_report()
        
        # 测试Webhook消息
        results['webhook_message'] = await self.test_webhook_message()
        
        # 输出测试结果
        logger.info("\n" + "="*60)
        logger.info("测试结果汇总")
        logger.info("="*60)
        
        success_count = sum(results.values())
        total_count = len(results)
        
        for test_name, success in results.items():
            status = "✅" if success else "❌"
            logger.info(f"{test_name}: {status}")
        
        logger.info(f"\n总体成功率: {success_count}/{total_count} ({success_count/total_count*100:.1f}%)")
        
        if success_count == total_count:
            logger.info("\n🎉 所有测试通过！飞书集成功能正常工作。")
            logger.info("📱 请检查您的飞书是否收到了测试消息。")
        elif success_count > 0:
            logger.info("\n⚠️ 部分测试通过，请检查失败的功能。")
        else:
            logger.info("\n❌ 所有测试失败，请检查配置和网络连接。")

def main():
    """主函数"""
    tester = RealFeishuWeeklyTester()
    asyncio.run(tester.run_all_tests())

if __name__ == "__main__":
    main()