#!/usr/bin/env python3
"""
调试讨论获取问题
"""

import asyncio
from datetime import date, timedelta
from src.config import Config
from src.clients.github_client import GitHubClient

async def debug_discussions():
    """调试讨论获取"""
    print("🔍 开始调试讨论获取问题")
    print("=" * 50)
    
    # 初始化配置
    config = Config()
    client = GitHubClient(config.github)
    
    # 显示配置信息
    print(f"📋 当前配置:")
    print(f"   组织: {config.github.organization}")
    print(f"   仓库: {config.github.repository}")
    print(f"   使用组织讨论: {config.github.use_org_discussions}")
    print(f"   讨论分类: {config.github.discussion_category}")
    print()
    
    # 测试GitHub连接
    try:
        await client.test_connection()
        print("✅ GitHub连接正常")
    except Exception as e:
        print(f"❌ GitHub连接失败: {e}")
        return
    
    print()
    
    # 检查最近3天的讨论
    print("📅 检查最近3天的讨论:")
    total_discussions = 0
    
    for i in range(3):
        target_date = date.today() - timedelta(days=i)
        try:
            discussions = await client.get_daily_discussions(target_date)
            print(f"   {target_date}: {len(discussions)} 个讨论")
            total_discussions += len(discussions)
            
            # 如果有讨论，显示详细信息
            if discussions:
                for disc in discussions[:3]:  # 只显示前3个
                    print(f"      #{disc.number}: {disc.title[:50]}...")
                    print(f"         作者: {disc.author}, 分类: {disc.category}")
                    
        except Exception as e:
            print(f"   {target_date}: 获取失败 - {e}")
    
    print()
    print(f"📊 总计: {total_discussions} 个讨论")
    
    # 如果没有讨论，尝试获取所有讨论来调试
    if total_discussions == 0:
        print("\n🔍 没有找到日结讨论，尝试获取所有讨论来调试...")
        try:
            if config.github.use_org_discussions:
                all_discussions = await client._get_org_discussions()
            else:
                all_discussions = await client._get_repo_discussions()
                
            print(f"📋 仓库中总共有 {len(all_discussions)} 个讨论")
            
            # 显示所有分类
            categories = set()
            for disc in all_discussions:
                categories.add(disc.category.name)
            
            print(f"📂 可用的讨论分类: {list(categories)}")
            
            # 显示最近的几个讨论
            print(f"\n📝 最近的讨论 (前5个):")
            recent_discussions = sorted(all_discussions, key=lambda x: x.updated_at, reverse=True)[:5]
            for disc in recent_discussions:
                print(f"   #{disc.number}: {disc.title[:50]}...")
                print(f"      分类: {disc.category.name}, 更新: {disc.updated_at.date()}")
                
        except Exception as e:
            print(f"❌ 获取所有讨论失败: {e}")
    
    print("\n" + "=" * 50)
    print("🎯 调试完成")

if __name__ == "__main__":
    asyncio.run(debug_discussions())