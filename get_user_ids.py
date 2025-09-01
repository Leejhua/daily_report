#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
飞书用户ID获取工具
用于获取指定群组中的用户ID列表
"""

import sys
import os
import yaml
import requests
import json
from typing import Dict, List, Optional
from dotenv import load_dotenv

# 添加项目根目录到路径
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

# 加载.env文件
load_dotenv()

class FeishuUserIDGetter:
    def __init__(self, config_path: str = "config/config.yaml"):
        """初始化飞书用户ID获取器"""
        # 优先从环境变量读取
        self.app_id = os.getenv('FEISHU_APP_ID')
        self.app_secret = os.getenv('FEISHU_APP_SECRET')
        
        # 添加日志输出，显示实际使用的APP ID
        print(f"🔍 [DEBUG] 从环境变量读取的 FEISHU_APP_ID: {self.app_id}")
        print(f"🔍 [DEBUG] 从环境变量读取的 FEISHU_APP_SECRET: {'***' + self.app_secret[-4:] if self.app_secret else None}")
        
        # 如果环境变量没有，再从配置文件读取
        if not self.app_id or not self.app_secret:
            self.config = self._load_config(config_path)
            feishu_config = self.config.get('feishu', {})
            api_config = feishu_config.get('api', {})
            self.app_id = self.app_id or api_config.get('app_id')
            self.app_secret = self.app_secret or api_config.get('app_secret')
        
        self.access_token = None
        
        if not self.app_id or not self.app_secret:
            raise ValueError("飞书应用配置不完整，请检查 .env 文件中的 FEISHU_APP_ID 和 FEISHU_APP_SECRET 或 config.yaml 中的 feishu.api.app_id 和 feishu.api.app_secret")
        
    def _load_config(self, config_path: str) -> Dict:
        """加载配置文件"""
        try:
            with open(config_path, 'r', encoding='utf-8') as f:
                return yaml.safe_load(f)
        except Exception as e:
            print(f"❌ 加载配置文件失败: {e}")
            sys.exit(1)
    
    def _get_access_token(self) -> str:
        """获取访问令牌"""
        if self.access_token:
            return self.access_token
            
        url = "https://open.feishu.cn/open-apis/auth/v3/tenant_access_token/internal"
        headers = {
            "Content-Type": "application/json; charset=utf-8"
        }
        data = {
            "app_id": self.app_id,
            "app_secret": self.app_secret
        }
        
        try:
            response = requests.post(url, headers=headers, json=data)
            response.raise_for_status()
            result = response.json()
            
            if result.get('code') == 0:
                self.access_token = result['tenant_access_token']
                return self.access_token
            else:
                raise Exception(f"获取访问令牌失败: {result}")
                
        except Exception as e:
            print(f"❌ 获取访问令牌失败: {e}")
            return None
    
    def get_chat_members(self, chat_id: str) -> List[Dict]:
        """获取群组成员列表"""
        access_token = self._get_access_token()
        if not access_token:
            return []
            
        url = f"https://open.feishu.cn/open-apis/im/v1/chats/{chat_id}/members"
        headers = {
            "Authorization": f"Bearer {access_token}",
            "Content-Type": "application/json; charset=utf-8"
        }
        
        try:
            response = requests.get(url, headers=headers)
            response.raise_for_status()
            result = response.json()
            
            if result.get('code') == 0:
                return result.get('data', {}).get('items', [])
            else:
                print(f"❌ 获取群组成员失败: {result}")
                return []
                
        except Exception as e:
            print(f"❌ 获取群组成员失败: {e}")
            return []
    
    def get_user_info(self, user_id: str) -> Optional[Dict]:
        """获取用户详细信息"""
        access_token = self._get_access_token()
        if not access_token:
            return None
            
        url = f"https://open.feishu.cn/open-apis/contact/v3/users/{user_id}"
        headers = {
            "Authorization": f"Bearer {access_token}",
            "Content-Type": "application/json; charset=utf-8"
        }
        
        try:
            response = requests.get(url, headers=headers)
            response.raise_for_status()
            result = response.json()
            
            if result.get('code') == 0:
                return result.get('data', {}).get('user', {})
            else:
                return None
                
        except Exception as e:
            return None
    
    def display_chat_members(self, chat_id: str):
        """显示群组成员信息"""
        print(f"\n=== 获取群组 {chat_id} 的成员列表 ===")
        
        members = self.get_chat_members(chat_id)
        if not members:
            print("❌ 未找到群组成员或获取失败")
            return
        
        print(f"找到 {len(members)} 个成员:")
        print("-" * 80)
        
        user_list = []
        for i, member in enumerate(members, 1):
            member_id = member.get('member_id')
            member_type = member.get('member_id_type', 'user_id')
            
            # 获取用户详细信息
            user_info = self.get_user_info(member_id) if member_type == 'user_id' else None
            
            if user_info:
                name = user_info.get('name', '未知')
                email = user_info.get('email', '未知')
                print(f" {i:2d}. 姓名: {name}")
                print(f"     邮箱: {email}")
                print(f"     用户ID: {member_id}")
                print(f"     类型: {member_type}")
                
                user_list.append({
                    'name': name,
                    'email': email,
                    'user_id': member_id,
                    'type': member_type
                })
            else:
                print(f" {i:2d}. 成员ID: {member_id}")
                print(f"     类型: {member_type}")
                print(f"     (无法获取详细信息)")
                
                user_list.append({
                    'user_id': member_id,
                    'type': member_type
                })
            
            print("-" * 80)
        
        # 保存用户列表到文件
        output_file = f"chat_members_{chat_id}.json"
        try:
            with open(output_file, 'w', encoding='utf-8') as f:
                json.dump(user_list, f, ensure_ascii=False, indent=2)
            print(f"\n✅ 用户列表已保存到: {output_file}")
        except Exception as e:
            print(f"❌ 保存用户列表失败: {e}")
        
        # 生成配置示例
        print("\n📝 管理层用户配置示例:")
        print("在 config/config.yaml 中添加:")
        print("```yaml")
        print("management_users:")
        print("  enabled: true")
        print("  user_ids:")
        for user in user_list[:3]:  # 只显示前3个作为示例
            if user.get('name'):
                print(f"    - {user['user_id']}  # {user['name']}")
            else:
                print(f"    - {user['user_id']}")
        print("  notification_type: 'text'")
        print("```")

def main():
    """主函数"""
    if len(sys.argv) < 2:
        print("使用方法: python get_user_ids.py <群组ID>")
        print("\n可用的群组ID:")
        
        # 读取映射文件模板
        try:
            with open('feishu_mapping_template.json', 'r', encoding='utf-8') as f:
                mapping = json.load(f)
                groups = mapping.get('chat_mapping', {}).get('groups', {})
                for name, chat_id in groups.items():
                    print(f"  - {name}: {chat_id}")
        except:
            print("  请先运行 python get_feishu_ids.py 获取群组列表")
        
        sys.exit(1)
    
    chat_id = sys.argv[1]
    
    try:
        getter = FeishuUserIDGetter()
        getter.display_chat_members(chat_id)
        
        print("\n🎉 用户ID获取完成！")
        print("\n💡 下一步:")
        print("1. 复制需要的用户ID")
        print("2. 在 config/config.yaml 中配置 management_users")
        print("3. 确保管理层用户已添加机器人为好友")
        print("4. 运行测试: python test_management_notification.py")
        
    except KeyboardInterrupt:
        print("\n\n⏹️  用户取消操作")
    except Exception as e:
        print(f"\n❌ 运行出错: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()