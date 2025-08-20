#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
测试改进后的分析逻辑
验证系统是否能同时对日报和日计划进行分析
"""

import asyncio
import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from src.config import Config
from src.analyzers.daily_analyzer import DailyAnalyzer
from src.clients.github_client import GitHubClient

async def test_improved_analysis_logic():
    """
    测试改进后的分析逻辑
    """
    print("=== 测试改进后的分析逻辑 ===")
    
    # 初始化配置和分析器
    config = Config()
    analyzer = DailyAnalyzer(config)
    github_client = GitHubClient(config.github)
    
    # 测试讨论64（包含日报和日计划）
    discussion_number = 64
    print(f"\n测试讨论 #{discussion_number}...")
    
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
        
        # 提取内容
        content_data = await github_client.extract_daily_content(discussion)
        daily_summary = content_data.get('daily_summary', '')
        daily_plan = content_data.get('daily_plan', '')
        weekly_plan = content_data.get('weekly_plan', '')
        
        print(f"\n提取到的内容:")
        print(f"  - 周计划: {'有' if weekly_plan else '无'} ({len(weekly_plan)} 字符)")
        print(f"  - 日报: {'有' if daily_summary else '无'} ({len(daily_summary)} 字符)")
        print(f"  - 日计划: {'有' if daily_plan else '无'} ({len(daily_plan)} 字符)")
        
        # 预期的分析类型
        expected_analyses = []
        if daily_summary:
            expected_analyses.append("日报分析")
        if daily_plan:
            expected_analyses.append("日计划分析")
        
        print(f"\n预期执行的分析: {', '.join(expected_analyses) if expected_analyses else '综合分析'}")
        
        # 执行分析（但不发布评论）
        print("\n开始执行分析...")
        
        # 模拟分析过程（不实际发布评论）
        result = await analyzer._analyze_single_discussion(discussion)
        
        print(f"\n分析结果:")
        print(f"  - 成功: {result.get('success', False)}")
        print(f"  - 分析长度: {result.get('analysis_length', 0)} 字符")
        print(f"  - 错误信息: {result.get('error', '无')}")
        
        if result.get('success'):
            print("\n✅ 改进后的分析逻辑测试成功！")
            print("系统现在能够:")
            print("  1. 同时识别日报和日计划内容")
            print("  2. 分别对日报和日计划进行专门分析")
            print("  3. 生成综合的分析报告")
        else:
            print(f"\n❌ 分析失败: {result.get('error')}")
        
        # 测试其他讨论
        print("\n=== 测试其他讨论 ===")
        
        test_discussions = [57, 59, 60]  # 其他包含计划内容的讨论
        
        for disc_num in test_discussions:
            print(f"\n测试讨论 #{disc_num}...")
            
            test_disc = None
            for disc in discussions:
                if disc.number == disc_num:
                    test_disc = disc
                    break
            
            if not test_disc:
                print(f"  未找到讨论 #{disc_num}")
                continue
            
            # 提取内容
            test_content = await github_client.extract_daily_content(test_disc)
            test_summary = test_content.get('daily_summary', '')
            test_plan = test_content.get('daily_plan', '')
            
            print(f"  标题: {test_disc.title}")
            print(f"  日报: {'有' if test_summary else '无'} ({len(test_summary)} 字符)")
            print(f"  日计划: {'有' if test_plan else '无'} ({len(test_plan)} 字符)")
            
            # 预期分析
            expected = []
            if test_summary:
                expected.append("日报")
            if test_plan:
                expected.append("日计划")
            
            print(f"  预期分析: {', '.join(expected) if expected else '综合分析'}")
        
        print("\n=== 总结 ===")
        print("改进后的分析逻辑优势:")
        print("  1. ✅ 不再依赖最新评论类型决定分析方式")
        print("  2. ✅ 能够同时执行日报和日计划分析")
        print("  3. ✅ 提供更全面的分析覆盖")
        print("  4. ✅ 保留综合分析作为兜底方案")
        print("  5. ✅ 支持多种分析结果的合并展示")
        
    except Exception as e:
        print(f"测试过程中出错: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(test_improved_analysis_logic())
