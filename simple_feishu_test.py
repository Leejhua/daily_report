#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
简单飞书测试脚本

使用项目中的默认测试配置来验证飞书功能
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

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

class SimpleFeishuTester:
    """简单飞书测试器"""
    
    def __init__(self):
        """初始化测试器"""
        logger.info("初始化简单飞书测试器...")
        
        # 使用项目中的默认测试配置
        self.app_id = 'cli_a827d9eb278b101c'
        self.app_secret = 'U2kstRSDlTkWpa6FKUEIUdHM0LfGLxQk'
        
        # 初始化飞书客户端
        self.feishu_client = self._init_feishu_client()
        
        logger.info("简单飞书测试器初始化完成")
    
    def _init_feishu_client(self) -> FeishuClient:
        """初始化飞书客户端"""
        logger.info("初始化飞书客户端...")
        
        # 构建飞书配置
        feishu_config = {
            'webhook_url': '',  # 不使用webhook
            'mapping_file': 'feishu_mapping.json',
            'timeout': 30,
            'retry_count': 3,
            'api': {
                'app_id': self.app_id,
                'app_secret': self.app_secret,
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
        logger.info(f"  App ID: {self.app_id[:8]}...")
        logger.info(f"  映射文件: {feishu_config['mapping_file']}")
        
        # 初始化飞书客户端
        feishu_client = FeishuClient(feishu_config)
        
        logger.info("飞书客户端初始化完成")
        return feishu_client
    
    def test_connection(self) -> bool:
        """测试飞书连接"""
        logger.info("测试飞书连接...")
        
        try:
            result = self.feishu_client.test_connection()
            if result:
                logger.info("✅ 飞书连接测试成功")
            else:
                logger.warning("⚠️ 飞书连接测试失败")
            return result
        except Exception as e:
            logger.error(f"❌ 飞书连接测试异常: {e}")
            return False
    
    def test_user_mapping(self) -> dict:
        """测试用户映射"""
        logger.info("测试用户映射...")
        
        try:
            stats = self.feishu_client.get_user_mapping_stats()
            logger.info(f"用户映射统计: {stats}")
            
            if stats['total_users'] > 0:
                logger.info(f"✅ 找到 {stats['total_users']} 个用户映射")
                logger.info(f"  有效映射: {stats['valid_mappings']}")
                logger.info(f"  无效映射: {stats['invalid_mappings']}")
            else:
                logger.warning("⚠️ 没有找到用户映射")
            
            return stats
        except Exception as e:
            logger.error(f"❌ 用户映射测试异常: {e}")
            return {'total_users': 0, 'valid_mappings': 0, 'invalid_mappings': 0}
    
    def create_test_message(self) -> str:
        """创建测试消息"""
        current_time = datetime.now()
        
        message = f"""🤖 **飞书集成测试消息**

📅 **测试时间**: {current_time.strftime('%Y-%m-%d %H:%M:%S')}

## 🎯 测试目的
验证飞书API集成是否正常工作

## ✅ 测试项目
- 飞书客户端初始化
- API连接测试
- 用户映射检查
- 消息发送功能

## 📝 说明
这是一条自动化测试消息。如果您收到这条消息，说明飞书集成功能正常。

---
⏰ 发送时间: {current_time.strftime('%Y-%m-%d %H:%M:%S')}
🔧 测试模式: API模式"""
        
        return message
    
    def test_send_message(self, message: str) -> bool:
        """测试发送消息"""
        logger.info("测试发送消息...")
        
        try:
            # 尝试发送管理层通知
            success = self.feishu_client.send_management_notification(message)
            
            if success:
                logger.info("✅ 消息发送成功")
            else:
                logger.error("❌ 消息发送失败")
            
            return success
        except Exception as e:
            logger.error(f"❌ 消息发送异常: {e}")
            return False
    
    def run_test(self):
        """运行完整测试"""
        logger.info("="*60)
        logger.info("开始简单飞书测试")
        logger.info("="*60)
        
        results = {
            'client_init': False,
            'connection_test': False,
            'user_mapping': False,
            'message_sending': False
        }
        
        try:
            # 1. 客户端初始化（已完成）
            results['client_init'] = True
            logger.info("✅ 步骤 1: 客户端初始化成功")
            
            # 2. 连接测试
            logger.info("\n" + "-"*40)
            logger.info("步骤 2: 测试连接")
            logger.info("-"*40)
            results['connection_test'] = self.test_connection()
            
            # 3. 用户映射测试
            logger.info("\n" + "-"*40)
            logger.info("步骤 3: 测试用户映射")
            logger.info("-"*40)
            stats = self.test_user_mapping()
            results['user_mapping'] = stats['total_users'] > 0
            
            # 4. 消息发送测试
            logger.info("\n" + "-"*40)
            logger.info("步骤 4: 测试消息发送")
            logger.info("-"*40)
            
            test_message = self.create_test_message()
            logger.info(f"测试消息内容 ({len(test_message)} 字符):")
            logger.info(test_message[:200] + "..." if len(test_message) > 200 else test_message)
            
            results['message_sending'] = self.test_send_message(test_message)
            
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
        
        test_names = {
            'client_init': '客户端初始化',
            'connection_test': '连接测试',
            'user_mapping': '用户映射',
            'message_sending': '消息发送'
        }
        
        for test_key, success in results.items():
            status = "✅" if success else "❌"
            logger.info(f"{test_names[test_key]}: {status}")
        
        success_rate = (passed_tests / total_tests) * 100
        logger.info(f"\n总体成功率: {passed_tests}/{total_tests} ({success_rate:.1f}%)")
        
        if results['message_sending']:
            logger.info("\n🎉 消息发送成功！请检查飞书是否收到测试消息。")
            logger.info("📱 如果您收到了飞书消息，说明集成工作正常！")
        elif passed_tests > 0:
            logger.info("\n⚠️ 部分功能正常，但消息发送失败。")
            logger.info("请检查用户映射配置和飞书权限设置。")
        else:
            logger.error("\n❌ 所有测试都失败了，请检查配置和网络连接。")

def main():
    """主函数"""
    try:
        tester = SimpleFeishuTester()
        tester.run_test()
    except Exception as e:
        logger.error(f"测试失败: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()