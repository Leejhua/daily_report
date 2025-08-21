#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
测试分离的分析方法
验证日报分析和日计划分析是否能正确分离
"""

import asyncio
import sys
import os

# 添加项目根目录到Python路径
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from src.config import Config
from src.clients.glm_client import GLMClient

async def test_separate_analysis_methods():
    """
    测试分离的分析方法
    """
    print("=== 测试分离的分析方法 ===")
    
    try:
        # 初始化配置和客户端
        config = Config()
        glm_client = GLMClient(config.glm)
        
        # 测试数据
        daily_summary = """今日工作总结：
1. 完成了用户登录功能的开发，包括前端表单验证和后端API接口
2. 修复了JWT token过期的问题，调整过期时间为24小时
3. 参加了团队会议，讨论了下周的开发计划
4. 开始编写单元测试，完成了登录接口的基本测试用例

遇到的问题：
- 数据库连接池配置需要优化
- 前端参数格式与后端不一致，需要协调"""
        
        daily_plan = """今日计划：
1. 完成用户登录接口开发
2. 编写接口文档
3. 进行基本的功能测试
4. 准备明天的代码审查"""
        
        weekly_plan = """本周目标：
- 完成用户管理模块（登录、注册、权限）
- 提升代码覆盖率到80%以上
- 优化数据库查询性能
- 完善项目文档"""
        
        print("\n--- 测试日报分析方法 ---")
        print(f"日报内容长度: {len(daily_summary)} 字符")
        print(f"日计划内容长度: {len(daily_plan)} 字符")
        
        # 测试日报分析
        daily_report_analysis = await glm_client.analyze_daily_report_content(
            daily_summary=daily_summary,
            daily_plan=daily_plan
        )
        
        print(f"\n📊 日报分析结果 (长度: {len(daily_report_analysis)} 字符):")
        print("-" * 60)
        print(daily_report_analysis)
        
        print("\n" + "=" * 80)
        print("--- 测试日计划分析方法 ---")
        print(f"日计划内容长度: {len(daily_plan)} 字符")
        print(f"周计划内容长度: {len(weekly_plan)} 字符")
        
        # 测试日计划分析
        daily_plan_analysis = await glm_client.analyze_daily_plan_content(
            daily_plan=daily_plan,
            weekly_plan=weekly_plan
        )
        
        print(f"\n📋 日计划分析结果 (长度: {len(daily_plan_analysis)} 字符):")
        print("-" * 60)
        print(daily_plan_analysis)
        
        print("\n" + "=" * 80)
        print("--- 验证分析内容分离 ---")
        
        # 验证分析内容是否正确分离
        report_has_plan_content = "日计划" in daily_report_analysis or "周计划" in daily_report_analysis
        plan_has_report_content = "日报" in daily_plan_analysis or "日结" in daily_plan_analysis
        
        print(f"\n✅ 分析方法测试结果:")
        print(f"- 日报分析方法: {'存在' if hasattr(glm_client, 'analyze_daily_report_content') else '不存在'}")
        print(f"- 日计划分析方法: {'存在' if hasattr(glm_client, 'analyze_daily_plan_content') else '不存在'}")
        
        print(f"\n📊 日报分析内容检查:")
        print(f"- 标题正确: {'✅' if daily_report_analysis.startswith('## 📊 日报分析') else '❌'}")
        print(f"- 内容独立: {'❌ 包含计划分析内容' if report_has_plan_content else '✅ 内容独立'}")
        
        print(f"\n📋 日计划分析内容检查:")
        print(f"- 标题正确: {'✅' if daily_plan_analysis.startswith('## 📋 日计划分析') else '❌'}")
        print(f"- 内容独立: {'❌ 包含日报分析内容' if plan_has_report_content else '✅ 内容独立'}")
        
        # 总结
        if (daily_report_analysis.startswith('## 📊 日报分析') and 
            daily_plan_analysis.startswith('## 📋 日计划分析') and 
            not report_has_plan_content and not plan_has_report_content):
            print("\n🎉 测试通过：日报分析和日计划分析已正确分离！")
            return True
        else:
            print("\n⚠️ 测试发现问题：分析内容可能仍有混合")
            return False
            
    except Exception as e:
        print(f"\n❌ 测试过程中出错: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    asyncio.run(test_separate_analysis_methods())
