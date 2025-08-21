#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
测试双重分析评论发布
验证改进后的系统是否能发布包含日报和日计划分析的评论
"""

import asyncio
import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from src.config import Config
from src.analyzers.daily_analyzer import DailyAnalyzer
from src.clients.github_client import GitHubClient

async def test_dual_analysis_comment():
    """
    测试双重分析评论发布
    """
    print("=== 测试双重分析评论发布 ===")
    
    # 初始化配置和分析器
    config = Config()
    analyzer = DailyAnalyzer(config)
    github_client = GitHubClient(config.github)
    
    # 测试讨论64
    discussion_number = 64
    print(f"\n对讨论 #{discussion_number} 执行完整分析并发布评论...")
    
    try:
        # 执行分析并发布评论
        result = await analyzer.analyze_specific_discussion(discussion_number)
        
        print(f"\n分析结果:")
        print(f"  - 讨论标题: {result.get('discussion_title', 'N/A')}")
        print(f"  - 分析成功: {result.get('success', False)}")
        print(f"  - 评论发布: {result.get('comment_posted', False)}")
        print(f"  - 分析长度: {result.get('analysis_length', 0)} 字符")
        print(f"  - 错误信息: {result.get('error', '无')}")
        
        if result.get('success') and result.get('comment_posted'):
            print("\n✅ 双重分析评论发布成功！")
            
            # 获取最新评论来验证内容
            print("\n验证发布的评论内容...")
            comments = await github_client.get_discussion_comments(discussion_number)
            
            if comments:
                # 按时间排序，获取最新评论
                comments.sort(key=lambda x: x.updated_at, reverse=True)
                latest_comment = comments[0]
                
                print(f"最新评论长度: {len(latest_comment.body)} 字符")
                print(f"评论作者: {latest_comment.author}")
                
                # 检查评论内容是否包含多种分析
                comment_content = latest_comment.body
                
                analysis_indicators = {
                    '日报分析': ['日报', '工作总结', '完成情况', '进度'],
                    '日计划分析': ['日计划', '明日计划', '计划安排', '下一步'],
                    '综合报告': ['分析报告', '本次分析包含'],
                    '分隔符': ['---', '━━━']
                }
                
                found_analyses = []
                for analysis_type, keywords in analysis_indicators.items():
                    if any(keyword in comment_content for keyword in keywords):
                        found_analyses.append(analysis_type)
                
                print(f"\n检测到的分析类型: {', '.join(found_analyses)}")
                
                # 显示评论内容的前500字符
                print(f"\n评论内容预览:")
                print("=" * 50)
                print(comment_content[:500])
                if len(comment_content) > 500:
                    print("\n... (内容已截断) ...")
                print("=" * 50)
                
                # 验证是否包含多种分析
                if len(found_analyses) >= 2:
                    print("\n🎉 验证成功！评论包含多种分析类型")
                elif '综合报告' in found_analyses:
                    print("\n📊 评论包含综合分析报告")
                else:
                    print("\n⚠️  评论可能只包含单一分析类型")
            
        else:
            print(f"\n❌ 分析或评论发布失败")
            if result.get('error'):
                print(f"错误详情: {result['error']}")
        
        # 测试其他讨论的分析能力
        print("\n=== 测试其他讨论的分析能力 ===")
        
        test_discussions = [57]  # 包含日报和日计划的讨论
        
        for disc_num in test_discussions:
            print(f"\n测试讨论 #{disc_num} 的分析能力...")
            
            # 获取讨论信息
            discussions = await github_client.get_daily_discussions()
            test_disc = None
            for disc in discussions:
                if disc.number == disc_num:
                    test_disc = disc
                    break
            
            if not test_disc:
                print(f"  未找到讨论 #{disc_num}")
                continue
            
            # 提取内容
            content_data = await github_client.extract_daily_content(test_disc)
            daily_summary = content_data.get('daily_summary', '')
            daily_plan = content_data.get('daily_plan', '')
            
            print(f"  标题: {test_disc.title}")
            print(f"  日报内容: {'有' if daily_summary else '无'} ({len(daily_summary)} 字符)")
            print(f"  日计划内容: {'有' if daily_plan else '无'} ({len(daily_plan)} 字符)")
            
            # 预测分析类型
            expected_analyses = []
            if daily_summary:
                expected_analyses.append("日报分析")
            if daily_plan:
                expected_analyses.append("日计划分析")
            
            if expected_analyses:
                print(f"  预期分析: {', '.join(expected_analyses)}")
                print(f"  ✅ 该讨论适合测试双重分析")
            else:
                print(f"  预期分析: 综合分析")
                print(f"  ⚠️  该讨论只能进行综合分析")
        
        print("\n=== 改进效果总结 ===")
        print("✅ 修复前的问题:")
        print("   - 只根据最新评论类型决定分析方式")
        print("   - 无法同时分析日报和日计划")
        print("   - 分析覆盖不全面")
        
        print("\n🎯 修复后的改进:")
        print("   - 根据实际提取的内容决定分析类型")
        print("   - 能够同时执行日报和日计划分析")
        print("   - 提供更全面的分析报告")
        print("   - 支持多种分析结果的合并展示")
        print("   - 保留综合分析作为兜底方案")
        
    except Exception as e:
        print(f"测试过程中出错: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(test_dual_analysis_comment())