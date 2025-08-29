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
from dotenv import load_dotenv

# 加载环境变量
load_dotenv()

# 添加项目根目录到Python路径
sys.path.append(str(Path(__file__).parent.parent))

from src.config import Config
from src.analyzers.daily_analyzer import DailyAnalyzer
from src.clients.glm_client import GLMClient
from src.utils.logger import setup_logging


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
            print(f"✅ 状态: {'成功' if result['success'] else '失败'}")
            
            if result['errors']:
                print(f"❌ 错误: {result['errors']}")
            
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
    print("\n=== 测试分析组件 ===")
    
    # 初始化配置和客户端
    config = Config()
    glm_client = GLMClient(config.glm)
    
    # 测试数据
    test_plan = "完成项目文档编写，优化代码性能"
    test_summary = "今天主要写了一些文档，但是代码优化没有完成"
    
    try:
        # 测试连接
        print("\n1. 测试GLM API连接...")
        connection_ok = await glm_client.test_connection()
        print(f"连接状态: {'✅ 成功' if connection_ok else '❌ 失败'}")
        
        if not connection_ok:
            print("❌ API连接失败，无法继续测试")
            return
        
        # 测试日报内容分析
        print("\n2. 测试日报内容分析...")
        report_result = await glm_client.analyze_daily_report_content(test_summary, test_plan)
        print(f"日报分析结果: {report_result[:200]}...")
        
        # 测试日计划内容分析
        print("\n3. 测试日计划内容分析...")
        plan_result = await glm_client.analyze_daily_plan_content(test_plan)
        print(f"日计划分析结果: {plan_result[:200]}...")
        
        print("\n✅ 所有分析组件测试完成")
        
    except Exception as e:
        print(f"❌ 测试失败: {e}")
        import traceback
        traceback.print_exc()


def main():
    """主函数"""
    # 初始化日志系统
    setup_logging()
    
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

