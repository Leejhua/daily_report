#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import asyncio
from datetime import date
from src.config import Config
from src.clients.github_client import GitHubClient

async def get_discussions_for_date():
    config = Config()
    github_client = GitHubClient(config.github)
    
    target_date = date(2025, 8, 25)
    discussions = await github_client.get_daily_discussions(target_date)
    
    print(f"📅 {target_date} 的讨论:")
    print(f"总数: {len(discussions)}")
    print()
    
    for i, discussion in enumerate(discussions, 1):
        print(f"讨论 {i}:")
        print(f"  编号: #{discussion.number}")
        print(f"  标题: {discussion.title}")
        print(f"  作者: {discussion.author}")
        print(f"  分类: {discussion.category}")
        print(f"  评论数: {discussion.comments_count}")
        print(f"  创建时间: {discussion.created_at}")
        print(f"  URL: {discussion.url}")
        print(f"  内容预览: {discussion.body[:100]}...")
        print()
        
        # 获取评论
        comments = await github_client.get_discussion_comments(discussion.number)
        print(f"  评论详情 ({len(comments)} 条):")
        for j, comment in enumerate(comments, 1):
            print(f"    评论 {j}:")
            print(f"      作者: {comment.author}")
            print(f"      时间: {comment.created_at}")
            print(f"      内容: {comment.body[:200]}...")
            print()
        print("=" * 50)

if __name__ == "__main__":
    asyncio.run(get_discussions_for_date())