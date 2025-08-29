#!/usr/bin/env python3
"""
测试日报结构解析的脚本
验证新的日报模式：首楼=周期计划，评论=轮流的日计划和日报
"""

import asyncio
import sys
import argparse
from pathlib import Path
from datetime import date, datetime

# 添加项目根目录到Python路径
sys.path.append(str(Path(__file__).parent.parent))

from src.config import Config
from src.clients.github_client import GitHubClient
from src.analyzers.daily_analyzer import DailyAnalyzer


async def test_discussion_structure(discussion_number: int):
    """测试特定讨论的结构解析"""
    print(f"🔍 测试讨论 #{discussion_number} 的结构解析...")
    
    try:
        config = Config()
        github_client = GitHubClient(config.github)
        
        # 获取所有讨论数据
        if config.github.use_org_discussions:
            discussions = await github_client._get_org_discussions()
        else:
            discussions = await github_client._get_repo_discussions()
        
        target_discussion = None
        for discussion in discussions:
            if discussion.number == discussion_number:
                target_discussion = discussion
                break
        
        if not target_discussion:
            print(f"❌ 未找到讨论 #{discussion_number}")
            return False
        
        print(f"✅ 找到讨论: {target_discussion.title}")
        print(f"📅 创建时间: {target_discussion.created_at}")
        print(f"📅 更新时间: {target_discussion.updated_at}")
        print(f"👤 作者: {target_discussion.author}")
        print(f"💬 评论数: {target_discussion.comments_count}")
        
        # 显示首楼内容（周期计划）
        print(f"\n{'='*60}")
        print("📋 首楼内容（周期计划）:")
        print('='*60)
        weekly_plan = target_discussion.body[:500] + "..." if len(target_discussion.body) > 500 else target_discussion.body
        print(weekly_plan or "（首楼无内容）")
        
        # 获取所有评论
        comments = await github_client.get_discussion_comments(discussion_number)
        
        if comments:
            print(f"\n{'='*60}")
            print(f"💬 评论列表 ({len(comments)} 条):")
            print('='*60)
            
            for i, comment in enumerate(comments, 1):
                print(f"\n[{i}] 评论ID: {comment.id}")
                print(f"👤 作者: {comment.author}")
                print(f"📅 时间: {comment.created_at}")
                
                # 分析评论内容类型
                content_lower = comment.body.lower()
                content_type = "未知"
                
                # 日报关键词
                daily_report_keywords = ['日报', '日结', '今日完成', '今日工作', '进度', '遇到问题']
                if any(keyword in content_lower for keyword in daily_report_keywords):
                    content_type = "🗒️ 日报"
                
                # 日计划关键词
                daily_plan_keywords = ['日计划', '明日计划', '明天计划', '下一步', '待办']
                if any(keyword in content_lower for keyword in daily_plan_keywords):
                    content_type = "📋 日计划"
                
                # 工作相关内容
                work_keywords = ['完成', '开发', '测试', '修复', '问题', '功能', '任务', '会议']
                work_count = sum(1 for keyword in work_keywords if keyword in content_lower)
                if work_count >= 2 and len(comment.body) > 50:
                    content_type = "🗒️ 日报（推测）"
                
                print(f"📝 类型: {content_type}")
                print(f"📊 长度: {len(comment.body)} 字符")
                
                # 显示内容预览
                preview = comment.body[:200].replace('\n', ' ').strip()
                if len(comment.body) > 200:
                    preview += "..."
                print(f"📖 内容: {preview}")
                print("-" * 40)
        
        # 测试内容提取
        print(f"\n{'='*60}")
        print("🔍 测试内容提取:")
        print('='*60)
        
        content_data = await github_client.extract_daily_content(target_discussion)
        
        print(f"📋 周期计划长度: {len(content_data['weekly_plan'])} 字符")
        print(f"🗒️ 日报长度: {len(content_data['daily_summary'])} 字符")
        print(f"📅 日计划长度: {len(content_data['daily_plan'])} 字符")
        
        if content_data['daily_summary']:
            print(f"\n📖 提取的日报内容:")
            print("-" * 30)
            summary_preview = content_data['daily_summary'][:300] + "..." if len(content_data['daily_summary']) > 300 else content_data['daily_summary']
            print(summary_preview)
        
        if content_data['daily_plan']:
            print(f"\n📖 提取的日计划内容:")
            print("-" * 30)
            plan_preview = content_data['daily_plan'][:300] + "..." if len(content_data['daily_plan']) > 300 else content_data['daily_plan']
            print(plan_preview)
        
        return True
        
    except Exception as e:
        print(f"❌ 测试失败: {e}")
        return False


async def test_recent_discussions(days: int = 3):
    """测试最近几天的讨论结构"""
    print(f"🔍 测试最近 {days} 天的讨论结构...")
    
    try:
        config = Config()
        github_client = GitHubClient(config.github)
        
        # 获取最近的讨论
        discussions = await github_client.get_daily_discussions()
        
        if not discussions:
            print("❌ 未找到任何讨论")
            return False
        
        # 按更新时间排序
        discussions.sort(key=lambda x: x.updated_at, reverse=True)
        recent_discussions = discussions[:5]  # 取最近5个
        
        print(f"📄 找到 {len(discussions)} 个讨论，分析最近 {len(recent_discussions)} 个:")
        print("="*80)
        
        for i, discussion in enumerate(recent_discussions, 1):
            print(f"\n[{i}] #{discussion.number}: {discussion.title}")
            print(f"📅 更新: {discussion.updated_at.strftime('%Y-%m-%d %H:%M')}")
            print(f"💬 评论: {discussion.comments_count} 条")
            
            # 快速内容提取测试
            try:
                content_data = await github_client.extract_daily_content(discussion)
                
                has_weekly = len(content_data['weekly_plan']) > 0
                has_daily = len(content_data['daily_summary']) > 0
                has_plan = len(content_data['daily_plan']) > 0
                
                print(f"📊 结构: 周期计划{'✅' if has_weekly else '❌'} | "
                      f"日报{'✅' if has_daily else '❌'} | "
                      f"日计划{'✅' if has_plan else '❌'}")
                
                if has_daily:
                    # 分析日报内容特征
                    daily_content = content_data['daily_summary'].lower()
                    has_progress = any(word in daily_content for word in ['完成', '进度', '百分'])
                    has_problems = any(word in daily_content for word in ['问题', '困难', '阻塞', 'bug'])
                    has_tasks = any(word in daily_content for word in ['开发', '测试', '修复', '会议', '任务'])
                    
                    features = []
                    if has_progress: features.append("进度描述")
                    if has_problems: features.append("问题记录")
                    if has_tasks: features.append("任务内容")
                    
                    print(f"🏷️ 日报特征: {', '.join(features) if features else '无明显特征'}")
                
            except Exception as e:
                print(f"❌ 内容提取失败: {e}")
            
            print("-" * 60)
        
        return True
        
    except Exception as e:
        print(f"❌ 测试失败: {e}")
        return False


async def test_analysis_preview(discussion_number: int):
    """测试分析预览功能"""
    print(f"🔍 测试讨论 #{discussion_number} 的分析预览...")
    
    try:
        config = Config()
        analyzer = DailyAnalyzer(config)
        
        # 生成分析预览
        preview = await analyzer.get_analysis_preview(discussion_number)
        
        if preview['success']:
            print(f"✅ 分析预览成功")
            print(f"📄 讨论标题: {preview['discussion_title']}")
            print(f"📊 数据摘要:")
            print(f"   - 日报长度: {len(preview['daily_summary'])} 字符")
            print(f"   - 日计划长度: {len(preview['daily_plan'])} 字符")
            print(f"   - 周期计划长度: {len(preview.get('weekly_plan', ''))} 字符")
            print(f"   - 分析报告长度: {preview['report_length']} 字符")
            
            print(f"\n{'='*60}")
            print("📋 分析报告预览:")
            print('='*60)
            print(preview['analysis_report'])
            print('='*60)
            
            return True
        else:
            print(f"❌ 分析预览失败: {preview.get('error', '未知错误')}")
            return False
            
    except Exception as e:
        print(f"❌ 测试失败: {e}")
        return False


def main():
    """主函数"""
    parser = argparse.ArgumentParser(description="测试日报结构解析")
    
    subparsers = parser.add_subparsers(dest='command', help='可用命令')
    
    # 测试特定讨论
    discuss_parser = subparsers.add_parser('discuss', help='测试特定讨论结构')
    discuss_parser.add_argument('number', type=int, help='讨论编号')
    
    # 测试最近讨论
    recent_parser = subparsers.add_parser('recent', help='测试最近讨论结构')
    recent_parser.add_argument('--days', type=int, default=3, help='测试天数')
    
    # 测试分析预览
    preview_parser = subparsers.add_parser('preview', help='测试分析预览')
    preview_parser.add_argument('number', type=int, help='讨论编号')
    
    # 全面测试
    subparsers.add_parser('all', help='运行所有测试')
    
    args = parser.parse_args()
    
    if not args.command:
        parser.print_help()
        return
    
    if args.command == 'discuss':
        success = asyncio.run(test_discussion_structure(args.number))
        sys.exit(0 if success else 1)
        
    elif args.command == 'recent':
        success = asyncio.run(test_recent_discussions(args.days))
        sys.exit(0 if success else 1)
        
    elif args.command == 'preview':
        success = asyncio.run(test_analysis_preview(args.number))
        sys.exit(0 if success else 1)
        
    elif args.command == 'all':
        print("🚀 开始全面测试...")
        
        # 测试最近讨论
        recent_ok = asyncio.run(test_recent_discussions(3))
        
        if recent_ok:
            print("\n" + "="*60)
            print("请选择一个讨论编号进行详细测试:")
            discussion_number = input("输入讨论编号: ")
            
            try:
                number = int(discussion_number)
                structure_ok = asyncio.run(test_discussion_structure(number))
                
                if structure_ok:
                    print(f"\n是否要测试讨论 #{number} 的分析预览？(y/n): ", end="")
                    if input().lower() == 'y':
                        preview_ok = asyncio.run(test_analysis_preview(number))
                        sys.exit(0 if preview_ok else 1)
                
                sys.exit(0 if structure_ok else 1)
                
            except ValueError:
                print("❌ 无效的讨论编号")
                sys.exit(1)
        else:
            sys.exit(1)


if __name__ == "__main__":
    main()

