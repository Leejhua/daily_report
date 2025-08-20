#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
测试分离分析评论功能
验证日报分析和日计划分析是否能分别发布到对应的讨论中
"""

import asyncio
import sys
import os
from datetime import datetime

# 添加项目根目录到Python路径
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from src.config import Config
from src.analyzers.daily_analyzer import DailyAnalyzer
from src.clients.github_client import GitHubClient

async def test_separate_analysis_comments():
    """
    测试分离分析评论功能
    """
    print("=" * 60)
    print("测试分离分析评论功能")
    print("=" * 60)
    
    try:
        # 1. 初始化配置和分析器
        config = Config()
        analyzer = DailyAnalyzer(config)
        github_client = GitHubClient(config.github)
        
        print("\n1. 获取最近的讨论列表...")
        discussions = await github_client.get_daily_discussions()
        print(f"找到 {len(discussions)} 个讨论")
        
        # 2. 查找包含日报和日计划的讨论（如讨论#64）
        target_discussion = None
        for discussion in discussions:
            if discussion.number == 64:  # 测试讨论#64
                target_discussion = discussion
                break
        
        if not target_discussion:
            print("未找到讨论#64，尝试分析第一个讨论")
            if discussions:
                target_discussion = discussions[0]
            else:
                print("没有可用的讨论进行测试")
                return
        
        print(f"\n2. 分析讨论 #{target_discussion.number}: {target_discussion.title}")
        
        # 3. 提取内容
        content_data = await github_client.extract_daily_content(target_discussion)
        print(f"\n提取的内容:")
        print(f"- 日报内容: {'有' if content_data.get('daily_summary') else '无'} ({len(content_data.get('daily_summary', ''))} 字符)")
        print(f"- 日计划内容: {'有' if content_data.get('daily_plan') else '无'} ({len(content_data.get('daily_plan', ''))} 字符)")
        print(f"- 周计划内容: {'有' if content_data.get('weekly_plan') else '无'} ({len(content_data.get('weekly_plan', ''))} 字符)")
        
        # 4. 执行分析
        print(f"\n3. 执行分析...")
        result = await analyzer._analyze_single_discussion(target_discussion)
        
        # 5. 显示分析结果
        print(f"\n4. 分析结果:")
        print(f"- 分析成功: {result.get('success', False)}")
        
        if 'analyses' in result:
            analyses = result['analyses']
            print(f"- 执行的分析数量: {len(analyses)}")
            print(f"- 成功的分析: {result.get('successful_count', 0)}")
            print(f"- 失败的分析: {result.get('failed_count', 0)}")
            
            print("\n分析详情:")
            for i, analysis in enumerate(analyses, 1):
                print(f"  {i}. {analysis['type']}:")
                print(f"     - 成功: {analysis.get('success', False)}")
                print(f"     - 发布到讨论: #{analysis.get('discussion_number', 'N/A')}")
                if 'length' in analysis:
                    print(f"     - 内容长度: {analysis['length']} 字符")
                if 'note' in analysis:
                    print(f"     - 备注: {analysis['note']}")
                if 'error' in analysis:
                    print(f"     - 错误: {analysis['error']}")
        
        if 'error' in result:
            print(f"- 错误信息: {result['error']}")
        
        # 6. 验证评论发布情况
        print(f"\n5. 验证评论发布情况...")
        
        # 检查原讨论的最新评论
        print(f"\n检查讨论 #{target_discussion.number} 的最新评论:")
        comments = await github_client.get_discussion_comments(target_discussion.number)
        if comments:
            latest_comment = comments[-1]
            print(f"- 最新评论作者: {latest_comment.author}")
            print(f"- 评论时间: {latest_comment.created_at}")
            print(f"- 评论长度: {len(latest_comment.body)} 字符")
            print(f"- 是否为分析评论: {'是' if '本分析由GLM-4.5自动生成' in latest_comment.body else '否'}")
        else:
            print("- 没有评论")
        
        # 7. 测试查找日计划讨论的功能
        if content_data.get('daily_plan'):
            print(f"\n6. 测试查找日计划讨论功能...")
            plan_discussion_number = await analyzer._find_plan_discussion(content_data['daily_plan'])
            if plan_discussion_number:
                print(f"- 找到日计划讨论: #{plan_discussion_number}")
                
                # 检查该讨论的最新评论
                plan_comments = await github_client.get_discussion_comments(plan_discussion_number)
                if plan_comments:
                    latest_plan_comment = plan_comments[-1]
                    print(f"- 日计划讨论最新评论作者: {latest_plan_comment.author}")
                    print(f"- 评论时间: {latest_plan_comment.created_at}")
                    print(f"- 是否为分析评论: {'是' if '本分析由GLM-4.5自动生成' in latest_plan_comment.body else '否'}")
            else:
                print("- 未找到对应的日计划讨论")
        
        print(f"\n=" * 60)
        print("测试完成")
        print(f"=" * 60)
        
    except Exception as e:
        print(f"测试过程中发生错误: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(test_separate_analysis_comments())
