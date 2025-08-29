#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
飞书API快速测试脚本
用于快速验证飞书应用配置和基本功能
"""

import os
import sys
import json
import yaml
import requests
from pathlib import Path
from dotenv import load_dotenv

# 添加项目根目录到Python路径
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

from src.clients.enhanced_feishu_client import EnhancedFeishuClient, FeishuConfig

def load_config():
    """加载配置"""
    # 加载环境变量
    load_dotenv()
    
    config = {
        'feishu': {
            'enabled': True,
            'api_type': 'api',
            'app_id': os.getenv('FEISHU_APP_ID'),
            'app_secret': os.getenv('FEISHU_APP_SECRET'),
            'default_chat_id': '',
            'webhook_url': ''
        }
    }
    
    # 尝试从config.yaml加载配置
    config_file = project_root / 'config' / 'config.yaml'
    if config_file.exists():
        try:
            with open(config_file, 'r', encoding='utf-8') as f:
                yaml_config = yaml.safe_load(f)
                if yaml_config and 'feishu' in yaml_config:
                    config['feishu'].update(yaml_config['feishu'])
        except Exception as e:
            print(f"⚠️  读取config.yaml失败: {e}")
    
    return config

def test_basic_auth(client):
    """测试基本认证"""
    print("\n🔐 测试应用认证...")
    try:
        token = client._get_tenant_access_token()
        if token:
            print("✅ 认证成功")
            print(f"🎫 访问令牌: {token[:20]}...")
            return True
        else:
            print("❌ 认证失败")
            return False
    except Exception as e:
        print(f"❌ 认证异常: {e}")
        return False

def test_app_permissions(client):
    """测试应用权限"""
    print("\n🔍 检查应用权限...")
    try:
        token = client._get_tenant_access_token()
        if not token:
            print("❌ 无法获取访问令牌")
            return False
            
        headers = {
            'Authorization': f'Bearer {token}',
            'Content-Type': 'application/json'
        }
        
        # 测试获取机器人信息权限
        print("📱 测试机器人信息权限...")
        bot_info_url = 'https://open.feishu.cn/open-apis/bot/v3/info'
        response = requests.get(bot_info_url, headers=headers)
        
        if response.status_code == 200:
            data = response.json()
            if data.get('code') == 0:
                bot_info = data.get('data', {}).get('bot', {})
                print(f"✅ 机器人信息: {bot_info.get('app_name', 'N/A')}")
            else:
                print(f"⚠️  机器人信息获取失败: {data.get('msg', 'Unknown')}")
        else:
            print(f"❌ 机器人信息API失败: {response.status_code}")
        
        # 测试获取群聊列表权限
        print("💬 测试群聊列表权限...")
        try:
            chats = client.get_chat_list()
            if chats:
                print(f"✅ 群聊列表获取成功，共 {len(chats)} 个群聊")
                for i, chat in enumerate(chats[:3], 1):  # 只显示前3个
                    print(f"  {i}. {chat.get('name', 'N/A')} (ID: {chat.get('chat_id', 'N/A')})")
                return True
            else:
                print("⚠️  未获取到群聊列表")
                return False
        except Exception as e:
            print(f"❌ 群聊列表获取失败: {e}")
            return False
            
    except Exception as e:
        print(f"❌ 权限检查异常: {e}")
        return False

def test_message_permission(client, chat_id=None):
    """测试消息发送权限"""
    print("\n📤 测试消息发送权限...")
    
    if not chat_id:
        print("⚠️  未提供群组ID，跳过消息发送测试")
        print("💡 使用 'python quick_feishu_test.py <群组ID>' 进行消息发送测试")
        return False
    
    try:
        # 先检查群聊信息
        chat_info = client.get_chat_info(chat_id)
        if not chat_info:
            print(f"❌ 无法获取群聊信息，群组ID可能不正确: {chat_id}")
            return False
            
        print(f"✅ 群聊信息: {chat_info.get('name', 'N/A')}")
        
        # 尝试发送测试消息
        print("📝 尝试发送测试消息...")
        test_message = "🤖 飞书API测试消息 - 如果您看到这条消息，说明配置成功！"
        
        try:
            result = client.send_text_message(chat_id, test_message)
            if result:
                print("✅ 测试消息发送成功！")
                print("🎉 飞书API配置完全正常")
                return True
            else:
                print("❌ 测试消息发送失败")
                return False
        except Exception as e:
            print(f"❌ 消息发送异常: {e}")
            print("\n🔍 可能的原因:")
            print("  1. 机器人未添加到群聊中")
            print("  2. 缺少 im:message 权限")
            print("  3. 权限未审核通过")
            print("  4. 群聊不允许机器人发送消息")
            return False
            
    except Exception as e:
        print(f"❌ 消息权限测试异常: {e}")
        return False

def print_summary(auth_ok, permissions_ok, message_ok):
    """打印测试总结"""
    print("\n" + "=" * 50)
    print("📊 测试结果总结")
    print("=" * 50)
    
    total_tests = 3
    passed_tests = sum([auth_ok, permissions_ok, message_ok])
    
    print(f"✅ 认证测试: {'通过' if auth_ok else '失败'}")
    print(f"🔍 权限测试: {'通过' if permissions_ok else '失败'}")
    print(f"📤 消息测试: {'通过' if message_ok else '跳过/失败'}")
    
    print(f"\n🎯 总体结果: {passed_tests}/{total_tests} 项通过")
    
    if passed_tests == total_tests:
        print("🎉 恭喜！飞书API配置完全正常")
        print("✨ 您可以开始使用飞书功能了")
    elif passed_tests >= 2:
        print("⚠️  基本功能正常，但消息发送可能需要调整")
        print("💡 请检查机器人是否在目标群聊中")
    elif passed_tests >= 1:
        print("🔧 认证成功但权限不足")
        print("📋 请检查应用权限配置")
    else:
        print("❌ 配置存在问题，请检查应用设置")
        print("📖 请参考 FEISHU_SETUP_GUIDE.md 进行配置")

def print_next_steps(auth_ok, permissions_ok, message_ok):
    """打印下一步建议"""
    print("\n🎯 下一步建议:")
    
    if not auth_ok:
        print("1. 检查 App ID 和 App Secret 配置")
        print("2. 确认应用凭证正确")
        print("3. 检查网络连接")
    elif not permissions_ok:
        print("1. 登录飞书开放平台检查权限配置")
        print("2. 确保所有必需权限已申请并审核通过")
        print("3. 检查应用是否已发布")
    elif not message_ok:
        print("1. 将机器人添加到目标群聊")
        print("2. 确认群聊允许机器人发送消息")
        print("3. 检查 im:message 权限状态")
    else:
        print("1. 运行完整测试: python test_enhanced_feishu.py")
        print("2. 配置群组映射: 编辑 feishu_mapping.json")
        print("3. 开始使用飞书通知功能")
    
    print("\n📚 更多帮助:")
    print("- 查看配置指南: FEISHU_SETUP_GUIDE.md")
    print("- 运行权限检查: python check_feishu_permissions.py")
    print("- 获取群组ID: python get_feishu_ids.py")

def main():
    """主函数"""
    print("🚀 飞书API快速测试")
    print("=" * 50)
    
    # 加载配置
    config = load_config()
    
    # 检查基本配置
    if not config['feishu']['app_id'] or not config['feishu']['app_secret']:
        print("❌ 飞书应用配置不完整")
        print("\n📋 请设置以下配置:")
        print("环境变量:")
        print("  - FEISHU_APP_ID")
        print("  - FEISHU_APP_SECRET")
        print("\n或在 config/config.yaml 中配置:")
        print("  feishu:")
        print("    app_id: 'your_app_id'")
        print("    app_secret: 'your_app_secret'")
        return
    
    print(f"📱 App ID: {config['feishu']['app_id'][:10]}...")
    print(f"🔑 App Secret: {'已配置' if config['feishu']['app_secret'] else '未配置'}")
    
    # 创建飞书客户端
    feishu_config = FeishuConfig(
        app_id=config['feishu']['app_id'],
        app_secret=config['feishu']['app_secret']
    )
    client = EnhancedFeishuClient(feishu_config)
    
    # 运行测试
    auth_ok = test_basic_auth(client)
    permissions_ok = test_app_permissions(client) if auth_ok else False
    
    # 检查是否提供了群组ID
    chat_id = sys.argv[1] if len(sys.argv) > 1 else None
    message_ok = test_message_permission(client, chat_id) if permissions_ok else False
    
    # 打印结果
    print_summary(auth_ok, permissions_ok, message_ok)
    print_next_steps(auth_ok, permissions_ok, message_ok)

if __name__ == '__main__':
    main()