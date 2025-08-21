#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
分析内容提取和分析逻辑问题
验证系统是否正确提取和分析所有内容类型
"""

import asyncio
import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from src.config import Config
from src.clients.github_client import GitHubClient
from src.clients.glm_client import GLMClient

async def analyze_content_extraction_logic():
    """
    分析当前内容提取和分析逻辑的问题
    """
    print("=== 内容提取和分析逻辑分析 ===")
    
    # 初始化配置和客户端
    config = Config()
    github_client = GitHubClient(config.github)
    glm_client = GLMClient(config.glm)
    
    # 测试讨论64的内容提取
    discussion_number = 64
    print(f"\n分析讨论 #{discussion_number} 的内容提取逻辑...")
    
    try:
        # 获取讨论信息
        discussions = await github_client.get_daily_discussions()
        discussion = None
        for disc in discussions:
            if disc.number == discussion_number:
                discussion = disc
                break
        
        if not discussion:
            print(f"未找到讨论 #{discussion_number}")
            return
        
        print(f"讨论标题: {discussion.title}")
        print(f"首楼内容长度: {len(discussion.body)} 字符")
        
        # 1. 提取内容
        print("\n=== 步骤1: 内容提取 ===")
        content_data = await github_client.extract_daily_content(discussion)
        
        print(f"周计划内容: {len(content_data.get('weekly_plan', ''))} 字符")
        print(f"日报内容: {len(content_data.get('daily_summary', ''))} 字符")
        print(f"日计划内容: {len(content_data.get('daily_plan', ''))} 字符")
        
        # 2. 获取所有评论并分析类型
        print("\n=== 步骤2: 评论类型分析 ===")
        comments = await github_client.get_discussion_comments(discussion.number)
        
        if comments:
            print(f"共有 {len(comments)} 条评论")
            
            for i, comment in enumerate(comments, 1):
                content_type = github_client.identify_content_type(comment.body)
                print(f"评论 {i}: 类型={content_type}, 长度={len(comment.body)} 字符")
                print(f"  内容预览: {comment.body[:100]}...")
                print()
            
            # 最新评论分析
            comments.sort(key=lambda x: x.updated_at, reverse=True)
            latest_comment = comments[0]
            latest_type = github_client.identify_content_type(latest_comment.body)
            
            print(f"最新评论类型: {latest_type}")
            print(f"最新评论内容: {latest_comment.body[:200]}...")
        
        # 3. 分析当前逻辑的问题
        print("\n=== 步骤3: 当前逻辑问题分析 ===")
        
        daily_summary = content_data.get('daily_summary', '')
        daily_plan = content_data.get('daily_plan', '')
        weekly_plan = content_data.get('weekly_plan', '')
        
        print(f"提取到的内容:")
        print(f"  - 周计划: {'有' if weekly_plan else '无'} ({len(weekly_plan)} 字符)")
        print(f"  - 日报: {'有' if daily_summary else '无'} ({len(daily_summary)} 字符)")
        print(f"  - 日计划: {'有' if daily_plan else '无'} ({len(daily_plan)} 字符)")
        
        # 模拟当前分析逻辑
        if comments:
            latest_type = github_client.identify_content_type(comments[0].body)
            print(f"\n当前分析逻辑会执行:")
            
            if latest_type == 'daily_report' and daily_summary:
                print("  ✓ 日报分析 (analyze_daily_report_content)")
                print("  ✗ 日计划分析 (未执行)")
            elif latest_type == 'daily_plan' and daily_plan:
                print("  ✗ 日报分析 (未执行)")
                print("  ✓ 日计划分析 (analyze_daily_plan_content)")
            else:
                print("  ✓ 综合分析 (generate_comprehensive_analysis)")
                print("  ✗ 专门的日报/日计划分析 (未执行)")
        
        # 4. 提出改进方案
        print("\n=== 步骤4: 改进方案 ===")
        print("问题: 当前逻辑只根据最新评论类型决定分析方法，导致:")
        print("  1. 如果最新是日报，不会分析日计划")
        print("  2. 如果最新是日计划，不会分析日报")
        print("  3. 无法同时对日报和日计划进行专门分析")
        
        print("\n建议的改进方案:")
        print("  1. 分别检查是否有日报和日计划内容")
        print("  2. 如果有日报内容，执行日报分析")
        print("  3. 如果有日计划内容，执行日计划分析")
        print("  4. 可以同时执行多种分析，生成综合报告")
        
        # 5. 演示改进后的逻辑
        print("\n=== 步骤5: 改进后的分析逻辑演示 ===")
        
        analyses_to_run = []
        
        if daily_summary:
            analyses_to_run.append("日报分析")
            print(f"  ✓ 将执行日报分析 (内容长度: {len(daily_summary)} 字符)")
        
        if daily_plan:
            analyses_to_run.append("日计划分析")
            print(f"  ✓ 将执行日计划分析 (内容长度: {len(daily_plan)} 字符)")
        
        if not analyses_to_run:
            print("  ✓ 将执行综合分析 (兜底方案)")
        
        print(f"\n总共将执行 {len(analyses_to_run)} 种分析: {', '.join(analyses_to_run)}")
        
    except Exception as e:
        print(f"分析过程中出错: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(analyze_content_extraction_logic())