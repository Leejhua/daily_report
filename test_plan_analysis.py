#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
测试日计划分析功能
验证系统是否能正确识别和分析日计划内容
"""

import asyncio
import sys
import os
from datetime import date

# 添加项目根目录到路径
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from src.config import Config
from src.clients.github_client import GitHubClient
from src.clients.glm_client import GLMClient
from src.analyzers.daily_analyzer import DailyAnalyzer

async def test_content_type_identification():
    """测试内容类型识别功能"""
    print("=== 测试内容类型识别 ===")
    
    config = Config()
    github_client = GitHubClient(config.github)
    
    # 测试不同类型的内容
    test_contents = [
        {
            "content": "今日完成了用户登录功能的开发，修复了两个bug，测试通过。遇到了数据库连接问题，已解决。",
            "expected": "daily_report"
        },
        {
            "content": "明日计划：1. 完成用户注册功能 2. 进行单元测试 3. 准备代码review",
            "expected": "daily_plan"
        },
        {
            "content": "本周计划：完成用户管理模块的开发，包括登录、注册、权限管理等功能",
            "expected": "weekly_plan"
        },
        {
            "content": "这是一条普通的评论，没有特定的工作内容",
            "expected": "unknown"
        }
    ]
    
    for i, test_case in enumerate(test_contents, 1):
        content = test_case["content"]
        expected = test_case["expected"]
        
        identified_type = github_client.identify_content_type(content)
        
        print(f"\n测试 {i}:")
        print(f"内容: {content}")
        print(f"预期类型: {expected}")
        print(f"识别类型: {identified_type}")
        print(f"结果: {'✅ 正确' if identified_type == expected else '❌ 错误'}")

async def test_plan_analysis():
    """测试日计划分析功能"""
    print("\n=== 测试日计划分析功能 ===")
    
    config = Config()
    glm_client = GLMClient(config.glm)
    
    # 测试日计划内容
    daily_plan = """明日计划：
1. 完成用户注册API的开发
2. 编写单元测试用例
3. 进行代码review
4. 更新项目文档
5. 参加团队会议讨论下周安排"""
    
    weekly_plan = """本周目标：
- 完成用户管理模块（登录、注册、权限）
- 提升代码覆盖率到80%以上
- 优化数据库查询性能
- 完善项目文档"""
    
    print(f"\n日计划内容:\n{daily_plan}")
    print(f"\n周计划内容:\n{weekly_plan}")
    
    try:
        analysis_result = await glm_client.analyze_daily_plan_content(
            daily_plan=daily_plan,
            weekly_plan=weekly_plan
        )
        
        print(f"\n分析结果:\n{analysis_result}")
        
        if analysis_result and not analysis_result.startswith("## ❌"):
            print("\n✅ 日计划分析功能正常")
        else:
            print("\n❌ 日计划分析功能异常")
            
    except Exception as e:
        print(f"\n❌ 分析过程出错: {e}")

async def test_recent_discussions():
    """测试最近讨论中的日计划识别"""
    print("\n=== 测试最近讨论中的日计划识别 ===")
    
    config = Config()
    github_client = GitHubClient(config.github)
    
    try:
        # 获取最近的讨论
        discussions = await github_client.get_daily_discussions(date.today())
        
        print(f"\n找到 {len(discussions)} 个今日讨论")
        
        plan_discussions = []
        
        for discussion in discussions[:5]:  # 只检查前5个
            print(f"\n检查讨论 #{discussion.number}: {discussion.title}")
            
            # 获取评论
            comments = await github_client.get_discussion_comments(discussion.number)
            
            if comments:
                # 检查最新评论的类型
                comments.sort(key=lambda x: x.updated_at, reverse=True)
                latest_comment = comments[0]
                content_type = github_client.identify_content_type(latest_comment.body)
                
                print(f"  最新评论类型: {content_type}")
                print(f"  评论内容预览: {latest_comment.body[:100]}...")
                
                if content_type == 'daily_plan':
                    plan_discussions.append({
                        'discussion': discussion,
                        'comment': latest_comment
                    })
                    print(f"  ✅ 发现日计划内容")
            else:
                print(f"  无评论")
        
        print(f"\n总结: 发现 {len(plan_discussions)} 个包含日计划的讨论")
        
        if plan_discussions:
            print("\n日计划讨论列表:")
            for item in plan_discussions:
                discussion = item['discussion']
                print(f"  - #{discussion.number}: {discussion.title}")
        
    except Exception as e:
        print(f"\n❌ 获取讨论失败: {e}")

async def main():
    """主函数"""
    print("开始测试日计划分析功能...\n")
    
    # 测试内容类型识别
    await test_content_type_identification()
    
    # 测试日计划分析
    await test_plan_analysis()
    
    # 测试实际讨论中的日计划识别
    await test_recent_discussions()
    
    print("\n测试完成！")

if __name__ == "__main__":
    asyncio.run(main())
