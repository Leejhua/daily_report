"""
定时任务调度器模块
负责定时执行分析任务
"""

import asyncio
import logging
import signal
from datetime import datetime, timezone
from typing import Optional, Callable, Any
from contextlib import asynccontextmanager

import schedule
import pytz
from croniter import croniter

from src.config import Config
from src.analyzers.daily_analyzer import DailyAnalyzer
from src.utils.logger import get_logger


class AnalysisScheduler:
    """分析任务调度器"""
    
    def __init__(self, config: Config):
        self.config = config
        self.logger = get_logger(__name__)
        self.analyzer = DailyAnalyzer(config)
        self.running = False
        self.current_task = None
        self.timezone = pytz.timezone(config.scheduler.timezone)
        
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
        """获取下次执行时间"""
        cron = croniter(self.config.scheduler.cron_expression, datetime.now(self.timezone))
        return cron.get_next(datetime)
        
    async def _run_scheduler(self):
        """运行调度循环"""
        while self.running:
            try:
                # 计算下次执行时间
                next_run = self._get_next_run_time()
                now = datetime.now(self.timezone)
                
                # 计算等待时间
                wait_seconds = (next_run - now).total_seconds()
                
                if wait_seconds > 0:
                    self.logger.debug(f"等待 {wait_seconds:.1f} 秒后执行下次任务")
                    await asyncio.sleep(min(wait_seconds, 60))  # 最多等待60秒，然后重新计算
                    continue
                    
                # 执行任务
                if self._should_run_now():
                    await self._execute_analysis_task()
                    
                    # 等待至少1分钟，避免重复执行
                    await asyncio.sleep(60)
                    
            except Exception as e:
                self.logger.error(f"调度循环出错: {e}")
                await asyncio.sleep(60)  # 出错后等待1分钟再继续
                
    def _should_run_now(self) -> bool:
        """检查当前时间是否应该执行任务"""
        cron = croniter(self.config.scheduler.cron_expression)
        now = datetime.now(self.timezone)
        
        # 检查当前时间是否匹配Cron表达式
        # 允许1分钟的误差
        for i in range(2):  # 检查当前分钟和前一分钟
            check_time = now.replace(second=0, microsecond=0)
            if i > 0:
                check_time = check_time.replace(minute=check_time.minute - 1)
                
            if cron.match(check_time):
                return True
                
        return False
        
    async def _execute_analysis_task(self):
        """执行分析任务"""
        task_start_time = datetime.now(self.timezone)
        self.logger.info(f"开始执行定时分析任务: {task_start_time}")
        
        try:
            # 创建任务
            self.current_task = asyncio.create_task(
                self._run_analysis_with_timeout()
            )
            
            # 执行任务
            await self.current_task
            
            duration = (datetime.now(self.timezone) - task_start_time).total_seconds()
            self.logger.info(f"分析任务执行完成，耗时: {duration:.1f}秒")
            
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
                self.analyzer.run_daily_analysis(),
                timeout=self.config.scheduler.max_execution_time
            )
        except asyncio.TimeoutError:
            self.logger.error(f"分析任务超时（{self.config.scheduler.max_execution_time}秒）")
            raise
            
    async def run_once(self):
        """手动执行一次分析任务（用于测试）"""
        self.logger.info("手动执行分析任务...")
        await self._execute_analysis_task()
        
    async def get_status(self) -> dict:
        """获取调度器状态"""
        try:
            next_run_time = self._get_next_run_time().isoformat()
        except Exception as e:
            self.logger.error(f"计算下次执行时间失败: {e}")
            next_run_time = None
            
        status = {
            'running': self.running,
            'cron_expression': self.config.scheduler.cron_expression,
            'timezone': self.config.scheduler.timezone,
            'next_run_time': next_run_time,
            'current_task_running': self.current_task is not None and not self.current_task.done(),
            'last_run_time': None  # 可以添加上次运行时间的记录
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
