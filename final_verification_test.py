#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
最终验证测试：确认评论ID识别一致性问题已完全解决

验证要点：
1. extract_daily_content 和 _find_corresponding_daily_plan 使用一致的逻辑
2. 日计划分析回复到正确的对应评论ID
3. 日报分析使用正确的对应日计划内容
"""

import asyncio
import sys
import os

# 添加项目根目录到Python路径
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from src.utils.logger import setup_logging
from src.config import Config
from src.analyzers.daily_analyzer import DailyAnalyzer
from src.clients.github_client import GitHubClient
from src.clients.glm_client import GLMClient

async def main():
    """主测试函数"""
    # 初始化配置和日志
    config = Config()
    setup_logging(config.logging)
    
    import logging
    logger = logging.getLogger(__name__)
    logger.info("开始最终验证测试")
    
    try:
        # 初始化分析器
        analyzer = DailyAnalyzer(config)
        
        # 测试讨论#57
        discussion_number = 57
        logger.info(f"开始验证讨论 #{discussion_number}")
        
        # 1. 获取讨论数据
        discussions = await analyzer.github_client.get_daily_discussions()
        target_discussion = None
        for disc in discussions:
            if disc.number == discussion_number:
                target_discussion = disc
                break
        
        if not target_discussion:
            logger.error(f"未找到讨论 #{discussion_number}")
            return
      # 2. 提取内容
        logger.info("提取讨论内容...")
        content_data = await analyzer.github_client.extract_daily_content(target_discussion)
        daily_summary = content_data.get('daily_summary', '')
        daily_plan = content_data.get('daily_plan', '')
        logger.info(f"提取的日报长度: {len(daily_summary) if daily_summary else 0}")
        logger.info(f"提取的日计划长度: {len(daily_plan) if daily_plan else 0}")
        
        # 3. 查找对应的日计划
        if daily_summary:
            corresponding_plan, corresponding_plan_comment_id = await analyzer._find_corresponding_daily_plan(
                target_discussion, daily_summary
            )
            logger.info(f"对应日计划长度: {len(corresponding_plan) if corresponding_plan else 0}")
            logger.info(f"对应日计划评论ID: {corresponding_plan_comment_id}")
            
            # 4. 验证一致性
            if daily_plan and corresponding_plan:
                if daily_plan == corresponding_plan:
                    logger.info("✅ 提取的日计划与对应日计划内容一致")
                else:
                    logger.warning("⚠️ 提取的日计划与对应日计划内容不一致")
                    logger.info(f"提取的日计划前50字符: {daily_plan[:50]}...")
                    logger.info(f"对应日计划前50字符: {corresponding_plan[:50]}...")
        
        # 5. 查找评论ID
        daily_summary_comment_id = await analyzer._find_content_comment_id(
            discussion_number, 'daily_summary'
        )
        daily_plan_comment_id = await analyzer._find_content_comment_id(
            discussion_number, 'daily_plan'
        )
        
        logger.info(f"日报评论ID: {daily_summary_comment_id}")
        logger.info(f"日计划评论ID: {daily_plan_comment_id}")
        
        # 6. 验证评论ID一致性
        if corresponding_plan_comment_id and daily_plan_comment_id:
            if corresponding_plan_comment_id == daily_plan_comment_id:
                logger.info("✅ 对应日计划评论ID与查找到的日计划评论ID一致")
            else:
                logger.warning("⚠️ 对应日计划评论ID与查找到的日计划评论ID不一致")
                logger.info(f"对应日计划评论ID: {corresponding_plan_comment_id}")
                logger.info(f"查找到的日计划评论ID: {daily_plan_comment_id}")
        
        # 7. 运行完整分析验证
        logger.info("开始运行完整分析验证...")
        result = await analyzer.analyze_specific_discussion(discussion_number)
        
        if result.get('success'):
            analyses = result.get('analyses', [])
            for analysis in analyses:
                analysis_type = analysis.get('type')
                reply_to_comment_id = analysis.get('reply_to_comment_id')
                logger.info(f"{analysis_type} 回复到评论ID: {reply_to_comment_id}")
                
                # 验证回复ID的正确性
                if analysis_type == '日计划分析' and corresponding_plan_comment_id:
                    if reply_to_comment_id == corresponding_plan_comment_id:
                        logger.info("✅ 日计划分析回复到正确的对应评论ID")
                    else:
                        logger.error("❌ 日计划分析回复到错误的评论ID")
        
        logger.info("✅ 最终验证测试完成")
        
    except Exception as e:
        logger.error(f"验证测试失败: {e}", exc_info=True)

if __name__ == "__main__":
    asyncio.run(main())