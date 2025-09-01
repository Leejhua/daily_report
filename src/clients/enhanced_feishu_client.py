#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
增强版飞书客户端 - 基于飞书开放平台API
支持应用凭证认证、获取access_token、发送消息等功能
"""

import json
import time
import logging
import requests
from typing import Dict, List, Optional, Any, Union
from dataclasses import dataclass
from datetime import datetime, timedelta


@dataclass
class FeishuConfig:
    """飞书配置类"""
    app_id: str
    app_secret: str
    base_url: str = "https://open.feishu.cn"
    timeout: int = 30
    max_retries: int = 3
    retry_delay: float = 1.0


@dataclass
class AccessToken:
    """访问令牌类"""
    token: str
    expires_at: datetime
    
    @property
    def is_expired(self) -> bool:
        """检查令牌是否过期"""
        return datetime.now() >= self.expires_at - timedelta(minutes=5)  # 提前5分钟刷新


class EnhancedFeishuClient:
    """增强版飞书客户端 - 基于飞书开放平台API"""
    
    def __init__(self, config: FeishuConfig):
        self.config = config
        self.logger = logging.getLogger(__name__)
        self._access_token: Optional[AccessToken] = None
        self.session = requests.Session()
        self.session.timeout = config.timeout
        
    def _get_tenant_access_token(self) -> str:
        """获取tenant_access_token"""
        if self._access_token and not self._access_token.is_expired:
            return self._access_token.token
            
        url = f"{self.config.base_url}/open-apis/auth/v3/tenant_access_token/internal"
        payload = {
            "app_id": self.config.app_id,
            "app_secret": self.config.app_secret
        }
        
        try:
            response = self.session.post(url, json=payload)
            response.raise_for_status()
            
            data = response.json()
            if data.get("code") != 0:
                raise Exception(f"获取access_token失败: {data.get('msg')}")
                
            token = data["tenant_access_token"]
            expires_in = data.get("expire", 7200)  # 默认2小时
            expires_at = datetime.now() + timedelta(seconds=expires_in)
            
            self._access_token = AccessToken(token=token, expires_at=expires_at)
            self.logger.info("成功获取tenant_access_token")
            
            return token
            
        except Exception as e:
            self.logger.error(f"获取tenant_access_token失败: {e}")
            raise
    
    def _make_api_request(self, method: str, endpoint: str, data: Optional[Dict] = None, 
                         headers: Optional[Dict] = None) -> Dict:
        """发起API请求"""
        token = self._get_tenant_access_token()
        
        default_headers = {
            "Authorization": f"Bearer {token}",
            "Content-Type": "application/json"
        }
        
        if headers:
            default_headers.update(headers)
            
        url = f"{self.config.base_url}{endpoint}"
        
        for attempt in range(self.config.max_retries):
            try:
                if method.upper() == "GET":
                    response = self.session.get(url, headers=default_headers, params=data)
                else:
                    response = self.session.request(method, url, headers=default_headers, json=data)
                    
                result = response.json()
                
                if response.status_code != 200:
                    self.logger.error(f"HTTP错误 {response.status_code}: {result}")
                    raise Exception(f"HTTP {response.status_code}: {result.get('msg', result)}")
                
                if result.get("code") != 0:
                    self.logger.error(f"API错误码 {result.get('code')}: {result.get('msg')}")
                    raise Exception(f"API请求失败 (错误码: {result.get('code')}): {result.get('msg')}")
                    
                return result
                
            except Exception as e:
                self.logger.warning(f"API请求失败 (尝试 {attempt + 1}/{self.config.max_retries}): {e}")
                if attempt == self.config.max_retries - 1:
                    raise
                time.sleep(self.config.retry_delay * (attempt + 1))
    
    def send_message_to_chat(self, chat_id: str, msg_type: str, content: Dict) -> bool:
        """发送消息到群聊"""
        try:
            endpoint = "/open-apis/im/v1/messages"
            params = {
                "receive_id_type": "chat_id"
            }
            data = {
                "receive_id": chat_id,
                "msg_type": msg_type,
                "content": json.dumps(content, ensure_ascii=False)
            }
            
            # 使用查询参数传递receive_id_type
            url = f"{self.config.base_url}{endpoint}?receive_id_type=chat_id"
            token = self._get_tenant_access_token()
            headers = {
                "Authorization": f"Bearer {token}",
                "Content-Type": "application/json"
            }
            
            response = self.session.post(url, headers=headers, json=data)
            result = response.json()
            
            if response.status_code != 200:
                self.logger.error(f"HTTP错误 {response.status_code}: {result}")
                raise Exception(f"HTTP {response.status_code}: {result.get('msg', result)}")
            
            if result.get("code") != 0:
                self.logger.error(f"API错误码 {result.get('code')}: {result.get('msg')}")
                raise Exception(f"API请求失败 (错误码: {result.get('code')}): {result.get('msg')}")
            
            self.logger.info(f"成功发送消息到群聊 {chat_id}")
            return True
            
        except Exception as e:
            self.logger.error(f"发送群聊消息失败: {e}")
            return False
    
    def send_message_to_user(self, user_id: str, msg_type: str, content: Dict, 
                           id_type: str = "user_id") -> bool:
        """发送消息到用户"""
        try:
            endpoint = "/open-apis/im/v1/messages"
            data = {
                "receive_id": user_id,
                "msg_type": msg_type,
                "content": json.dumps(content, ensure_ascii=False)
            }
            
            # 使用查询参数传递receive_id_type
            url = f"{self.config.base_url}{endpoint}?receive_id_type={id_type}"
            token = self._get_tenant_access_token()
            headers = {
                "Authorization": f"Bearer {token}",
                "Content-Type": "application/json"
            }
            
            response = self.session.post(url, headers=headers, json=data)
            result = response.json()
            
            if response.status_code != 200:
                self.logger.error(f"HTTP错误 {response.status_code}: {result}")
                raise Exception(f"HTTP {response.status_code}: {result.get('msg', result)}")
            
            if result.get("code") != 0:
                self.logger.error(f"API错误码 {result.get('code')}: {result.get('msg')}")
                raise Exception(f"API请求失败 (错误码: {result.get('code')}): {result.get('msg')}")
            
            self.logger.info(f"成功发送消息到用户 {user_id}")
            return True
            
        except Exception as e:
            self.logger.error(f"发送用户消息失败: {e}")
            return False
    
    def send_text_message(self, receive_id: str, text: str, 
                         receive_id_type: str = "chat_id") -> bool:
        """发送文本消息"""
        content = {"text": text}
        
        if receive_id_type == "chat_id":
            return self.send_message_to_chat(receive_id, "text", content)
        else:
            return self.send_message_to_user(receive_id, "text", content, receive_id_type)
    
    def send_rich_text_message(self, receive_id: str, rich_text: Dict, 
                              receive_id_type: str = "chat_id") -> bool:
        """发送富文本消息"""
        if receive_id_type == "chat_id":
            return self.send_message_to_chat(receive_id, "rich_text", rich_text)
        else:
            return self.send_message_to_user(receive_id, "rich_text", rich_text, receive_id_type)
    
    def send_interactive_card(self, receive_id: str, card: Dict, 
                             receive_id_type: str = "chat_id") -> bool:
        """发送交互式卡片消息"""
        if receive_id_type == "chat_id":
            return self.send_message_to_chat(receive_id, "interactive", card)
        else:
            return self.send_message_to_user(receive_id, "interactive", card, receive_id_type)
    
    def get_chat_info(self, chat_id: str) -> Optional[Dict]:
        """获取群聊信息"""
        try:
            endpoint = f"/open-apis/im/v1/chats/{chat_id}"
            result = self._make_api_request("GET", endpoint)
            return result.get("data")
            
        except Exception as e:
            self.logger.error(f"获取群聊信息失败: {e}")
            return None
    
    def get_user_info(self, user_id: str, id_type: str = "user_id") -> Optional[Dict]:
        """获取用户信息"""
        try:
            endpoint = f"/open-apis/contact/v3/users/{user_id}"
            params = {"user_id_type": id_type}
            result = self._make_api_request("GET", endpoint, params)
            return result.get("data")
            
        except Exception as e:
            self.logger.error(f"获取用户信息失败: {e}")
            return None
    
    def get_chat_list(self, page_size: int = 20) -> Optional[List[Dict]]:
        """获取群聊列表"""
        try:
            endpoint = "/open-apis/im/v1/chats"
            params = {"page_size": page_size}
            result = self._make_api_request("GET", endpoint, params)
            return result.get("data", {}).get("items", [])
            
        except Exception as e:
            self.logger.error(f"获取群聊列表失败: {e}")
            return None
    
    def batch_send_messages(self, messages: List[Dict]) -> Dict[str, bool]:
        """批量发送消息"""
        results = {}
        
        for i, msg in enumerate(messages):
            try:
                receive_id = msg["receive_id"]
                receive_id_type = msg.get("receive_id_type", "chat_id")
                msg_type = msg["msg_type"]
                content = msg["content"]
                
                if msg_type == "text":
                    success = self.send_text_message(receive_id, content, receive_id_type)
                elif msg_type == "rich_text":
                    success = self.send_rich_text_message(receive_id, content, receive_id_type)
                elif msg_type == "interactive":
                    success = self.send_interactive_card(receive_id, content, receive_id_type)
                else:
                    self.logger.warning(f"不支持的消息类型: {msg_type}")
                    success = False
                    
                results[f"message_{i}"] = success
                
                # 避免频率限制
                if i < len(messages) - 1:
                    time.sleep(0.1)
                    
            except Exception as e:
                self.logger.error(f"批量发送消息失败 (消息 {i}): {e}")
                results[f"message_{i}"] = False
                
        return results
    
    def create_rich_text_content(self, title: str, content_blocks: List[Dict]) -> Dict:
        """创建富文本内容"""
        return {
            "rich_text": {
                "title": title,
                "content": content_blocks
            }
        }
    
    def create_card_content(self, header: Dict, elements: List[Dict], 
                           config: Optional[Dict] = None) -> Dict:
        """创建卡片内容"""
        card = {
            "config": config or {"wide_screen_mode": True},
            "header": header,
            "elements": elements
        }
        return card
    
    def test_connection(self) -> bool:
        """测试连接"""
        try:
            token = self._get_tenant_access_token()
            self.logger.info("飞书API连接测试成功")
            return True
        except Exception as e:
            self.logger.error(f"飞书API连接测试失败: {e}")
            return False


# 兼容性包装器，保持与原有FeishuClient接口的兼容性
class FeishuClientWrapper:
    """飞书客户端包装器 - 保持接口兼容性"""
    
    def __init__(self, enhanced_client: EnhancedFeishuClient, 
                 default_chat_id: Optional[str] = None):
        self.client = enhanced_client
        self.default_chat_id = default_chat_id
        self.logger = logging.getLogger(__name__)
    
    def send_message(self, message: str, chat_id: Optional[str] = None, 
                    message_type: str = "text") -> bool:
        """发送消息 - 兼容原有接口"""
        target_chat_id = chat_id or self.default_chat_id
        if not target_chat_id:
            self.logger.error("未指定chat_id")
            return False
            
        if message_type == "text":
            return self.client.send_text_message(target_chat_id, message)
        else:
            # 对于其他类型，尝试解析为JSON
            try:
                content = json.loads(message) if isinstance(message, str) else message
                if message_type == "rich_text":
                    return self.client.send_rich_text_message(target_chat_id, content)
                elif message_type == "interactive":
                    return self.client.send_interactive_card(target_chat_id, content)
            except Exception as e:
                self.logger.error(f"解析消息内容失败: {e}")
                return False
        
        return False
    
    def send_notification(self, users: List[str], message: str, 
                         message_type: str = "text") -> Dict[str, bool]:
        """发送通知给多个用户 - 兼容原有接口"""
        results = {}
        
        for user in users:
            if message_type == "text":
                success = self.client.send_text_message(user, message, "user_id")
            else:
                try:
                    content = json.loads(message) if isinstance(message, str) else message
                    if message_type == "rich_text":
                        success = self.client.send_rich_text_message(user, content, "user_id")
                    elif message_type == "interactive":
                        success = self.client.send_interactive_card(user, content, "user_id")
                    else:
                        success = False
                except Exception:
                    success = False
                    
            results[user] = success
            
        return results
    
    def send_management_notification(self, message_content: str) -> bool:
        """发送管理层通知 - 兼容原有接口"""
        try:
            # 读取管理层通知配置
            import yaml
            import os
            
            config_path = os.path.join(os.getcwd(), 'config', 'config.yaml')
            if not os.path.exists(config_path):
                self.logger.warning("配置文件不存在，跳过管理层通知")
                return True
                
            with open(config_path, 'r', encoding='utf-8') as f:
                config = yaml.safe_load(f)
            
            management_config = config.get('management_notification', {})
            if not management_config.get('enabled', False):
                self.logger.info("管理层通知未启用")
                return True
                
            user_ids = management_config.get('user_ids', [])
            if not user_ids:
                self.logger.warning("未配置管理层用户ID")
                return True
            
            # 发送通知给所有管理层用户
            success_count = 0
            for user_id in user_ids:
                try:
                    success = self.client.send_text_message(
                        receive_id=user_id,
                        text=message_content,
                        receive_id_type='open_id'
                    )
                    if success:
                        success_count += 1
                        self.logger.info(f"管理层通知发送成功: {user_id}")
                    else:
                        self.logger.error(f"管理层通知发送失败: {user_id}")
                except Exception as e:
                    self.logger.error(f"发送管理层通知给 {user_id} 时发生错误: {e}")
            
            # 至少有一个成功就认为整体成功
            return success_count > 0
            
        except Exception as e:
            self.logger.error(f"管理层通知发送失败: {e}")
            return False