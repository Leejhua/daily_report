#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import asyncio
from src.config import Config
from src.clients.github_client import GitHubClient
from src.analyzers.daily_analyzer import DailyAnalyzer

async def run_plan_analysis():
    """为讨论#62运行日计划分析"""
    config = Config()
    github_client = GitHubClient(config.github)
    analyzer = DailyAnalyzer(config)
    
    print("🔍 开始分析讨论#62的日计划...")
    
    # 获取所有讨论
    discussions = await github_client.get_daily_discussions()
    discussion_data = None
    
    for disc in discussions:
        if disc.number == 62:
            discussion_data = disc
            break
    
    if not discussion_data:
        print("❌ 未找到讨论#62")
        return
    
    print(f"📋 找到讨论: {discussion_data.title}")
    
    # 提取内容
    daily_content = await github_client.extract_daily_content(discussion_data)
    
    if not daily_content.get('daily_plan'):
        print("❌ 未找到日计划内容")
        return
    
    print("✅ 找到日计划内容，开始分析...")
    
    # 查找日计划评论ID
    plan_comment_id = await analyzer._find_content_comment_id(discussion_data.number, 'daily_plan')
    
    if not plan_comment_id:
        print("❌ 无法找到日计划评论ID")
        return
    
    print(f"📋 日计划评论ID: {plan_comment_id}")
    
    # 检查是否已有回复
    has_reply = await github_client.check_already_replied(
        discussion_data.number, plan_comment_id, 'daily_plan'
    )
    print(f"📋 是否已有回复: {has_reply}")
    
    if has_reply:
        print("✅ 日计划已有分析回复，无需重复分析")
        return
    
    # 执行日计划分析
    analysis_result = await analyzer.glm_client.analyze_daily_plan_content(
        daily_plan=daily_content['daily_plan'],
        weekly_plan=daily_content.get('weekly_plan', '')
    )
    print(f"📋 分析结果: {analysis_result[:200]}...")
    
    # 发布分析回复
    await github_client.post_analysis_comment(
        discussion_number=discussion_data.number,
        analysis_content=analysis_result,
        reply_to_comment_id=plan_comment_id,
        content_type='daily_plan'
    )
    
    print("✅ 日计划分析回复发布成功")

if __name__ == "__main__":
    asyncio.run(run_plan_analysis())