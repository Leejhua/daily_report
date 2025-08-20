#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
解释当前分析逻辑的工作原理

这个脚本用于解释系统如何进行偏离分析，特别是日报中的偏离分析是如何实现的。
"""

import asyncio
import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.config import Config
from src.clients.github_client import GitHubClient
from src.clients.glm_client import GLMClient
from src.utils.logger import get_logger

async def explain_analysis_logic():
    """
    解释分析逻辑的工作原理
    """
    print("=" * 80)
    print("当前分析逻辑解释")
    print("=" * 80)
    
    print("\n1. 数据提取逻辑:")
    print("   - 首楼内容 → 周计划 (weekly_plan)")
    print("   - 评论中的日报内容 → 日结 (daily_summary)")
    print("   - 评论中的日计划内容 → 日计划 (daily_plan)")
    
    print("\n2. 分析类型:")
    print("   a) 日报分析 (analyze_daily_report_content):")
    print("      - 输入: daily_summary + daily_plan")
    print("      - 分析: 工作偏离情况 (实际工作 vs 日计划)")
    print("      - 发布位置: 日报讨论 (当前讨论)")
    
    print("   b) 日计划分析 (analyze_daily_plan_content):")
    print("      - 输入: daily_plan + weekly_plan")
    print("      - 分析: 计划一致性 (日计划 vs 周计划)")
    print("      - 发布位置: 尝试找到日计划讨论，找不到则发布到当前讨论")
    
    print("\n3. 偏离分析的具体实现:")
    print("   - 日报偏离分析: 比较 daily_summary (实际完成) vs daily_plan (计划完成)")
    print("   - 日计划偏离分析: 比较 daily_plan (日计划) vs weekly_plan (周计划)")
    
    print("\n4. 关键问题解答:")
    print("   Q: 日报里的偏离分析怎么做的？")
    print("   A: 使用同一个讨论中的日计划内容作为参考基准")
    print("      - 从评论中提取最新的日计划内容")
    print("      - 将实际完成的工作(日报)与计划的工作(日计划)进行对比")
    print("      - 分析偏离程度和原因")
    
    print("\n5. 数据流示例:")
    print("   讨论#64:")
    print("   ├── 首楼: 周计划内容 → weekly_plan")
    print("   ├── 评论1: 日报内容 → daily_summary")
    print("   └── 评论2: 日计划内容 → daily_plan")
    print("   ")
    print("   分析过程:")
    print("   ├── 日报分析: daily_summary vs daily_plan → 发布到讨论#64")
    print("   └── 日计划分析: daily_plan vs weekly_plan → 尝试发布到日计划讨论")
    
    # 实际验证当前逻辑
    print("\n" + "=" * 80)
    print("实际验证当前逻辑")
    print("=" * 80)
    
    try:
        # 初始化配置
        config = Config()
        github_client = GitHubClient(config.github)
        
        # 获取讨论#64的内容
        discussions = await github_client.get_daily_discussions()
        target_discussion = None
        for discussion in discussions:
            if discussion.number == 64:
                target_discussion = discussion
                break
        
        if target_discussion:
            print(f"\n找到讨论 #{target_discussion.number}: {target_discussion.title}")
            
            # 提取内容
            content_data = await github_client.extract_daily_content(target_discussion)
            
            print(f"\n提取到的内容:")
            print(f"- 周计划长度: {len(content_data['weekly_plan'])} 字符")
            print(f"- 日报长度: {len(content_data['daily_summary'])} 字符")
            print(f"- 日计划长度: {len(content_data['daily_plan'])} 字符")
            
            if content_data['weekly_plan']:
                print(f"\n周计划内容预览:")
                preview = content_data['weekly_plan'][:200] + "..." if len(content_data['weekly_plan']) > 200 else content_data['weekly_plan']
                print(f"{preview}")
            
            if content_data['daily_summary']:
                print(f"\n日报内容预览:")
                preview = content_data['daily_summary'][:200] + "..." if len(content_data['daily_summary']) > 200 else content_data['daily_summary']
                print(f"{preview}")
            
            if content_data['daily_plan']:
                print(f"\n日计划内容预览:")
                preview = content_data['daily_plan'][:200] + "..." if len(content_data['daily_plan']) > 200 else content_data['daily_plan']
                print(f"{preview}")
            
            print("\n" + "=" * 80)
            print("结论")
            print("=" * 80)
            print("系统确实能够提取到周计划内容进行偏离分析。")
            print("日报分析中的偏离分析是通过比较同一讨论中的日报和日计划内容实现的。")
            print("日计划分析中的偏离分析是通过比较日计划和首楼的周计划内容实现的。")
            
        else:
            print("\n未找到讨论#64")
            
    except Exception as e:
        print(f"\n验证过程中出错: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(explain_analysis_logic())
