"""
辅助工具函数
提供各种通用的工具函数
"""

import re
import json
import hashlib
from datetime import datetime, date, timezone, timedelta
from typing import Dict, Any, List, Optional, Union, Callable
from pathlib import Path
import asyncio
import functools


def format_datetime(dt: datetime, format_str: str = "%Y-%m-%d %H:%M:%S") -> str:
    """
    格式化日期时间
    
    Args:
        dt: 日期时间对象
        format_str: 格式字符串
        
    Returns:
        str: 格式化后的字符串
    """
    return dt.strftime(format_str)


def parse_datetime(dt_str: str, format_str: str = "%Y-%m-%d %H:%M:%S") -> datetime:
    """
    解析日期时间字符串
    
    Args:
        dt_str: 日期时间字符串
        format_str: 格式字符串
        
    Returns:
        datetime: 日期时间对象
    """
    return datetime.strptime(dt_str, format_str)


def get_today_date() -> date:
    """获取今天的日期"""
    return date.today()


def get_current_datetime() -> datetime:
    """获取当前日期时间（UTC）"""
    return datetime.now(timezone.utc)


def calculate_duration(start_time: datetime, end_time: Optional[datetime] = None) -> float:
    """
    计算时间间隔（秒）
    
    Args:
        start_time: 开始时间
        end_time: 结束时间，默认为当前时间
        
    Returns:
        float: 时间间隔（秒）
    """
    if end_time is None:
        end_time = get_current_datetime()
    return (end_time - start_time).total_seconds()


def clean_text(text: str) -> str:
    """
    清理文本内容
    
    Args:
        text: 原始文本
        
    Returns:
        str: 清理后的文本
    """
    if not text:
        return ""
        
    # 移除多余的空白字符
    text = re.sub(r'\s+', ' ', text.strip())
    
    # 移除特殊字符（保留基本标点）
    text = re.sub(r'[^\w\s\u4e00-\u9fff.,!?;:(){}[\]"\'-]', '', text)
    
    return text


def extract_keywords(text: str, max_keywords: int = 10) -> List[str]:
    """
    从文本中提取关键词
    
    Args:
        text: 输入文本
        max_keywords: 最大关键词数量
        
    Returns:
        List[str]: 关键词列表
    """
    if not text:
        return []
        
    # 简单的关键词提取（基于词频）
    words = re.findall(r'\b\w+\b', text.lower())
    
    # 过滤停用词
    stop_words = {'的', '是', '在', '了', '和', '有', '我', '你', '他', '她', '它', '这', '那', '一', '二', '三'}
    words = [word for word in words if word not in stop_words and len(word) > 1]
    
    # 统计词频
    word_freq = {}
    for word in words:
        word_freq[word] = word_freq.get(word, 0) + 1
    
    # 按频率排序并返回前N个
    sorted_words = sorted(word_freq.items(), key=lambda x: x[1], reverse=True)
    return [word for word, freq in sorted_words[:max_keywords]]


def calculate_text_similarity(text1: str, text2: str) -> float:
    """
    计算两个文本的相似度（简单版本）
    
    Args:
        text1: 文本1
        text2: 文本2
        
    Returns:
        float: 相似度（0-1）
    """
    if not text1 or not text2:
        return 0.0
        
    # 提取关键词
    keywords1 = set(extract_keywords(text1))
    keywords2 = set(extract_keywords(text2))
    
    if not keywords1 or not keywords2:
        return 0.0
        
    # 计算Jaccard相似度
    intersection = len(keywords1.intersection(keywords2))
    union = len(keywords1.union(keywords2))
    
    return intersection / union if union > 0 else 0.0


def generate_hash(content: str) -> str:
    """
    生成内容的哈希值
    
    Args:
        content: 内容字符串
        
    Returns:
        str: MD5哈希值
    """
    return hashlib.md5(content.encode('utf-8')).hexdigest()


def safe_json_loads(json_str: str, default: Any = None) -> Any:
    """
    安全地解析JSON字符串
    
    Args:
        json_str: JSON字符串
        default: 解析失败时的默认值
        
    Returns:
        Any: 解析结果或默认值
    """
    try:
        return json.loads(json_str)
    except (json.JSONDecodeError, TypeError):
        return default


def safe_json_dumps(obj: Any, default: str = "{}") -> str:
    """
    安全地序列化为JSON字符串
    
    Args:
        obj: 要序列化的对象
        default: 序列化失败时的默认值
        
    Returns:
        str: JSON字符串或默认值
    """
    try:
        return json.dumps(obj, ensure_ascii=False, indent=2)
    except (TypeError, ValueError):
        return default


def truncate_text(text: str, max_length: int = 100, suffix: str = "...") -> str:
    """
    截断文本
    
    Args:
        text: 原始文本
        max_length: 最大长度
        suffix: 截断后的后缀
        
    Returns:
        str: 截断后的文本
    """
    if len(text) <= max_length:
        return text
    return text[:max_length - len(suffix)] + suffix


def format_file_size(size_bytes: int) -> str:
    """
    格式化文件大小
    
    Args:
        size_bytes: 字节数
        
    Returns:
        str: 格式化后的大小字符串
    """
    if size_bytes == 0:
        return "0B"
        
    size_names = ["B", "KB", "MB", "GB", "TB"]
    i = 0
    while size_bytes >= 1024 and i < len(size_names) - 1:
        size_bytes /= 1024.0
        i += 1
        
    return f"{size_bytes:.1f}{size_names[i]}"


def ensure_directory(path: Union[str, Path]) -> Path:
    """
    确保目录存在
    
    Args:
        path: 目录路径
        
    Returns:
        Path: 目录路径对象
    """
    path_obj = Path(path)
    path_obj.mkdir(parents=True, exist_ok=True)
    return path_obj


def read_file_safe(file_path: Union[str, Path], encoding: str = 'utf-8') -> Optional[str]:
    """
    安全地读取文件
    
    Args:
        file_path: 文件路径
        encoding: 文件编码
        
    Returns:
        Optional[str]: 文件内容或None
    """
    try:
        with open(file_path, 'r', encoding=encoding) as f:
            return f.read()
    except (FileNotFoundError, IOError, UnicodeDecodeError):
        return None


def write_file_safe(file_path: Union[str, Path], content: str, encoding: str = 'utf-8') -> bool:
    """
    安全地写入文件
    
    Args:
        file_path: 文件路径
        content: 文件内容
        encoding: 文件编码
        
    Returns:
        bool: 是否写入成功
    """
    try:
        path_obj = Path(file_path)
        path_obj.parent.mkdir(parents=True, exist_ok=True)
        
        with open(file_path, 'w', encoding=encoding) as f:
            f.write(content)
        return True
    except (IOError, UnicodeEncodeError):
        return False


def retry_async(max_attempts: int = 3, delay: float = 1.0, backoff_factor: float = 2.0):
    """
    异步函数重试装饰器
    
    Args:
        max_attempts: 最大尝试次数
        delay: 初始延迟时间（秒）
        backoff_factor: 退避因子
    """
    def decorator(func: Callable):
        @functools.wraps(func)
        async def wrapper(*args, **kwargs):
            current_delay = delay
            last_exception = None
            
            for attempt in range(max_attempts):
                try:
                    return await func(*args, **kwargs)
                except Exception as e:
                    last_exception = e
                    if attempt < max_attempts - 1:
                        await asyncio.sleep(current_delay)
                        current_delay *= backoff_factor
                    else:
                        raise last_exception
                        
        return wrapper
    return decorator


def rate_limit(calls_per_second: float):
    """
    速率限制装饰器
    
    Args:
        calls_per_second: 每秒调用次数限制
    """
    min_interval = 1.0 / calls_per_second
    last_called = [0.0]
    
    def decorator(func: Callable):
        @functools.wraps(func)
        async def wrapper(*args, **kwargs):
            elapsed = asyncio.get_event_loop().time() - last_called[0]
            left_to_wait = min_interval - elapsed
            
            if left_to_wait > 0:
                await asyncio.sleep(left_to_wait)
                
            last_called[0] = asyncio.get_event_loop().time()
            return await func(*args, **kwargs)
            
        return wrapper
    return decorator


def validate_discussion_number(number: Union[str, int]) -> Optional[int]:
    """
    验证讨论编号
    
    Args:
        number: 讨论编号
        
    Returns:
        Optional[int]: 有效的讨论编号或None
    """
    try:
        num = int(number)
        return num if num > 0 else None
    except (ValueError, TypeError):
        return None


def extract_discussion_sections(content: str) -> Dict[str, str]:
    """
    从讨论内容中提取不同部分
    
    Args:
        content: 讨论内容
        
    Returns:
        Dict[str, str]: 各部分内容
    """
    sections = {
        'summary': '',
        'plan': '',
        'other': ''
    }
    
    if not content:
        return sections
        
    # 定义各部分的关键词
    summary_patterns = [
        r'#+\s*日结',
        r'#+\s*今日完成',
        r'#+\s*工作总结',
        r'#+\s*完成情况'
    ]
    
    plan_patterns = [
        r'#+\s*计划',
        r'#+\s*明日计划',
        r'#+\s*下一步',
        r'#+\s*待办'
    ]
    
    lines = content.split('\n')
    current_section = 'other'
    section_content = {'summary': [], 'plan': [], 'other': []}
    
    for line in lines:
        line_stripped = line.strip()
        
        # 检查是否是总结部分
        if any(re.search(pattern, line_stripped, re.IGNORECASE) for pattern in summary_patterns):
            current_section = 'summary'
            continue
            
        # 检查是否是计划部分
        if any(re.search(pattern, line_stripped, re.IGNORECASE) for pattern in plan_patterns):
            current_section = 'plan'
            continue
            
        # 添加内容到当前部分
        if line_stripped:
            section_content[current_section].append(line_stripped)
    
    # 合并各部分内容
    for section, lines in section_content.items():
        sections[section] = '\n'.join(lines)
    
    return sections


def calculate_content_metrics(content: str) -> Dict[str, Union[int, float]]:
    """
    计算内容指标
    
    Args:
        content: 内容文本
        
    Returns:
        Dict[str, Union[int, float]]: 内容指标
    """
    if not content:
        return {
            'character_count': 0,
            'word_count': 0,
            'line_count': 0,
            'paragraph_count': 0,
            'avg_words_per_line': 0.0,
            'readability_score': 0.0
        }
    
    # 基本统计
    char_count = len(content)
    word_count = len(re.findall(r'\b\w+\b', content))
    lines = [line.strip() for line in content.split('\n') if line.strip()]
    line_count = len(lines)
    paragraph_count = len([line for line in lines if not line.startswith(('- ', '* ', '1. ', '2. '))])
    
    # 平均每行词数
    avg_words_per_line = word_count / line_count if line_count > 0 else 0.0
    
    # 简单的可读性评分（基于句子长度和词汇复杂度）
    sentences = re.split(r'[.!?]+', content)
    avg_sentence_length = sum(len(s.split()) for s in sentences) / len(sentences) if sentences else 0
    readability_score = max(0, min(10, 10 - (avg_sentence_length - 10) * 0.5))
    
    return {
        'character_count': char_count,
        'word_count': word_count,
        'line_count': line_count,
        'paragraph_count': paragraph_count,
        'avg_words_per_line': avg_words_per_line,
        'readability_score': readability_score
    }


def format_analysis_score(score: float, max_score: float = 10.0) -> str:
    """
    格式化分析评分
    
    Args:
        score: 评分
        max_score: 最大评分
        
    Returns:
        str: 格式化后的评分字符串
    """
    percentage = (score / max_score) * 100
    
    if percentage >= 90:
        emoji = "🌟"
        level = "优秀"
    elif percentage >= 80:
        emoji = "✅"
        level = "良好"
    elif percentage >= 70:
        emoji = "👍"
        level = "中等"
    elif percentage >= 60:
        emoji = "⚠️"
        level = "需改进"
    else:
        emoji = "❌"
        level = "较差"
    
    return f"{emoji} {score:.1f}/{max_score} ({level})"
