#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
增强版启动脚本
支持命令行参数和调度器启动
"""

import argparse
import sys
import os
from datetime import datetime

# 添加项目根目录到Python路径
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

def parse_arguments():
    """解析命令行参数"""
    parser = argparse.ArgumentParser(
        description='GitHub Discussions 自动化分析工具',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
使用示例:
  %(prog)s --run-once                    # 运行一次分析
  %(prog)s --date 2024-01-15 --run-once  # 分析指定日期
  %(prog)s --scheduler                   # 启动调度器
  %(prog)s --help                       # 显示帮助信息
        """
    )
    
    parser.add_argument(
        '--date',
        type=str,
        help='指定分析日期 (格式: YYYY-MM-DD)，默认为今天'
    )
    
    parser.add_argument(
        '--run-once',
        action='store_true',
        help='运行一次分析后退出'
    )
    
    parser.add_argument(
        '--scheduler',
        action='store_true',
        help='启动调度器模式'
    )
    
    parser.add_argument(
        '--config',
        type=str,
        help='指定配置文件路径'
    )
    
    return parser.parse_args()

def run_analysis(target_date=None):
    """运行分析"""
    try:
        from src.main import main as original_main
        
        # 设置命令行参数
        if target_date:
            sys.argv = ['main.py', '--date', target_date, '--run-once']
        else:
            sys.argv = ['main.py', '--run-once']
        
        # 运行原始main函数
        original_main()
        
    except Exception as e:
        print(f"运行分析时出错: {e}")
        return False
    
    return True

def start_scheduler():
    """启动调度器"""
    try:
        import asyncio
        from src.scheduler import AnalysisScheduler
        from src.config import Config
        from src.utils.logger import setup_logging
        
        print("正在启动调度器...")
        
        # 初始化日志配置 - 设置为DEBUG级别以显示调试信息
        import logging
        
        # 创建一个临时配置对象来设置DEBUG级别
        class DebugLogConfig:
            level = 'DEBUG'
            file_path = 'logs/analyzer.log'
            max_size = '10MB'
            backup_count = 5
        
        setup_logging(DebugLogConfig())
        
        # 加载配置
        config = Config()
        
        # 创建调度器
        scheduler = AnalysisScheduler(config)
        
        print("调度器已启动，按 Ctrl+C 停止")
        
        # 启动异步调度器
        try:
            asyncio.run(scheduler.start())
        except KeyboardInterrupt:
            print("\n正在停止调度器...")
            asyncio.run(scheduler.stop())
            print("调度器已停止")
        
    except Exception as e:
        print(f"启动调度器时出错: {e}")
        return False
    
    return True

def main():
    """主函数"""
    args = parse_arguments()
    
    # 如果没有指定任何模式，显示帮助
    if not args.run_once and not args.scheduler:
        print("请指定运行模式:")
        print("  --run-once   运行一次分析")
        print("  --scheduler  启动调度器")
        print("  --help       显示帮助信息")
        return 1
    
    # 设置配置文件路径（如果指定）
    if args.config:
        os.environ['CONFIG_FILE'] = args.config
    
    # 运行一次模式
    if args.run_once:
        print(f"开始运行分析 (日期: {args.date or '今天'})...")
        success = run_analysis(args.date)
        if success:
            print("分析完成")
            return 0
        else:
            print("分析失败")
            return 1
    
    # 调度器模式
    if args.scheduler:
        success = start_scheduler()
        return 0 if success else 1

if __name__ == '__main__':
    sys.exit(main())