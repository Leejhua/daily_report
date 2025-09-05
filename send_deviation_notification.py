#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import json
import os
import requests
import yaml
import argparse
from datetime import datetime
from typing import Dict, Any, Optional
from src.schedulers.notification_scheduler import NotificationScheduler
from src.clients.feishu_client import FeishuClient
from src.generators.report_generator import ReportGenerator

class FeishuNotificationSender:
    def __init__(self, config):
        self.config = config
        self.notification_scheduler = NotificationScheduler(config)
        
        # 创建正确的Config实例以确保GLM配置可用
        from src.config import Config
        try:
            # 创建包含环境变量配置的Config实例
            full_config = Config()
            self.report_generator = ReportGenerator(full_config)
            print(f"✅ ReportGenerator初始化成功，GLM客户端状态: {'已配置' if self.report_generator.glm_client else '未配置'}")
        except Exception as e:
            print(f"⚠️ 创建完整Config实例失败，使用YAML配置: {e}")
            self.report_generator = ReportGenerator(config)
        
        # 构建飞书客户端配置
        feishu_config = {
            'api': {
                'app_id': os.getenv('FEISHU_APP_ID'),
                'app_secret': os.getenv('FEISHU_APP_SECRET'),
                'base_url': 'https://open.feishu.cn',
                'timeout': 30,
                'max_retries': 3,
                'retry_delay': 1.0
            },
            'management_users': {
                'enabled': True,
                'user_ids': ['ou_6fb88a7bee0b98c450beb18e25152456'],  # leejhua的正确飞书用户ID
                'notification_type': 'private'
            },
            'mapping_file': 'feishu_github_mapping.json'
        }
        
        self.feishu_client = FeishuClient(feishu_config)
        self.app_id = os.getenv('FEISHU_APP_ID', 'cli_a827d9eb278b101c')
        self.app_secret = os.getenv('FEISHU_APP_SECRET', 'U2kstRSDlTkWpa6FKUEIUdHM0LfGLxQk')
        self.access_token = None
        
        # 从.env文件加载配置
        self.load_env_config()
    
    def load_env_config(self):
        """从.env文件加载配置"""
        env_file = '.env'
        if os.path.exists(env_file):
            with open(env_file, 'r', encoding='utf-8') as f:
                for line in f:
                    line = line.strip()
                    if line and not line.startswith('#') and '=' in line:
                        key, value = line.split('=', 1)
                        if key == 'FEISHU_APP_ID':
                            self.app_id = value
                        elif key == 'FEISHU_APP_SECRET':
                            self.app_secret = value
    
    def get_access_token(self) -> Optional[str]:
        """获取访问令牌"""
        url = 'https://open.feishu.cn/open-apis/auth/v3/tenant_access_token/internal'
        headers = {
            'Content-Type': 'application/json; charset=utf-8'
        }
        data = {
            'app_id': self.app_id,
            'app_secret': self.app_secret
        }
        
        try:
            response = requests.post(url, headers=headers, json=data)
            response.raise_for_status()
            result = response.json()
            
            if result.get('code') == 0:
                self.access_token = result.get('tenant_access_token')
                return self.access_token
            else:
                print(f"获取访问令牌失败: {result.get('msg', 'Unknown error')}")
                return None
        except Exception as e:
            print(f"获取访问令牌时发生错误: {e}")
            return None
    
    def load_analysis_report(self, report_file: str = None, user_name: str = "leejhua") -> Optional[Dict[str, Any]]:
        """加载分析报告"""
        if report_file:
            try:
                with open(report_file, 'r', encoding='utf-8') as f:
                    return json.load(f)
            except FileNotFoundError:
                print(f"找不到分析报告文件: {report_file}")
                return None
            except json.JSONDecodeError:
                print(f"分析报告文件格式错误: {report_file}")
                return None
        else:
            # 加载leejhua的偏离数据
            leejhua_data_file = "data/leejhua_deviation_data.json"
            try:
                with open(leejhua_data_file, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    
                # 提取leejhua的数据
                leejhua_data = data.get("leejhua", {})
                if not leejhua_data:
                    print(f"未找到用户 {user_name} 的数据")
                    return None
                
                # 计算统计信息
                dates = sorted(leejhua_data.keys())
                scores = [leejhua_data[date]["score"] for date in dates]
                completion_rates = [leejhua_data[date]["completion_rate"] for date in dates]
                
                # 构建分析报告格式
                return {
                    "user_name": "李嘉华",
                    "user_id": "leejhua",
                    "consecutive_days": len(dates),
                    "avg_score": sum(scores) / len(scores),
                    "avg_completion_rate": sum(completion_rates) / len(completion_rates),
                    "deviation_dates": dates,
                    "deviation_scores": scores,
                    "completion_rates": completion_rates,
                    "detailed_data": leejhua_data,
                    "analysis_summary": f"用户李嘉华在{dates[0]}到{dates[-1]}期间连续{len(dates)}天出现工作偏离，平均偏离分数{sum(scores)/len(scores):.1f}，平均完成率{sum(completion_rates)/len(completion_rates)*100:.1f}%。偏离原因包括密集会议、客户现场出差和生产环境故障处理。"
                }
            except FileNotFoundError:
                print(f"找不到leejhua数据文件: {leejhua_data_file}")
                # 返回默认模拟数据
                return {
                    "user_name": "李嘉华",
                    "user_id": "user_001",
                    "consecutive_days": 3,
                    "avg_score": 2.5,
                    "deviation_dates": ["2024-01-15", "2024-01-16", "2024-01-17"],
                    "deviation_scores": [2.3, 2.7, 2.5],
                    "analysis_summary": "用户在过去3天中工作状态持续偏离正常水平，需要关注和改进。"
                }
            except json.JSONDecodeError:
                print(f"leejhua数据文件格式错误: {leejhua_data_file}")
                return None
    
    def format_notification_message(self, report: Dict[str, Any]) -> str:
        """使用优化过的个人通知模板格式化消息"""
        user_info = report.get('user_info', {})
        analysis_summary = report.get('analysis_summary', {})
        trend_analysis = report.get('trend_analysis', {})
        meeting_analysis = report.get('meeting_analysis', {})
        recommendations = report.get('recommendations', [])
        severity = report.get('severity_level', 'unknown')
        
        # 构建偏离信息字典
        period = analysis_summary.get('analysis_period', {})
        deviation_info = {
            'user': user_info.get('name', 'Unknown'),
            'period': {
                'start': period.get('start_date', ''),
                'end': period.get('end_date', '')
            },
            'total_deviation_hours': analysis_summary.get('total_deviation_hours', 0),
            'deviation_percentage': analysis_summary.get('deviation_percentage', 0),
            'severity': severity,
            'consecutive_deviation_days': trend_analysis.get('max_consecutive_deviation_days', 0),
            'details': {
                'average_daily_deviation_rate': trend_analysis.get('average_deviation_rate', 0),
                'total_meeting_hours': meeting_analysis.get('total_meeting_hours', 0),
                'most_time_consuming_meeting_type': meeting_analysis.get('most_time_consuming_type', 'unknown')
            },
            'suggestions': recommendations,
            'report_generated_at': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        }
        
        # 加载配置并使用NotificationScheduler的_format_personal_message方法
        try:
            with open('config/config.yaml', 'r', encoding='utf-8') as f:
                config = yaml.safe_load(f)
        except Exception as e:
            # 如果配置文件加载失败，使用默认配置
            config = {
                'deviation_tracking': {},
                'report': {},
                'feishu': {'enabled': False},
                'storage': {'base_dir': 'data'}
            }
        
        scheduler = NotificationScheduler(config)
        return scheduler._format_personal_message(
            report_content=json.dumps(report, ensure_ascii=False, indent=2),
            user=user_info.get('name', 'Unknown'),
            deviation=deviation_info
        )
    
    def send_message_to_user(self, user_id: str, message: str) -> bool:
        """发送消息给指定用户"""
        if not self.access_token:
            if not self.get_access_token():
                return False
        
        url = 'https://open.feishu.cn/open-apis/im/v1/messages'
        headers = {
            'Authorization': f'Bearer {self.access_token}',
            'Content-Type': 'application/json; charset=utf-8'
        }
        
        data = {
            'receive_id': user_id,
            'msg_type': 'text',
            'content': json.dumps({
                'text': message
            }, ensure_ascii=False)
        }
        
        # receive_id_type作为查询参数
        params = {
            'receive_id_type': 'open_id'
        }
        
        try:
            print(f"发送请求到: {url}")
            print(f"请求头: {headers}")
            print(f"请求数据: {json.dumps(data, ensure_ascii=False, indent=2)}")
            print(f"查询参数: {params}")
            
            response = requests.post(url, headers=headers, json=data, params=params)
            print(f"响应状态码: {response.status_code}")
            print(f"响应内容: {response.text}")
            
            if response.status_code == 200:
                result = response.json()
                if result.get('code') == 0:
                    print(f"消息发送成功! 消息ID: {result.get('data', {}).get('message_id', 'Unknown')}")
                    return True
                else:
                    print(f"消息发送失败: {result.get('msg', 'Unknown error')}")
                    print(f"错误代码: {result.get('code')}")
                    return False
            else:
                print(f"HTTP请求失败: {response.status_code} - {response.text}")
                return False
        except Exception as e:
            print(f"发送消息时发生错误: {e}")
            return False
    
    async def generate_llm_report(self, report_type: str = "personal") -> str:
        """生成LLM分析报告
        
        Args:
            report_type: 报告类型，"personal" 或 "management"
            
        Returns:
            LLM生成的报告内容
        """
        # 加载分析报告数据
        report_data = self.load_analysis_report()
        if not report_data:
            return "无法加载分析报告数据"
        
        # 准备用户名称
        user_name = report_data.get("user_name", "测试用户")
        
        # 将详细数据转换为ReportGenerator期望的格式
        detailed_data = report_data.get("detailed_data", {})
        analyses = []
        
        for date, day_data in detailed_data.items():
            analyses.append({
                "analysis_date": date,
                "score": day_data.get("score", 0),
                "completion_rate": day_data.get("completion_rate", 0),
                "deviation_reasons": day_data.get("deviation_reasons", []),
                "additional_work": day_data.get("additional_work", []),
                "suggestions": day_data.get("suggestions", []),
                "summary": day_data.get("summary", ""),
                "confidence": day_data.get("confidence", 0),
                "user_id": day_data.get("user_id", "leejhua"),
                "is_deviation": day_data.get("is_deviation", True),
                "grade": day_data.get("grade", "需改进")
            })
        
        print(f"转换后的分析数据: {len(analyses)}条记录")
        for i, analysis in enumerate(analyses):
            print(f"第{i+1}天: {analysis['analysis_date']}, 分数: {analysis['score']}, 完成率: {analysis['completion_rate']*100:.1f}%")
        
        # 调用ReportGenerator生成LLM报告
        try:
            report_result = self.report_generator.generate_llm_report(
                user_name=user_name,
                analyses=analyses,
                report_type=report_type
            )
            
            if report_result.get("success"):
                return report_result.get("content", "报告生成成功但内容为空")
            else:
                return f"报告生成失败: {report_result.get('error', '未知错误')}"
                
        except Exception as e:
            print(f"生成LLM报告失败: {e}")
            return f"生成LLM报告失败: {e}"
    
    async def send_notification(self, report_type: str = "personal"):
        """发送通知
        
        Args:
            report_type: 报告类型，"personal" 或 "management"
        """
        # 生成LLM报告
        report_content = await self.generate_llm_report(report_type)
        
        print(f"\n=== {report_type.upper()} 报告 ===")
        print(report_content)
        print("=" * 50)
        
        # 根据报告类型选择发送方式，使用飞书API而不是webhook
        try:
            if report_type == "management":
                # 发送管理层通知 - 使用飞书API
                success = self.feishu_client.send_management_notification(report_content)
            else:
                # 发送个人偏离通知 - 使用飞书API发送私聊消息
                # 直接传递GitHub用户名，让_send_private_message方法内部处理ID转换
                username = "leejhua"
                success = self.feishu_client._send_private_message(
                     user_id=username,  # 传递GitHub用户名而不是飞书ID
                     message_content=report_content
                 )
                if success:
                    print(f"✅ 个人报告已通过飞书API发送给用户: {username}")
                else:
                    print(f"❌ 发送飞书API消息失败")
            
            if report_type == "management":
                if success:
                    print(f"✅ {report_type} 报告已成功通过飞书API发送")
                else:
                    print(f"❌ {report_type} 报告通过飞书API发送失败")
        except Exception as e:
            print(f"❌ 发送飞书API消息失败: {e}")
    
    def send_deviation_notification(self, report_file: str, user_id: str) -> bool:
        """发送偏离通知"""
        # 加载分析报告
        report = self.load_analysis_report(report_file)
        if not report:
            return False
        
        # 格式化消息
        message = self.format_notification_message(report)
        
        # 发送消息
        return self.send_message_to_user(user_id, message)

async def main():
    try:
        # 解析命令行参数
        parser = argparse.ArgumentParser(description='发送偏离分析通知')
        parser.add_argument('--type', choices=['personal', 'management'], 
                          default='personal', help='报告类型：personal(个人) 或 management(管理层)')
        parser.add_argument('--legacy', action='store_true', help='使用原有的发送方式')
        args = parser.parse_args()
        
        # 加载配置
        config_path = os.path.join(os.path.dirname(__file__), 'config', 'config.yaml')
        
        if os.path.exists(config_path):
            with open(config_path, 'r', encoding='utf-8') as f:
                config = yaml.safe_load(f)
        else:
            # 默认配置
            config = {
                'feishu': {
                    'app_id': 'your_app_id',
                    'app_secret': 'your_app_secret'
                },
                'notification': {
                    'templates': {
                        'personal': {
                            'title': '工作状态提醒',
                            'content': '您好 {user_name}，检测到您最近 {consecutive_days} 天工作状态有所偏离，平均分数为 {avg_score}。请注意调整工作状态。'
                        }
                    }
                }
            }
        
        if args.legacy:
            # 使用原有的发送方式
            leejhua_user_id = 'ou_6fb88a7bee0b98c450beb18e25152456'
            report_file = 'leejhua_deviation_analysis_report.json'
            
            print("正在发送会议偏离分析通知给leejhua...")
            
            sender = FeishuNotificationSender(config)
            success = sender.send_deviation_notification(report_file, leejhua_user_id)
            
            if success:
                print("✅ 通知发送成功!")
                print(f"📧 已向用户 {leejhua_user_id} 发送会议偏离分析报告")
            else:
                print("❌ 通知发送失败!")
                print("请检查网络连接和API配置")
        else:
            # 创建发送器并发送通知
            sender = FeishuNotificationSender(config)
            await sender.send_notification(report_type=args.type)
        
    except Exception as e:
        print(f"程序执行失败: {e}")

if __name__ == '__main__':
    import asyncio
    asyncio.run(main())