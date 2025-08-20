#!/usr/bin/env python3
"""
GitHub Discussions 自动化分析服务主程序
基于GLM-4.5模型的内容分析和自动评论系统
"""

import asyncio
import sys
import signal
import logging
from pathlib import Path

# 添加项目根目录到Python路径
sys.path.append(str(Path(__file__).parent.parent))

from src.config import Config
from src.scheduler import AnalysisScheduler
from src.utils.logger import setup_logging


class AnalysisService:
    """主服务类"""
    
    def __init__(self):
        self.config = Config()
        self.scheduler = None
        self.logger = logging.getLogger(__name__)
        self.running = False
        
    async def start(self):
        """启动服务"""
        try:
            self.logger.info("正在启动GitHub Discussions自动化分析服务...")
            
            # 初始化调度器
            # self.scheduler = AnalysisScheduler(self.config)
            
            # 启动调度器
            # await self.scheduler.start()
            self.running = True
            
            self.logger.info("⚠️ 定时功能已禁用，服务以手动模式运行")
            # self.logger.info(f"服务启动成功，调度时间: {self.config.scheduler.cron_expression}")
            self.logger.info(f"目标GitHub组织: {self.config.github.organization}")
            self.logger.info(f"目标仓库: {self.config.github.repository}")
            self.logger.info(f"Discussion分类: {self.config.github.discussion_category}")
            self.logger.info("💡 如需执行分析，请使用测试脚本手动触发")
            
            # 保持服务运行
            while self.running:
                await asyncio.sleep(1)
                
        except Exception as e:
            self.logger.error(f"服务启动失败: {e}", exc_info=True)
            raise
            
    async def stop(self):
        """停止服务"""
        self.logger.info("正在停止服务...")
        self.running = False
        
        # if self.scheduler:
        #     await self.scheduler.stop()
            
        self.logger.info("服务已停止")
        
    def handle_signal(self, signum, frame):
        """处理系统信号"""
        self.logger.info(f"接收到信号 {signum}，准备停止服务...")
        asyncio.create_task(self.stop())


async def main():
    """主函数"""
    # 设置日志
    setup_logging()
    logger = logging.getLogger(__name__)
    
    try:
        # 创建服务实例
        service = AnalysisService()
        
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
