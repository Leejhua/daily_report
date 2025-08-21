#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
分析日计划检测问题
详细分析为什么某些包含计划内容的讨论没有被识别为日计划类型
"""

import asyncio
import sys
import os
from datetime import date

# 添加项目根目录到路径
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from src.config import Config
from src.clients.github_client import GitHubClient

async def analyze_specific_discussions():
    """分析特定讨论的内容识别问题"""
    print("=== 分析讨论内容识别问题 ===")
    
    config = Config()
    github_client = GitHubClient(config.github)
    
    # 需要分析的讨论编号（从测试结果中获取）
    target_discussions = [59, 60]  # 这两个被识别为unknown
    
    for discussion_num in target_discussions:
        print(f"\n分析讨论 #{discussion_num}:")
        
        try:
            # 获取评论
            comments = await github_client.get_discussion_comments(discussion_num)
            
            if not comments:
                print("  无评论")
                continue
                
            # 按时间排序，获取最新评论
            comments.sort(key=lambda x: x.updated_at, reverse=True)
            latest_comment = comments[0]
            
            print(f"  最新评论内容:")
            print(f"  {latest_comment.body}")
            print(f"  评论长度: {len(latest_comment.body)} 字符")
            
            # 详细分析内容类型识别过程
            content = latest_comment.body
            content_lower = content.lower()
            
            # 日报关键词
            daily_report_keywords = [
                '日报', '日结', '今日完成', '今日工作', '工作总结', 
                '完成情况', '今天完成', '今天做了', '进度', '遇到问题',
                '今日进展', '工作内容'
            ]
            
            # 日计划关键词  
            daily_plan_keywords = [
                '日计划', '明日计划', '明天计划', '下一步', '待办',
                '明日安排', '明天安排', '计划完成', '准备'
            ]
            
            # 周计划关键词
            weekly_plan_keywords = [
                '周计划', '本周', '周期计划', '周安排', '周目标',
                '本周计划', '这周', '周工作'
            ]
            
            # 工作相关内容特征
            work_keywords = ['完成', '开发', '测试', '修复', '问题', '功能', '任务', '会议']
            
            # 计算得分
            daily_report_score = sum(1 for keyword in daily_report_keywords if keyword in content_lower)
            daily_plan_score = sum(1 for keyword in daily_plan_keywords if keyword in content_lower)
            weekly_plan_score = sum(1 for keyword in weekly_plan_keywords if keyword in content_lower)
            work_score = sum(1 for keyword in work_keywords if keyword in content_lower)
            
            # 长内容工作特征加分
            if len(content) > 50 and work_score >= 2:
                daily_report_score += 1
                
            print(f"\n  关键词分析:")
            print(f"    日报得分: {daily_report_score}")
            print(f"    日计划得分: {daily_plan_score}")
            print(f"    周计划得分: {weekly_plan_score}")
            print(f"    工作词汇得分: {work_score}")
            
            # 找到匹配的关键词
            matched_report_keywords = [kw for kw in daily_report_keywords if kw in content_lower]
            matched_plan_keywords = [kw for kw in daily_plan_keywords if kw in content_lower]
            matched_work_keywords = [kw for kw in work_keywords if kw in content_lower]
            
            print(f"\n  匹配的关键词:")
            print(f"    日报关键词: {matched_report_keywords}")
            print(f"    日计划关键词: {matched_plan_keywords}")
            print(f"    工作关键词: {matched_work_keywords}")
            
            # 最终识别结果
            identified_type = github_client.identify_content_type(content)
            print(f"\n  识别结果: {identified_type}")
            
            # 分析为什么没有被识别为日计划
            if '明天' in content_lower or '明日' in content_lower:
                print(f"  ⚠️  内容包含'明天'或'明日'，但日计划得分为 {daily_plan_score}")
                print(f"      可能需要添加更多日计划关键词")
                
        except Exception as e:
            print(f"  ❌ 分析失败: {e}")

async def test_keyword_coverage():
    """测试关键词覆盖情况"""
    print("\n=== 测试关键词覆盖情况 ===")
    
    config = Config()
    github_client = GitHubClient(config.github)
    
    # 测试一些可能被遗漏的表达方式
    test_cases = [
        "明天整理需求清单和prd",
        "明日计划扩大",
        "下一步工作安排",
        "接下来要做的事情",
        "明天的任务",
        "后续计划",
        "下步计划"
    ]
    
    print("\n测试各种计划表达方式:")
    for i, test_content in enumerate(test_cases, 1):
        identified_type = github_client.identify_content_type(test_content)
        print(f"  {i}. '{test_content}' -> {identified_type}")

async def suggest_improvements():
    """建议改进方案"""
    print("\n=== 改进建议 ===")
    
    suggestions = [
        "1. 扩展日计划关键词列表，添加：",
        "   - '明天', '后续', '接下来', '下步', '下一步工作'",
        "   - '明天的', '明日的', '后续的', '接下来的'",
        "   - '任务安排', '工作安排', '计划安排'",
        "",
        "2. 优化识别逻辑：",
        "   - 考虑上下文，如果同时包含今日和明日内容，应该识别为包含计划",
        "   - 降低识别阈值，单个明确的计划关键词就应该被识别",
        "",
        "3. 增加模糊匹配：",
        "   - 使用正则表达式匹配'明天.*计划'、'下.*步'等模式",
        "   - 考虑同义词和变体形式"
    ]
    
    for suggestion in suggestions:
        print(suggestion)

async def main():
    """主函数"""
    print("开始分析日计划检测问题...\n")
    
    # 分析特定讨论
    await analyze_specific_discussions()
    
    # 测试关键词覆盖
    await test_keyword_coverage()
    
    # 提供改进建议
    await suggest_improvements()
    
    print("\n分析完成！")

if __name__ == "__main__":
    asyncio.run(main())