#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from src.config import Config
from src.analyzers.daily_analyzer import DailyAnalyzer

async def run_plan_analysis():
    """执行讨论#64的日计划分析"""
    print("🔍 开始执行讨论#64的日计划分析...")
    
    try:
        # 初始化配置和分析器
        config = Config()
        analyzer = DailyAnalyzer(config)
        
        # 获取讨论数据
        discussions = await analyzer.github_client.get_daily_discussions()
        discussion_data = None
        for disc in discussions:
            if disc.number == 64:
                discussion_data = disc
                break
                
        if not discussion_data:
            print("❌ 无法获取讨论#64的数据")
            return
            
        print(f"📋 讨论标题: {discussion_data.title}")
        
        # 提取日计划内容
        daily_content = await analyzer.github_client.extract_daily_content(discussion_data)
        print(f"📋 提取的内容: {daily_content}")
        
        if 'daily_plan' not in daily_content or not daily_content['daily_plan']:
            print("❌ 未找到日计划内容")
            return
            
        print("✅ 找到日计划内容，开始分析...")
        
        # 查找日计划评论ID
        plan_comment_id = await analyzer._find_content_comment_id(discussion_data.number, 'daily_plan')
        if not plan_comment_id:
            print("❌ 无法找到日计划评论ID")
            return
            
        print(f"📋 日计划评论ID: {plan_comment_id}")
        
        # 检查是否已有回复
        has_reply = await analyzer.github_client.check_already_replied(64, plan_comment_id, 'daily_plan')
        print(f"📋 是否已有回复: {has_reply}")
        
        if has_reply:
            print("✅ 日计划分析已存在回复")
            return
            
        # 执行日计划分析
        analysis_result = await analyzer.glm_client.analyze_daily_plan_content(
            daily_plan=daily_content['daily_plan'],
            weekly_plan=daily_content.get('weekly_plan', '')
        )
        print(f"📋 分析结果: {analysis_result[:200]}...")
        
        # 发布回复
        reply_result = await analyzer.github_client.post_analysis_comment(
            discussion_number=64,
            analysis_content=analysis_result,
            reply_to_comment_id=plan_comment_id,
            content_type='daily_plan'
        )
        
        if reply_result:
            print("✅ 日计划分析回复发布成功")
        else:
            print("❌ 日计划分析回复发布失败")
        
    except Exception as e:
        print(f"❌ 执行失败: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    import asyncio
    asyncio.run(run_plan_analysis())