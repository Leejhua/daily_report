#!/usr/bin/env python3
"""
GitHub Discussions 自动化分析服务主程序（增强版）
基于GLM-4.5模型的内容分析和自动评论系统
集成内容检查和日常分析的定时调度功能
支持命令行参数和一次性执行模式
"""

import asyncio
import sys
import signal
import logging
import argparse
from pathlib import Path
from datetime import datetime, date
from typing import Optional

# 添加项目根目录到Python路径
sys.path.append(str(Path(__file__).parent.parent))

from src.config import Config
from src.scheduler import RetryableScheduler
from src.utils.logger import setup_logging
from src.analyzers.daily_analyzer import DailyAnalyzer
from src.content_checker.daily_content_checker import DailyContentChecker


class AnalysisService:
    """主服务类"""
    
    def __init__(self):
        self.config = Config()
        self.scheduler = None
        self.logger = logging.getLogger(__name__)
        self.running = False
        self._validate_config()
        
    async def start(self):
        """启动服务"""
        try:
            self.logger.info("正在启动GitHub Discussions自动化分析服务...")
            
            # 初始化调度器（使用RetryableScheduler支持重试机制）
            self.scheduler = RetryableScheduler(self.config)
            
            # 启动调度器
            await self.scheduler.start()
            self.running = True
            
            # 显示服务状态信息
            await self._display_service_status()
            
            # 启动健康检查
            health_check_task = asyncio.create_task(self._health_check_loop())
            
            # 保持服务运行
            try:
                while self.running:
                    await asyncio.sleep(1)
            finally:
                health_check_task.cancel()
                try:
                    await health_check_task
                except asyncio.CancelledError:
                    pass
                
        except Exception as e:
            self.logger.error(f"服务启动失败: {e}", exc_info=True)
            raise
    
    async def run_once_analysis(self, target_date: Optional[date] = None):
        """执行一次性分析任务"""
        try:
            self.logger.info(f"开始执行一次性分析任务，目标日期: {target_date or '今天'}")
            
            # 初始化分析器
            analyzer = DailyAnalyzer(self.config)
            
            # 执行分析
            result = await analyzer.run_daily_analysis(target_date)
            
            if result.get('success'):
                self.logger.info("✅ 一次性分析任务执行成功")
                self.logger.info(f"分析结果: {result.get('summary', 'N/A')}")
            else:
                self.logger.error(f"❌ 一次性分析任务执行失败: {result.get('error', 'Unknown error')}")
                
            return result
            
        except Exception as e:
            self.logger.error(f"一次性分析任务执行出错: {e}", exc_info=True)
            return {'success': False, 'error': str(e)}
    
    async def run_once_content_check(self, target_date: Optional[date] = None):
        """执行一次性内容检查任务"""
        try:
            self.logger.info(f"开始执行一次性内容检查任务，目标日期: {target_date or '今天'}")
            
            # 初始化内容检查器
            content_checker = DailyContentChecker(self.config)
            
            # 执行内容检查
            result = await content_checker.check_daily_content(target_date)
            
            if result.get('success'):
                self.logger.info("✅ 一次性内容检查任务执行成功")
                self.logger.info(f"检查结果: {result.get('summary', 'N/A')}")
            else:
                self.logger.error(f"❌ 一次性内容检查任务执行失败: {result.get('error', 'Unknown error')}")
                
            return result
            
        except Exception as e:
            self.logger.error(f"一次性内容检查任务执行出错: {e}", exc_info=True)
            return {'success': False, 'error': str(e)}
            
    async def stop(self):
        """停止服务"""
        self.logger.info("正在停止服务...")
        self.running = False
        
        if self.scheduler:
            try:
                # 优雅关闭调度器，等待正在运行的任务完成
                await asyncio.wait_for(self.scheduler.stop(), timeout=60)
                self.logger.info("调度器已优雅停止")
            except asyncio.TimeoutError:
                self.logger.warning("调度器停止超时，强制关闭")
            except Exception as e:
                self.logger.error(f"停止调度器时出错: {e}")
            
        self.logger.info("服务已停止")
        
    def handle_signal(self, signum, frame):
        """处理系统信号"""
        self.logger.info(f"接收到信号 {signum}，准备停止服务...")
        asyncio.create_task(self.stop())
        
    def _validate_config(self):
        """验证配置项"""
        try:
            # 验证基础配置
            if not self.config.github.organization:
                raise ValueError("GitHub组织名称未配置")
            if not self.config.github.discussion_category:
                raise ValueError("Discussion分类未配置")
                
            # 验证调度器配置
            if not self.config.scheduler.cron_expression:
                raise ValueError("调度器Cron表达式未配置")
                
            # 验证内容检查配置
            if hasattr(self.config, 'daily_content_check') and self.config.daily_content_check.enabled:
                if not self.config.daily_content_check.content_check_cron:
                    raise ValueError("内容检查Cron表达式未配置")
                if not self.config.daily_content_check.analysis_cron:
                    raise ValueError("日常分析Cron表达式未配置")
                    
            self.logger.info("配置验证通过")
            
        except Exception as e:
            self.logger.error(f"配置验证失败: {e}")
            raise
            
    async def _display_service_status(self):
        """显示服务状态信息"""
        try:
            status = await self.scheduler.get_status()
            
            self.logger.info("=" * 60)
            self.logger.info("📊 GitHub Discussions 自动化分析服务已启动")
            self.logger.info("=" * 60)
            self.logger.info(f"🏢 目标GitHub组织: {self.config.github.organization}")
            self.logger.info(f"📁 目标仓库: {self.config.github.repository or '组织级别'}")
            self.logger.info(f"📂 Discussion分类: {self.config.github.discussion_category}")
            self.logger.info(f"🌍 时区设置: {self.config.scheduler.timezone}")
            
            if status.get('content_check_enabled'):
                self.logger.info(f"🔍 内容检查时间: {status.get('next_content_check_time', 'N/A')}")
            if status.get('analysis_enabled'):
                self.logger.info(f"📈 日常分析时间: {status.get('next_analysis_time', 'N/A')}")
            if status.get('weekly_report_enabled'):
                self.logger.info("📋 周报功能: 已启用 (每周五17:00)")
                
            self.logger.info(f"🔄 重试配置: {self.config.scheduler.retry_attempts}次重试，间隔{self.config.scheduler.retry_delay}秒")
            self.logger.info("=" * 60)
            
        except Exception as e:
            self.logger.error(f"显示服务状态失败: {e}")
            
    async def _health_check_loop(self):
        """健康检查循环"""
        check_interval = 300  # 5分钟检查一次
        
        while self.running:
            try:
                await asyncio.sleep(check_interval)
                
                if not self.running:
                    break
                    
                # 检查调度器状态
                if self.scheduler:
                    status = await self.scheduler.get_status()
                    if not status.get('running'):
                        self.logger.warning("⚠️ 调度器状态异常，尝试重启...")
                        try:
                            await self.scheduler.start()
                            self.logger.info("✅ 调度器重启成功")
                        except Exception as e:
                            self.logger.error(f"❌ 调度器重启失败: {e}")
                else:
                    self.logger.warning("⚠️ 调度器实例不存在")
                    
            except asyncio.CancelledError:
                break
            except Exception as e:
                self.logger.error(f"健康检查出错: {e}")


def parse_arguments():
    """解析命令行参数"""
    parser = argparse.ArgumentParser(
        description="GitHub Discussions 自动化分析服务",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
示例用法:
  python src/main_enhanced.py                    # 启动定时服务
  python src/main_enhanced.py --run-once         # 执行一次分析任务
  python src/main_enhanced.py --content-check    # 执行一次内容检查
  python src/main_enhanced.py --date 2025-01-25  # 分析指定日期
        """
    )
    
    parser.add_argument(
        '--run-once',
        action='store_true',
        help='执行一次分析任务后退出（不启动定时服务）'
    )
    
    parser.add_argument(
        '--content-check',
        action='store_true',
        help='执行一次内容检查任务后退出'
    )
    
    parser.add_argument(
        '--date',
        type=str,
        help='指定分析日期（格式：YYYY-MM-DD），默认为今天'
    )
    
    parser.add_argument(
        '--log-level',
        choices=['DEBUG', 'INFO', 'WARNING', 'ERROR'],
        default='INFO',
        help='设置日志级别'
    )
    
    parser.add_argument(
        '--config',
        type=str,
        help='指定配置文件路径'
    )
    
    return parser.parse_args()


async def main():
    """主函数"""
    # 解析命令行参数
    args = parse_arguments()
    
    # 设置日志
    setup_logging(level=args.log_level)
    logger = logging.getLogger(__name__)
    
    # 解析目标日期
    target_date = None
    if args.date:
        try:
            target_date = datetime.strptime(args.date, '%Y-%m-%d').date()
            logger.info(f"目标分析日期: {target_date}")
        except ValueError:
            logger.error(f"无效的日期格式: {args.date}，请使用 YYYY-MM-DD 格式")
            sys.exit(1)
    
    try:
        # 创建服务实例
        service = AnalysisService()
        
        # 根据参数决定执行模式
        if args.run_once:
            logger.info("🚀 执行一次性分析任务模式")
            result = await service.run_once_analysis(target_date)
            sys.exit(0 if result.get('success') else 1)
            
        elif args.content_check:
            logger.info("🔍 执行一次性内容检查模式")
            result = await service.run_once_content_check(target_date)
            sys.exit(0 if result.get('success') else 1)
            
        else:
            logger.info("⏰ 启动定时服务模式")
            # 注册信号处理器
            signal.signal(signal.SIGINT, service.handle_signal)
            signal.signal(signal.SIGTERM, service.handle_signal)
            
            # 启动服务
            await service.start()
        
    except KeyboardInterrupt:
        logger.info("接收到键盘中断信号")
    except Exception as e:
        logger.error(f"服务运行出错: {e}", exc_info=True)
        sys.exit(1)


if __name__ == "__main__":
    # 运行主程序
    asyncio.run(main())