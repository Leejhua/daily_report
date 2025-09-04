#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
最终飞书周报测试脚本

这个脚本用于验证飞书周报功能是否正常工作，包括：
1. 使用真实的飞书配置
2. 生成并发送周报消息
3. 验证消息是否成功发送
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

from src.clients.feishu_client import FeishuClient
from src.config import Config

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler('feishu_test.log', encoding='utf-8')
    ]
)
logger = logging.getLogger(__name__)

class FinalFeishuTester:
    """最终飞书测试器"""
    
    def __init__(self):
        """初始化测试器"""
        logger.info("初始化最终飞书测试器...")
        
        # 检查环境变量
        self._check_environment()
        
        # 初始化飞书客户端
        self.feishu_client = self._init_feishu_client()
        
        logger.info("最终飞书测试器初始化完成")
    
    def _check_environment(self):
        """检查环境变量配置"""
        logger.info("检查环境变量配置...")
        
        required_vars = ['FEISHU_APP_ID', 'FEISHU_APP_SECRET']
        optional_vars = ['FEISHU_WEBHOOK_URL']
        
        missing_vars = []
        for var in required_vars:
            if not os.getenv(var):
                missing_vars.append(var)
            else:
                logger.info(f"✅ {var}: 已设置")
        
        for var in optional_vars:
            if os.getenv(var):
                logger.info(f"✅ {var}: 已设置")
            else:
                logger.warning(f"⚠️ {var}: 未设置")
        
        if missing_vars:
            logger.error(f"❌ 缺少必需的环境变量: {missing_vars}")
            logger.error("请设置以下环境变量:")
            for var in missing_vars:
                logger.error(f"  {var}=your_value")
            raise ValueError(f"缺少必需的环境变量: {missing_vars}")
        
        logger.info("环境变量检查完成")
    
    def _init_feishu_client(self) -> FeishuClient:
        """初始化飞书客户端"""
        logger.info("初始化飞书客户端...")
        
        # 从环境变量获取配置
        app_id = os.getenv('FEISHU_APP_ID')
        app_secret = os.getenv('FEISHU_APP_SECRET')
        webhook_url = os.getenv('FEISHU_WEBHOOK_URL', '')
        
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
            },
            'management_users': {
                'enabled': True,
                'user_ids': []  # 可以在这里添加管理员用户ID
            }
        }
        
        logger.info(f"飞书配置:")
        logger.info(f"  App ID: {app_id[:8]}...")
        logger.info(f"  Webhook URL: {'已设置' if webhook_url else '未设置'}")
        logger.info(f"  映射文件: {feishu_config['mapping_file']}")
        
        # 初始化飞书客户端
        feishu_client = FeishuClient(feishu_config)
        
        # 测试连接
        logger.info("测试飞书连接...")
        if feishu_client.test_connection():
            logger.info("✅ 飞书连接测试成功")
        else:
            logger.warning("⚠️ 飞书连接测试失败")
        
        logger.info("飞书客户端初始化完成")
        return feishu_client
    
    def create_test_report(self) -> str:
        """创建测试周报内容"""
        logger.info("创建测试周报内容...")
        
        current_time = datetime.now()
        week_start = current_time - timedelta(days=current_time.weekday())
        week_end = week_start + timedelta(days=6)
        
        report_content = f"""📊 **周报测试消息**
📅 **测试时间**: {current_time.strftime('%Y-%m-%d %H:%M:%S')}
📅 **报告周期**: {week_start.strftime('%Y-%m-%d')} ~ {week_end.strftime('%Y-%m-%d')}

## 🎯 测试目的
验证飞书周报发送功能是否正常工作

## 📋 测试内容
- ✅ 飞书客户端初始化
- ✅ 环境变量配置检查
- ✅ 周报内容生成
- 🔄 消息发送测试

## 📝 测试说明
这是一条测试消息，用于验证飞书集成是否正常工作。
如果您收到这条消息，说明飞书周报功能运行正常。

---
⏰ 发送时间: {current_time.strftime('%Y-%m-%d %H:%M:%S')}
🤖 发送方式: 飞书API/Webhook"""
        
        logger.info(f"测试周报内容生成完成，长度: {len(report_content)} 字符")
        return report_content
    
    def test_webhook_sending(self, report_content: str) -> bool:
        """测试Webhook方式发送"""
        logger.info("测试Webhook方式发送...")
        
        if not self.feishu_client.webhook_url:
            logger.warning("Webhook URL未配置，跳过Webhook测试")
            return False
        
        try:
            # 使用send_weekly_report方法发送到群聊
            success = self.feishu_client.send_weekly_report(
                report_content=report_content,
                report_type='management',
                target_type='group'
            )
            
            if success:
                logger.info("✅ Webhook消息发送成功")
                return True
            else:
                logger.error("❌ Webhook消息发送失败")
                return False
                
        except Exception as e:
            logger.error(f"❌ Webhook发送异常: {e}")
            return False
    
    def test_api_sending(self, report_content: str) -> bool:
        """测试API方式发送"""
        logger.info("测试API方式发送...")
        
        try:
            # 获取用户映射统计
            stats = self.feishu_client.get_user_mapping_stats()
            logger.info(f"用户映射统计: {stats}")
            
            if stats['total_users'] == 0:
                logger.warning("没有配置用户映射，无法测试API发送")
                return False
            
            # 发送管理层通知
            success = self.feishu_client.send_management_notification(
                report_content=report_content,
                notification_type='weekly_report'
            )
            
            if success:
                logger.info("✅ API消息发送成功")
                return True
            else:
                logger.error("❌ API消息发送失败")
                return False
                
        except Exception as e:
            logger.error(f"❌ API发送异常: {e}")
            return False
    
    def run_test(self):
        """运行完整测试"""
        logger.info("="*60)
        logger.info("开始最终飞书周报测试")
        logger.info("="*60)
        
        results = {
            'report_generation': False,
            'webhook_sending': False,
            'api_sending': False
        }
        
        try:
            # 1. 生成测试周报
            logger.info("\n" + "-"*40)
            logger.info("步骤 1: 生成测试周报")
            logger.info("-"*40)
            
            report_content = self.create_test_report()
            results['report_generation'] = True
            logger.info("✅ 测试周报生成成功")
            
            # 2. 测试Webhook发送
            logger.info("\n" + "-"*40)
            logger.info("步骤 2: 测试Webhook发送")
            logger.info("-"*40)
            
            results['webhook_sending'] = self.test_webhook_sending(report_content)
            
            # 3. 测试API发送
            logger.info("\n" + "-"*40)
            logger.info("步骤 3: 测试API发送")
            logger.info("-"*40)
            
            results['api_sending'] = self.test_api_sending(report_content)
            
        except Exception as e:
            logger.error(f"测试过程中发生异常: {e}")
        
        # 输出测试结果
        self._print_test_results(results)
    
    def _print_test_results(self, results: dict):
        """打印测试结果"""
        logger.info("\n" + "="*60)
        logger.info("测试结果汇总")
        logger.info("="*60)
        
        total_tests = len(results)
        passed_tests = sum(1 for success in results.values() if success)
        
        for test_name, success in results.items():
            status = "✅" if success else "❌"
            test_display = {
                'report_generation': '周报生成',
                'webhook_sending': 'Webhook发送',
                'api_sending': 'API发送'
            }
            logger.info(f"{test_display[test_name]}: {status}")
        
        success_rate = (passed_tests / total_tests) * 100
        logger.info(f"\n总体成功率: {passed_tests}/{total_tests} ({success_rate:.1f}%)")
        
        if passed_tests > 0:
            logger.info("\n🎉 至少有一项测试成功！请检查飞书是否收到消息。")
            if results['webhook_sending'] or results['api_sending']:
                logger.info("📱 如果您收到了飞书消息，说明集成工作正常！")
        else:
            logger.error("\n❌ 所有测试都失败了，请检查配置和网络连接。")

def main():
    """主函数"""
    try:
        tester = FinalFeishuTester()
        tester.run_test()
    except Exception as e:
        logger.error(f"测试失败: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()