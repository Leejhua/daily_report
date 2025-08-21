#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
测试回复逻辑
验证日报分析和日计划分析是否正确回复到对应的评论楼层
"""

import asyncio
import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from src.config import Config
from src.clients.github_client import GitHubClient
from src.analyzers.daily_analyzer import DailyAnalyzer

async def test_reply_logic():
    """
    测试回复逻辑
    """
    print("=" * 80)
    print("测试回复逻辑")
    print("=" * 80)
    
    try:
        # 初始化
        config = Config()
        github_client = GitHubClient(config.github)
        analyzer = DailyAnalyzer(config)
        
        # 测试讨论编号
        test_discussion_number = 64
        
        print(f"\n🔍 测试讨论 #{test_discussion_number}")
        
        # 获取讨论信息
        discussions = await github_client.get_daily_discussions()
        target_discussion = None
        for discussion in discussions:
            if discussion.number == test_discussion_number:
                target_discussion = discussion
                break
        
        if not target_discussion:
            print(f"❌ 未找到讨论 #{test_discussion_number}")
            return
        
        print(f"✅ 找到讨论: {target_discussion.title}")
        
        # 获取评论
        comments = await github_client.get_discussion_comments(test_discussion_number)
        print(f"\n📝 评论数量: {len(comments)}")
        
        if len(comments) < 2:
            print("❌ 评论数量不足，无法测试回复逻辑")
            return
        
        # 按时间排序评论，最新的在前
        comments.sort(key=lambda x: x.updated_at, reverse=True)
        
        print("\n📋 评论列表:")
        for i, comment in enumerate(comments[:5], 1):
            print(f"  [{i}] ID: {comment.id}")
            print(f"      作者: {comment.author}")
            print(f"      时间: {comment.created_at}")
            print(f"      内容预览: {comment.body[:100]}...")
            print()
        
        # 测试查找日报评论ID
        print("\n🔍 测试查找日报评论ID:")
        daily_summary_comment_id = await analyzer._find_content_comment_id(
            test_discussion_number, 'daily_summary'
        )
        if daily_summary_comment_id:
            print(f"✅ 找到日报评论ID: {daily_summary_comment_id}")
        else:
            print("❌ 未找到日报评论ID")
        
        # 测试查找日计划评论ID
        print("\n🔍 测试查找日计划评论ID:")
        daily_plan_comment_id = await analyzer._find_content_comment_id(
            test_discussion_number, 'daily_plan'
        )
        if daily_plan_comment_id:
            print(f"✅ 找到日计划评论ID: {daily_plan_comment_id}")
        else:
            print("❌ 未找到日计划评论ID")
        
        # 检查现有的分析回复
        print("\n🔍 检查现有的分析回复:")
        analysis_replies = []
        
        for comment in comments:
            if comment.body.startswith("## 📊") or comment.body.startswith("## 📋"):
                analysis_replies.append({
                    'id': comment.id,
                    'type': '📊 日报分析' if '📊' in comment.body else '📋 日计划分析',
                    'author': comment.author,
                    'created_at': comment.created_at,
                    'reply_to': getattr(comment, 'reply_to_id', None)
                })
        
        if analysis_replies:
            print(f"找到 {len(analysis_replies)} 个分析回复:")
            for reply in analysis_replies:
                print(f"  - {reply['type']} (ID: {reply['id']})")
                print(f"    作者: {reply['author']}")
                print(f"    时间: {reply['created_at']}")
                if reply['reply_to']:
                    print(f"    回复到: {reply['reply_to']}")
                else:
                    print(f"    类型: 顶级评论")
                print()
        else:
            print("未找到分析回复")
        
        # 验证回复逻辑
        print("\n📊 回复逻辑验证:")
        print("-" * 40)
        
        if daily_summary_comment_id and daily_plan_comment_id:
            print("✅ 评论ID识别正常")
            print(f"   日报评论ID: {daily_summary_comment_id}")
            print(f"   日计划评论ID: {daily_plan_comment_id}")
            
            # 检查分析回复是否正确回复到对应评论
            daily_report_analysis_correct = False
            daily_plan_analysis_correct = False
            
            for reply in analysis_replies:
                if '📊' in reply['type'] and reply.get('reply_to') == daily_summary_comment_id:
                    daily_report_analysis_correct = True
                    print(f"✅ 日报分析正确回复到日报评论楼层")
                elif '📋' in reply['type'] and reply.get('reply_to') == daily_plan_comment_id:
                    daily_plan_analysis_correct = True
                    print(f"✅ 日计划分析正确回复到日计划评论楼层")
            
            if not daily_report_analysis_correct:
                print(f"❌ 日报分析未正确回复到日报评论楼层")
            if not daily_plan_analysis_correct:
                print(f"❌ 日计划分析未正确回复到日计划评论楼层")
        else:
            print("❌ 评论ID识别失败")
        
        print("\n" + "=" * 80)
        print("测试完成")
        print("=" * 80)
        
    except Exception as e:
        print(f"❌ 测试失败: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(test_reply_logic())