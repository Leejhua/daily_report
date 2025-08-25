#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import asyncio
from src.clients.github_client import GitHubClient
from src.config import Config
from src.analyzers.daily_analyzer import DailyAnalyzer

async def reply_to_specific_comment():
    """为讨论#62中ID为DC_kwDOPMm80c4A2IFa的评论生成分析回复"""
    config = Config()
    client = GitHubClient(config)
    analyzer = DailyAnalyzer(config)
    
    discussion_number = 62
    target_comment_id = "DC_kwDOPMm80c4A2IFa"
    
    print(f"📋 为讨论#{discussion_number}的评论{target_comment_id}生成分析回复...")
    
    # 获取评论列表
    comments = await client.get_discussion_comments(discussion_number)
    
    # 找到目标评论
    target_comment = None
    for comment in comments:
        if comment.id == target_comment_id:
            target_comment = comment
            break
    
    if not target_comment:
        print(f"❌ 未找到评论 {target_comment_id}")
        return
    
    print(f"✅ 找到目标评论:")
    print(f"   作者: {target_comment.author.login}")
    print(f"   时间: {target_comment.created_at}")
    print(f"   内容预览: {target_comment.body[:100]}...")
    
    # 检查是否已有回复
    has_reply = await client.check_already_replied(
        discussion_number, target_comment_id, 'daily_summary'
    )
    print(f"   已有分析回复: {has_reply}")
    
    if has_reply:
        print("⚠️  该评论已有分析回复，跳过")
        return
    
    # 生成分析内容
    print("\n🧠 生成日报分析...")
    analysis_result = await analyzer.analyze_daily_content(
        target_comment.body, 'daily_summary'
    )
    
    if not analysis_result:
        print("❌ 分析生成失败")
        return
    
    print(f"✅ 分析生成成功: {len(analysis_result)} 字符")
    print(f"   内容预览: {analysis_result[:100]}...")
    
    # 发布回复
    print("\n📤 发布分析回复...")
    success = await client.post_analysis_comment(
        discussion_number, analysis_result, target_comment_id, 'daily_summary'
    )
    
    if success:
        print("✅ 分析回复发布成功！")
    else:
        print("❌ 分析回复发布失败")

if __name__ == "__main__":
    asyncio.run(reply_to_specific_comment())