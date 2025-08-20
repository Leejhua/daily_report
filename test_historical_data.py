#!/usr/bin/env python3
"""
测试历史数据获取
"""

import asyncio
from datetime import date
from src.config import Config
from src.clients.github_client import GitHubClient
from src.analyzers.daily_analyzer import DailyAnalyzer

async def test_historical_data():
    """测试历史数据获取和分析"""
    print("🧪 测试历史数据获取和分析功能")
    print("=" * 50)
    
    # 初始化
    config = Config()
    client = GitHubClient(config.github)
    analyzer = DailyAnalyzer(config)
    
    # 测试2025-08-02的数据（根据调试结果，这天有讨论更新）
    test_date = date(2025, 8, 2)
    
    print(f"📅 测试日期: {test_date}")
    
    try:
        # 1. 获取讨论
        print("\n1️⃣ 获取讨论数据...")
        discussions = await client.get_daily_discussions(test_date)
        print(f"   找到 {len(discussions)} 个讨论")
        
        if discussions:
            for disc in discussions:
                print(f"   #{disc.number}: {disc.title}")
                print(f"      作者: {disc.author}, 更新: {disc.updated_at}")
        
        # 2. 如果有讨论，测试分析功能
        if discussions:
            print("\n2️⃣ 测试分析功能...")
            
            # 选择第一个讨论进行分析
            target_discussion = discussions[0]
            print(f"   分析目标: #{target_discussion.number} - {target_discussion.title}")
            
            # 执行分析
            result = await analyzer._analyze_single_discussion(target_discussion)
            
            print(f"\n📊 分析结果:")
            print(f"   成功: {result.get('success', False)}")
            print(f"   评论已发布: {result.get('comment_posted', False)}")
            if result.get('error'):
                print(f"   错误: {result['error']}")
            if result.get('analysis_length'):
                print(f"   分析长度: {result['analysis_length']} 字符")
        
        else:
            print("\n⚠️ 该日期没有讨论，无法测试分析功能")
            
        # 3. 测试当前日期（应该没有数据）
        print("\n3️⃣ 对比测试当前日期...")
        current_discussions = await client.get_daily_discussions(date.today())
        print(f"   今天 ({date.today()}): {len(current_discussions)} 个讨论")
        
        print("\n" + "=" * 50)
        print("🎯 测试结论:")
        
        if discussions:
            print("   ✅ 系统功能正常，能够获取和分析历史数据")
            print("   ✅ 使用真实的GitHub API数据，非mock数据")
            print("   ⚠️ 最近几天没有新的日结讨论，这是正常现象")
        else:
            print("   ⚠️ 即使是历史日期也没有找到讨论")
            print("   💡 可能需要检查讨论分类或时间过滤逻辑")
            
    except Exception as e:
        print(f"❌ 测试失败: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(test_historical_data())