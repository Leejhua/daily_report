"""
定时任务调度器模块
负责定时执行分析任务
"""

import logging
import time
from datetime import datetime, timedelta
from croniter import croniter
from typing import Optional
import threading
import signal
import sys
import asyncio
import pytz
from contextlib import asynccontextmanager

from src.analyzers.daily_analyzer import DailyAnalyzer
from src.weekly_summarizer import WeeklyReportSummarizer
from src.checkers.daily_content_checker import DailyContentChecker
from src.config import Config
from src.utils.logger import get_logger


class AnalysisScheduler:
    """分析任务调度器"""
    
    def __init__(self, config: Config):
        self.config = config
        self.logger = get_logger(__name__)
        self.running = False
        self.thread = None
        
        # 初始化分析器、内容检查器和周报汇总器
        self.daily_analyzer = DailyAnalyzer(config)
        self.daily_content_checker = DailyContentChecker(config)
        
        # 初始化数据管理器和周报汇总器
        from src.storage.json_data_manager import JSONDataManager
        data_manager = JSONDataManager(data_dir='data')
        self.weekly_summarizer = WeeklyReportSummarizer(data_manager)
        
        # 初始化时区
        self.timezone = pytz.timezone(self.config.scheduler.timezone)
        
        # 当前任务引用
        self.current_task = None
        
        # 设置信号处理器
        signal.signal(signal.SIGINT, self._signal_handler)
        signal.signal(signal.SIGTERM, self._signal_handler)
        
    def _signal_handler(self, signum, frame):
        """信号处理器"""
        self.logger.info(f"收到信号 {signum}，正在停止调度器...")
        self.running = False
        if self.current_task and not self.current_task.done():
            self.current_task.cancel()
        
    async def start(self):
        """启动调度器"""
        self.logger.info("正在启动分析任务调度器...")
        
        try:
            # 验证Cron表达式
            self._validate_cron_expression()
            
            # 设置调度任务
            self._setup_schedule()
            
            self.running = True
            self.logger.info(f"调度器启动成功，下次执行时间: {self._get_next_run_time()}")
            
            # 启动调度循环
            await self._run_scheduler()
            
        except Exception as e:
            self.logger.error(f"调度器启动失败: {e}")
            raise
            
    async def stop(self):
        """停止调度器"""
        self.logger.info("正在停止调度器...")
        self.running = False
        
        # 如果有正在运行的任务，等待其完成
        if self.current_task and not self.current_task.done():
            self.logger.info("等待当前任务完成...")
            try:
                await asyncio.wait_for(self.current_task, timeout=30)
            except asyncio.TimeoutError:
                self.logger.warning("任务超时，强制取消")
                self.current_task.cancel()
                
        self.logger.info("调度器已停止")
        
    def _validate_cron_expression(self):
        """验证Cron表达式的有效性"""
        try:
            cron = croniter(self.config.scheduler.cron_expression)
            next_time = cron.get_next(datetime)
            self.logger.debug(f"Cron表达式验证成功，下次执行时间: {next_time}")
        except Exception as e:
            raise ValueError(f"无效的Cron表达式 '{self.config.scheduler.cron_expression}': {e}")
            
    def _setup_schedule(self):
        """设置调度任务"""
        # 解析Cron表达式
        cron = croniter(self.config.scheduler.cron_expression)
        
        # 由于schedule库不直接支持Cron，我们使用自定义调度逻辑
        self.logger.info(f"设置定时任务: {self.config.scheduler.cron_expression}")
        
    def _get_next_run_time(self) -> datetime:
        """获取下次执行时间（基于日常分析的cron表达式）"""
        # 使用配置中的analysis_cron来计算下次运行时间
        current_time = datetime.now(self.timezone)
        return self._get_next_analysis_time(current_time)
        
    async def _run_scheduler(self):
        """运行调度循环"""
        while self.running:
            try:
                now = datetime.now(self.timezone)
                
                # 检查是否应该执行内容检查
                if self._should_run_content_check(now):
                    await self._execute_content_check_task()
                    # 等待1分钟避免重复执行
                    await asyncio.sleep(60)
                    continue
                
                # 检查是否应该执行日常分析
                if self._should_run_task(now):
                    await self._execute_analysis_task()
                    
                    # 检查是否需要执行周报任务
                    if self._should_run_weekly_report():
                        await self._execute_weekly_report_task()
                    
                    # 等待至少1分钟，避免重复执行
                    await asyncio.sleep(60)
                    continue
                    
                # 如果没有任务需要执行，等待30秒后重新检查
                await asyncio.sleep(30)
                    
            except Exception as e:
                self.logger.error(f"调度循环出错: {e}")
                await asyncio.sleep(60)  # 出错后等待1分钟再继续
                

        
    def _should_run_task(self, current_time: datetime) -> bool:
        """检查是否应该运行任务（使用日常分析的cron表达式）"""
        # 使用配置中的analysis_cron来判断是否应该执行任务
        analysis_cron = getattr(self.config.daily_content_check, 'analysis_cron', self.config.scheduler.cron_expression)
        
        # 如果是列表，检查每个时间点
        if isinstance(analysis_cron, list):
            for cron_expr in analysis_cron:
                if self._check_cron_time(cron_expr, current_time):
                    return True
            return False
        else:
            # 单个cron表达式
            return self._check_cron_time(analysis_cron, current_time)
        
    def _should_run_content_check(self, current_time: datetime) -> bool:
        """检查当前时间是否应该执行内容检查任务"""
        if not hasattr(self.config, 'daily_content_check') or not self.config.daily_content_check.enabled:
            return False
            
        # 获取内容检查的cron表达式，支持单个或多个时间点
        content_check_cron = getattr(self.config.daily_content_check, 'content_check_cron', '0 14 * * *')
        
        # 如果是列表，检查每个时间点
        if isinstance(content_check_cron, list):
            for cron_expr in content_check_cron:
                if self._check_cron_time(cron_expr, current_time):
                    return True
            return False
        else:
            # 单个cron表达式
            return self._check_cron_time(content_check_cron, current_time)
    
    def _check_cron_time(self, cron_expr: str, current_time: datetime) -> bool:
        """检查单个cron表达式是否匹配当前时间"""
        try:
            cron = croniter(cron_expr, current_time)
            next_run = cron.get_next(datetime)
            prev_run = cron.get_prev(datetime)
            
            # 检查当前时间是否在预定运行时间的1分钟内
            time_diff = abs((current_time - prev_run).total_seconds())
            return time_diff <= 60
        except Exception as e:
            self.logger.error(f"解析cron表达式失败: {cron_expr}, 错误: {e}")
            return False
    
    def _get_next_content_check_time(self, current_time: datetime) -> datetime:
        """获取下次内容检查时间"""
        content_check_cron = getattr(self.config.daily_content_check, 'content_check_cron', '0 14 * * *')
        
        if isinstance(content_check_cron, list):
            # 如果是多个时间点，找到最近的下次执行时间
            next_times = []
            for cron_expr in content_check_cron:
                try:
                    cron = croniter(cron_expr, current_time)
                    next_times.append(cron.get_next(datetime))
                except Exception as e:
                    self.logger.error(f"解析cron表达式失败: {cron_expr}, 错误: {e}")
            
            if next_times:
                return min(next_times)  # 返回最近的时间
            else:
                # 如果解析失败，返回默认时间（下午2点）
                next_time = current_time.replace(hour=14, minute=0, second=0, microsecond=0)
                if current_time.hour >= 14:
                    next_time += timedelta(days=1)
                return next_time
        else:
            # 单个cron表达式
            try:
                cron = croniter(content_check_cron, current_time)
                return cron.get_next(datetime)
            except Exception as e:
                self.logger.error(f"解析cron表达式失败: {content_check_cron}, 错误: {e}")
                # 返回默认时间
                next_time = current_time.replace(hour=14, minute=0, second=0, microsecond=0)
                if current_time.hour >= 14:
                    next_time += timedelta(days=1)
                return next_time
    
    def _get_next_analysis_time(self, current_time: datetime) -> datetime:
        """获取下次分析时间"""
        analysis_cron = getattr(self.config.daily_content_check, 'analysis_cron', '0 18 * * *')
        
        if isinstance(analysis_cron, list):
            # 如果是多个时间点，找到最近的下次执行时间
            next_times = []
            for cron_expr in analysis_cron:
                try:
                    cron = croniter(cron_expr, current_time)
                    next_times.append(cron.get_next(datetime))
                except Exception as e:
                    self.logger.error(f"解析分析cron表达式失败: {cron_expr}, 错误: {e}")
            
            if next_times:
                return min(next_times)  # 返回最近的时间
            else:
                # 如果解析失败，返回默认时间（下午6点）
                next_time = current_time.replace(hour=18, minute=0, second=0, microsecond=0)
                if current_time.hour >= 18:
                    next_time += timedelta(days=1)
                return next_time
        else:
            # 单个cron表达式
            try:
                cron = croniter(analysis_cron, current_time)
                return cron.get_next(datetime)
            except Exception as e:
                self.logger.error(f"解析分析cron表达式失败: {analysis_cron}, 错误: {e}")
                # 返回默认时间（下午6点）
                next_time = current_time.replace(hour=18, minute=0, second=0, microsecond=0)
                if current_time.hour >= 18:
                    next_time += timedelta(days=1)
                return next_time
        
    async def _execute_content_check_task(self):
        """执行内容检查任务"""
        task_start_time = datetime.now(self.timezone)
        self.logger.info(f"开始执行内容检查任务: {task_start_time}")
        
        try:
            # 执行内容检查
            results = await asyncio.create_task(
                self._run_content_check_with_timeout()
            )
            
            duration = (datetime.now(self.timezone) - task_start_time).total_seconds()
            self.logger.info(f"内容检查任务执行完成，耗时: {duration:.1f}秒")
            
            if results:
                # 统计检查结果
                total_users = len(results)
                users_with_missing = sum(1 for result in results.values() if result.missing_content)
                self.logger.info(f"内容检查结果: 检查了 {total_users} 个用户，{users_with_missing} 个用户有缺失内容")
            
        except asyncio.CancelledError:
            self.logger.warning("内容检查任务被取消")
        except Exception as e:
            self.logger.error(f"内容检查任务执行失败: {e}", exc_info=True)
            
    async def _run_content_check_with_timeout(self):
        """在超时限制内运行内容检查"""
        try:
            timeout = self.config.daily_content_check.max_execution_time
            results = await asyncio.wait_for(
                self.daily_content_checker.check_and_remind_all_users(),
                timeout=timeout
            )
            self.logger.info(f"内容检查任务完成，检查了 {len(results)} 个用户")
            return results
        except asyncio.TimeoutError:
            self.logger.error(f"内容检查任务超时（{timeout}秒）")
            raise
        except Exception as e:
            self.logger.error(f"内容检查任务执行失败: {e}")
            raise
        
    async def _execute_analysis_task(self):
        """执行日常分析任务"""
        task_start_time = datetime.now(self.timezone)
        self.logger.info(f"开始执行日常分析任务: {task_start_time}")
        
        try:
            # 创建任务
            self.current_task = asyncio.create_task(
                self._run_analysis_with_timeout()
            )
            
            # 执行任务
            await self.current_task
            
            duration = (datetime.now(self.timezone) - task_start_time).total_seconds()
            self.logger.info(f"日常分析任务执行完成，耗时: {duration:.1f}秒")
            
        except asyncio.CancelledError:
            self.logger.warning("分析任务被取消")
        except Exception as e:
            self.logger.error(f"分析任务执行失败: {e}", exc_info=True)
        finally:
            self.current_task = None
            
    async def _run_analysis_with_timeout(self):
        """带超时的分析任务执行"""
        try:
            await asyncio.wait_for(
                self.daily_analyzer.run_daily_analysis(),
                timeout=self.config.scheduler.max_execution_time
            )
        except asyncio.TimeoutError:
            self.logger.error(f"分析任务超时（{self.config.scheduler.max_execution_time}秒）")
            raise
            
    async def run_once(self):
        """手动执行一次分析任务（用于测试）"""
        self.logger.info("手动执行分析任务...")
        await self._execute_analysis_task()
        
    async def run_content_check_once(self):
        """手动执行一次内容检查任务（用于测试）"""
        self.logger.info("手动执行内容检查任务...")
        await self._execute_content_check_task()
        
    def _should_run_weekly_report(self) -> bool:
        """检查是否应该执行周报任务（每周五执行）"""
        if not hasattr(self.config, 'weekly_reports') or not self.config.weekly_reports.enabled:
            return False
            
        now = datetime.now(self.timezone)
        # 检查是否是周五（weekday() 返回 0-6，其中 4 是周五）
        if now.weekday() != 4:
            return False
            
        # 检查是否在配置的执行时间范围内
        current_hour = now.hour
        if hasattr(self.config.weekly_reports, 'execution_hour'):
            target_hour = self.config.weekly_reports.execution_hour
            return current_hour == target_hour
        else:
            # 默认在下午5点执行
            return current_hour == 17
            
    async def _execute_weekly_report_task(self):
        """执行周报任务"""
        task_start_time = datetime.now(self.timezone)
        self.logger.info(f"开始执行周报任务: {task_start_time}")
        
        try:
            # 创建周报任务
            weekly_task = asyncio.create_task(
                self._run_weekly_report_with_timeout()
            )
            
            # 执行任务
            await weekly_task
            
            duration = (datetime.now(self.timezone) - task_start_time).total_seconds()
            self.logger.info(f"周报任务执行完成，耗时: {duration:.1f}秒")
            
        except asyncio.CancelledError:
            self.logger.warning("周报任务被取消")
        except Exception as e:
            self.logger.error(f"周报任务执行失败: {e}", exc_info=True)
            
    async def _run_weekly_report_with_timeout(self):
        """带超时的周报任务执行"""
        try:
            timeout = getattr(self.config.scheduler, 'max_execution_time', 300)
            await asyncio.wait_for(
                self.weekly_summarizer.generate_and_send_weekly_reports(),
                timeout=timeout
            )
        except asyncio.TimeoutError:
            self.logger.error(f"周报任务超时（{timeout}秒）")
            raise
            
    async def run_weekly_report_once(self):
        """手动执行一次周报任务（用于测试）"""
        self.logger.info("手动执行周报任务...")
        await self._execute_weekly_report_task()
        
    async def get_status(self) -> dict:
        """获取调度器状态"""
        now = datetime.now(self.timezone)
        
        # 计算下次内容检查时间
        next_content_check = self._get_next_content_check_time(now)
            
        # 计算下次分析时间
        next_analysis = self._get_next_analysis_time(now)
            
        status = {
            'running': self.running,
            'timezone': self.config.scheduler.timezone,
            'cron_expression': self.config.scheduler.cron_expression,
            'next_run_time': self._get_next_run_time().isoformat(),
            'next_content_check_time': next_content_check.isoformat(),
            'next_analysis_time': next_analysis.isoformat(),
            'current_task_running': self.current_task is not None and not self.current_task.done(),
            'content_check_enabled': True,
            'analysis_enabled': True,
            'weekly_report_enabled': hasattr(self.config, 'weekly_reports') and self.config.weekly_reports.enabled
        }
        
        return status
        
    @asynccontextmanager
    async def _task_context(self):
        """任务执行上下文管理器"""
        start_time = datetime.now()
        task_id = f"task_{start_time.strftime('%Y%m%d_%H%M%S')}"
        
        self.logger.info(f"开始执行任务: {task_id}")
        
        try:
            yield task_id
        except Exception as e:
            self.logger.error(f"任务 {task_id} 执行失败: {e}")
            raise
        finally:
            duration = (datetime.now() - start_time).total_seconds()
            self.logger.info(f"任务 {task_id} 执行完成，耗时: {duration:.1f}秒")


class RetryableScheduler(AnalysisScheduler):
    """支持重试的调度器"""
    
    async def _execute_analysis_task(self):
        """带重试的任务执行"""
        task_start_time = datetime.now(self.timezone)
        self.logger.info(f"开始执行定时分析任务: {task_start_time}")
        
        for attempt in range(1, self.config.scheduler.retry_attempts + 1):
            try:
                self.logger.info(f"第 {attempt} 次尝试执行分析任务")
                
                # 创建任务
                self.current_task = asyncio.create_task(
                    self._run_analysis_with_timeout()
                )
                
                # 执行任务
                await self.current_task
                
                duration = (datetime.now(self.timezone) - task_start_time).total_seconds()
                self.logger.info(f"分析任务执行成功，耗时: {duration:.1f}秒")
                
                return  # 成功后退出重试循环
                
            except asyncio.CancelledError:
                self.logger.warning("分析任务被取消")
                break
            except Exception as e:
                self.logger.error(f"第 {attempt} 次尝试失败: {e}")
                
                if attempt < self.config.scheduler.retry_attempts:
                    wait_time = self.config.scheduler.retry_delay
                    self.logger.info(f"等待 {wait_time} 秒后重试...")
                    await asyncio.sleep(wait_time)
                else:
                    self.logger.error("所有重试尝试均失败")
                    
            finally:
                self.current_task = None
                
    async def _execute_content_check_task_with_retry(self):
        """带重试机制的内容检查任务执行"""
        for attempt in range(1, self.config.scheduler.retry_attempts + 1):
            try:
                self.logger.info(f"执行内容检查任务 (尝试 {attempt}/{self.config.scheduler.retry_attempts})")
                await self._execute_content_check_task()
                self.logger.info("内容检查任务执行成功")
                return  # 成功后退出重试循环
                
            except Exception as e:
                self.logger.error(f"内容检查任务执行失败 (尝试 {attempt}/{self.config.scheduler.retry_attempts}): {e}")
                if attempt < self.config.scheduler.retry_attempts:
                    wait_time = self.config.scheduler.retry_delay
                    self.logger.info(f"等待 {wait_time} 秒后重试...")
                    await asyncio.sleep(wait_time)
                else:
                    self.logger.error("内容检查任务所有重试尝试都失败了")
                    raise
                
    async def _execute_weekly_report_task_with_retry(self):
        """带重试机制的周报任务执行"""
        for attempt in range(1, self.config.scheduler.retry_attempts + 1):
            try:
                self.logger.info(f"执行周报任务 (尝试 {attempt}/{self.config.scheduler.retry_attempts})")
                await self._execute_weekly_report_task()
                self.logger.info("周报任务执行成功")
                return  # 成功后退出重试循环
                
            except Exception as e:
                self.logger.error(f"周报任务执行失败 (尝试 {attempt}/{self.config.scheduler.retry_attempts}): {e}")
                if attempt < self.config.scheduler.retry_attempts:
                    wait_time = self.config.scheduler.retry_delay
                    self.logger.info(f"等待 {wait_time} 秒后重试...")
                    await asyncio.sleep(wait_time)
                else:
                    self.logger.error("周报任务所有重试尝试都失败了")
                    raise
