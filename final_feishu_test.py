#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
最终飞书消息发送验证脚本
用于确认用户是否能真正收到飞书消息
"""

import os
import sys
import json
from datetime import datetime
from dotenv import load_dotenv

# 加载环境变量
load_dotenv()

# 添加项目根目录到Python路径
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from src.clients.feishu_client import FeishuClient

def main():
    print("=== 飞书消息发送最终验证 ===")
    print(f"测试时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print()
    
    # 1. 检查环境变量
    print("1. 检查环境变量...")
    app_id = os.getenv('FEISHU_APP_ID')
    app_secret = os.getenv('FEISHU_APP_SECRET')
    
    if not app_id or not app_secret:
        print("❌ 飞书环境变量未配置")
        print(f"   FEISHU_APP_ID: {'已设置' if app_id else '未设置'}")
        print(f"   FEISHU_APP_SECRET: {'已设置' if app_secret else '未设置'}")
        return False
    
    print(f"✅ 环境变量已配置")
    print(f"   APP_ID: {app_id[:8]}...")
    print(f"   APP_SECRET: {app_secret[:8]}...")
    print()
    
    # 2. 初始化飞书客户端
    print("2. 初始化飞书客户端...")
    try:
        feishu_config = {
            'api': {
                'app_id': app_id,
                'app_secret': app_secret,
                'base_url': 'https://open.feishu.cn',
                'timeout': 30,
                'max_retries': 3,
                'retry_delay': 1
            },
            'mapping_file': 'feishu_mapping.json'
        }
        
        client = FeishuClient(feishu_config)
        print("✅ 飞书客户端初始化成功")
    except Exception as e:
        print(f"❌ 飞书客户端初始化失败: {e}")
        return False
    print()
    
    # 3. 检查用户映射
    print("3. 检查用户映射...")
    try:
        feishu_id = client._get_feishu_user_id('leejhua')
        if feishu_id:
            print(f"✅ 用户映射正常")
            print(f"   GitHub用户: leejhua")
            print(f"   飞书ID: {feishu_id}")
        else:
            print("❌ 无法获取用户飞书ID")
            return False
    except Exception as e:
        print(f"❌ 检查用户映射失败: {e}")
        return False
    print()
    
    # 4. 获取访问令牌
    print("4. 获取访问令牌...")
    try:
        token = client._get_access_token()
        if token:
            print(f"✅ 访问令牌获取成功")
            print(f"   Token: {token[:20]}...")
        else:
            print("❌ 无法获取访问令牌")
            return False
    except Exception as e:
        print(f"❌ 获取访问令牌失败: {e}")
        return False
    print()
    
    # 5. 发送测试消息
    print("5. 发送测试消息...")
    test_message = f"""
🔔 **飞书消息发送测试**

测试时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
测试目的: 验证飞书API消息发送功能

如果您收到这条消息，说明飞书API配置正确，消息发送功能正常！

---
此消息由系统自动发送，用于测试目的。
    """.strip()
    
    try:
        print(f"发送消息给用户: leejhua")
        print(f"消息内容预览: {test_message[:50]}...")
        
        success = client._send_private_message(
            user_id='leejhua',  # GitHub用户名
            message_content=test_message
        )
        
        if success:
            print("✅ 测试消息发送成功！")
            print()
            print("📱 请检查您的飞书客户端是否收到测试消息")
            print("💡 如果没有收到消息，可能的原因：")
            print("   1. 飞书应用权限不足")
            print("   2. 用户未安装或登录飞书客户端")
            print("   3. 用户ID映射不正确")
            print("   4. 网络连接问题")
            return True
        else:
            print("❌ 测试消息发送失败")
            return False
            
    except Exception as e:
        print(f"❌ 发送测试消息时发生错误: {e}")
        return False

if __name__ == '__main__':
    try:
        success = main()
        print()
        if success:
            print("🎉 飞书消息发送验证完成！")
            print("📋 总结: 所有测试步骤均通过，消息已成功发送")
        else:
            print("❌ 飞书消息发送验证失败")
            print("🔧 请检查上述错误信息并修复相关问题")
    except KeyboardInterrupt:
        print("\n⏹️ 测试被用户中断")
    except Exception as e:
        print(f"\n💥 测试过程中发生未预期的错误: {e}")