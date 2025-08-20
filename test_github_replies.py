#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
测试GitHub回复功能
验证GitHub API是否能正确获取和发布回复评论
"""

import asyncio
import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from src.config import Config
from src.clients.github_client import GitHubClient

async def test_github_replies():
    """
    测试GitHub回复功能
    """
    print("=" * 80)
    print("测试GitHub回复功能")
    print("=" * 80)
    
    try:
        # 初始化
        config = Config()
        github_client = GitHubClient(config.github)
        
        # 测试讨论编号
        test_discussion_number = 64
        
        print(f"\n🔍 测试讨论 #{test_discussion_number}")
        
        # 获取结构化评论数据（包括回复）
        print("\n📝 获取结构化评论数据...")
        structured_comments = await github_client._get_all_comments_with_replies(test_discussion_number)
        
        print(f"\n📊 评论结构:")
        print(f"  顶级评论数量: {len(structured_comments['top_level'])}")
        print(f"  回复评论数量: {len(structured_comments['replies'])}")
        
        # 显示顶级评论
        print("\n📋 顶级评论列表:")
        for i, comment in enumerate(structured_comments['top_level'], 1):
            print(f"  [{i}] ID: {comment.id}")
            print(f"      作者: {comment.user.login}")
            print(f"      时间: {comment.created_at}")
            print(f"      内容预览: {comment.body[:100]}...")
            
            # 检查是否是分析评论
            if "## 📊" in comment.body or "## 📋" in comment.body:
                print(f"      🎯 类型: 分析评论")
            elif "日报" in comment.body:
                print(f"      🎯 类型: 日报评论")
            elif "日计划" in comment.body or "计划" in comment.body:
                print(f"      🎯 类型: 日计划评论")
            else:
                print(f"      🎯 类型: 普通评论")
            print()
        
        # 显示回复评论
        if structured_comments['replies']:
            print("\n💬 回复评论列表:")
            for parent_id, replies in structured_comments['replies'].items():
                print(f"\n  回复到评论 {parent_id}:")
                for j, reply in enumerate(replies, 1):
                    print(f"    [{j}] ID: {reply.id}")
                    print(f"        作者: {reply.user.login}")
                    print(f"        时间: {reply.created_at}")
                    print(f"        内容预览: {reply.body[:100]}...")
                    
                    # 检查是否是分析回复
                    if "## 📊" in reply.body or "## 📋" in reply.body:
                        print(f"        🎯 类型: 分析回复")
                    print()
        else:
            print("\n💬 没有找到回复评论")
        
        # 测试发布一个测试回复
        print("\n🧪 测试发布回复功能...")
        
        # 获取第一个评论的ID作为回复目标
        if structured_comments['top_level']:
            target_comment_id = structured_comments['top_level'][0].id
            test_content = "## 🧪 测试回复\n\n这是一个测试回复，用于验证回复功能是否正常工作。\n\n---\n*测试时间: 2025-01-20*"
            
            print(f"目标评论ID: {target_comment_id}")
            print(f"回复内容: {test_content[:50]}...")
            
            # 发布测试回复
            success = await github_client._post_repo_discussion_comment(
                test_discussion_number, 
                test_content, 
                reply_to_comment_id=target_comment_id
            )
            
            if success:
                print("✅ 测试回复发布成功")
                
                # 等待一下，然后重新获取评论验证
                print("\n⏳ 等待3秒后重新获取评论...")
                await asyncio.sleep(3)
                
                updated_structured_comments = await github_client._get_all_comments_with_replies(test_discussion_number)
                
                # 检查是否有新的回复
                new_replies_count = len(updated_structured_comments['replies'].get(target_comment_id, []))
                old_replies_count = len(structured_comments['replies'].get(target_comment_id, []))
                
                if new_replies_count > old_replies_count:
                    print(f"✅ 回复功能验证成功，新增回复数量: {new_replies_count - old_replies_count}")
                else:
                    print(f"❌ 回复功能验证失败，回复数量未增加")
                    
            else:
                print("❌ 测试回复发布失败")
        else:
            print("❌ 没有找到可以回复的评论")
        
        print("\n" + "=" * 80)
        print("测试完成")
        print("=" * 80)
        
    except Exception as e:
        print(f"❌ 测试失败: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(test_github_replies())