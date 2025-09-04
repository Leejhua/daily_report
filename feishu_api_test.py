#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
飞书API真实测试脚本
测试使用app_id和app_secret进行API认证，发送私聊和群聊消息
"""

import os
import sys
import json
import logging
from datetime import datetime
from pathlib import Path

# 添加项目根目录到Python路径
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

from src.clients.feishu_client import FeishuClient
from src.models.data_models import DeviationAnalysisResult
from src.weekly_summarizer import UserWeeklyData
from src.config import Config

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

class FeishuAPITester:
    """飞书API测试器"""
    
    def __init__(self):
        self.config = None
        self.feishu_client = None
        self.user_mapping = {}
        
    def load_config(self):
        """加载配置"""
        try:
            logger.info("正在加载配置...")
            self.config = Config()
            
            # 检查飞书配置
            if not hasattr(self.config, 'feishu') or not self.config.feishu:
                logger.error("未找到飞书配置")
                return False
                
            feishu_config = self.config.feishu
            logger.info(f"飞书配置加载成功: {type(feishu_config)}")
            
            # 检查必要的API配置
            if hasattr(feishu_config, 'api') and feishu_config.api.app_id:
                logger.info(f"App ID: {feishu_config.api.app_id[:10]}...")
            else:
                logger.error("未找到app_id配置")
                return False
                
            if hasattr(feishu_config, 'api') and feishu_config.api.app_secret:
                logger.info(f"App Secret: {feishu_config.api.app_secret[:10]}...")
            else:
                logger.error("未找到app_secret配置")
                return False
                
            return True
            
        except Exception as e:
            logger.error(f"加载配置失败: {e}")
            return False
    
    def load_user_mapping(self):
        """加载用户映射"""
        try:
            mapping_file = project_root / "feishu_mapping.json"
            if mapping_file.exists():
                with open(mapping_file, 'r', encoding='utf-8') as f:
                    mapping_data = json.load(f)
                    # 提取实际的用户映射数据
                    self.user_mapping = mapping_data.get('user_mapping', {})
                logger.info(f"用户映射加载成功，共{len(self.user_mapping)}个用户")
                for github_user, feishu_id in self.user_mapping.items():
                    logger.info(f"  {github_user} -> {feishu_id}")
                return True
            else:
                logger.warning(f"用户映射文件不存在: {mapping_file}")
                return False
        except Exception as e:
            logger.error(f"加载用户映射失败: {e}")
            return False
    
    def initialize_client(self):
        """初始化飞书客户端"""
        try:
            logger.info("正在初始化飞书客户端...")
            self.feishu_client = FeishuClient(self.config.feishu)
            logger.info("飞书客户端初始化成功")
            return True
        except Exception as e:
            logger.error(f"初始化飞书客户端失败: {e}")
            return False
    
    def test_access_token(self):
        """测试获取访问令牌"""
        try:
            logger.info("正在测试API认证...")
            # 调用私有方法获取访问令牌
            token = self.feishu_client._get_access_token()
            if token:
                logger.info(f"API认证成功，获取到访问令牌: {token[:20]}...")
                return True
            else:
                logger.error("API认证失败，未获取到访问令牌")
                return False
        except Exception as e:
            logger.error(f"API认证测试失败: {e}")
            return False
    
    def create_mock_weekly_data(self):
        """创建模拟周报数据"""
        try:
            # 创建模拟的偏差分析结果
            deviation_result = DeviationAnalysisResult(
                score=85,
                completion_rate=0.9,
                deviation_reasons=["部分任务延期"],
                additional_work=["额外的代码优化工作"],
                suggestions=["建议提前规划时间"],
                summary="本周工作完成度较好，有少量延期",
                confidence=0.8,
                user_id="test_user",
                analysis_date=datetime.now().strftime("%Y-%m-%d"),
                discussion_number=1,
                is_deviation=True,
                raw_analysis_text="原始分析文本",
                content_type="weekly_report",
                original_content="原始内容"
            )
            
            # 创建模拟的用户周报数据
            weekly_data = UserWeeklyData(
                user_id="test_user",
                week_id="2024-W03",
                total_reports=5,
                deviation_count=1,
                avg_score=8.5,
                daily_summaries=["完成任务1", "完成任务2", "处理额外工作"],
                daily_plans=["计划任务1", "计划任务2"],
                weekly_plans=["下周任务1", "下周任务2"],
                work_completion_rate=0.9,
                key_achievements=["重要成就1", "重要成就2"],
                identified_issues=["发现问题1"],
                analysis_results=[deviation_result]
            )
            
            logger.info("模拟周报数据创建成功")
            return weekly_data
            
        except Exception as e:
            logger.error(f"创建模拟周报数据失败: {e}")
            return None
    
    def test_private_message(self, test_user_id=None):
        """测试发送私聊消息"""
        try:
            logger.info("正在测试私聊消息发送...")
            
            # 如果没有指定测试用户，使用映射中的第一个用户
            if not test_user_id and self.user_mapping:
                test_github_user = list(self.user_mapping.keys())[0]  # 取第一个GitHub用户名
                test_user_id = self.user_mapping[test_github_user]  # 对应的飞书用户ID
                logger.info(f"使用测试用户: {test_github_user} -> {test_user_id}")
            
            if not test_user_id:
                logger.error("未找到可用的测试用户")
                return False
            
            # 构建简单的文本消息
            message_content = "这是一条API测试消息 - " + datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            
            result = self.feishu_client._send_private_message(
                user_id=test_user_id,
                message_content=message_content
            )
            
            if result:
                logger.info("私聊消息发送成功")
                return True
            else:
                logger.error("私聊消息发送失败")
                return False
                
        except Exception as e:
            logger.error(f"私聊消息测试失败: {e}")
            return False
    
    def test_weekly_report_message(self, test_user_id=None):
        """测试发送周报消息"""
        try:
            logger.info("正在测试周报消息发送...")
            
            # 创建模拟周报数据
            weekly_data = self.create_mock_weekly_data()
            if not weekly_data:
                return False
            
            # 如果没有指定测试用户，使用映射中的第一个用户
            if not test_user_id and self.user_mapping:
                test_user_id = list(self.user_mapping.values())[0]
                test_github_user = list(self.user_mapping.keys())[0]
                logger.info(f"使用测试用户: {test_github_user} -> {test_user_id}")
            
            if not test_user_id:
                logger.error("没有可用的测试用户ID")
                return False
            
            # 构建周报内容
            report_content = f"""
📊 周报汇总 - {weekly_data.week_id}

👤 用户: {weekly_data.user_id}
📈 完成率: {weekly_data.work_completion_rate * 100:.1f}%
⭐ 平均评分: {weekly_data.avg_score}
📝 总报告数: {weekly_data.total_reports}
⚠️ 偏离次数: {weekly_data.deviation_count}

🎯 主要成就:
{chr(10).join([f'• {achievement}' for achievement in weekly_data.key_achievements])}

📋 每日总结:
{chr(10).join([f'• {summary}' for summary in weekly_data.daily_summaries])}

📅 下周计划:
{chr(10).join([f'• {plan}' for plan in weekly_data.weekly_plans])}
"""
            
            # 发送周报消息 - 使用飞书用户ID而不是GitHub用户名
            test_user_github = list(self.user_mapping.keys())[0]  # 取第一个GitHub用户名
            test_feishu_id = self.user_mapping[test_user_github]  # 对应的飞书用户ID
            result = self.feishu_client.send_weekly_report(
                report_content=report_content,
                report_type="employee",
                users=[test_feishu_id]  # 传入飞书用户ID
            )
            
            if result:
                logger.info("周报消息发送成功")
                return True
            else:
                logger.error("周报消息发送失败")
                return False
                
        except Exception as e:
            logger.error(f"周报消息测试失败: {e}")
            return False
    
    def test_group_message(self):
        """测试发送群聊消息"""
        try:
            logger.info("正在测试群聊消息发送...")
            
            # 检查是否配置了默认群聊ID
            if hasattr(self.config.feishu, 'default_chat_id') and self.config.feishu.default_chat_id:
                chat_id = self.config.feishu.default_chat_id
                logger.info(f"使用配置的群聊ID: {chat_id}")
                
                # 创建测试消息
                test_message = {
                    "msg_type": "text",
                    "content": {
                        "text": f"飞书API群聊测试消息 - {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}"
                    }
                }
                
                # 这里需要实现群聊消息发送方法
                # 目前FeishuClient可能没有直接的群聊API方法
                logger.warning("群聊消息发送功能需要在FeishuClient中实现")
                return False
            else:
                logger.warning("未配置默认群聊ID，跳过群聊消息测试")
                return False
                
        except Exception as e:
            logger.error(f"群聊消息测试失败: {e}")
            return False
    
    def run_all_tests(self):
        """运行所有测试"""
        logger.info("=" * 50)
        logger.info("开始飞书API测试")
        logger.info("=" * 50)
        
        test_results = {
            "config_load": False,
            "user_mapping": False,
            "client_init": False,
            "api_auth": False,
            "private_message": False,
            "weekly_report": False,
            "group_message": False
        }
        
        # 1. 加载配置
        test_results["config_load"] = self.load_config()
        if not test_results["config_load"]:
            logger.error("配置加载失败，终止测试")
            return test_results
        
        # 2. 加载用户映射
        test_results["user_mapping"] = self.load_user_mapping()
        
        # 3. 初始化客户端
        test_results["client_init"] = self.initialize_client()
        if not test_results["client_init"]:
            logger.error("客户端初始化失败，终止测试")
            return test_results
        
        # 4. 测试API认证
        test_results["api_auth"] = self.test_access_token()
        if not test_results["api_auth"]:
            logger.error("API认证失败，跳过消息发送测试")
            return test_results
        
        # 5. 测试私聊消息
        test_results["private_message"] = self.test_private_message()
        
        # 6. 测试周报消息
        test_results["weekly_report"] = self.test_weekly_report_message()
        
        # 7. 测试群聊消息
        test_results["group_message"] = self.test_group_message()
        
        # 输出测试结果
        logger.info("=" * 50)
        logger.info("测试结果汇总:")
        logger.info("=" * 50)
        for test_name, result in test_results.items():
            status = "✓ 通过" if result else "✗ 失败"
            logger.info(f"{test_name:15} : {status}")
        
        # 计算成功率
        passed_tests = sum(test_results.values())
        total_tests = len(test_results)
        success_rate = (passed_tests / total_tests) * 100
        logger.info(f"\n总体成功率: {passed_tests}/{total_tests} ({success_rate:.1f}%)")
        
        return test_results

def main():
    """主函数"""
    tester = FeishuAPITester()
    results = tester.run_all_tests()
    
    # 根据测试结果设置退出码
    if results["config_load"] and results["client_init"] and results["api_auth"]:
        sys.exit(0)  # 基本功能正常
    else:
        sys.exit(1)  # 基本功能异常

if __name__ == "__main__":
    main()