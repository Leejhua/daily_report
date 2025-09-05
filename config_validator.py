#!/usr/bin/env python3
"""
配置验证脚本
用于验证GitHub连接和定时任务配置
"""

import os
import sys
import asyncio
from datetime import datetime
import pytz
from croniter import croniter

# 添加项目根目录到Python路径
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from src.config import Config
from src.clients.github_client import GitHubClient
from src.utils.logger import get_logger

logger = get_logger(__name__)

def validate_cron_expressions(config: Config):
    """验证所有cron表达式的有效性"""
    print("\n=== 验证Cron表达式 ===")
    
    # 验证主调度器cron
    try:
        cron = croniter(config.scheduler.cron_expression)
        next_time = cron.get_next(datetime)
        print(f"✅ 主调度器cron表达式有效: {config.scheduler.cron_expression}")
        print(f"   下次执行时间: {next_time}")
    except Exception as e:
        print(f"❌ 主调度器cron表达式无效: {config.scheduler.cron_expression}")
        print(f"   错误: {e}")
        return False
    
    # 验证内容检查cron
    if hasattr(config, 'daily_content_check') and config.daily_content_check.enabled:
        content_check_cron = config.daily_content_check.content_check_cron
        if isinstance(content_check_cron, list):
            for i, cron_expr in enumerate(content_check_cron):
                try:
                    cron = croniter(cron_expr)
                    next_time = cron.get_next(datetime)
                    print(f"✅ 内容检查cron[{i}]有效: {cron_expr}")
                    print(f"   下次执行时间: {next_time}")
                except Exception as e:
                    print(f"❌ 内容检查cron[{i}]无效: {cron_expr}")
                    print(f"   错误: {e}")
                    return False
        else:
            try:
                cron = croniter(content_check_cron)
                next_time = cron.get_next(datetime)
                print(f"✅ 内容检查cron有效: {content_check_cron}")
                print(f"   下次执行时间: {next_time}")
            except Exception as e:
                print(f"❌ 内容检查cron无效: {content_check_cron}")
                print(f"   错误: {e}")
                return False
    
    # 验证分析cron
    if hasattr(config, 'daily_content_check') and hasattr(config.daily_content_check, 'analysis_cron'):
        analysis_cron = config.daily_content_check.analysis_cron
        if isinstance(analysis_cron, list):
            for i, cron_expr in enumerate(analysis_cron):
                try:
                    cron = croniter(cron_expr)
                    next_time = cron.get_next(datetime)
                    print(f"✅ 分析cron[{i}]有效: {cron_expr}")
                    print(f"   下次执行时间: {next_time}")
                except Exception as e:
                    print(f"❌ 分析cron[{i}]无效: {cron_expr}")
                    print(f"   错误: {e}")
                    return False
        else:
            try:
                cron = croniter(analysis_cron)
                next_time = cron.get_next(datetime)
                print(f"✅ 分析cron有效: {analysis_cron}")
                print(f"   下次执行时间: {next_time}")
            except Exception as e:
                print(f"❌ 分析cron无效: {analysis_cron}")
                print(f"   错误: {e}")
                return False
    
    return True

async def validate_github_connection(config: Config):
    """验证GitHub连接"""
    print("\n=== 验证GitHub连接 ===")
    
    # 检查环境变量
    github_token = os.getenv('GITHUB_TOKEN')
    if not github_token:
        print("❌ 未找到GITHUB_TOKEN环境变量")
        return False
    
    print(f"✅ GitHub Token已设置 (长度: {len(github_token)})")
    print(f"✅ GitHub组织: {config.github.organization}")
    print(f"✅ GitHub仓库: {config.github.repository}")
    print(f"✅ 使用仓库级Discussions: {not config.github.use_org_discussions}")
    print(f"✅ Discussion分类: {config.github.discussion_category}")
    
    try:
        # 创建GitHub客户端
        github_client = GitHubClient(config.github)
        
        # 测试基本连接
        print("\n测试GitHub API连接...")
        
        # 测试获取仓库信息
        import aiohttp
        async with aiohttp.ClientSession() as session:
            headers = {
                'Authorization': f'token {github_token}',
                'Accept': 'application/vnd.github.v3+json'
            }
            
            # 测试仓库访问
            repo_url = f"https://api.github.com/repos/{config.github.organization}/{config.github.repository}"
            async with session.get(repo_url, headers=headers) as response:
                if response.status == 200:
                    repo_data = await response.json()
                    print(f"✅ 仓库访问成功: {repo_data['full_name']}")
                    print(f"   仓库描述: {repo_data.get('description', 'N/A')}")
                else:
                    print(f"❌ 仓库访问失败: HTTP {response.status}")
                    return False
            
            # 测试Discussions访问
            discussions_url = f"https://api.github.com/repos/{config.github.organization}/{config.github.repository}/discussions"
            async with session.get(discussions_url, headers=headers) as response:
                if response.status == 200:
                    discussions_data = await response.json()
                    print(f"✅ Discussions访问成功，找到 {len(discussions_data)} 个讨论")
                    
                    # 检查是否有目标分类的讨论
                    target_category = config.github.discussion_category
                    category_discussions = [d for d in discussions_data if d.get('category', {}).get('name') == target_category]
                    print(f"✅ '{target_category}'分类讨论数量: {len(category_discussions)}")
                    
                else:
                    print(f"❌ Discussions访问失败: HTTP {response.status}")
                    return False
        
        return True
        
    except Exception as e:
        print(f"❌ GitHub连接测试失败: {e}")
        return False

def validate_scheduler_config(config: Config):
    """验证调度器配置"""
    print("\n=== 验证调度器配置 ===")
    
    # 检查时区
    try:
        tz = pytz.timezone(config.scheduler.timezone)
        current_time = datetime.now(tz)
        print(f"✅ 时区配置有效: {config.scheduler.timezone}")
        print(f"   当前时间: {current_time}")
    except Exception as e:
        print(f"❌ 时区配置无效: {config.scheduler.timezone}")
        print(f"   错误: {e}")
        return False
    
    # 检查重试配置
    print(f"✅ 重试次数: {config.scheduler.retry_attempts}")
    print(f"✅ 重试延迟: {config.scheduler.retry_delay}秒")
    print(f"✅ 最大执行时间: {config.scheduler.max_execution_time}秒")
    
    # 检查内容检查配置
    if hasattr(config, 'daily_content_check'):
        dcc = config.daily_content_check
        print(f"\n内容检查配置:")
        print(f"✅ 启用状态: {dcc.enabled}")
        print(f"✅ 周末检查: {dcc.weekend_check_enabled}")
        print(f"✅ 提醒功能: {dcc.reminder_enabled}")
        print(f"✅ 防重复提醒时间: {dcc.duplicate_prevention_hours}小时")
    
    # 检查周报配置
    if hasattr(config, 'weekly_reports'):
        wr = config.weekly_reports
        print(f"\n周报配置:")
        print(f"✅ 启用状态: {wr.enabled}")
        print(f"✅ 执行时间: 周{wr.execution_day} {wr.execution_hour}:00")
    
    return True

async def main():
    """主函数"""
    print("GitHub Discussions 自动化分析服务 - 配置验证工具")
    print("=" * 60)
    
    try:
        # 加载配置
        config = Config()
        print("✅ 配置文件加载成功")
        
        # 验证各项配置
        cron_valid = validate_cron_expressions(config)
        scheduler_valid = validate_scheduler_config(config)
        github_valid = await validate_github_connection(config)
        
        print("\n=== 验证结果汇总 ===")
        print(f"Cron表达式: {'✅ 通过' if cron_valid else '❌ 失败'}")
        print(f"调度器配置: {'✅ 通过' if scheduler_valid else '❌ 失败'}")
        print(f"GitHub连接: {'✅ 通过' if github_valid else '❌ 失败'}")
        
        if all([cron_valid, scheduler_valid, github_valid]):
            print("\n🎉 所有配置验证通过！系统应该能正常运行。")
            return 0
        else:
            print("\n⚠️  存在配置问题，请根据上述错误信息进行修复。")
            return 1
            
    except Exception as e:
        print(f"\n❌ 配置验证失败: {e}")
        return 1

if __name__ == "__main__":
    exit_code = asyncio.run(main())
    sys.exit(exit_code)