#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
测试楼层内容类型识别和分析功能
验证系统是否能够：
1. 正确识别楼层内容类型（日报、日计划、周计划）
2. 根据楼层类型执行相应的分析
"""

import asyncio
import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.config import Config
from src.clients.github_client import GitHubClient
from src.clients.glm_client import GLMClient
from src.analyzers.daily_analyzer import DailyAnalyzer

async def test_content_type_identification():
    """
    测试内容类型识别功能
    """
    print("=== 测试内容类型识别功能 ===")
    
    try:
        # 初始化配置和客户端
        config = Config()
        github_client = GitHubClient(config.github)
        
        # 测试不同类型的内容
        test_contents = [
            {
                'content': '今日完成了用户登录功能的开发，遇到了数据库连接问题，已解决。明天计划继续开发注册功能。',
                'expected': 'daily_report'
            },
            {
                'content': '明日计划：1. 完成用户注册功能开发 2. 编写单元测试 3. 更新技术文档',
                'expected': 'daily_plan'
            },
            {
                'content': '本周计划：完成用户管理模块的所有功能，包括登录、注册、密码重置等。',
                'expected': 'weekly_plan'
            },
            {
                'content': '开会讨论了项目进度，完成了代码审查，修复了3个bug。',
                'expected': 'daily_report'
            },
            {
                'content': '下一步准备开始API接口的开发工作。',
                'expected': 'daily_plan'
            }
        ]
        
        print("\n--- 内容类型识别测试 ---")
        for i, test_case in enumerate(test_contents, 1):
            identified_type = github_client.identify_content_type(test_case['content'])
            status = "✅" if identified_type == test_case['expected'] else "❌"
            
            print(f"\n[{i}] {status} 测试用例")
            print(f"内容: {test_case['content'][:50]}...")
            print(f"预期类型: {test_case['expected']}")
            print(f"识别类型: {identified_type}")
            
        return True
        
    except Exception as e:
        print(f"❌ 内容类型识别测试失败: {e}")
        import traceback
        traceback.print_exc()
        return False

async def test_discussion_64_analysis():
    """
    测试Discussion #64的楼层类型分析
    """
    print("\n=== 测试Discussion #64楼层类型分析 ===")
    
    try:
        # 初始化分析器
        config = Config()
        analyzer = DailyAnalyzer(config)
        
        # 分析Discussion #64
        print("\n--- 分析Discussion #64 ---")
        result = await analyzer.analyze_specific_discussion(64)
        
        if result.get('success', False):
            print("✅ 分析成功完成")
            print(f"讨论标题: {result.get('discussion_title', 'N/A')}")
            print(f"评论已发布: {'是' if result.get('comment_posted', False) else '否'}")
            if result.get('comment_posted', False):
                print(f"评论ID: {result.get('comment_id', 'N/A')}")
        else:
            print(f"❌ 分析失败: {result.get('error', '未知错误')}")
            
        return result.get('success', False)
        
    except Exception as e:
        print(f"❌ Discussion #64分析测试失败: {e}")
        import traceback
        traceback.print_exc()
        return False

async def test_specific_content_analysis():
    """
    测试特定内容类型的分析功能
    """
    print("\n=== 测试特定内容类型分析功能 ===")
    
    try:
        # 初始化GLM客户端
        config = Config()
        glm_client = GLMClient(config.glm)
        
        # 测试日报分析
        print("\n--- 测试日报分析 ---")
        daily_summary = "今天完成了用户登录功能的开发，包括前端表单验证和后端API接口。遇到了JWT token过期的问题，通过调整过期时间解决了。还参加了团队会议，讨论了下周的开发计划。"
        daily_plan = "计划完成用户登录功能开发和基本的表单验证。"
        
        report_analysis = await glm_client.analyze_daily_report_content(daily_summary, daily_plan)
        print(f"日报分析结果长度: {len(report_analysis)} 字符")
        print(f"分析结果预览: {report_analysis[:200]}...")
        
        # 测试日计划分析
        print("\n--- 测试日计划分析 ---")
        daily_plan_content = "明日计划：1. 完成用户注册功能开发 2. 编写登录功能的单元测试 3. 更新API文档 4. 准备代码审查"
        weekly_plan = "本周目标：完成用户管理模块的核心功能，包括登录、注册、密码重置等功能的开发和测试。"
        
        plan_analysis = await glm_client.analyze_daily_plan_content(daily_plan_content, weekly_plan)
        print(f"日计划分析结果长度: {len(plan_analysis)} 字符")
        print(f"分析结果预览: {plan_analysis[:200]}...")
        
        return True
        
    except Exception as e:
        print(f"❌ 特定内容类型分析测试失败: {e}")
        import traceback
        traceback.print_exc()
        return False

async def main():
    """
    主测试函数
    """
    print("🚀 开始测试楼层内容类型识别和分析功能")
    print("=" * 60)
    
    # 执行所有测试
    test_results = []
    
    # 测试1: 内容类型识别
    result1 = await test_content_type_identification()
    test_results.append(('内容类型识别', result1))
    
    # 测试2: 特定内容分析
    result2 = await test_specific_content_analysis()
    test_results.append(('特定内容分析', result2))
    
    # 测试3: Discussion #64分析
    result3 = await test_discussion_64_analysis()
    test_results.append(('Discussion #64分析', result3))
    
    # 输出测试总结
    print("\n" + "=" * 60)
    print("📊 测试结果总结")
    print("=" * 60)
    
    passed_tests = 0
    for test_name, result in test_results:
        status = "✅ 通过" if result else "❌ 失败"
        print(f"{test_name}: {status}")
        if result:
            passed_tests += 1
    
    print(f"\n总计: {passed_tests}/{len(test_results)} 个测试通过")
    
    if passed_tests == len(test_results):
        print("🎉 所有测试通过！楼层内容类型识别和分析功能正常工作。")
    else:
        print("⚠️ 部分测试失败，请检查相关功能。")

if __name__ == "__main__":
    asyncio.run(main())
