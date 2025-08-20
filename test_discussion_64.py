#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
测试#64讨论的分析功能
"""

import asyncio
import sys
import os
from datetime import datetime

# 添加项目根目录到Python路径
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from src.config import Config
from src.clients.github_client import GitHubClient
from src.clients.glm_client import GLMClient
from src.analyzers.daily_analyzer import DailyAnalyzer
from src.utils.logger import setup_logging
import logging

async def test_discussion_64():
    """测试#64讨论"""
    setup_logging()
    logger = logging.getLogger("test_discussion_64")
    
    print("\n" + "="*60)
    print("🧪 测试#64讨论分析功能")
    print("="*60)
    
    try:
        # 加载配置
        config = Config()
        logger.info("配置加载成功")
        
        # 初始化分析器
        analyzer = DailyAnalyzer(config)
        github_client = analyzer.github_client
        glm_client = analyzer.glm_client
        
        print("\n✅ 客户端初始化成功")
        
        # 获取#64讨论
        print("\n📋 获取#64讨论...")
        
        # 获取所有讨论并找到#64
        if config.github.use_org_discussions:
            all_discussions = await github_client._get_org_discussions()
        else:
            all_discussions = await github_client._get_repo_discussions()
        
        discussion = None
        for disc in all_discussions:
            if disc.number == 64:
                discussion = disc
                break
        
        if not discussion:
            print("❌ 未找到#64讨论")
            print(f"   可用讨论编号: {[d.number for d in all_discussions[:10]]}...")
            return
        
        print(f"✅ 找到讨论: {discussion.title}")
        print(f"   📅 创建时间: {discussion.created_at}")
        print(f"   📅 更新时间: {discussion.updated_at}")
        print(f"   💬 评论数: {discussion.comments_count}")
        print(f"   📂 分类: {discussion.category}")
        
        # 提取内容
        print("\n📝 提取讨论内容...")
        content_data = await github_client.extract_daily_content(discussion)
        
        print(f"\n📊 内容提取结果:")
        print(f"   - 周期计划: {len(content_data.get('weekly_plan', ''))} 字符")
        print(f"   - 日报: {len(content_data.get('daily_summary', ''))} 字符")
        print(f"   - 日计划: {len(content_data.get('daily_plan', ''))} 字符")
        
        # 显示内容预览
        if content_data.get('weekly_plan'):
            preview = content_data['weekly_plan'][:200] + "..." if len(content_data['weekly_plan']) > 200 else content_data['weekly_plan']
            print(f"\n📋 周期计划预览:\n{preview}")
        
        if content_data.get('daily_summary'):
            preview = content_data['daily_summary'][:200] + "..." if len(content_data['daily_summary']) > 200 else content_data['daily_summary']
            print(f"\n🗒️ 日报预览:\n{preview}")
        
        if content_data.get('daily_plan'):
            preview = content_data['daily_plan'][:200] + "..." if len(content_data['daily_plan']) > 200 else content_data['daily_plan']
            print(f"\n📅 日计划预览:\n{preview}")
        
        # 进行分析
        if content_data.get('daily_summary') or content_data.get('daily_plan'):
            print("\n🤖 开始AI分析...")
            
            analysis_result = await analyzer.analyze_specific_discussion(discussion.number)
            
            print(f"\n📊 分析结果:")
            if analysis_result.get('success'):
                print(f"   - 分析状态: 成功")
                print(f"   - 讨论编号: {analysis_result.get('discussion_number', 'N/A')}")
                print(f"   - 讨论标题: {analysis_result.get('discussion_title', 'N/A')}")
                print(f"   - 评论发布: {'成功' if analysis_result.get('comment_posted') else '失败'}")
                print(f"   - 分析报告长度: {analysis_result.get('analysis_length', 0)} 字符")
                
                if analysis_result.get('error'):
                    print(f"   - 警告: {analysis_result.get('error')}")
            else:
                print(f"   - 分析状态: 失败")
                print(f"   - 错误信息: {analysis_result.get('error', 'Unknown error')}")
            
            # 评论功能已在分析过程中测试
            print("\n💬 评论功能测试结果:")
            if analysis_result.get('comment_posted'):
                print("✅ 评论发布成功 (已在分析过程中完成)")
            else:
                print("❌ 评论发布失败或未尝试发布")
        
        else:
            print("\n⚠️ 没有足够的内容进行分析")
        
        print("\n" + "="*60)
        print("🎉 #64讨论测试完成")
        print("="*60)
        
    except Exception as e:
        logger.error(f"测试过程中出错: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(test_discussion_64())