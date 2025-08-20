#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
调试日计划提取问题
"""

import asyncio
import sys
import os

# 添加项目根目录到Python路径
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from src.config import Config
from src.clients.github_client import GitHubClient
from src.utils.logger import setup_logging
import logging

async def debug_daily_plan_extraction():
    """调试日计划提取"""
    setup_logging()
    logger = logging.getLogger("debug_daily_plan")
    
    try:
        # 加载配置
        config = Config()
        logger.info("配置加载成功")
        
        # 初始化GitHub客户端
        github_client = GitHubClient(config.github)
        logger.info("GitHub客户端初始化成功")
        
        # 获取日结讨论
        daily_discussions = await github_client.get_daily_discussions()
        logger.info(f"获取到 {len(daily_discussions)} 个日结讨论")
        
        if not daily_discussions:
            logger.warning("没有找到日结讨论")
            return
        
        # 分析每个讨论
        for i, discussion in enumerate(daily_discussions[:3], 1):
            print(f"\n{'='*60}")
            print(f"📋 讨论 #{i}: {discussion.title}")
            print(f"📅 更新时间: {discussion.updated_at}")
            print(f"💬 评论数: {discussion.comments_count}")
            print(f"{'='*60}")
            
            # 提取内容
            content_data = await github_client.extract_daily_content(discussion)
            
            print(f"\n📊 提取结果:")
            print(f"  - 周期计划: {len(content_data.get('weekly_plan', ''))} 字符")
            print(f"  - 日报: {len(content_data.get('daily_summary', ''))} 字符")
            print(f"  - 日计划: {len(content_data.get('daily_plan', ''))} 字符")
            
            # 显示详细内容
            if content_data.get('weekly_plan'):
                print(f"\n📋 周期计划内容:")
                print(content_data['weekly_plan'][:300] + "..." if len(content_data['weekly_plan']) > 300 else content_data['weekly_plan'])
            
            if content_data.get('daily_summary'):
                print(f"\n🗒️ 日报内容:")
                print(content_data['daily_summary'][:300] + "..." if len(content_data['daily_summary']) > 300 else content_data['daily_summary'])
            
            if content_data.get('daily_plan'):
                print(f"\n📅 日计划内容:")
                print(content_data['daily_plan'][:300] + "..." if len(content_data['daily_plan']) > 300 else content_data['daily_plan'])
            else:
                print(f"\n❌ 未找到日计划内容")
                
                # 获取评论详情进行分析
                print(f"\n🔍 分析评论内容:")
                comments = await github_client.get_discussion_comments(discussion.number)
                
                daily_plan_keywords = [
                    '日计划', '明日计划', '明天计划', '下一步', '待办',
                    '明日安排', '明天安排', '计划完成', '准备'
                ]
                
                for j, comment in enumerate(comments[:5], 1):
                    comment_content = comment.body.lower()
                    has_keywords = any(keyword in comment_content for keyword in daily_plan_keywords)
                    
                    print(f"\n  评论 #{j}:")
                    print(f"    长度: {len(comment.body)} 字符")
                    print(f"    包含日计划关键词: {has_keywords}")
                    if has_keywords:
                        matched_keywords = [kw for kw in daily_plan_keywords if kw in comment_content]
                        print(f"    匹配的关键词: {matched_keywords}")
                    print(f"    内容预览: {comment.body[:100]}...")
            
            print(f"\n{'-'*60}")
    
    except Exception as e:
        logger.error(f"调试过程中出错: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(debug_daily_plan_extraction())