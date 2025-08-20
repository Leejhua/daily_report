#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
测试GitHub API分页功能
验证是否能正确获取所有讨论数据
"""

import asyncio
import sys
import os
from datetime import datetime, timedelta

# 添加项目根目录到Python路径
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from src.clients.github_client import GitHubClient
from src.config import Config

async def test_pagination():
    """测试分页功能"""
    print("🔍 测试GitHub API分页功能")
    print("=" * 50)
    
    # 初始化配置和客户端
    config = Config()
    github_client = GitHubClient(config.github)
    
    print(f"📋 配置信息:")
    print(f"   组织: {config.github.organization}")
    print(f"   仓库: {config.github.repository}")
    print(f"   使用组织讨论: {config.github.use_org_discussions}")
    print(f"   目标分类: {config.github.discussion_category}")
    print(f"   Token: {'已配置' if config.github.token else '未配置'}")
    print()
    
    try:
        # 测试连接
        if not await github_client.test_connection():
            print("❌ GitHub连接失败")
            return
        
        print("✅ GitHub连接成功")
        print()
        
        # 获取所有讨论（使用修复后的分页功能）
        print("📊 获取所有讨论（使用分页）...")
        if config.github.use_org_discussions:
            all_discussions = await github_client._get_org_discussions()
        else:
            all_discussions = await github_client._get_repo_discussions()
        
        print(f"📈 总讨论数: {len(all_discussions)}")
        print()
        
        # 按分类统计
        category_stats = {}
        for discussion in all_discussions:
            category = discussion.category.name if hasattr(discussion.category, 'name') else str(discussion.category)
            category_stats[category] = category_stats.get(category, 0) + 1
        
        print("📊 按分类统计:")
        for category, count in sorted(category_stats.items()):
            print(f"   {category}: {count} 个")
        print()
        
        # 重点关注目标分类
        target_category = config.github.discussion_category
        target_discussions = [d for d in all_discussions 
                            if (hasattr(d.category, 'name') and d.category.name == target_category) or 
                               str(d.category) == target_category]
        
        print(f"🎯 目标分类 '{target_category}' 的讨论: {len(target_discussions)} 个")
        
        if target_discussions:
            print("📋 目标分类讨论详情:")
            for discussion in target_discussions:
                updated_at = discussion.updated_at
                if hasattr(updated_at, 'strftime'):
                    updated_str = updated_at.strftime('%Y-%m-%d %H:%M:%S')
                else:
                    updated_str = str(updated_at)
                print(f"   #{discussion.number}: {discussion.title[:50]}... (更新: {updated_str})")
        print()
        
        # 检查最近更新
        now = datetime.now()
        recent_days = 7  # 检查最近7天
        recent_cutoff = now - timedelta(days=recent_days)
        
        recent_target_discussions = []
        for discussion in target_discussions:
            updated_at = discussion.updated_at
            if hasattr(updated_at, 'date'):
                updated_date = updated_at.date()
            else:
                # 尝试解析字符串日期
                try:
                    if isinstance(updated_at, str):
                        updated_datetime = datetime.fromisoformat(updated_at.replace('Z', '+00:00'))
                        updated_date = updated_datetime.date()
                    else:
                        continue
                except:
                    continue
            
            if updated_date >= recent_cutoff.date():
                recent_target_discussions.append(discussion)
        
        print(f"📅 最近{recent_days}天更新的目标讨论: {len(recent_target_discussions)} 个")
        
        if recent_target_discussions:
            print("📋 最近更新的讨论:")
            for discussion in recent_target_discussions:
                updated_at = discussion.updated_at
                if hasattr(updated_at, 'strftime'):
                    updated_str = updated_at.strftime('%Y-%m-%d %H:%M:%S')
                else:
                    updated_str = str(updated_at)
                print(f"   #{discussion.number}: {discussion.title[:50]}... (更新: {updated_str})")
        else:
            print(f"❌ 最近{recent_days}天没有目标分类的讨论更新")
        
        print()
        print("🎯 结论:")
        if len(all_discussions) > 30:
            print("✅ 分页功能正常工作，获取到超过30个讨论")
        else:
            print("ℹ️ 仓库讨论总数不超过30个，分页功能可能未被触发")
        
        if recent_target_discussions:
            print(f"✅ 找到最近{recent_days}天的目标分类更新")
        else:
            print(f"❌ 最近{recent_days}天确实没有目标分类的讨论更新")
            
    except Exception as e:
        print(f"❌ 测试过程中出现错误: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(test_pagination())