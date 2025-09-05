#!/usr/bin/env python3
"""
探索GitHub Discussions结构的脚本
用于了解实际的日报模块组织方式
"""

import asyncio
import sys
import argparse
import json
from pathlib import Path
from datetime import date, datetime, timedelta
from collections import defaultdict

# 添加项目根目录到Python路径
sys.path.append(str(Path(__file__).parent.parent))

from src.config import Config
from src.clients.github_client import GitHubClient


async def explore_discussion_categories():
    """探索Discussion分类结构"""
    print("🔍 探索GitHub Discussions分类结构...")
    
    try:
        config = Config()
        client = GitHubClient(config.github)
        
        # 根据配置获取discussions
        if config.github.use_org_discussions:
            discussions = await client._get_org_discussions()
        else:
            discussions = await client._get_repo_discussions()
        
        # 统计分类
        categories = defaultdict(int)
        category_details = defaultdict(list)
        
        for discussion in discussions:
            category_name = discussion.category.name
            categories[category_name] += 1
            
            category_details[category_name].append({
                'number': discussion.number,
                'title': discussion.title,
                'created_at': discussion.created_at.strftime('%Y-%m-%d'),
                'updated_at': discussion.updated_at.strftime('%Y-%m-%d'),
                'author': discussion.user.login,
                'comments': discussion.comments
            })
        
        print(f"\n📊 找到 {len(categories)} 个Discussion分类：")
        print("="*60)
        
        for category, count in sorted(categories.items()):
            print(f"📁 {category}: {count} 个讨论")
            
            # 显示最近的几个讨论示例
            recent_discussions = sorted(
                category_details[category], 
                key=lambda x: x['updated_at'], 
                reverse=True
            )[:3]
            
            for disc in recent_discussions:
                print(f"   └─ #{disc['number']}: {disc['title'][:50]}{'...' if len(disc['title']) > 50 else ''}")
                print(f"      📅 {disc['updated_at']} | 👤 {disc['author']} | 💬 {disc['comments']}")
            
            if len(category_details[category]) > 3:
                print(f"   └─ ... 还有 {len(category_details[category]) - 3} 个讨论")
            print()
        
        return categories, category_details
        
    except Exception as e:
        print(f"❌ 探索分类失败: {e}")
        return {}, {}


async def analyze_category_content(category_name: str, max_discussions: int = 10):
    """分析特定分类的内容结构"""
    print(f"🔍 分析分类 '{category_name}' 的内容结构...")
    
    try:
        config = Config()
        client = GitHubClient(config.github)
        
        # 根据配置获取discussions
        if config.github.use_org_discussions:
            discussions = await client._get_org_discussions()
        else:
            discussions = await client._get_repo_discussions()
        target_discussions = []
        
        for discussion in discussions:
            if discussion.category.name == category_name:
                target_discussions.append(discussion)
                if len(target_discussions) >= max_discussions:
                    break
        
        if not target_discussions:
            print(f"❌ 未找到分类 '{category_name}' 的讨论")
            return
        
        print(f"📄 分析 {len(target_discussions)} 个讨论的内容结构：")
        print("="*80)
        
        # 分析内容模式
        common_patterns = defaultdict(int)
        title_patterns = defaultdict(int)
        
        for i, discussion in enumerate(target_discussions, 1):
            print(f"\n[{i}] #{discussion.number}: {discussion.title}")
            print(f"📅 创建: {discussion.created_at.strftime('%Y-%m-%d %H:%M')}")
            print(f"📅 更新: {discussion.updated_at.strftime('%Y-%m-%d %H:%M')}")
            print(f"👤 作者: {discussion.user.login}")
            print(f"💬 评论: {discussion.comments} 条")
            
            # 分析标题模式
            title_lower = discussion.title.lower()
            if '日结' in title_lower or '日报' in title_lower:
                title_patterns['日结/日报'] += 1
            if '周结' in title_lower or '周报' in title_lower:
                title_patterns['周结/周报'] += 1
            if '月结' in title_lower or '月报' in title_lower:
                title_patterns['月结/月报'] += 1
            if '计划' in title_lower:
                title_patterns['计划'] += 1
            
            # 分析内容长度和结构
            body = discussion.body or ""
            print(f"📝 内容长度: {len(body)} 字符")
            
            if body:
                # 查找常见关键词
                keywords = ['日结', '日报', '今日', '完成', '计划', '明日', '待办', '总结', '工作', '任务']
                found_keywords = []
                for keyword in keywords:
                    if keyword in body:
                        found_keywords.append(keyword)
                        common_patterns[keyword] += 1
                
                if found_keywords:
                    print(f"🔑 关键词: {', '.join(found_keywords)}")
                
                # 显示内容预览
                preview = body[:200].replace('\n', ' ').strip()
                if len(body) > 200:
                    preview += "..."
                print(f"📖 内容预览: {preview}")
            
            print("-" * 80)
        
        # 总结分析结果
        print(f"\n📊 内容分析总结:")
        print("="*50)
        
        print(f"📁 标题模式统计:")
        for pattern, count in sorted(title_patterns.items(), key=lambda x: x[1], reverse=True):
            print(f"   {pattern}: {count} 次")
        
        print(f"\n🔑 关键词统计:")
        for keyword, count in sorted(common_patterns.items(), key=lambda x: x[1], reverse=True):
            print(f"   {keyword}: {count} 次")
            
    except Exception as e:
        print(f"❌ 内容分析失败: {e}")


async def analyze_recent_activity(days: int = 7):
    """分析最近几天的活动情况"""
    print(f"📅 分析最近 {days} 天的Discussion活动...")
    
    try:
        config = Config()
        client = GitHubClient(config.github)
        
        end_date = date.today()
        start_date = end_date - timedelta(days=days-1)
        
        # 根据配置获取discussions
        if config.github.use_org_discussions:
            discussions = await client._get_org_discussions()
        else:
            discussions = await client._get_repo_discussions()
        daily_activity = defaultdict(lambda: defaultdict(int))
        
        for discussion in discussions:
            updated_date = discussion.updated_at.date()
            
            if start_date <= updated_date <= end_date:
                category = discussion.category.name
                daily_activity[updated_date][category] += 1
        
        print(f"\n📊 {start_date} 到 {end_date} 的活动统计:")
        print("="*60)
        
        current_date = start_date
        while current_date <= end_date:
            activity = daily_activity.get(current_date, {})
            total = sum(activity.values())
            
            print(f"📅 {current_date.strftime('%Y-%m-%d')} ({current_date.strftime('%A')}): {total} 个更新")
            
            if activity:
                for category, count in sorted(activity.items()):
                    print(f"   └─ {category}: {count} 个")
            else:
                print("   └─ 无活动")
            
            current_date += timedelta(days=1)
            
    except Exception as e:
        print(f"❌ 活动分析失败: {e}")


async def suggest_configuration(categories: dict):
    """基于分析结果建议配置"""
    print("\n💡 基于分析结果的配置建议:")
    print("="*50)
    
    # 寻找可能的日报分类
    daily_categories = []
    for category in categories.keys():
        category_lower = category.lower()
        if any(keyword in category_lower for keyword in ['日结', '日报', 'daily', '工作']):
            daily_categories.append(category)
    
    if daily_categories:
        print("📁 建议的日报分类:")
        for category in daily_categories:
            print(f"   - {category} ({categories[category]} 个讨论)")
        
        recommended = daily_categories[0]
        print(f"\n🎯 推荐使用: '{recommended}'")
        print(f"配置方式:")
        print(f"   环境变量: GITHUB_DISCUSSION_CATEGORY=\"{recommended}\"")
        print(f"   YAML配置: discussion_category: \"{recommended}\"")
    else:
        print("⚠️ 未找到明显的日报分类，请手动指定")
        print("📁 所有可用分类:")
        for category, count in categories.items():
            print(f"   - {category} ({count} 个讨论)")


async def full_exploration():
    """完整探索功能"""
    print("🚀 开始完整探索...")
    categories, details = await explore_discussion_categories()
    
    if categories:
        # 分析最活跃的分类
        most_active = max(categories.items(), key=lambda x: x[1])
        print(f"\n🔥 分析最活跃的分类: {most_active[0]}")
        await analyze_category_content(most_active[0], 5)
    
    await analyze_recent_activity(7)
    await suggest_configuration(categories)


def main():
    """主函数"""
    parser = argparse.ArgumentParser(description="探索GitHub Discussions结构")
    
    subparsers = parser.add_subparsers(dest='command', help='可用命令')
    
    # 探索分类
    subparsers.add_parser('categories', help='探索Discussion分类结构')
    
    # 分析特定分类
    analyze_parser = subparsers.add_parser('analyze', help='分析特定分类内容')
    analyze_parser.add_argument('category', help='要分析的分类名称')
    analyze_parser.add_argument('--max', type=int, default=10, help='最大分析讨论数')
    
    # 分析最近活动
    activity_parser = subparsers.add_parser('activity', help='分析最近活动')
    activity_parser.add_argument('--days', type=int, default=7, help='分析天数')
    
    # 完整探索
    subparsers.add_parser('full', help='完整探索（包含所有分析）')
    
    args = parser.parse_args()
    
    if not args.command:
        parser.print_help()
        return
    
    if args.command == 'categories':
        categories, details = asyncio.run(explore_discussion_categories())
        asyncio.run(suggest_configuration(categories))
        
    elif args.command == 'analyze':
        asyncio.run(analyze_category_content(args.category, args.max))
        
    elif args.command == 'activity':
        asyncio.run(analyze_recent_activity(args.days))
        
    elif args.command == 'full':
        asyncio.run(full_exploration())


if __name__ == "__main__":
    main()
