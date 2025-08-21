#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
检查讨论64的最新评论情况
验证分析评论是否成功发布
"""

import asyncio
import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from src.config import Config
from src.clients.github_client import GitHubClient
from datetime import datetime

async def check_latest_comments():
    """
    检查讨论64的最新评论
    """
    print("=== 检查讨论64的最新评论 ===")
    
    # 初始化客户端
    config = Config()
    github_client = GitHubClient(config.github)
    
    discussion_number = 64
    
    try:
        # 获取所有评论
        comments = await github_client.get_discussion_comments(discussion_number)
        
        if not comments:
            print("该讨论没有评论")
            return
        
        print(f"共找到 {len(comments)} 条评论")
        
        # 按时间排序
        comments.sort(key=lambda x: x.updated_at, reverse=True)
        
        print("\n=== 所有评论（按时间倒序） ===")
        
        for i, comment in enumerate(comments, 1):
            print(f"\n评论 {i}:")
            print(f"  ID: {comment.id}")
            print(f"  作者: {comment.author}")
            print(f"  创建时间: {comment.created_at}")
            print(f"  更新时间: {comment.updated_at}")
            print(f"  内容长度: {len(comment.body)} 字符")
            
            # 检查是否是分析评论
            content = comment.body
            is_analysis = any(keyword in content for keyword in [
                '分析报告', '## 📊', '日报分析', '日计划分析', 
                '工作完成情况', '计划执行', '建议', '评估'
            ])
            
            print(f"  是否为分析评论: {'是' if is_analysis else '否'}")
            
            # 显示内容预览
            print(f"  内容预览: {content[:100]}...")
            
            # 如果是分析评论，显示更多内容
            if is_analysis:
                print(f"\n  完整分析内容:")
                print("  " + "="*50)
                print("  " + content.replace('\n', '\n  '))
                print("  " + "="*50)
        
        # 检查最新评论的详细信息
        latest_comment = comments[0]
        print(f"\n=== 最新评论详细信息 ===")
        print(f"作者: {latest_comment.author}")
        print(f"时间: {latest_comment.updated_at}")
        print(f"内容类型: {github_client.identify_content_type(latest_comment.body)}")
        
        # 检查是否有机器人评论
        bot_comments = [c for c in comments if 'bot' in c.author.lower() or c.author == config.github.username]
        print(f"\n机器人评论数量: {len(bot_comments)}")
        
        if bot_comments:
            print("机器人评论:")
            for bot_comment in bot_comments:
                print(f"  - {bot_comment.author}: {bot_comment.updated_at} ({len(bot_comment.body)} 字符)")
        
        # 检查最近5分钟内的评论
        now = datetime.now()
        recent_comments = []
        for comment in comments:
            # 计算时间差（注意时区问题）
            time_diff = abs((now - comment.updated_at.replace(tzinfo=None)).total_seconds())
            if time_diff < 300:  # 5分钟内
                recent_comments.append(comment)
        
        print(f"\n最近5分钟内的评论: {len(recent_comments)} 条")
        for recent in recent_comments:
            print(f"  - {recent.author}: {recent.updated_at} ({len(recent.body)} 字符)")
        
    except Exception as e:
        print(f"检查评论时出错: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(check_latest_comments())