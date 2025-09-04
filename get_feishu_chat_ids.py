#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
飞书群聊ID获取脚本
使用App ID和Secret获取所有群聊的ID和名称
"""

import requests
import json
import time

# 飞书配置
FEISHU_APP_ID = "cli_a827d9eb278b101c"
FEISHU_APP_SECRET = "U2kstRSDlTkWpa6FKUEIUdHM0LfGLxQk"

class FeishuChatIDFetcher:
    def __init__(self, app_id, app_secret):
        self.app_id = app_id
        self.app_secret = app_secret
        self.access_token = None
        
    def get_access_token(self):
        """获取访问令牌"""
        url = "https://open.feishu.cn/open-apis/auth/v3/app_access_token/internal"
        
        payload = {
            "app_id": self.app_id,
            "app_secret": self.app_secret
        }
        
        headers = {
            "Content-Type": "application/json"
        }
        
        try:
            response = requests.post(url, json=payload, headers=headers)
            response.raise_for_status()
            
            data = response.json()
            if data.get("code") == 0:
                self.access_token = data.get("app_access_token")
                print(f"✅ 成功获取访问令牌")
                return True
            else:
                print(f"❌ 获取访问令牌失败: {data.get('msg', '未知错误')}")
                return False
                
        except requests.exceptions.RequestException as e:
            print(f"❌ 网络请求失败: {e}")
            return False
        except Exception as e:
            print(f"❌ 获取访问令牌时发生错误: {e}")
            return False
    
    def get_chat_list(self):
        """获取群聊列表"""
        if not self.access_token:
            print("❌ 访问令牌为空，请先获取访问令牌")
            return []
        
        url = "https://open.feishu.cn/open-apis/im/v1/chats"
        
        headers = {
            "Authorization": f"Bearer {self.access_token}",
            "Content-Type": "application/json"
        }
        
        all_chats = []
        page_token = None
        
        try:
            while True:
                params = {
                    "page_size": 100
                }
                
                if page_token:
                    params["page_token"] = page_token
                
                response = requests.get(url, headers=headers, params=params)
                response.raise_for_status()
                
                data = response.json()
                
                if data.get("code") == 0:
                    items = data.get("data", {}).get("items", [])
                    all_chats.extend(items)
                    
                    # 检查是否还有更多页面
                    page_token = data.get("data", {}).get("page_token")
                    if not page_token:
                        break
                        
                    # 避免请求过于频繁
                    time.sleep(0.1)
                else:
                    print(f"❌ 获取群聊列表失败: {data.get('msg', '未知错误')}")
                    break
                    
        except requests.exceptions.RequestException as e:
            print(f"❌ 网络请求失败: {e}")
        except Exception as e:
            print(f"❌ 获取群聊列表时发生错误: {e}")
        
        return all_chats
    
    def display_chat_info(self, chats):
        """显示群聊信息"""
        if not chats:
            print("❌ 没有找到任何群聊")
            return
        
        print(f"\n📋 找到 {len(chats)} 个群聊:")
        print("=" * 80)
        
        for i, chat in enumerate(chats, 1):
            chat_id = chat.get("chat_id", "未知")
            name = chat.get("name", "未命名群聊")
            description = chat.get("description", "")
            chat_type = chat.get("chat_type", "未知类型")
            
            print(f"{i:2d}. 群聊名称: {name}")
            print(f"    群聊ID: {chat_id}")
            print(f"    类型: {chat_type}")
            if description:
                print(f"    描述: {description}")
            print("-" * 60)
        
        # 保存到文件
        self.save_to_file(chats)
    
    def save_to_file(self, chats):
        """保存群聊信息到文件"""
        try:
            output_data = []
            for chat in chats:
                output_data.append({
                    "chat_id": chat.get("chat_id"),
                    "name": chat.get("name"),
                    "description": chat.get("description", ""),
                    "chat_type": chat.get("chat_type")
                })
            
            with open("feishu_chat_ids.json", "w", encoding="utf-8") as f:
                json.dump(output_data, f, ensure_ascii=False, indent=2)
            
            print(f"\n💾 群聊信息已保存到 feishu_chat_ids.json")
            
        except Exception as e:
            print(f"❌ 保存文件时发生错误: {e}")

def main():
    """主函数"""
    print("🚀 开始获取飞书群聊ID列表...")
    print(f"App ID: {FEISHU_APP_ID}")
    print(f"App Secret: {FEISHU_APP_SECRET[:10]}...")
    print()
    
    # 创建获取器实例
    fetcher = FeishuChatIDFetcher(FEISHU_APP_ID, FEISHU_APP_SECRET)
    
    # 获取访问令牌
    if not fetcher.get_access_token():
        print("❌ 无法获取访问令牌，请检查App ID和Secret是否正确")
        return
    
    # 获取群聊列表
    print("📡 正在获取群聊列表...")
    chats = fetcher.get_chat_list()
    
    # 显示群聊信息
    fetcher.display_chat_info(chats)
    
    print("\n✅ 完成！")
    print("\n💡 使用说明:")
    print("1. 找到你需要的群聊，复制对应的 chat_id")
    print("2. 在部署配置中设置 FEISHU_CHAT_ID 环境变量")
    print("3. 群聊信息已保存到 feishu_chat_ids.json 文件中")

if __name__ == "__main__":
    main()