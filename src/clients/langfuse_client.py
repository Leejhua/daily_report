import os
from typing import Optional, Dict, Any
from langfuse import Langfuse
import logging
from dotenv import load_dotenv

class SimpleLangfuseClient:
    """简化的Langfuse客户端"""
    
    def __init__(self):
        self.logger = logging.getLogger(__name__)
        
        # 确保加载.env文件
        load_dotenv()
        
        # 从环境变量获取配置
        public_key = os.getenv('LANGFUSE_PUBLIC_KEY')
        secret_key = os.getenv('LANGFUSE_SECRET_KEY')
        host = os.getenv('LANGFUSE_HOST', 'https://cloud.langfuse.com')
        
        if not public_key or not secret_key:
            self.logger.warning("Langfuse配置不完整，将使用降级模式")
            self.client = None
            self.enabled = False
        else:
            try:
                self.client = Langfuse(
                    public_key=public_key,
                    secret_key=secret_key,
                    host=host
                )
                self.enabled = True
                self.logger.info("Langfuse客户端初始化成功")
            except Exception as e:
                self.logger.error(f"Langfuse客户端初始化失败: {e}")
                self.client = None
                self.enabled = False
    
    def get_prompt(self, name: str, variables: Optional[Dict[str, Any]] = None) -> Optional[Dict[str, str]]:
        """获取提示词
        
        Args:
            name: 提示词名称
            variables: 模板变量
            
        Returns:
            Dict包含system_prompt和user_prompt，如果失败返回None
        """
        if not self.enabled or not self.client:
            return None
        
        try:
            # 获取提示词
            prompt = self.client.get_prompt(name)
            
            if not prompt:
                self.logger.warning(f"提示词 '{name}' 不存在")
                return None
            
            # 编译提示词（如果有变量）
            if variables:
                compiled_prompt = prompt.compile(**variables)
            else:
                compiled_prompt = prompt.compile()
            
            # 获取提示词内容
            content = ""
            if hasattr(compiled_prompt, 'content'):
                content = compiled_prompt.content
            elif hasattr(compiled_prompt, 'prompt'):
                content = compiled_prompt.prompt
            elif isinstance(compiled_prompt, str):
                content = compiled_prompt
            
            # 对于文本格式的提示词，将整个内容作为用户提示词
            # 系统提示词留空，因为我们的模板将所有内容放在一个文本中
            return {
                'system_prompt': "",
                'user_prompt': content if isinstance(content, str) else str(content)
            }
            
        except Exception as e:
            self.logger.error(f"获取提示词 '{name}' 失败: {e}")
            return None
    
    def is_available(self) -> bool:
        """检查Langfuse是否可用"""
        return self.enabled and self.client is not None

# 全局实例
langfuse_client = SimpleLangfuseClient()