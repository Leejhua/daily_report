#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
测试不同楼层类型的分析效果
验证系统是否能够根据楼层类型执行不同的分析：
- 日报楼层：分析日报与日计划的偏离
- 日计划楼层：分析日计划与周计划的一致性
"""

import asyncio
import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.config import Config
from src.clients.github_client import GitHubClient
from src.clients.glm_client import GLMClient

async def test_daily_report_analysis():
    """
    测试日报分析功能
    """
    print("=== 测试日报分析功能 ===")
    
    try:
        config = Config()
        glm_client = GLMClient(config.glm)
        
        # 模拟日报内容
        daily_summary = """
今日工作总结：
1. 完成了用户登录接口的开发，包括参数验证和错误处理
2. 修复了JWT token过期的bug，调整过期时间为24小时
3. 参加了产品需求评审会议，讨论了用户权限管理功能
4. 开始编写单元测试，完成了登录接口的基本测试用例

遇到的问题：
- 数据库连接池配置需要优化，偶尔出现连接超时
- 前端传递的参数格式与后端期望不一致，需要协调
"""
        
        # 模拟日计划内容
        daily_plan = """
今日计划：
1. 完成用户登录接口开发
2. 编写接口文档
3. 进行基本的功能测试
4. 准备明天的代码审查
"""
        
        print("\n--- 执行日报分析 ---")
        print(f"日报内容长度: {len(daily_summary)} 字符")
        print(f"日计划内容长度: {len(daily_plan)} 字符")
        
        analysis_result = await glm_client.analyze_daily_report_content(daily_summary, daily_plan)
        
        print(f"\n📋 日报分析结果 (长度: {len(analysis_result)} 字符):")
        print("-" * 50)
        print(analysis_result)
        
        return True
        
    except Exception as e:
        print(f"❌ 日报分析测试失败: {e}")
        import traceback
        traceback.print_exc()
        return False

async def test_daily_plan_analysis():
    """
    测试日计划分析功能
    """
    print("\n=== 测试日计划分析功能 ===")
    
    try:
        config = Config()
        glm_client = GLMClient(config.glm)
        
        # 模拟日计划内容
        daily_plan = """
明日计划：
1. 完成用户注册功能的后端接口开发
2. 实现邮箱验证功能
3. 编写用户注册的单元测试
4. 更新API文档，添加注册接口说明
5. 与前端同事对接注册页面的数据格式

重点关注：
- 确保邮箱验证的安全性
- 注册流程的用户体验优化
"""
        
        # 模拟周计划内容
        weekly_plan = """
本周目标：
完成用户管理模块的核心功能开发，包括：
1. 用户登录功能（已完成）
2. 用户注册功能
3. 密码重置功能
4. 用户信息管理功能
5. 权限验证机制

本周重点：
- 确保所有接口的安全性和稳定性
- 完善错误处理和参数验证
- 编写完整的单元测试
- 更新技术文档
"""
        
        print("\n--- 执行日计划分析 ---")
        print(f"日计划内容长度: {len(daily_plan)} 字符")
        print(f"周计划内容长度: {len(weekly_plan)} 字符")
        
        analysis_result = await glm_client.analyze_daily_plan_content(daily_plan, weekly_plan)
        
        print(f"\n📋 日计划分析结果 (长度: {len(analysis_result)} 字符):")
        print("-" * 50)
        print(analysis_result)
        
        return True
        
    except Exception as e:
        print(f"❌ 日计划分析测试失败: {e}")
        import traceback
        traceback.print_exc()
        return False

async def test_content_type_detection():
    """
    测试内容类型检测的准确性
    """
    print("\n=== 测试内容类型检测准确性 ===")
    
    try:
        config = Config()
        github_client = GitHubClient(config.github)
        
        test_cases = [
            {
                'name': '典型日报内容',
                'content': '今日完成了API开发，遇到了数据库连接问题，已解决。测试了登录功能，发现了一个小bug。',
                'expected': 'daily_report'
            },
            {
                'name': '典型日计划内容',
                'content': '明日计划：1. 完成用户注册功能 2. 编写单元测试 3. 更新文档 4. 准备代码审查',
                'expected': 'daily_plan'
            },
            {
                'name': '典型周计划内容',
                'content': '本周计划：完成用户管理模块的所有功能，包括登录、注册、权限管理等核心功能。',
                'expected': 'weekly_plan'
            },
            {
                'name': '工作总结类日报',
                'content': '工作总结：开发了三个接口，修复了两个bug，参加了需求评审会议，完成了代码审查。',
                'expected': 'daily_report'
            },
            {
                'name': '待办事项类日计划',
                'content': '待办事项：下一步需要完成数据库设计，准备开始前端页面开发，安排测试计划。',
                'expected': 'daily_plan'
            }
        ]
        
        print("\n--- 内容类型检测结果 ---")
        correct_count = 0
        
        for i, test_case in enumerate(test_cases, 1):
            detected_type = github_client.identify_content_type(test_case['content'])
            is_correct = detected_type == test_case['expected']
            status = "✅" if is_correct else "❌"
            
            if is_correct:
                correct_count += 1
                
            print(f"\n[{i}] {status} {test_case['name']}")
            print(f"内容: {test_case['content'][:60]}...")
            print(f"预期: {test_case['expected']} | 检测: {detected_type}")
        
        accuracy = (correct_count / len(test_cases)) * 100
        print(f"\n📊 检测准确率: {correct_count}/{len(test_cases)} ({accuracy:.1f}%)")
        
        return accuracy >= 80  # 80%以上准确率视为通过
        
    except Exception as e:
        print(f"❌ 内容类型检测测试失败: {e}")
        import traceback
        traceback.print_exc()
        return False

async def main():
    """
    主测试函数
    """
    print("🚀 开始测试不同楼层类型的分析效果")
    print("=" * 60)
    
    # 执行所有测试
    test_results = []
    
    # 测试1: 内容类型检测
    result1 = await test_content_type_detection()
    test_results.append(('内容类型检测', result1))
    
    # 测试2: 日报分析
    result2 = await test_daily_report_analysis()
    test_results.append(('日报分析功能', result2))
    
    # 测试3: 日计划分析
    result3 = await test_daily_plan_analysis()
    test_results.append(('日计划分析功能', result3))
    
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
        print("\n🎉 所有测试通过！")
        print("✅ 系统现在能够正确识别楼层类型并执行相应的分析：")
        print("   - 日报楼层：分析日报与日计划的偏离")
        print("   - 日计划楼层：分析日计划与周计划的一致性")
        print("   - 其他情况：使用综合分析（兼容旧逻辑）")
    else:
        print("\n⚠️ 部分测试失败，请检查相关功能。")

if __name__ == "__main__":
    asyncio.run(main())
