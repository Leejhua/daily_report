#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
测试Discussion #64的楼层结构分析
验证系统是否正确识别：
- 一楼：周计划
- 二楼：日计划  
- 三楼：日报
"""

import asyncio
import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.config import Config
from src.clients.github_client import GitHubClient

async def test_discussion_structure():
    """测试Discussion #64的楼层结构分析"""
    print("=== Discussion #64 楼层结构分析测试 ===")
    
    try:
        # 初始化配置和客户端
        config = Config()
        github_client = GitHubClient(config.github)
        
        # 获取Discussion #64
        discussions = await github_client.get_daily_discussions()
        discussion_64 = None
        
        for discussion in discussions:
            if discussion.number == 64:
                discussion_64 = discussion
                break
        
        if not discussion_64:
            print("❌ 未找到Discussion #64")
            return
        
        print(f"✅ 找到Discussion #64: {discussion_64.title}")
        print(f"📅 创建时间: {discussion_64.created_at}")
        print(f"💬 评论数量: {discussion_64.comments_count}")
        print()
        
        # 分析一楼内容（周计划）
        print("=== 一楼内容分析（应为周计划） ===")
        first_floor = discussion_64.body
        print(f"内容长度: {len(first_floor)} 字符")
        print(f"内容预览: {first_floor[:200]}..." if len(first_floor) > 200 else f"完整内容: {first_floor}")
        print()
        
        # 获取评论（二楼、三楼等）
        comments = await github_client.get_discussion_comments(64)
        print(f"=== 评论分析（共{len(comments)}条评论） ===")
        
        if len(comments) >= 1:
            print("--- 二楼内容（应为日计划） ---")
            second_floor = comments[0]
            print(f"作者: {second_floor.author}")
            print(f"时间: {second_floor.created_at}")
            print(f"内容长度: {len(second_floor.body)} 字符")
            print(f"内容预览: {second_floor.body[:200]}..." if len(second_floor.body) > 200 else f"完整内容: {second_floor.body}")
            print()
        
        if len(comments) >= 2:
            print("--- 三楼内容（应为日报） ---")
            third_floor = comments[1]
            print(f"作者: {third_floor.author}")
            print(f"时间: {third_floor.created_at}")
            print(f"内容长度: {len(third_floor.body)} 字符")
            print(f"内容预览: {third_floor.body[:200]}..." if len(third_floor.body) > 200 else f"完整内容: {third_floor.body}")
            print()
        
        # 使用系统的extract_daily_content方法分析
        print("=== 系统自动分析结果 ===")
        extracted_content = await github_client.extract_daily_content(discussion_64)
        
        print(f"周计划长度: {len(extracted_content['weekly_plan'])} 字符")
        print(f"日计划长度: {len(extracted_content['daily_plan'])} 字符")
        print(f"日报长度: {len(extracted_content['daily_summary'])} 字符")
        print()
        
        # 验证分析结果
        print("=== 分析结果验证 ===")
        
        # 检查周计划是否来自一楼
        if extracted_content['weekly_plan'] == first_floor:
            print("✅ 周计划正确识别为一楼内容")
        else:
            print("❌ 周计划识别错误")
        
        # 检查日计划和日报是否来自评论
        daily_plan_found = False
        daily_summary_found = False
        
        for i, comment in enumerate(comments):
            floor_number = i + 2  # 评论从二楼开始
            
            if extracted_content['daily_plan'] == comment.body:
                print(f"✅ 日计划正确识别为{floor_number}楼内容")
                daily_plan_found = True
            
            if extracted_content['daily_summary'] == comment.body:
                print(f"✅ 日报正确识别为{floor_number}楼内容")
                daily_summary_found = True
        
        if not daily_plan_found and extracted_content['daily_plan']:
            print("❌ 日计划识别错误或来源不明")
        elif not extracted_content['daily_plan']:
            print("⚠️ 未识别到日计划内容")
        
        if not daily_summary_found and extracted_content['daily_summary']:
            print("❌ 日报识别错误或来源不明")
        elif not extracted_content['daily_summary']:
            print("⚠️ 未识别到日报内容")
        
        print()
        print("=== 测试完成 ===")
        
    except Exception as e:
        print(f"❌ 测试过程中出现错误: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(test_discussion_structure())