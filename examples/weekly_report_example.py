#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
周报汇总功能使用示例

本示例展示如何使用周报汇总功能：
1. 手动触发周报生成
2. 查看周报内容
3. 发送周报到飞书
"""

import asyncio
import sys
from pathlib import Path
from datetime import datetime, timedelta

# 添加项目根目录到路径
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from src.weekly_summarizer import WeeklyReportSummarizer
from src.report_generator import ReportGenerator
from src.clients.feishu_client import FeishuClient
from src.storage.json_data_manager import JSONDataManager
from src.utils.config_manager import ConfigManager


async def main():
    """主函数"""
    print("📊 周报汇总功能演示")
    print("=" * 50)
    
    try:
        # 1. 初始化组件
        print("\n🔧 初始化组件...")
        config_manager = ConfigManager()
        data_manager = JSONDataManager(config_manager)
        
        # 初始化周报汇总器
        summarizer = WeeklyReportSummarizer(data_manager)
        
        # 初始化报告生成器
        report_generator = ReportGenerator(config_manager)
        
        # 初始化飞书客户端（如果配置了的话）
        feishu_client = None
        try:
            feishu_client = FeishuClient(config_manager)
            print("✅ 飞书客户端初始化成功")
        except Exception as e:
            print(f"⚠️ 飞书客户端初始化失败: {e}")
        
        # 2. 生成周报汇总
        print("\n📈 生成周报汇总...")
        
        # 计算本周的日期范围
        today = datetime.now()
        start_of_week = today - timedelta(days=today.weekday())
        end_of_week = start_of_week + timedelta(days=6)
        
        print(f"汇总期间: {start_of_week.strftime('%Y-%m-%d')} 至 {end_of_week.strftime('%Y-%m-%d')}")
        
        # 执行周报汇总
        summary_record = await summarizer.process_weekly_summary(
            start_date=start_of_week.strftime('%Y-%m-%d'),
            end_date=end_of_week.strftime('%Y-%m-%d')
        )
        
        if summary_record:
            print(f"✅ 周报汇总完成")
            print(f"   - 汇总ID: {summary_record.week_id}")
            print(f"   - 用户数量: {summary_record.user_count}")
            print(f"   - 报告数量: {summary_record.total_reports}")
            print(f"   - 状态: {summary_record.status}")
        else:
            print("❌ 周报汇总失败")
            return
        
        # 3. 生成员工版周报
        print("\n📝 生成员工版周报...")
        employee_report = await report_generator.generate_weekly_report(
            week_id=summary_record.week_id,
            report_type="employee"
        )
        
        if employee_report:
            print("✅ 员工版周报生成成功")
            print("\n📄 员工版周报内容预览:")
            print("-" * 40)
            # 显示前500个字符
            preview = employee_report[:500] + "..." if len(employee_report) > 500 else employee_report
            print(preview)
            print("-" * 40)
        else:
            print("❌ 员工版周报生成失败")
        
        # 4. 生成管理版周报
        print("\n📊 生成管理版周报...")
        management_report = await report_generator.generate_weekly_report(
            week_id=summary_record.week_id,
            report_type="management"
        )
        
        if management_report:
            print("✅ 管理版周报生成成功")
            print("\n📄 管理版周报内容预览:")
            print("-" * 40)
            # 显示前500个字符
            preview = management_report[:500] + "..." if len(management_report) > 500 else management_report
            print(preview)
            print("-" * 40)
        else:
            print("❌ 管理版周报生成失败")
        
        # 5. 发送周报（如果配置了飞书）
        if feishu_client and employee_report:
            print("\n📤 发送周报到飞书...")
            
            # 发送员工版周报到群聊
            if feishu_client.send_weekly_report(employee_report, "employee"):
                print("✅ 员工版周报发送成功")
            else:
                print("❌ 员工版周报发送失败")
            
            # 发送管理版周报给管理层
            if management_report and feishu_client.send_weekly_report(management_report, "management"):
                print("✅ 管理版周报发送成功")
            else:
                print("❌ 管理版周报发送失败")
        else:
            print("\n⚠️ 跳过飞书发送（未配置或无报告内容）")
        
        print("\n🎉 周报汇总演示完成！")
        
    except Exception as e:
        print(f"\n❌ 演示过程中发生错误: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    asyncio.run(main())