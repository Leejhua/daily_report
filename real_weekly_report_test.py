#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
真实飞书周报测试脚本

功能:
1. 使用真实的feishu_mapping.json配置
2. 创建模拟的周报数据
3. 实际发送飞书消息（不只是预览）
4. 使用webhook或API方式发送
5. 确保消息能真正发送到飞书群聊
6. 添加详细的日志输出以便调试
"""

import os
import sys
import json
import logging
from datetime import datetime, timedelta
from pathlib import Path

# 添加项目根目录到Python路径
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

from src.config import Config
from src.weekly_summarizer import WeeklyReportSummarizer
from src.generators.report_generator import ReportGenerator
from src.clients.feishu_client import FeishuClient
from src.storage.json_data_manager import JSONDataManager

# 配置日志
logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler('real_weekly_report_test.log', encoding='utf-8')
    ]
)
logger = logging.getLogger(__name__)

class RealWeeklyReportTester:
    """真实飞书周报测试器"""
    
    def __init__(self):
        """初始化测试器"""
        self.config = Config()
        self.data_manager = JSONDataManager("data")
        self.weekly_summarizer = WeeklyReportSummarizer(self.data_manager)
        self.report_generator = ReportGenerator(self.config)
        
        # 初始化飞书客户端
        self.feishu_client = self._init_feishu_client()
        
        logger.info("真实飞书周报测试器初始化完成")
    
    def _init_feishu_client(self) -> FeishuClient:
        """初始化飞书客户端"""
        logger.info("初始化飞书客户端...")
        
        # 从环境变量获取配置
        app_id = os.getenv('FEISHU_APP_ID')
        app_secret = os.getenv('FEISHU_APP_SECRET')
        webhook_url = os.getenv('FEISHU_WEBHOOK_URL')
        
        # 检查配置是否完整
        if not app_id:
            logger.warning("FEISHU_APP_ID 未设置")
        if not app_secret:
            logger.warning("FEISHU_APP_SECRET 未设置")
        if not webhook_url:
            logger.warning("FEISHU_WEBHOOK_URL 未设置")
            # 设置一个默认的测试URL
            webhook_url = "https://open.feishu.cn/open-apis/bot/v2/hook/test"
        
        logger.info(f"飞书配置 - App ID: {app_id[:8] if app_id else 'None'}...")
        logger.info(f"飞书配置 - Webhook URL: {webhook_url[:50] if webhook_url else 'None'}...")
        
        # 构建飞书配置
        feishu_config = {
            'webhook_url': webhook_url,
            'mapping_file': 'feishu_mapping.json',
            'timeout': 30,
            'retry_count': 3,
            'api': {
                'app_id': app_id,
                'app_secret': app_secret,
                'base_url': 'https://open.feishu.cn',
                'timeout': 30,
                'max_retries': 3,
                'retry_delay': 1.0
            }
        }
        
        # 初始化飞书客户端
        feishu_client = FeishuClient(feishu_config)
        
        logger.info("飞书客户端初始化完成")
        return feishu_client
    
    def create_mock_weekly_data(self) -> dict:
        """创建模拟的周报数据"""
        logger.info("创建模拟周报数据...")
        
        # 计算本周时间范围
        today = datetime.now()
        start_of_week = today - timedelta(days=today.weekday())
        end_of_week = start_of_week + timedelta(days=6)
        
        # 模拟用户数据
        mock_users = ['XK-UI', 'leejhua', 'goudaren0528']
        
        weekly_data = {
            'period': {
                'start': start_of_week.strftime('%Y-%m-%d'),
                'end': end_of_week.strftime('%Y-%m-%d')
            },
            'users': {},
            'summary': {
                'total_users': len(mock_users),
                'total_reports': len(mock_users) * 5,  # 假设每人5份报告
                'avg_score': 85.6
            }
        }
        
        # 为每个用户创建模拟数据
        for i, user in enumerate(mock_users):
            weekly_data['users'][user] = {
                'daily_reports': [
                    {
                        'date': (start_of_week + timedelta(days=j)).strftime('%Y-%m-%d'),
                        'clarity_score': 80 + (i * 5) + (j * 2),
                        'consistency_score': 75 + (i * 3) + (j * 3),
                        'deviation_score': 90 - (i * 2) - (j * 1),
                        'summary': f"{user}在{(start_of_week + timedelta(days=j)).strftime('%m-%d')}的工作汇报",
                        'key_points': [
                            f"完成了{user}的核心任务{j+1}",
                            f"解决了{j+2}个技术问题",
                            f"与团队协作完成项目模块{j+1}"
                        ]
                    }
                    for j in range(5)  # 工作日
                ],
                'weekly_stats': {
                    'avg_clarity': 80 + (i * 5) + 2.5,
                    'avg_consistency': 75 + (i * 3) + 7.5,
                    'avg_deviation': 90 - (i * 2) - 2.5,
                    'total_reports': 5,
                    'improvement_trend': 'positive' if i % 2 == 0 else 'stable'
                }
            }
        
        logger.info(f"模拟数据创建完成，包含 {len(mock_users)} 个用户")
        return weekly_data
    
    def test_employee_report(self, weekly_data: dict) -> str:
        """测试员工版周报"""
        logger.info("生成员工版周报...")
        
        try:
            # 选择一个用户生成个人周报
            test_user = 'XK-UI'
            user_data = weekly_data['users'][test_user]
            
            # 创建UserWeeklyData对象
            from src.weekly_summarizer import UserWeeklyData
            from datetime import datetime
            
            # 模拟UserWeeklyData对象
            user_weekly_data = type('UserWeeklyData', (), {
                'user_name': test_user,
                'week_start': datetime.strptime(weekly_data['period']['start'], '%Y-%m-%d'),
                'week_end': datetime.strptime(weekly_data['period']['end'], '%Y-%m-%d'),
                'work_days': 5,
                'avg_completion_rate': user_data['weekly_stats']['avg_clarity'] / 100,
                'deviation_days': 2,
                'risk_level': '中',
                'achievements': ["完成核心功能开发", "解决关键技术问题", "团队协作良好"],
                'issues': ["时间管理需要改进", "部分任务延期"]
            })()
            
            # 使用asyncio运行异步方法
            import asyncio
            employee_report = asyncio.run(
                self.report_generator.generate_weekly_report(
                    weekly_data=user_weekly_data,
                    report_type='personal'
                )
            )
            
            logger.info(f"员工版周报生成成功，长度: {len(employee_report)} 字符")
            logger.debug(f"员工版周报内容:\n{employee_report}")
            
            return employee_report
            
        except Exception as e:
            logger.error(f"生成员工版周报失败: {e}")
            raise
    
    def test_management_report(self, weekly_data: dict) -> str:
        """测试管理版周报"""
        logger.info("生成管理版周报...")
        
        try:
            # 创建团队汇总的UserWeeklyData对象
            from datetime import datetime
            import asyncio
            
            # 模拟团队汇总数据
            team_weekly_data = type('UserWeeklyData', (), {
                'user_name': '团队汇总',
                'week_start': datetime.strptime(weekly_data['period']['start'], '%Y-%m-%d'),
                'week_end': datetime.strptime(weekly_data['period']['end'], '%Y-%m-%d'),
                'work_days': 5,
                'avg_completion_rate': weekly_data['summary']['avg_score'] / 100,
                'deviation_days': 3,
                'risk_level': '中',
                'achievements': ["团队整体表现良好", "关键项目按期推进", "技术难题得到解决"],
                'issues': ["部分成员工作负荷较重", "沟通协调需要加强"]
            })()
            
            management_report = asyncio.run(
                self.report_generator.generate_weekly_report(
                    weekly_data=team_weekly_data,
                    report_type='management'
                )
            )
            
            logger.info(f"管理版周报生成成功，长度: {len(management_report)} 字符")
            logger.debug(f"管理版周报内容:\n{management_report}")
            
            return management_report
            
        except Exception as e:
            logger.error(f"生成管理版周报失败: {e}")
            raise
    
    def test_feishu_sending(self, report_content: str, report_type: str, target_user: str = None) -> bool:
        """测试飞书消息发送"""
        logger.info(f"测试飞书发送 - 报告类型: {report_type}, 目标用户: {target_user}")
        
        try:
            if report_type == 'employee' and target_user:
                # 发送个人周报
                success = self.feishu_client.send_weekly_report(
                    report_content=report_content,
                    report_type='employee',
                    users=[target_user]
                )
            elif report_type == 'management':
                # 发送管理版周报
                success = self.feishu_client.send_weekly_report(
                    report_content=report_content,
                    report_type='management'
                )
            else:
                # 发送到群聊
                success = self.feishu_client.send_weekly_report(
                    report_content=report_content,
                    report_type='employee'
                )
            
            if success:
                logger.info(f"飞书消息发送成功 - {report_type}")
            else:
                logger.error(f"飞书消息发送失败 - {report_type}")
            
            return success
            
        except Exception as e:
            logger.error(f"飞书消息发送异常: {e}")
            return False
    
    def run_comprehensive_test(self):
        """运行综合测试"""
        logger.info("="*60)
        logger.info("开始真实飞书周报测试")
        logger.info("="*60)
        
        try:
            # 1. 创建模拟数据
            weekly_data = self.create_mock_weekly_data()
            
            # 2. 测试员工版周报
            logger.info("\n" + "-"*40)
            logger.info("测试员工版周报")
            logger.info("-"*40)
            
            employee_report = self.test_employee_report(weekly_data)
            
            # 3. 发送员工版周报给指定用户
            logger.info("\n发送员工版周报给 XK-UI...")
            employee_send_success = self.test_feishu_sending(
                employee_report, 
                'employee', 
                'XK-UI'
            )
            
            # 4. 测试管理版周报
            logger.info("\n" + "-"*40)
            logger.info("测试管理版周报")
            logger.info("-"*40)
            
            management_report = self.test_management_report(weekly_data)
            
            # 5. 发送管理版周报
            logger.info("\n发送管理版周报...")
            management_send_success = self.test_feishu_sending(
                management_report, 
                'management'
            )
            
            # 6. 测试群聊发送
            logger.info("\n" + "-"*40)
            logger.info("测试群聊发送")
            logger.info("-"*40)
            
            group_send_success = self.test_feishu_sending(
                "📊 这是一条测试周报消息\n\n测试时间: " + datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
                'employee'
            )
            
            # 7. 输出测试结果
            logger.info("\n" + "="*60)
            logger.info("测试结果汇总")
            logger.info("="*60)
            logger.info(f"员工版周报生成: ✅")
            logger.info(f"管理版周报生成: ✅")
            logger.info(f"员工版周报发送: {'✅' if employee_send_success else '❌'}")
            logger.info(f"管理版周报发送: {'✅' if management_send_success else '❌'}")
            logger.info(f"群聊消息发送: {'✅' if group_send_success else '❌'}")
            
            total_success = sum([
                employee_send_success,
                management_send_success,
                group_send_success
            ])
            
            logger.info(f"\n总体成功率: {total_success}/3 ({total_success/3*100:.1f}%)")
            
            if total_success > 0:
                logger.info("\n🎉 至少有一条消息发送成功！请检查飞书是否收到消息。")
            else:
                logger.warning("\n⚠️ 所有消息发送都失败了，请检查配置和网络连接。")
            
        except Exception as e:
            logger.error(f"测试过程中发生错误: {e}")
            raise

def main():
    """主函数"""
    try:
        tester = RealWeeklyReportTester()
        tester.run_comprehensive_test()
        
    except Exception as e:
        logger.error(f"测试失败: {e}")
        sys.exit(1)

if __name__ == '__main__':
    main()