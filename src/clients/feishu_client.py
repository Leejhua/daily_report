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
    
    def __init__(self, config: Dict[str, Any]):
        """初始化飞书客户端
        
        Args:
            config: 飞书配置，包含webhook_url、mapping_file等
        """
        self.config = config
        self.webhook_url = config.get('webhook_url', '')
        self.mapping_file = config.get('mapping_file', 'feishu_mapping.json')
        self.timeout = config.get('timeout', 30)
        self.retry_count = config.get('retry_count', 3)
        
        # 加载用户映射配置
        self.user_mapping = self._load_user_mapping()
        
    def _load_user_mapping(self) -> Dict[str, Any]:
        """加载飞书用户映射配置
        
        Returns:
            用户映射配置字典
        """
        try:
            mapping_path = Path(self.mapping_file)
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
        user_mappings = self.user_mapping.get('user_mappings', {})
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