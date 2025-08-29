#!/usr/bin/env python3
"""
服务测试脚本
用于测试GitHub Discussions自动化分析服务的各项功能
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
from src.clients.github_client import GitHubClient
from src.clients.glm_client import GLMClient
from src.scheduler import AnalysisScheduler


async def test_connections():
    """测试所有外部连接"""
    print("🔍 测试外部连接...")
    
    try:
        config = Config()
        analyzer = DailyAnalyzer(config)
        
        connections = await analyzer.test_connections()
        
        print(f"✅ GitHub连接: {'正常' if connections['github'] else '失败'}")
        print(f"✅ GLM连接: {'正常' if connections['glm'] else '失败'}")
        print(f"🎯 整体状态: {'正常' if connections['overall'] else '异常'}")
        
        return connections['overall']
        
    except Exception as e:
        print(f"❌ 连接测试失败: {e}")
        return False


async def test_github_api():
    """测试GitHub API功能"""
    print("\n🐙 测试GitHub API...")
    
    try:
        config = Config()
        client = GitHubClient(config.github)
        
        # 测试获取讨论
        discussions = await client.get_daily_discussions()
        print(f"📄 找到 {len(discussions)} 个今日讨论")
        
        if discussions:
            # 测试内容提取
            first_discussion = discussions[0]
            print(f"📝 测试讨论: #{first_discussion.number} - {first_discussion.title}")
            
            content = await client.extract_daily_content(first_discussion)
            print(f"📊 日结长度: {len(content['daily_summary'])} 字符")
            print(f"📋 计划长度: {len(content['daily_plan'])} 字符")
            
            # 测试获取评论
            comments = await client.get_discussion_comments(first_discussion.number)
            print(f"💬 评论数量: {len(comments)}")
        
        return True
        
    except Exception as e:
        print(f"❌ GitHub API测试失败: {e}")
        return False


async def test_glm_api():
    """测试GLM API功能"""
    print("\n🤖 测试GLM API...")
    
    try:
        config = Config()
        client = GLMClient(config.glm)
        
        # 测试基本连接
        connection_ok = await client.test_connection()
        if not connection_ok:
            print("❌ GLM API连接失败")
            return False
            
        # 测试分析功能
        test_summary = "今天完成了用户认证模块的开发，修复了3个bug，参加了项目评审会议。"
        test_plan = "完成用户认证模块开发，修复已知bug，参加项目评审。"
        
        print("🔍 测试偏离度分析...")
        deviation_result = await client.analyze_work_deviation(test_summary, test_plan)
        print(f"📊 偏离度评分: {deviation_result.get('score', 'N/A')}")
        
        print("🔍 测试清晰度分析...")
        clarity_result = await client.analyze_content_clarity(test_summary)
        print(f"📝 清晰度评分: {clarity_result.get('clarity_score', 'N/A')}")
        
        print("🔍 测试一致性分析...")
        consistency_result = await client.analyze_plan_consistency(test_plan, test_plan)
        print(f"🔄 一致性评分: {consistency_result.get('consistency_score', 'N/A')}")
        
        return True
        
    except Exception as e:
        print(f"❌ GLM API测试失败: {e}")
        return False


async def test_analysis_preview(discussion_number: int):
    """测试分析预览功能"""
    print(f"\n📊 测试分析预览 (讨论 #{discussion_number})...")
    
    try:
        config = Config()
        analyzer = DailyAnalyzer(config)
        
        preview = await analyzer.get_analysis_preview(discussion_number)
        
        if preview['success']:
            print(f"✅ 分析成功")
            print(f"📄 讨论标题: {preview['discussion_title']}")
            print(f"📝 日结长度: {len(preview['daily_summary'])} 字符")
            print(f"📋 计划长度: {len(preview['daily_plan'])} 字符")
            print(f"📊 报告长度: {preview['report_length']} 字符")
            
            # 显示报告预览
            report_preview = preview['analysis_report'][:500] + "..." if len(preview['analysis_report']) > 500 else preview['analysis_report']
            print(f"\n📋 报告预览:\n{report_preview}")
            
        else:
            print(f"❌ 分析失败: {preview.get('error', '未知错误')}")
            
        return preview['success']
        
    except Exception as e:
        print(f"❌ 分析预览失败: {e}")
        return False


async def test_full_analysis():
    """测试完整分析流程"""
    print("\n🚀 测试完整分析流程...")
    
    try:
        config = Config()
        analyzer = DailyAnalyzer(config)
        
        # 运行今日分析
        result = await analyzer.run_daily_analysis()
        
        print(f"📅 分析日期: {result['date']}")
        print(f"📄 分析讨论数: {result['discussions_analyzed']}")
        print(f"💬 发布评论数: {result['comments_posted']}")
        print(f"✅ 分析状态: {'成功' if result['success'] else '失败'}")
        
        if result['errors']:
            print(f"❌ 错误信息: {result['errors']}")
            
        return result['success']
        
    except Exception as e:
        print(f"❌ 完整分析测试失败: {e}")
        return False


async def test_scheduler():
    """测试调度器功能"""
    print("\n⏰ 测试调度器...")
    
    try:
        config = Config()
        scheduler = AnalysisScheduler(config)
        
        # 获取调度器状态
        status = await scheduler.get_status()
        
        print(f"🔄 Cron表达式: {status['cron_expression']}")
        print(f"🌍 时区: {status['timezone']}")
        print(f"⏭️ 下次运行: {status['next_run_time']}")
        
        return True
        
    except Exception as e:
        print(f"❌ 调度器测试失败: {e}")
        return False


def test_configuration():
    """测试配置加载"""
    print("\n⚙️ 测试配置...")
    
    try:
        config = Config()
        config.validate()
        
        summary = config.get_config_summary()
        print(f"🐙 GitHub组织: {summary['github']['organization']}")
        print(f"📦 GitHub仓库: {summary['github']['repository']}")
        print(f"🤖 GLM模型: {summary['glm']['model']}")
        print(f"⏰ 调度表达式: {summary['scheduler']['cron_expression']}")
        
        return True
        
    except Exception as e:
        print(f"❌ 配置测试失败: {e}")
        return False


async def run_all_tests():
    """运行所有测试"""
    print("🧪 开始运行所有测试...\n")
    
    tests = [
        ("配置加载", test_configuration, False),
        ("外部连接", test_connections, True),
        ("GitHub API", test_github_api, True),
        ("GLM API", test_glm_api, True),
        ("调度器", test_scheduler, True),
        ("完整分析", test_full_analysis, True),
    ]
    
    results = {}
    
    for test_name, test_func, is_async in tests:
        print(f"\n{'='*50}")
        print(f"🧪 测试: {test_name}")
        print('='*50)
        
        try:
            if is_async:
                result = await test_func()
            else:
                result = test_func()
            results[test_name] = result
        except Exception as e:
            print(f"❌ 测试异常: {e}")
            results[test_name] = False
    
    # 显示测试总结
    print(f"\n{'='*50}")
    print("📊 测试总结")
    print('='*50)
    
    passed = sum(results.values())
    total = len(results)
    
    for test_name, result in results.items():
        status = "✅ 通过" if result else "❌ 失败"
        print(f"{test_name}: {status}")
    
    print(f"\n🎯 总体结果: {passed}/{total} 项测试通过")
    
    if passed == total:
        print("🎉 所有测试通过！服务配置正确。")
    else:
        print("⚠️ 部分测试失败，请检查配置和网络连接。")
    
    return passed == total


def main():
    """主函数"""
    parser = argparse.ArgumentParser(description="GitHub Discussions自动化分析服务测试工具")
    parser.add_argument("--test", choices=[
        "all", "config", "connections", "github", "glm", "scheduler", "analysis", "preview"
    ], default="all", help="要运行的测试类型")
    parser.add_argument("--discussion", type=int, help="用于预览测试的讨论编号")
    
    args = parser.parse_args()
    
    if args.test == "all":
        success = asyncio.run(run_all_tests())
        sys.exit(0 if success else 1)
    elif args.test == "config":
        success = test_configuration()
        sys.exit(0 if success else 1)
    elif args.test == "connections":
        success = asyncio.run(test_connections())
        sys.exit(0 if success else 1)
    elif args.test == "github":
        success = asyncio.run(test_github_api())
        sys.exit(0 if success else 1)
    elif args.test == "glm":
        success = asyncio.run(test_glm_api())
        sys.exit(0 if success else 1)
    elif args.test == "scheduler":
        success = asyncio.run(test_scheduler())
        sys.exit(0 if success else 1)
    elif args.test == "analysis":
        success = asyncio.run(test_full_analysis())
        sys.exit(0 if success else 1)
    elif args.test == "preview":
        if not args.discussion:
            print("❌ 预览测试需要指定 --discussion 参数")
            sys.exit(1)
        success = asyncio.run(test_analysis_preview(args.discussion))
        sys.exit(0 if success else 1)


if __name__ == "__main__":
    main()

