#!/usr/bin/env python3
"""
手动分析脚本
用于手动触发特定讨论的分析或测试分析功能
"""

import asyncio
import sys
import argparse
import json
from pathlib import Path
from datetime import date, datetime

# 添加项目根目录到Python路径
sys.path.append(str(Path(__file__).parent.parent))

from src.config import Config
from src.analyzers.daily_analyzer import DailyAnalyzer


async def analyze_discussion(discussion_number: int, preview_only: bool = False):
    """分析指定讨论"""
    print(f"🔍 {'预览' if preview_only else '分析'}讨论 #{discussion_number}...")
    
    try:
        config = Config()
        analyzer = DailyAnalyzer(config)
        
        if preview_only:
            # 仅预览，不发布评论
            result = await analyzer.get_analysis_preview(discussion_number)
            
            if result['success']:
                print(f"✅ 预览生成成功")
                print(f"📄 讨论标题: {result['discussion_title']}")
                print(f"📝 日结内容长度: {len(result['daily_summary'])} 字符")
                print(f"📋 日计划长度: {len(result['daily_plan'])} 字符")
                print(f"📊 周期计划长度: {len(result.get('weekly_plan', ''))} 字符")
                print(f"📈 分析报告长度: {result['report_length']} 字符")
                
                print(f"\n{'='*60}")
                print("📋 分析报告预览:")
                print('='*60)
                print(result['analysis_report'])
                print('='*60)
                
            else:
                print(f"❌ 预览失败: {result.get('error', '未知错误')}")
                
        else:
            # 完整分析并发布评论
            result = await analyzer.analyze_specific_discussion(discussion_number)
            
            if result['success']:
                print(f"✅ 分析完成")
                print(f"💬 评论发布: {'成功' if result.get('comment_posted', False) else '失败'}")
                
                if result.get('analysis_length'):
                    print(f"📊 分析报告长度: {result['analysis_length']} 字符")
                    
            else:
                print(f"❌ 分析失败: {result.get('error', '未知错误')}")
        
        return result
        
    except Exception as e:
        print(f"❌ 操作失败: {e}")
        return {'success': False, 'error': str(e)}


async def analyze_date_range(start_date: str, end_date: str = None):
    """分析日期范围内的讨论"""
    print(f"📅 分析日期范围: {start_date} 到 {end_date or start_date}")
    
    try:
        from datetime import datetime, timedelta
        
        start = datetime.strptime(start_date, '%Y-%m-%d').date()
        end = datetime.strptime(end_date, '%Y-%m-%d').date() if end_date else start
        
        config = Config()
        analyzer = DailyAnalyzer(config)
        
        current_date = start
        total_results = []
        
        while current_date <= end:
            print(f"\n📅 分析日期: {current_date}")
            
            result = await analyzer.run_daily_analysis(current_date)
            total_results.append(result)
            
            print(f"📄 讨论数: {result['discussions_analyzed']}")
            print(f"💬 评论数: {result['comments_posted']}")
            print(f"🔄 已有回复: {result.get('already_replied_count', 0)}")
            print(f"✅ 状态: {'成功' if result['success'] else '失败'}")
            
            if result['errors']:
                print(f"❌ 错误: {result['errors']}")
                
            # 显示详细的讨论状态
            if result.get('discussion_details'):
                print("\n📋 讨论详情:")
                for detail in result['discussion_details']:
                    status_icon = "✅" if detail.get('success') else "❌"
                    print(f"  {status_icon} #{detail['number']}: {detail['title'][:50]}...")
                    if detail.get('already_replied'):
                        print(f"     🔄 已有分析回复，跳过")
                    elif detail.get('new_comments_posted', 0) > 0:
                        print(f"     💬 新发布 {detail['new_comments_posted']} 条评论")
                    if detail.get('error'):
                        print(f"     ❌ 错误: {detail['error']}")
            
            current_date += timedelta(days=1)
        
        # 统计总结
        total_discussions = sum(r['discussions_analyzed'] for r in total_results)
        total_comments = sum(r['comments_posted'] for r in total_results)
        successful_days = sum(1 for r in total_results if r['success'])
        
        print(f"\n{'='*50}")
        print("📊 分析总结")
        print('='*50)
        print(f"📅 分析天数: {len(total_results)}")
        print(f"📄 总讨论数: {total_discussions}")
        print(f"💬 总评论数: {total_comments}")
        print(f"✅ 成功天数: {successful_days}/{len(total_results)}")
        
        return total_results
        
    except Exception as e:
        print(f"❌ 日期范围分析失败: {e}")
        return []


async def batch_analyze_discussions(discussion_numbers: list, preview_only: bool = False):
    """批量分析多个讨论"""
    print(f"🔄 批量{'预览' if preview_only else '分析'} {len(discussion_numbers)} 个讨论...")
    
    results = []
    
    for i, number in enumerate(discussion_numbers, 1):
        print(f"\n[{i}/{len(discussion_numbers)}] 处理讨论 #{number}")
        
        result = await analyze_discussion(number, preview_only)
        results.append({
            'discussion_number': number,
            'result': result
        })
        
        # 添加延迟避免API限制
        if i < len(discussion_numbers):
            await asyncio.sleep(2)
    
    # 统计结果
    successful = sum(1 for r in results if r['result']['success'])
    
    print(f"\n{'='*50}")
    print("📊 批量处理结果")
    print('='*50)
    print(f"📄 总讨论数: {len(discussion_numbers)}")
    print(f"✅ 成功处理: {successful}")
    print(f"❌ 失败处理: {len(discussion_numbers) - successful}")
    
    # 显示失败的讨论
    failed = [r for r in results if not r['result']['success']]
    if failed:
        print(f"\n❌ 失败的讨论:")
        for item in failed:
            error = item['result'].get('error', '未知错误')
            print(f"  #{item['discussion_number']}: {error}")
    
    return results


async def test_analysis_components():
    """测试分析组件"""
    print("🧪 测试分析组件...")
    
    try:
        config = Config()
        
        from src.clients.github_client import GitHubClient
        from src.clients.glm_client import GLMClient
        
        github_client = GitHubClient(config.github)
        glm_client = GLMClient(config.glm)
        
        # 测试数据
        test_summary = """
        今天完成了以下工作：
        1. 完成了用户认证模块的开发和测试
        2. 修复了登录页面的3个UI bug
        3. 参加了项目进度评审会议
        4. 更新了API文档
        5. 协助新同事解决技术问题
        """
        
        test_plan = """
        今日计划：
        1. 完成用户认证模块开发
        2. 修复已知的UI问题
        3. 参加项目评审会议
        4. 更新相关文档
        """
        
        test_weekly_plan = """
        本周计划：
        - 完成用户认证功能
        - 优化系统性能
        - 完善项目文档
        - 团队协作和知识分享
        """
        
        print("🔍 测试偏离度分析...")
        deviation_result = await glm_client.analyze_work_deviation(test_summary, test_plan)
        print(f"📊 偏离度评分: {deviation_result.get('score', 'N/A')}/10")
        print(f"📈 完成率: {deviation_result.get('completion_rate', 0)*100:.1f}%")
        
        print("\n🔍 测试清晰度分析...")
        clarity_result = await glm_client.analyze_content_clarity(test_summary)
        print(f"📝 清晰度评分: {clarity_result.get('clarity_score', 'N/A')}/10")
        print(f"🎯 具体性评分: {clarity_result.get('specificity_score', 'N/A')}/10")
        print(f"📋 完整性评分: {clarity_result.get('completeness_score', 'N/A')}/10")
        
        print("\n🔍 测试一致性分析...")
        consistency_result = await glm_client.analyze_plan_consistency(test_plan, test_weekly_plan)
        print(f"🔄 一致性评分: {consistency_result.get('consistency_score', 'N/A')}/10")
        print(f"🎯 目标对齐度: {consistency_result.get('alignment_level', 'N/A')}/10")
        
        print("\n🔍 测试综合分析...")
        comprehensive_report = await glm_client.generate_comprehensive_analysis(
            test_summary, test_plan, test_weekly_plan
        )
        
        print(f"📊 综合报告长度: {len(comprehensive_report)} 字符")
        print(f"\n{'='*60}")
        print("📋 综合分析报告:")
        print('='*60)
        print(comprehensive_report)
        print('='*60)
        
        return True
        
    except Exception as e:
        print(f"❌ 组件测试失败: {e}")
        return False


def main():
    """主函数"""
    parser = argparse.ArgumentParser(description="手动分析工具")
    
    subparsers = parser.add_subparsers(dest='command', help='可用命令')
    
    # 单个讨论分析
    discuss_parser = subparsers.add_parser('discuss', help='分析单个讨论')
    discuss_parser.add_argument('number', type=int, help='讨论编号')
    discuss_parser.add_argument('--preview', action='store_true', help='仅预览，不发布评论')
    
    # 批量讨论分析
    batch_parser = subparsers.add_parser('batch', help='批量分析讨论')
    batch_parser.add_argument('numbers', nargs='+', type=int, help='讨论编号列表')
    batch_parser.add_argument('--preview', action='store_true', help='仅预览，不发布评论')
    
    # 日期范围分析
    date_parser = subparsers.add_parser('date', help='按日期范围分析')
    date_parser.add_argument('start_date', help='开始日期 (YYYY-MM-DD)')
    date_parser.add_argument('--end_date', help='结束日期 (YYYY-MM-DD)')
    
    # 组件测试
    subparsers.add_parser('test', help='测试分析组件')
    
    args = parser.parse_args()
    
    if not args.command:
        parser.print_help()
        return
    
    if args.command == 'discuss':
        result = asyncio.run(analyze_discussion(args.number, args.preview))
        sys.exit(0 if result['success'] else 1)
        
    elif args.command == 'batch':
        results = asyncio.run(batch_analyze_discussions(args.numbers, args.preview))
        success_count = sum(1 for r in results if r['result']['success'])
        sys.exit(0 if success_count == len(results) else 1)
        
    elif args.command == 'date':
        results = asyncio.run(analyze_date_range(args.start_date, args.end_date))
        success_count = sum(1 for r in results if r['success'])
        sys.exit(0 if success_count == len(results) else 1)
        
    elif args.command == 'test':
        success = asyncio.run(test_analysis_components())
        sys.exit(0 if success else 1)


if __name__ == "__main__":
    main()
