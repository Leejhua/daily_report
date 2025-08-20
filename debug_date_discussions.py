#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
调试特定日期的讨论获取问题
"""

import asyncio
import sys
from datetime import date
from src.config import Config
from src.clients.github_client import GitHubClient

async def debug_date_discussions():
    """调试2025-08-20的讨论获取"""
    print("🔍 调试2025-08-20讨论获取情况")
    print("=" * 50)
    
    config = Config()
    client = GitHubClient(config.github)
    
    target_date = date(2025, 8, 20)
    print(f"📅 目标日期: {target_date}")
    
    try:
        # 1. 获取所有讨论
        print("\n📥 获取所有讨论...")
        if config.github.use_org_discussions:
            all_discussions = await client._get_org_discussions()
        else:
            all_discussions = await client._get_repo_discussions()
        
        print(f"📊 总讨论数: {len(all_discussions)}")
        
        # 2. 过滤日结分类
        daily_category_discussions = []
        for discussion in all_discussions:
            if discussion.category.name == config.github.discussion_category:
                daily_category_discussions.append(discussion)
        
        print(f"📋 日结分类讨论数: {len(daily_category_discussions)}")
        
        # 3. 过滤目标日期
        target_date_discussions = []
        for discussion in daily_category_discussions:
            updated_date = discussion.updated_at.date()
            if updated_date == target_date:
                target_date_discussions.append(discussion)
                print(f"  ✅ #{discussion.number}: {discussion.title}")
                print(f"     📅 创建: {discussion.created_at.date()}, 更新: {updated_date}")
        
        print(f"\n🎯 目标日期讨论数: {len(target_date_discussions)}")
        
        # 4. 使用get_daily_discussions方法验证
        print("\n🔄 使用get_daily_discussions方法验证...")
        daily_discussions = await client.get_daily_discussions(target_date)
        print(f"📊 get_daily_discussions返回: {len(daily_discussions)}个讨论")
        
        for discussion in daily_discussions:
            print(f"  ✅ #{discussion.number}: {discussion.title}")
        
        # 5. 检查差异
        if len(target_date_discussions) != len(daily_discussions):
            print(f"\n⚠️ 发现差异!")
            print(f"   直接过滤: {len(target_date_discussions)}个")
            print(f"   方法返回: {len(daily_discussions)}个")
        else:
            print(f"\n✅ 数据一致: {len(daily_discussions)}个讨论")
            
    except Exception as e:
        print(f"❌ 调试过程中出错: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(debug_date_discussions())
