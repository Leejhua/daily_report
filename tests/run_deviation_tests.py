#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
偏离检测测试运行器

这个脚本整合了所有偏离检测测试组件，提供简单的命令行接口来运行测试。

使用方法:
    python run_deviation_tests.py --all                    # 运行所有测试
    python run_deviation_tests.py --quick                  # 快速测试
    python run_deviation_tests.py --scenario excellent     # 测试特定场景
    python run_deviation_tests.py --generate-data          # 只生成测试数据
    python run_deviation_tests.py --report-only            # 只生成报告
"""

import argparse
import sys
import os
from pathlib import Path
from datetime import datetime
import json

# 添加项目根目录到路径
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from tests.mock_data_generator import MockDataGenerator
from tests.test_deviation_detection import DeviationTestRunner
from tests.batch_test_runner import BatchTestRunner
from tests.test_report_generator import TestReportGenerator

class DeviationTestSuite:
    """偏离检测测试套件"""
    
    def __init__(self):
        self.test_dir = Path(__file__).parent
        self.output_dir = self.test_dir / "output"
        self.output_dir.mkdir(exist_ok=True)
        
        # 初始化组件
        self.data_generator = MockDataGenerator()
        self.test_runner = DeviationTestRunner()
        self.batch_runner = BatchTestRunner()
        self.report_generator = TestReportGenerator()
        
    def generate_test_data(self, count=50):
        """生成测试数据"""
        print(f"🔄 生成 {count} 条测试数据...")
        
        # 生成不同场景的数据
        scenarios = ['excellent', 'good', 'moderate', 'significant', 'severe']
        data_per_scenario = count // len(scenarios)
        
        all_data = []
        for scenario in scenarios:
            for i in range(data_per_scenario):
                result = self.data_generator.generate_single_result(
                    scenario_type=scenario,
                    user_id=f"test_user_{i}"
                )
                all_data.append(result.to_dict())
            print(f"  ✅ {scenario}: {data_per_scenario} 条数据")
        
        # 保存数据
        data_file = self.output_dir / "test_data.json"
        with open(data_file, 'w', encoding='utf-8') as f:
            json.dump(all_data, f, ensure_ascii=False, indent=2, default=str)
        
        print(f"📁 测试数据已保存到: {data_file}")
        return all_data
    
    def run_quick_test(self):
        """运行快速测试"""
        print("🚀 运行快速测试...")
        
        # 生成少量测试数据
        test_data = self.generate_test_data(count=20)
        
        # 运行基础测试
        results = self.test_runner.run_comprehensive_test()
        
        # 生成简单报告
        self._print_quick_results(results)
        
        return results
    
    def run_full_test(self):
        """运行完整测试"""
        print("🔥 运行完整测试套件...")
        
        # 生成完整测试数据
        test_data = self.generate_test_data(count=100)
        
        # 运行批量测试
        batch_results = self.batch_runner.run_all_tests(test_data)
        
        # 生成详细报告
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        
        # HTML报告
        html_file = self.output_dir / f"test_report_{timestamp}.html"
        self.report_generator.generate_html_report(batch_results, str(html_file))
        
        # JSON报告
        json_file = self.output_dir / f"test_results_{timestamp}.json"
        self.report_generator.generate_json_report(batch_results, str(json_file))
        
        # Markdown报告
        md_file = self.output_dir / f"test_summary_{timestamp}.md"
        self.report_generator.generate_markdown_report(batch_results, str(md_file))
        
        print(f"📊 详细报告已生成:")
        print(f"  - HTML: {html_file}")
        print(f"  - JSON: {json_file}")
        print(f"  - Markdown: {md_file}")
        
        # 打印摘要
        self._print_test_summary(batch_results)
        
        return batch_results
    
    def run_scenario_test(self, scenario):
        """运行特定场景测试"""
        print(f"🎯 运行 {scenario} 场景测试...")
        
        # 生成特定场景数据
        test_data = []
        for i in range(20):
            result = self.data_generator.generate_single_result(
                scenario_type=scenario,
                user_id=f"test_user_{i}"
            )
            test_data.append(result.to_dict())
        
        # 运行测试
        results = self.test_runner.run_comprehensive_test()
        
        # 打印结果
        self._print_scenario_results(scenario, results)
        
        return results
    
    def _print_quick_results(self, results):
        """打印快速测试结果"""
        print("\n📊 测试结果:")
        
        test_exec = results.get('test_execution', {})
        print(f"  总测试数: {test_exec.get('tests_run', 0)}")
        print(f"  失败数: {test_exec.get('failures', 0)}")
        print(f"  错误数: {test_exec.get('errors', 0)}")
        print(f"  成功率: {test_exec.get('success_rate', 0):.1%}")
        
        dataset_info = results.get('dataset_info', {})
        print("\n📈 数据集信息:")
        print(f"  场景数: {dataset_info.get('scenarios', 0)}")
        print(f"  单个结果: {dataset_info.get('single_results', 0)}")
        print(f"  连续偏离案例: {dataset_info.get('continuous_deviation_cases', 0)}")
        print(f"  模式变化案例: {dataset_info.get('pattern_change_cases', 0)}")
        print(f"  用户时间线: {dataset_info.get('user_timelines', 0)}")
        
        scenario_coverage = results.get('scenario_coverage', [])
        if scenario_coverage:
            print(f"\n🎯 场景覆盖: {', '.join(scenario_coverage)}")
        
        print("\n✅ 快速测试完成!")
    
    def _print_test_summary(self, batch_results):
        """打印测试摘要"""
        print("\n📊 测试摘要:")
        
        # batch_results 是 BatchTestSummary 对象
        print(f"  总测试数: {batch_results.total_tests}")
        print(f"  通过数: {batch_results.passed_tests}")
        print(f"  失败数: {batch_results.failed_tests}")
        print(f"  成功率: {batch_results.success_rate:.1%}")
        print(f"  总执行时间: {batch_results.total_execution_time:.2f}秒")
        print(f"  平均执行时间: {batch_results.average_execution_time:.3f}秒")
        
        # 预警统计
        if batch_results.alert_statistics:
            print("\n🚨 预警统计:")
            for alert_type, count in batch_results.alert_statistics.items():
                print(f"  {alert_type}: {count}")
        
        # 场景统计
        if batch_results.scenario_statistics:
            print("\n📈 场景统计:")
            for scenario, stats in batch_results.scenario_statistics.items():
                passed = stats.get('passed', 0)
                total = stats.get('total', 0)
                print(f"  {scenario}: {passed}/{total} 通过")
        
        print("\n✅ 完整测试完成!")
    
    def _print_scenario_results(self, scenario, results):
        """打印场景测试结果"""
        print(f"\n📋 {scenario} 场景测试结果:")
        print(f"  测试数据: {results['total_tests']} 条")
        print(f"  检测准确率: {results['success_rate']:.1f}%")
        
        # 显示偏离度分布
        if 'deviation_distribution' in results:
            print("\n📊 偏离度分布:")
            for level, count in results['deviation_distribution'].items():
                print(f"  {level}: {count} 条")

def main():
    """主函数"""
    parser = argparse.ArgumentParser(description='偏离检测测试运行器')
    parser.add_argument('--all', action='store_true', help='运行所有测试')
    parser.add_argument('--quick', action='store_true', help='运行快速测试')
    parser.add_argument('--scenario', choices=['excellent', 'good', 'average', 'significant', 'severe'], 
                       help='运行特定场景测试')
    parser.add_argument('--generate-data', action='store_true', help='只生成测试数据')
    parser.add_argument('--count', type=int, default=50, help='生成数据数量')
    
    args = parser.parse_args()
    
    # 创建测试套件
    test_suite = DeviationTestSuite()
    
    print("🧪 偏离检测测试套件")
    print("=" * 50)
    
    try:
        if args.generate_data:
            test_suite.generate_test_data(count=args.count)
        elif args.quick:
            test_suite.run_quick_test()
        elif args.scenario:
            test_suite.run_scenario_test(args.scenario)
        elif args.all:
            test_suite.run_full_test()
        else:
            # 默认运行快速测试
            print("💡 未指定测试类型，运行快速测试...")
            test_suite.run_quick_test()
            
        print("\n✅ 测试完成!")
        
    except Exception as e:
        print(f"\n❌ 测试过程中出现错误: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)

if __name__ == "__main__":
    main()