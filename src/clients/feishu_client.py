import json
import requests
from typing import Dict, List, Optional, Any
from datetime import datetime
import logging
from pathlib import Path

logger = logging.getLogger(__name__)

class FeishuClient:
    """飞书群组通知客户端
    
    负责发送偏离预警通知到飞书群组，支持富文本消息和卡片消息格式。
    """
    
    def __init__(self, config):
        """初始化飞书客户端
        
        Args:
            config: 飞书配置，可以是字典或FeishuConfig对象
        """
        self.config = config
        
        # 处理不同类型的配置对象
        if hasattr(config, 'api'):
            # FeishuConfig对象
            self.webhook_url = getattr(config.webhook, 'url', '') if hasattr(config, 'webhook') else ''
            self.mapping_file = getattr(config, 'mapping_file', 'feishu_mapping.json')
            self.timeout = getattr(config.api, 'timeout', 30) if hasattr(config, 'api') else 30
            self.retry_count = getattr(config.api, 'max_retries', 3) if hasattr(config, 'api') else 3
            
            # 飞书开放平台API配置
            self.app_id = getattr(config.api, 'app_id', '') if hasattr(config, 'api') else ''
            self.app_secret = getattr(config.api, 'app_secret', '') if hasattr(config, 'api') else ''
            self.api_base_url = getattr(config.api, 'base_url', 'https://open.feishu.cn') if hasattr(config, 'api') else 'https://open.feishu.cn'
            self.api_timeout = getattr(config.api, 'timeout', 30) if hasattr(config, 'api') else 30
            self.api_max_retries = getattr(config.api, 'max_retries', 3) if hasattr(config, 'api') else 3
            self.api_retry_delay = getattr(config.api, 'retry_delay', 1.0) if hasattr(config, 'api') else 1.0
            
            # 默认聊天ID
            self.default_chat_id = getattr(config.api, 'default_chat_id', '') if hasattr(config, 'api') else ''
            
            # 管理层通知配置 - 从全局配置获取
            self.management_enabled = False
            self.management_user_ids = []
        else:
            # 字典配置
            self.webhook_url = config.get('webhook_url', '')
            self.mapping_file = config.get('mapping_file', 'feishu_mapping.json')
            self.timeout = config.get('timeout', 30)
            self.retry_count = config.get('retry_count', 3)
            
            # 飞书开放平台API配置
            api_config = config.get('api', {})
            self.app_id = api_config.get('app_id', '')
            self.app_secret = api_config.get('app_secret', '')
            self.api_base_url = api_config.get('base_url', 'https://open.feishu.cn')
            self.api_timeout = api_config.get('timeout', 30)
            self.api_max_retries = api_config.get('max_retries', 3)
            self.api_retry_delay = api_config.get('retry_delay', 1.0)
            self.default_chat_id = api_config.get('default_chat_id', '')
            
            # 管理层通知配置
            management_config = config.get('management_users', {})
            self.management_enabled = management_config.get('enabled', False)
            self.management_user_ids = management_config.get('user_ids', [])
        
        # 访问令牌缓存
        self._access_token = None
        self._token_expires_at = None
        
        # 加载用户映射配置
        self.user_mapping = self._load_user_mapping()
        
    def _load_user_mapping(self) -> Dict[str, Any]:
        """加载飞书用户映射配置
        
        Returns:
            用户映射配置字典
        """
        try:
            # 如果是相对路径，转换为绝对路径
            mapping_path = Path(self.mapping_file)
            if not mapping_path.is_absolute():
                # 使用项目根目录作为基准
                project_root = Path(__file__).parent.parent.parent
                mapping_path = project_root / self.mapping_file
            
            if mapping_path.exists():
                with open(mapping_path, 'r', encoding='utf-8') as f:
                    return json.load(f)
            else:
                logger.warning(f"飞书映射文件不存在: {mapping_path}")
                return {}
        except Exception as e:
            logger.error(f"加载飞书映射配置失败: {e}")
            return {}
    
    def _get_feishu_user_id(self, github_username: str) -> Optional[str]:
        """获取GitHub用户名对应的飞书用户ID
        
        Args:
            github_username: GitHub用户名
            
        Returns:
            飞书用户ID，如果未找到则返回None
        """
        user_mappings = self.user_mapping.get('user_mapping', {})
        return user_mappings.get(github_username)
    
    def _build_simple_message(self, report_content: str, users: List[str]) -> Dict[str, Any]:
        """构建简单文本消息
        
        Args:
            report_content: 汇报内容
            users: 相关用户列表
            
        Returns:
            飞书消息体
        """
        # 构建@用户列表
        at_users = []
        for user in users:
            feishu_id = self._get_feishu_user_id(user)
            if feishu_id:
                at_users.append(f"<at user_id=\"{feishu_id}\"></at>")
        
        at_text = " ".join(at_users) if at_users else ""
        
        message = {
            "msg_type": "text",
            "content": {
                "text": f"📊 工作偏离预警通知\n\n{report_content}\n\n{at_text}"
            }
        }
        
        return message
    
    def _build_rich_text_message(self, report_content: str, users: List[str]) -> Dict[str, Any]:
        """构建富文本消息
        
        Args:
            report_content: 汇报内容
            users: 相关用户列表
            
        Returns:
            飞书富文本消息体
        """
        # 解析汇报内容为富文本格式
        content_lines = report_content.strip().split('\n')
        rich_content = []
        
        for line in content_lines:
            if line.strip():
                if line.startswith('#'):
                    # 标题
                    rich_content.append({
                        "tag": "text",
                        "text": line.replace('#', '').strip(),
                        "style": ["bold"]
                    })
                elif line.startswith('**') and line.endswith('**'):
                    # 粗体文本
                    rich_content.append({
                        "tag": "text",
                        "text": line.replace('**', ''),
                        "style": ["bold"]
                    })
                else:
                    # 普通文本
                    rich_content.append({
                        "tag": "text",
                        "text": line
                    })
                
                rich_content.append({"tag": "text", "text": "\n"})
        
        # 添加@用户
        if users:
            rich_content.append({"tag": "text", "text": "\n相关人员: "})
            for user in users:
                feishu_id = self._get_feishu_user_id(user)
                if feishu_id:
                    rich_content.append({
                        "tag": "at",
                        "user_id": feishu_id
                    })
                    rich_content.append({"tag": "text", "text": " "})
        
        message = {
            "msg_type": "post",
            "content": {
                "post": {
                    "zh_cn": {
                        "title": "📊 工作偏离预警通知",
                        "content": [rich_content]
                    }
                }
            }
        }
        
        return message
    
    def _build_card_message(self, report_data: Dict[str, Any], users: List[str]) -> Dict[str, Any]:
        """构建卡片消息
        
        Args:
            report_data: 汇报数据
            users: 相关用户列表
            
        Returns:
            飞书卡片消息体
        """
        # 构建卡片元素
        elements = []
        
        # 标题
        elements.append({
            "tag": "div",
            "text": {
                "tag": "lark_md",
                "content": "**📊 工作偏离预警通知**"
            }
        })
        
        # 预警信息
        if 'alert_info' in report_data:
            alert_info = report_data['alert_info']
            elements.append({
                "tag": "div",
                "fields": [
                    {
                        "is_short": True,
                        "text": {
                            "tag": "lark_md",
                            "content": f"**预警时间:**\n{alert_info.get('time', 'N/A')}"
                        }
                    },
                    {
                        "is_short": True,
                        "text": {
                            "tag": "lark_md",
                            "content": f"**预警类型:**\n{alert_info.get('type', 'N/A')}"
                        }
                    },
                    {
                        "is_short": True,
                        "text": {
                            "tag": "lark_md",
                            "content": f"**连续偏离天数:**\n{alert_info.get('consecutive_days', 'N/A')}"
                        }
                    },
                    {
                        "is_short": True,
                        "text": {
                            "tag": "lark_md",
                            "content": f"**平均偏离度:**\n{alert_info.get('avg_deviation', 'N/A')}"
                        }
                    }
                ]
            })
        
        # 偏离统计
        if 'deviation_stats' in report_data:
            stats = report_data['deviation_stats']
            stats_text = "\n".join([f"• {k}: {v}" for k, v in stats.items()])
            elements.append({
                "tag": "div",
                "text": {
                    "tag": "lark_md",
                    "content": f"**偏离统计:**\n{stats_text}"
                }
            })
        
        # 改进建议
        if 'suggestions' in report_data:
            suggestions = report_data['suggestions']
            if isinstance(suggestions, list):
                suggestions_text = "\n".join([f"• {s}" for s in suggestions])
            else:
                suggestions_text = str(suggestions)
            
            elements.append({
                "tag": "div",
                "text": {
                    "tag": "lark_md",
                    "content": f"**改进建议:**\n{suggestions_text}"
                }
            })
        
        # 相关人员
        if users:
            user_mentions = []
            for user in users:
                feishu_id = self._get_feishu_user_id(user)
                if feishu_id:
                    user_mentions.append(f"<at id={feishu_id}></at>")
                else:
                    user_mentions.append(user)
            
            elements.append({
                "tag": "div",
                "text": {
                    "tag": "lark_md",
                    "content": f"**相关人员:** {' '.join(user_mentions)}"
                }
            })
        
        # 分割线
        elements.append({"tag": "hr"})
        
        # 时间戳
        elements.append({
            "tag": "div",
            "text": {
                "tag": "lark_md",
                "content": f"*生成时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}*"
            }
        })
        
        message = {
            "msg_type": "interactive",
            "card": {
                "config": {
                    "wide_screen_mode": True
                },
                "header": {
                    "title": {
                        "tag": "plain_text",
                        "content": "工作偏离预警"
                    },
                    "template": "orange"
                },
                "elements": elements
            }
        }
        
        return message
    
    def send_deviation_alert(self, report_content: str, users: List[str], 
                           message_type: str = "rich_text", 
                           report_data: Optional[Dict[str, Any]] = None) -> bool:
        """发送偏离预警通知
        
        Args:
            report_content: 汇报内容
            users: 相关用户列表
            message_type: 消息类型 (text/rich_text/card)
            report_data: 结构化汇报数据（用于卡片消息）
            
        Returns:
            发送是否成功
        """
        if not self.webhook_url:
            logger.error("飞书Webhook URL未配置")
            return False
        
        try:
            # 根据消息类型构建消息体
            if message_type == "text":
                message = self._build_simple_message(report_content, users)
            elif message_type == "card" and report_data:
                message = self._build_card_message(report_data, users)
            else:
                message = self._build_rich_text_message(report_content, users)
            
            # 发送消息
            return self._send_webhook_message(message)
            
        except Exception as e:
            logger.error(f"发送飞书通知失败: {e}")
            return False
    
    def _send_webhook_message(self, message: Dict[str, Any]) -> bool:
        """发送Webhook消息
        
        Args:
            message: 消息体
            
        Returns:
            发送是否成功
        """
        for attempt in range(self.retry_count):
            try:
                response = requests.post(
                    self.webhook_url,
                    json=message,
                    timeout=self.timeout,
                    headers={'Content-Type': 'application/json'}
                )
                
                if response.status_code == 200:
                    result = response.json()
                    if result.get('StatusCode') == 0:
                        logger.info("飞书通知发送成功")
                        return True
                    else:
                        logger.error(f"飞书API返回错误: {result}")
                else:
                    logger.error(f"飞书Webhook请求失败: {response.status_code} - {response.text}")
                
            except requests.exceptions.Timeout:
                logger.warning(f"飞书通知发送超时，第{attempt + 1}次重试")
            except requests.exceptions.RequestException as e:
                logger.error(f"飞书通知发送异常: {e}")
            except Exception as e:
                logger.error(f"发送飞书消息时发生未知错误: {e}")
            
            if attempt < self.retry_count - 1:
                import time
                time.sleep(2 ** attempt)  # 指数退避
        
        logger.error(f"飞书通知发送失败，已重试{self.retry_count}次")
        return False
    
    def test_connection(self) -> bool:
        """测试飞书连接
        
        Returns:
            连接是否正常
        """
        test_message = {
            "msg_type": "text",
            "content": {
                "text": "🔧 飞书通知测试消息"
            }
        }
        
        return self._send_webhook_message(test_message)
    
    def get_user_mapping_stats(self) -> Dict[str, Any]:
        """获取用户映射统计信息
        
        Returns:
            映射统计信息
        """
        user_mappings = self.user_mapping.get('user_mappings', {})
        
        return {
            'total_mappings': len(user_mappings),
            'mapped_users': list(user_mappings.keys()),
            'webhook_configured': bool(self.webhook_url),
            'mapping_file_exists': Path(self.mapping_file).exists()
        }
    
    def _get_access_token(self) -> Optional[str]:
        """获取飞书开放平台访问令牌
        
        Returns:
            访问令牌，获取失败返回None
        """
        if not self.app_id or not self.app_secret:
            logger.error("飞书应用ID或密钥未配置")
            return None
        
        # 检查缓存的令牌是否有效
        if (self._access_token and self._token_expires_at and 
            datetime.now().timestamp() < self._token_expires_at):
            return self._access_token
        
        try:
            url = f"{self.api_base_url}/open-apis/auth/v3/tenant_access_token/internal"
            payload = {
                "app_id": self.app_id,
                "app_secret": self.app_secret
            }
            
            response = requests.post(
                url,
                json=payload,
                timeout=self.api_timeout,
                headers={'Content-Type': 'application/json'}
            )
            
            if response.status_code == 200:
                result = response.json()
                if result.get('code') == 0:
                    self._access_token = result.get('tenant_access_token')
                    # 设置过期时间（提前5分钟刷新）
                    expires_in = result.get('expire', 7200) - 300
                    self._token_expires_at = datetime.now().timestamp() + expires_in
                    logger.info("飞书访问令牌获取成功")
                    return self._access_token
                else:
                    logger.error(f"获取飞书访问令牌失败: {result}")
            else:
                logger.error(f"飞书API请求失败: {response.status_code} - {response.text}")
                
        except Exception as e:
            logger.error(f"获取飞书访问令牌异常: {e}")
        
        return None
    
    def _send_private_message(self, user_id: str, message_content: str) -> bool:
        """发送私聊消息给指定用户
        
        Args:
            user_id: 飞书用户ID
            message_content: 消息内容
            
        Returns:
            发送是否成功
        """
        access_token = self._get_access_token()
        if not access_token:
            return False
        
        try:
            url = f"{self.api_base_url}/open-apis/im/v1/messages?receive_id_type=open_id"
            headers = {
                'Authorization': f'Bearer {access_token}',
                'Content-Type': 'application/json'
            }
            
            # 构建消息体
            payload = {
                "receive_id": user_id,
                "msg_type": "text",
                "content": json.dumps({
                    "text": f"📊 管理层通知\n\n{message_content}"
                }, ensure_ascii=False)
            }
            
            for attempt in range(self.api_max_retries):
                try:
                    response = requests.post(
                        url,
                        json=payload,
                        headers=headers,
                        timeout=self.api_timeout
                    )
                    
                    if response.status_code == 200:
                        result = response.json()
                        if result.get('code') == 0:
                            logger.info(f"私聊消息发送成功: {user_id}")
                            return True
                        else:
                            logger.error(f"飞书私聊API返回错误: {result}")
                    else:
                        logger.error(f"飞书私聊请求失败: {response.status_code} - {response.text}")
                    
                except requests.exceptions.Timeout:
                    logger.warning(f"飞书私聊发送超时，第{attempt + 1}次重试")
                except requests.exceptions.RequestException as e:
                    logger.error(f"飞书私聊发送异常: {e}")
                
                if attempt < self.api_max_retries - 1:
                    import time
                    time.sleep(self.api_retry_delay * (attempt + 1))
            
            logger.error(f"飞书私聊发送失败，已重试{self.api_max_retries}次: {user_id}")
            return False
            
        except Exception as e:
            logger.error(f"发送飞书私聊消息时发生未知错误: {e}")
            return False
    
    def send_management_notification(self, report_content: str) -> bool:
        """发送管理层通知
        
        Args:
            report_content: 汇报内容
            
        Returns:
            发送是否成功（至少一个管理层用户收到消息）
        """
        if not self.management_enabled or not self.management_user_ids:
            logger.info("管理层通知未启用或未配置管理层用户")
            return True  # 未配置时视为成功
        
        success_count = 0
        total_count = len(self.management_user_ids)
        
        for user_id in self.management_user_ids:
            if self._send_private_message(user_id, report_content):
                success_count += 1
        
        if success_count > 0:
            logger.info(f"管理层通知发送完成: {success_count}/{total_count} 成功")
            return True
        else:
            logger.error("所有管理层通知发送失败")
            return False