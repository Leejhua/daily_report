#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
李嘉华偏离检测测试脚本

这个脚本专门用于测试李嘉华连续三天会议偏离的情况，
加载模拟数据并运行偏离检测和通知系统。
"""

import asyncio
import json
import sys
from datetime import datetime
from pathlib import Path

# 添加项目根目录到Python路径
sys.path.append(str(Path(__file__).parent))

# 导入必要的模块
from src.models.data_models import DeviationAnalysisResult
from src.trackers.deviation_tracker import DeviationTracker
from src.schedulers.notification_scheduler import NotificationScheduler
from src.storage.json_data_manager import JSONDataManager
import yaml

class LeejhuaDeviationTest:
    """李嘉华偏离测试类"""
    
    def __init__(self):
        self.config = self.load_config()
        self.data_manager = JSONDataManager()
        self.deviation_tracker = DeviationTracker(self.data_manager, self.config)
        self.notification_scheduler = NotificationScheduler(self.config, use_llm_reports=True)
        
    def load_config(self):
        """加载配置文件"""
        config_path = Path("config/config.yaml")
        if not config_path.exists():
            raise FileNotFoundError(f"配置文件不存在: {config_path}")
        
        with open(config_path, 'r', encoding='utf-8') as f:
            return yaml.safe_load(f)
    
    def load_mock_data(self):
        """加载模拟数据"""
        data_file = Path("data/mock_leejhua_deviation_data.json")
        if not data_file.exists():
            raise FileNotFoundError(f"模拟数据文件不存在: {data_file}")
        
        with open(data_file, 'r', encoding='utf-8') as f:
            data = json.load(f)
        
        print(f"✅ 成功加载模拟数据: {len(data['analysis_results'])} 条偏离分析结果")
        return data
    
    def convert_to_analysis_results(self, mock_data):
        """将模拟数据转换为DeviationAnalysisResult对象"""
        results = []
        
        for result_data in mock_data['analysis_results']:
            # 创建DeviationAnalysisResult对象
            result = DeviationAnalysisResult(
                score=result_data['score'],
                completion_rate=result_data['completion_rate'],
                deviation_reasons=result_data['deviation_reasons'],
                additional_work=result_data.get('additional_work', []),
                suggestions=result_data.get('suggestions', []),
                summary=result_data.get('summary', ''),
                confidence=result_data.get('confidence', 0.0),
                user_id=result_data['user_id'],
                analysis_date=result_data['analysis_date'],
                discussion_number=result_data['discussion_number'],
                is_deviation=result_data['is_deviation'],
                raw_analysis_text=result_data.get('raw_analysis_text', '')
            )
            
            # 添加额外字段
            if 'additional_work' in result_data:
                result.additional_work = result_data['additional_work']
            if 'suggestions' in result_data:
                result.suggestions = result_data['suggestions']
            if 'summary' in result_data:
                result.summary = result_data['summary']
            
            results.append(result)
        
        print(f"✅ 转换了 {len(results)} 个分析结果对象")
        return results
    
    async def process_deviation_results(self, analysis_results):
        """处理偏离分析结果"""
        print("\n🔄 开始处理偏离分析结果...")
        
        # 清空之前的预警
        self.deviation_tracker.alerts.clear()
        
        # 按日期顺序处理每个分析结果
        for result in sorted(analysis_results, key=lambda x: x.analysis_date):
            print(f"\n📅 处理日期: {result.analysis_date}")
            print(f"   用户: {result.user_id}")
            print(f"   偏离分数: {result.score}")
            print(f"   完成率: {result.completion_rate:.1%}")
            print(f"   是否偏离: {'是' if result.is_deviation else '否'}")
            
            # 记录分析结果到偏离跟踪器
            success = self.deviation_tracker.record_analysis_result(result)
            
            if success:
                print("   ✅ 分析结果记录成功")
            else:
                print("   ❌ 分析结果记录失败")
        
        # 获取所有触发的预警
        alerts = self.deviation_tracker.alerts.copy()
        
        print(f"\n📊 处理完成，共触发 {len(alerts)} 个预警")
        
        if alerts:
            print("\n🚨 触发的预警:")
            for i, alert in enumerate(alerts, 1):
                print(f"   {i}. {alert.alert_type} - {alert.user_id} ({alert.severity})")
        
        return alerts
    
    async def send_notifications(self, alerts):
        """发送通知"""
        if not alerts:
            print("\n📭 没有预警需要发送通知")
            return
        
        print(f"\n📤 开始发送 {len(alerts)} 个预警通知...")
        
        for i, alert in enumerate(alerts, 1):
            print(f"\n📧 发送第 {i} 个通知:")
            print(f"   预警类型: {alert.alert_type}")
            print(f"   用户: {alert.user_id}")
            print(f"   严重程度: {alert.severity}")
            print(f"   创建时间: {alert.created_at}")
            print(f"   消息: {alert.message}")
            
            try:
                # 构造偏离信息
                deviation_info = {
                    'user': alert.user_id,
                    'consecutive_days': 3,  # 连续3天偏离
                    'deviation_type': 'meeting_interference',
                    'severity': alert.severity,
                    'latest_score': 7.8,
                    'trend': 'increasing'
                }
                
                # 生成报告
                report_result = {
                    'success': True,
                    'content': f"用户 {alert.user_id} 连续3天因会议导致工作偏离，偏离分数: 7.8",
                    'data': deviation_info
                }
                
                # 发送飞书通知
                success = self.notification_scheduler._send_feishu_notification(
                    alert.user_id, 
                    report_result,
                    deviation_info
                )
                if success:
                    print("   ✅ 个人通知发送成功")
                else:
                    print("   ❌ 个人通知发送失败")
                
                # 如果是严重偏离，发送管理层通知
                if alert.severity == 'high':
                    # 管理层通知已在_send_feishu_notification中处理
                    print("   ✅ 管理层通知已包含在飞书通知中")
                
            except Exception as e:
                print(f"   ❌ 通知发送失败: {str(e)}")
    
    async def run_test(self):
        """运行完整测试"""
        print("🚀 开始李嘉华偏离检测测试")
        print(f"测试时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        print("=" * 60)
        
        try:
            # 1. 加载模拟数据
            print("\n📂 步骤1: 加载模拟数据")
            mock_data = self.load_mock_data()
            
            # 2. 转换为分析结果对象
            print("\n🔄 步骤2: 转换数据格式")
            analysis_results = self.convert_to_analysis_results(mock_data)
            
            # 3. 处理偏离分析结果
            print("\n🔍 步骤3: 处理偏离分析")
            alerts = await self.process_deviation_results(analysis_results)
            
            # 4. 发送通知
            print("\n📤 步骤4: 发送通知")
            await self.send_notifications(alerts)
            
            # 5. 输出测试结果
            print("\n📊 测试结果汇总:")
            print(f"   处理的分析结果: {len(analysis_results)} 条")
            print(f"   触发的预警: {len(alerts)} 个")
            
            if alerts:
                print("\n🚨 预警详情:")
                for alert in alerts:
                    print(f"   - {alert.alert_type}: {alert.user_id} ({alert.severity})")
            
            print("\n✅ 测试完成!")
            
        except Exception as e:
            print(f"\n❌ 测试失败: {str(e)}")
            import traceback
            traceback.print_exc()
            raise

async def main():
    """主函数"""
    test = LeejhuaDeviationTest()
    await test.run_test()

if __name__ == "__main__":
    # 运行测试
    asyncio.run(main())