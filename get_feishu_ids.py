#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
飞书ID获取工具
用于获取群组ID和用户ID，方便配置和测试
"""

import os
import sys
import yaml
from pathlib import Path
from dotenv import load_dotenv

# 添加项目根目录到Python路径
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

from src.clients.enhanced_feishu_client import EnhancedFeishuClient, FeishuConfig

def load_config():
    """加载配置"""
    # 加载.env文件
    env_file = project_root / ".env"
    if env_file.exists():
        load_dotenv(env_file)
    
    config = {}
    
    # 从环境变量加载
    config['app_id'] = os.getenv('FEISHU_APP_ID')
    config['app_secret'] = os.getenv('FEISHU_APP_SECRET')
    
    # 从config.yaml加载
    config_file = project_root / "config" / "config.yaml"
    if config_file.exists():
        with open(config_file, 'r', encoding='utf-8') as f:
            yaml_config = yaml.safe_load(f)
            feishu_config = yaml_config.get('feishu', {})
            
            if not config['app_id']:
                config['app_id'] = feishu_config.get('app_id')
            if not config['app_secret']:
                config['app_secret'] = feishu_config.get('app_secret')
    
    return config

def get_chat_list(client):
    """获取群组列表"""
    print("\n=== 获取群组列表 ===")
    try:
        chats = client.get_chat_list(page_size=50)
        if chats:
            print(f"找到 {len(chats)} 个群组:")
            print("-" * 80)
            for i, chat in enumerate(chats, 1):
                chat_id = chat.get('chat_id', 'N/A')
                name = chat.get('name', '未命名群组')
                description = chat.get('description', '')
                member_count = chat.get('member_count', 0)
                
                print(f"{i:2d}. 群组名称: {name}")
                print(f"    群组ID: {chat_id}")
                print(f"    描述: {description or '无'}")
                print(f"    成员数: {member_count}")
                print("-" * 80)
            
            return chats
        else:
            print("❌ 未找到任何群组")
            return []
    except Exception as e:
        print(f"❌ 获取群组列表失败: {e}")
        return []

def get_bot_info(client):
    """获取机器人信息"""
    print("\n=== 获取机器人信息 ===")
    try:
        # 获取应用信息
        endpoint = "/open-apis/application/v6/applications/self"
        result = client._make_api_request("GET", endpoint)
        
        if result and result.get('data'):
            app_info = result['data']['app']
            print(f"应用名称: {app_info.get('app_name', 'N/A')}")
            print(f"应用ID: {app_info.get('app_id', 'N/A')}")
            print(f"应用类型: {app_info.get('app_type', 'N/A')}")
            print(f"状态: {app_info.get('status', 'N/A')}")
            return app_info
        else:
            print("❌ 无法获取应用信息")
            return None
    except Exception as e:
        print(f"❌ 获取应用信息失败: {e}")
        return None

def create_mapping_template(chats):
    """创建映射文件模板"""
    print("\n=== 创建映射文件模板 ===")
    
    mapping_template = {
        "chat_mapping": {
            "default": "",  # 默认群组ID
            "groups": {}
        },
        "user_mapping": {
            "github_username1": "feishu_user_id1",
            "github_username2": "feishu_user_id2"
        }
    }
    
    # 添加找到的群组
    if chats:
        print("可用的群组:")
        for chat in chats:
            chat_id = chat.get('chat_id')
            name = chat.get('name', '未命名群组')
            if chat_id:
                mapping_template["chat_mapping"]["groups"][name] = chat_id
                print(f"  - {name}: {chat_id}")
    
    # 保存模板文件
    template_file = project_root / "feishu_mapping_template.json"
    import json
    with open(template_file, 'w', encoding='utf-8') as f:
        json.dump(mapping_template, f, ensure_ascii=False, indent=2)
    
    print(f"\n✅ 映射文件模板已保存到: {template_file}")
    print("\n📝 使用说明:")
    print("1. 复制 feishu_mapping_template.json 为 feishu_mapping.json")
    print("2. 在 chat_mapping.default 中设置默认群组ID")
    print("3. 在 user_mapping 中添加 GitHub用户名 -> 飞书用户ID 的映射")
    print("4. 飞书用户ID可以通过 @用户 在群组中获取")

def main():
    print("🔍 飞书ID获取工具")
    print("=" * 50)
    
    # 加载配置
    config = load_config()
    
    if not config['app_id'] or not config['app_secret']:
        print("❌ 缺少飞书应用配置")
        print("请确保设置了以下环境变量或在config.yaml中配置:")
        print("- FEISHU_APP_ID")
        print("- FEISHU_APP_SECRET")
        return
    
    print(f"App ID: {config['app_id'][:10]}...")
    
    # 创建飞书客户端
    try:
        feishu_config = FeishuConfig(
            app_id=config['app_id'],
            app_secret=config['app_secret']
        )
        client = EnhancedFeishuClient(feishu_config)
        
        # 测试连接
        print("\n=== 测试API连接 ===")
        token = client._get_tenant_access_token()
        print(f"✅ 连接成功，访问令牌: {token[:20]}...")
        
        # 获取应用信息
        get_bot_info(client)
        
        # 获取群组列表
        chats = get_chat_list(client)
        
        # 创建映射文件模板
        create_mapping_template(chats)
        
        print("\n🎉 ID获取完成！")
        print("\n💡 下一步:")
        print("1. 根据模板文件配置 feishu_mapping.json")
        print("2. 运行测试: python test_enhanced_feishu.py --chat-id <群组ID>")
        print("3. 运行完整测试: python scripts/full_test.py")
        
    except Exception as e:
        print(f"❌ 初始化失败: {e}")
        return

if __name__ == "__main__":
    main()