#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
调试分析过程中的问题
"""

import asyncio
import sys
from datetime import date
from src.config import Config
from src.analyzers.daily_analyzer import DailyAnalyzer

async def debug_analysis_process():
    """调试2025-08-20的分析过程"""
    print("🔍 调试2025-08-20分析过程")
    print("=" * 50)
    
    config = Config()
    analyzer = DailyAnalyzer(config)
    
    target_date = date(2025, 8, 20)
    print(f"📅 目标日期: {target_date}")
    
    try:
        # 1. 获取讨论列表
        print("\n📥 获取讨论列表...")
        discussions = await analyzer.github_client.get_daily_discussions(target_date)
        print(f"📊 获取到 {len(discussions)} 个讨论")
        
        for i, discussion in enumerate(discussions, 1):
            print(f"  {i}. #{discussion.number}: {discussion.title}")
        
        # 2. 逐个分析讨论
        print("\n🔄 开始逐个分析讨论...")
        successful_count = 0
        error_count = 0
        
        for i, discussion in enumerate(discussions, 1):
            print(f"\n--- 分析讨论 {i}/{len(discussions)}: #{discussion.number} ---")
            try:
                # 测试获取评论
                print(f"  📝 获取评论...")
                comments = await analyzer.github_client.get_discussion_comments(discussion.number)
                print(f"  📊 评论数: {len(comments)}")
                
                # 测试内容提取
                print(f"  📄 提取内容...")
                content_data = await analyzer.github_client.extract_daily_content(discussion)
                daily_summary = content_data.get('daily_summary', '')
                daily_plan = content_data.get('daily_plan', '')
                print(f"  📋 日结长度: {len(daily_summary)}, 计划长度: {len(daily_plan)}")
                
                if not daily_summary and not daily_plan:
                    print(f"  ⚠️ 未能提取到有效内容")
                    error_count += 1
                    continue
                
                print(f"  ✅ 讨论 #{discussion.number} 处理成功")
                successful_count += 1
                
            except Exception as e:
                print(f"  ❌ 讨论 #{discussion.number} 处理失败: {e}")
                error_count += 1
        
        print(f"\n📊 处理结果统计:")
        print(f"  ✅ 成功: {successful_count}")
        print(f"  ❌ 失败: {error_count}")
        print(f"  📊 总计: {len(discussions)}")
        
        # 3. 运行完整分析（不发布评论）
        print(f"\n🔄 运行完整分析流程...")
        # 临时禁用评论发布来测试
        original_post_comment = analyzer.github_client.post_analysis_comment
        
        async def mock_post_comment(discussion_number, content):
            print(f"  💬 模拟发布评论到 #{discussion_number} (长度: {len(content)})")
            return True
        
        analyzer.github_client.post_analysis_comment = mock_post_comment
        
        result = await analyzer.run_daily_analysis(target_date)
        
        # 恢复原始方法
        analyzer.github_client.post_analysis_comment = original_post_comment
        
        print(f"\n📋 完整分析结果:")
        print(f"  📄 分析的讨论数: {result['discussions_analyzed']}")
        print(f"  💬 发布的评论数: {result['comments_posted']}")
        print(f"  ✅ 成功状态: {result['success']}")
        print(f"  ❌ 错误数: {len(result['errors'])}")
        
        if result['errors']:
            print(f"\n❌ 错误详情:")
            for error in result['errors']:
                print(f"  - {error}")
            
    except Exception as e:
        print(f"❌ 调试过程中出错: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(debug_analysis_process())
