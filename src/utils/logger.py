"""
日志工具模块
提供统一的日志配置和管理
"""

import os
import sys
import logging
from pathlib import Path
from logging.handlers import RotatingFileHandler
from typing import Optional

import colorlog


def setup_logging(config=None):
    """
    设置全局日志配置
    
    Args:
        config: 日志配置对象，如果为None则使用默认配置
    """
    # 默认配置
    log_level = getattr(config, 'level', 'INFO') if config else os.getenv('LOG_LEVEL', 'INFO')
    log_file = getattr(config, 'file_path', 'logs/analyzer.log') if config else os.getenv('LOG_FILE', 'logs/analyzer.log')
    max_size = getattr(config, 'max_size', '10MB') if config else os.getenv('LOG_MAX_SIZE', '10MB')
    backup_count = getattr(config, 'backup_count', 5) if config else int(os.getenv('LOG_BACKUP_COUNT', '5'))
    
    # 创建日志目录
    log_path = Path(log_file)
    log_path.parent.mkdir(parents=True, exist_ok=True)
    
    # 解析最大文件大小
    max_bytes = _parse_size_string(max_size)
    
    # 获取根日志记录器
    root_logger = logging.getLogger()
    root_logger.setLevel(getattr(logging, log_level.upper()))
    
    # 清除现有的处理器
    for handler in root_logger.handlers[:]:
        root_logger.removeHandler(handler)
    
    # 创建格式化器
    file_formatter = logging.Formatter(
        '%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S'
    )
    
    # 控制台彩色格式化器
    console_formatter = colorlog.ColoredFormatter(
        '%(log_color)s%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        datefmt='%H:%M:%S',
        log_colors={
            'DEBUG': 'cyan',
            'INFO': 'green',
            'WARNING': 'yellow',
            'ERROR': 'red',
            'CRITICAL': 'red,bg_white',
        }
    )
    
    # 文件处理器（轮转日志）
    file_handler = RotatingFileHandler(
        log_file,
        maxBytes=max_bytes,
        backupCount=backup_count,
        encoding='utf-8'
    )
    file_handler.setLevel(getattr(logging, log_level.upper()))
    file_handler.setFormatter(file_formatter)
    
    # 控制台处理器
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setLevel(getattr(logging, log_level.upper()))
    console_handler.setFormatter(console_formatter)
    
    # 添加处理器到根日志记录器
    root_logger.addHandler(file_handler)
    root_logger.addHandler(console_handler)
    
    # 设置第三方库的日志级别
    logging.getLogger('urllib3').setLevel(logging.WARNING)
    logging.getLogger('github').setLevel(logging.WARNING)
    logging.getLogger('httpx').setLevel(logging.WARNING)
    logging.getLogger('httpcore').setLevel(logging.WARNING)
    
    # 记录日志配置信息
    logger = logging.getLogger(__name__)
    logger.info(f"日志系统初始化完成 - 级别: {log_level}, 文件: {log_file}")


def get_logger(name: str) -> logging.Logger:
    """
    获取指定名称的日志记录器
    
    Args:
        name: 日志记录器名称
        
    Returns:
        logging.Logger: 日志记录器实例
    """
    return logging.getLogger(name)


def _parse_size_string(size_str: str) -> int:
    """
    解析大小字符串为字节数
    
    Args:
        size_str: 大小字符串，如 "10MB", "1GB"
        
    Returns:
        int: 字节数
    """
    size_str = size_str.upper().strip()
    
    if size_str.endswith('KB'):
        return int(float(size_str[:-2]) * 1024)
    elif size_str.endswith('MB'):
        return int(float(size_str[:-2]) * 1024 * 1024)
    elif size_str.endswith('GB'):
        return int(float(size_str[:-2]) * 1024 * 1024 * 1024)
    else:
        # 假设是字节数
        return int(size_str)


class AnalysisLogger:
    """分析任务专用日志记录器"""
    
    def __init__(self, name: str):
        self.logger = get_logger(name)
        self.task_id: Optional[str] = None
        
    def set_task_id(self, task_id: str):
        """设置任务ID"""
        self.task_id = task_id
        
    def _format_message(self, message: str) -> str:
        """格式化消息，添加任务ID"""
        if self.task_id:
            return f"[{self.task_id}] {message}"
        return message
        
    def debug(self, message: str, *args, **kwargs):
        """调试日志"""
        self.logger.debug(self._format_message(message), *args, **kwargs)
        
    def info(self, message: str, *args, **kwargs):
        """信息日志"""
        self.logger.info(self._format_message(message), *args, **kwargs)
        
    def warning(self, message: str, *args, **kwargs):
        """警告日志"""
        self.logger.warning(self._format_message(message), *args, **kwargs)
        
    def error(self, message: str, *args, **kwargs):
        """错误日志"""
        self.logger.error(self._format_message(message), *args, **kwargs)
        
    def critical(self, message: str, *args, **kwargs):
        """严重错误日志"""
        self.logger.critical(self._format_message(message), *args, **kwargs)


class LogContext:
    """日志上下文管理器"""
    
    def __init__(self, logger: logging.Logger, context_info: str):
        self.logger = logger
        self.context_info = context_info
        self.start_time = None
        
    def __enter__(self):
        from datetime import datetime
        self.start_time = datetime.now()
        self.logger.info(f"开始 {self.context_info}")
        return self
        
    def __exit__(self, exc_type, exc_val, exc_tb):
        from datetime import datetime
        duration = (datetime.now() - self.start_time).total_seconds()
        
        if exc_type is None:
            self.logger.info(f"完成 {self.context_info}，耗时: {duration:.2f}秒")
        else:
            self.logger.error(f"失败 {self.context_info}，耗时: {duration:.2f}秒，错误: {exc_val}")
            
        return False  # 不抑制异常


def log_function_call(func):
    """
    函数调用日志装饰器
    
    Args:
        func: 被装饰的函数
        
    Returns:
        装饰后的函数
    """
    import functools
    
    @functools.wraps(func)
    def wrapper(*args, **kwargs):
        logger = get_logger(func.__module__)
        
        # 记录函数调用
        func_name = func.__name__
        logger.debug(f"调用函数: {func_name}")
        
        try:
            result = func(*args, **kwargs)
            logger.debug(f"函数 {func_name} 执行成功")
            return result
        except Exception as e:
            logger.error(f"函数 {func_name} 执行失败: {e}")
            raise
            
    return wrapper


def log_async_function_call(func):
    """
    异步函数调用日志装饰器
    
    Args:
        func: 被装饰的异步函数
        
    Returns:
        装饰后的异步函数
    """
    import functools
    
    @functools.wraps(func)
    async def wrapper(*args, **kwargs):
        logger = get_logger(func.__module__)
        
        # 记录函数调用
        func_name = func.__name__
        logger.debug(f"调用异步函数: {func_name}")
        
        try:
            result = await func(*args, **kwargs)
            logger.debug(f"异步函数 {func_name} 执行成功")
            return result
        except Exception as e:
            logger.error(f"异步函数 {func_name} 执行失败: {e}")
            raise
            
    return wrapper
