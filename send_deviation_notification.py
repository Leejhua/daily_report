#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import json
import os
import requests
from datetime import datetime
from typing import Dict, Any, Optional

class FeishuNotificationSender:
    def __init__(self):
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
    
    def load_analysis_report(self, report_file: str) -> Optional[Dict[str, Any]]:
        """加载分析报告"""
        try:
            with open(report_file, 'r', encoding='utf-8') as f:
                return json.load(f)
        except FileNotFoundError:
            print(f"找不到分析报告文件: {report_file}")
            return None
        except json.JSONDecodeError:
            print(f"分析报告文件格式错误: {report_file}")
            return None
    
    def format_notification_message(self, report: Dict[str, Any]) -> str:
        """格式化通知消息"""
        user_info = report.get('user_info', {})
        analysis_summary = report.get('analysis_summary', {})
        trend_analysis = report.get('trend_analysis', {})
        meeting_analysis = report.get('meeting_analysis', {})
        recommendations = report.get('recommendations', [])
        severity = report.get('severity_level', 'unknown')
        
        # 严重程度对应的emoji和描述
        severity_info = {
            'critical': {'emoji': '🚨', 'desc': '严重'},
            'high': {'emoji': '⚠️', 'desc': '高'},
            'medium': {'emoji': '⚡', 'desc': '中等'},
            'low': {'emoji': '💡', 'desc': '轻微'}
        }
        
        severity_emoji = severity_info.get(severity, {}).get('emoji', '📊')
        severity_desc = severity_info.get(severity, {}).get('desc', '未知')
        
        period = analysis_summary.get('analysis_period', {})
        start_date = period.get('start_date', '')
        end_date = period.get('end_date', '')
        
        message = f"""{severity_emoji} **会议偏离分析报告**

👤 **用户**: {user_info.get('name', 'Unknown')}
📅 **分析期间**: {start_date} 至 {end_date}
⏰ **总偏离时间**: {analysis_summary.get('total_deviation_hours', 0)} 小时
📈 **偏离百分比**: {analysis_summary.get('deviation_percentage', 0)}%
🎯 **严重程度**: {severity_desc}
📊 **连续偏离**: {trend_analysis.get('max_consecutive_deviation_days', 0)} 天

**📋 详细分析**:
• 平均每日偏离率: {trend_analysis.get('average_deviation_rate', 0)}%
• 总会议时间: {meeting_analysis.get('total_meeting_hours', 0)} 小时
• 最耗时会议类型: {meeting_analysis.get('most_time_consuming_type', 'unknown')}

**💡 改进建议**:
"""
        
        # 添加前5个建议
        for i, recommendation in enumerate(recommendations[:5], 1):
            message += f"{i}. {recommendation}\n"
        
        message += f"\n📝 **报告生成时间**: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}"
        message += "\n\n请及时调整工作安排，提高工作效率！💪"
        
        return message
    
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

def main():
    # leejhua的飞书用户ID
    leejhua_user_id = 'ou_6fb88a7bee0b98c450beb18e25152456'
    report_file = 'leejhua_deviation_analysis_report.json'
    
    print("正在发送会议偏离分析通知给leejhua...")
    
    sender = FeishuNotificationSender()
    success = sender.send_deviation_notification(report_file, leejhua_user_id)
    
    if success:
        print("✅ 通知发送成功!")
        print(f"📧 已向用户 {leejhua_user_id} 发送会议偏离分析报告")
    else:
        print("❌ 通知发送失败!")
        print("请检查网络连接和API配置")

if __name__ == '__main__':
    main()