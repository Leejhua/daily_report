#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
飞书配置验证测试脚本
专门测试飞书webhook和API配置是否正确
"""

import os
import sys
import json
import logging
from datetime import datetime
from pathlib import Path

# 添加项目根目录到Python路径
sys.path.append(str(Path(__file__).parent))

from src.clients.feishu_client import FeishuClient
from src.config import Config

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

class FeishuConfigTester:
    """飞书配置测试器"""
    
    def __init__(self):
        """初始化测试器"""
        self.config = Config()
        self.feishu_client = None
        self.test_results = {}
        
    def initialize_client(self):
        """初始化飞书客户端"""
        try:
            self.feishu_client = FeishuClient(self.config)
            logger.info("✅ 飞书客户端初始化成功")
            return True
        except Exception as e:
            logger.error(f"❌ 飞书客户端初始化失败: {e}")
            return False
    
    def check_environment_variables(self):
        """检查环境变量配置"""
        logger.info("\n" + "="*50)
        logger.info("检查飞书环境变量配置")
        logger.info("="*50)
        
        env_vars = {
            'FEISHU_APP_ID': os.getenv('FEISHU_APP_ID'),
            'FEISHU_APP_SECRET': os.getenv('FEISHU_APP_SECRET'),
            'FEISHU_WEBHOOK_URL': os.getenv('FEISHU_WEBHOOK_URL')
        }
        
        for var_name, var_value in env_vars.items():
            if var_value:
                # 只显示前几个字符，保护敏感信息
                masked_value = var_value[:8] + "..." if len(var_value) > 8 else var_value
                logger.info(f"✅ {var_name}: {masked_value}")
            else:
                logger.warning(f"⚠️ {var_name}: 未设置")
        
        return all(env_vars.values())
    
    def check_config_file(self):
        """检查配置文件"""
        logger.info("\n" + "="*50)
        logger.info("检查飞书配置文件")
        logger.info("="*50)
        
        config_file = Path('feishu_mapping.json')
        if config_file.exists():
            try:
                with open(config_file, 'r', encoding='utf-8') as f:
                    mapping_data = json.load(f)
                
                user_mapping = mapping_data.get('user_mapping', {})
                logger.info(f"✅ 配置文件存在: {config_file}")
                logger.info(f"📊 用户映射数量: {len(user_mapping)}")
                logger.info(f"📋 映射用户列表: {list(user_mapping.keys())}")
                return True
            except Exception as e:
                logger.error(f"❌ 配置文件读取失败: {e}")
                return False
        else:
            logger.warning(f"⚠️ 配置文件不存在: {config_file}")
            return False
    
    def test_webhook_sending(self):
        """测试webhook消息发送"""
        logger.info("\n" + "="*50)
        logger.info("测试Webhook消息发送")
        logger.info("="*50)
        
        if not self.feishu_client:
            logger.error("❌ 飞书客户端未初始化")
            return False
        
        test_message = f"🧪 飞书配置测试消息\n⏰ 发送时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n📝 这是一条测试消息，用于验证飞书webhook配置是否正确。"
        
        try:
            logger.info("发送测试消息到飞书群聊...")
            success = self.feishu_client.send_webhook_notification(test_message)
            
            if success:
                logger.info("✅ Webhook消息发送成功！")
                logger.info("📱 请检查飞书群聊是否收到测试消息")
                return True
            else:
                logger.error("❌ Webhook消息发送失败")
                return False
                
        except Exception as e:
            logger.error(f"❌ Webhook测试异常: {e}")
            return False
    
    def test_api_access(self):
        """测试API访问"""
        logger.info("\n" + "="*50)
        logger.info("测试飞书API访问")
        logger.info("="*50)
        
        if not self.feishu_client:
            logger.error("❌ 飞书客户端未初始化")
            return False
        
        try:
            # 测试获取access token
            if hasattr(self.feishu_client, '_get_access_token'):
                token = self.feishu_client._get_access_token()
                if token:
                    logger.info("✅ API访问令牌获取成功")
                    return True
                else:
                    logger.error("❌ API访问令牌获取失败")
                    return False
            else:
                logger.warning("⚠️ 无法测试API访问（方法不存在）")
                return None
                
        except Exception as e:
            logger.error(f"❌ API访问测试异常: {e}")
            return False
    
    def run_all_tests(self):
        """运行所有测试"""
        logger.info("🚀 开始飞书配置验证测试")
        logger.info("="*60)
        
        # 测试项目列表
        tests = [
            ('环境变量检查', self.check_environment_variables),
            ('配置文件检查', self.check_config_file),
            ('客户端初始化', self.initialize_client),
            ('API访问测试', self.test_api_access),
            ('Webhook发送测试', self.test_webhook_sending)
        ]
        
        results = {}
        
        for test_name, test_func in tests:
            try:
                result = test_func()
                results[test_name] = result
                self.test_results[test_name] = result
            except Exception as e:
                logger.error(f"❌ {test_name}执行异常: {e}")
                results[test_name] = False
                self.test_results[test_name] = False
        
        # 输出测试结果汇总
        self._print_test_summary(results)
        
        return results
    
    def _print_test_summary(self, results):
        """打印测试结果汇总"""
        logger.info("\n" + "="*60)
        logger.info("测试结果汇总")
        logger.info("="*60)
        
        success_count = 0
        total_count = 0
        
        for test_name, result in results.items():
            if result is None:
                status = "⚠️ 跳过"
            elif result:
                status = "✅ 通过"
                success_count += 1
            else:
                status = "❌ 失败"
            
            if result is not None:
                total_count += 1
            
            logger.info(f"{test_name}: {status}")
        
        if total_count > 0:
            success_rate = (success_count / total_count) * 100
            logger.info(f"\n总体成功率: {success_count}/{total_count} ({success_rate:.1f}%)")
            
            if success_rate == 100:
                logger.info("\n🎉 所有测试通过！飞书配置正确。")
            elif success_rate >= 80:
                logger.info("\n✅ 大部分测试通过，飞书基本配置正确。")
            elif success_rate >= 50:
                logger.info("\n⚠️ 部分测试通过，请检查失败的配置项。")
            else:
                logger.info("\n❌ 大部分测试失败，请检查飞书配置。")
        else:
            logger.info("\n⚠️ 没有有效的测试结果。")

def main():
    """主函数"""
    tester = FeishuConfigTester()
    results = tester.run_all_tests()
    
    # 根据测试结果设置退出码
    success_count = sum(1 for r in results.values() if r is True)
    total_count = sum(1 for r in results.values() if r is not None)
    
    if total_count > 0 and success_count == total_count:
        sys.exit(0)  # 所有测试通过
    else:
        sys.exit(1)  # 存在失败的测试

if __name__ == "__main__":
    main