#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
简化分析功能测试脚本
测试新的简化分析输出格式
"""

import asyncio
import sys
import os

# 添加项目根目录到Python路径
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from src.config import Config
from src.clients.github_client import GitHubClient
from src.clients.glm_client import GLMClient
from src.utils.logger import setup_logging
import logging

async def test_simple_analysis():
    """
    测试简化分析功能
    """
    print("\n" + "=" * 60)
    print("🧪 简化分析功能测试")
    print("=" * 60)
    
    # 初始化日志
    setup_logging()
    logger = logging.getLogger(__name__)
    
    try:
        # 加载配置
        config = Config()
        
        # 只初始化GLM客户端进行分析测试
        glm_client = GLMClient(config.glm)
        
        print("\n📋 测试数据:")
        
        # 模拟测试数据
        daily_summary = """
今天主要做了以下工作：
- 开发了用户登录接口，但遇到了一些问题
- 参加了项目会议
- 写了一些文档
        """.strip()
        
        daily_plan = """
明天计划：
- 完成登录接口开发
- 进行单元测试
- 优化数据库查询
        """.strip()
        
        weekly_plan = """
本周目标：
- 完成用户管理模块开发
- 完成所有接口的单元测试
- 编写技术文档
        """.strip()
        
        print(f"📝 日结内容: {daily_summary[:50]}...")
        print(f"📅 日计划内容: {daily_plan[:50]}...")
        print(f"📊 周期计划内容: {weekly_plan[:50]}...")
        
        print("\n🤖 开始简化分析...")
        
        # 生成简化分析报告
        analysis_report = await glm_client.generate_comprehensive_analysis(
            daily_summary=daily_summary,
            daily_plan=daily_plan,
            weekly_plan=weekly_plan
        )
        
        print("\n" + "=" * 60)
        print("📊 简化分析结果:")
        print("=" * 60)
        print(analysis_report)
        print("=" * 60)
        
        print(f"\n📏 分析报告长度: {len(analysis_report)} 字符")
        
        # 测试空内容情况
        print("\n🔍 测试空内容情况...")
        empty_analysis = await glm_client.generate_comprehensive_analysis(
            daily_summary="",
            daily_plan="",
            weekly_plan=""
        )
        
        print("\n📋 空内容分析结果:")
        print("-" * 40)
        print(empty_analysis)
        print("-" * 40)
        
        print("\n✅ 简化分析功能测试完成！")
        
    except Exception as e:
        logger.error(f"测试失败: {e}", exc_info=True)
        print(f"\n❌ 测试失败: {e}")
        return False
        
    return True

if __name__ == "__main__":
    success = asyncio.run(test_simple_analysis())
    sys.exit(0 if success else 1)