"""批量测试运行器
支持多场景自动化测试和结果统计
"""

import os
import sys
import json
import time
import argparse
from datetime import datetime, date, timedelta
from typing import List, Dict, Any, Tuple
from dataclasses import dataclass
from concurrent.futures import ThreadPoolExecutor, as_completed

# 添加项目根目录到路径
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.models.data_models import DeviationAnalysisResult
from src.trackers.deviation_tracker import DeviationTracker, DeviationAlert
from tests.mock_data_generator import MockDataGenerator
from tests.test_deviation_detection import MockJSONDataManager


@dataclass
class TestResult:
    """测试结果数据类"""
    test_name: str
    test_type: str
    user_id: str
    scenario: str
    expected_outcome: Dict[str, Any]
    actual_outcome: Dict[str, Any]
    success: bool
    execution_time: float
    error_message: str = ""


@dataclass
class BatchTestSummary:
    """批量测试汇总"""
    total_tests: int
    passed_tests: int
    failed_tests: int
    success_rate: float
    total_execution_time: float
    average_execution_time: float
    test_results: List[TestResult]
    alert_statistics: Dict[str, int]
    scenario_statistics: Dict[str, Dict[str, int]]


class BatchTestRunner:
    """批量测试运行器"""
    
    def __init__(self, config_file: str = "tests/test_scenarios.json"):
        """初始化批量测试运行器"""
        self.config_file = config_file
        self.mock_generator = MockDataGenerator()
        self.test_scenarios = self._load_test_scenarios()
        self.test_results: List[TestResult] = []
        
    def _load_test_scenarios(self) -> Dict[str, Any]:
        """加载测试场景配置"""
        try:
            with open(self.config_file, 'r', encoding='utf-8') as f:
                return json.load(f)
        except FileNotFoundError:
            print(f"警告: 测试场景配置文件 {self.config_file} 不存在，使用默认配置")
            return self._get_default_scenarios()
        except json.JSONDecodeError as e:
            print(f"错误: 解析测试场景配置文件失败: {e}")
            return self._get_default_scenarios()
    
    def _get_default_scenarios(self) -> Dict[str, Any]:
        """获取默认测试场景"""
        return {
            "test_scenarios": {
                "scenarios": {
                    "excellent": {"expected_deviation": False},
                    "good": {"expected_deviation": False},
                    "moderate": {"expected_deviation": True},
                    "significant": {"expected_deviation": True},
                    "severe": {"expected_deviation": True}
                },
                "test_cases": {
                    "single_result_tests": [],
                    "continuous_deviation_tests": [],
                    "pattern_change_tests": [],
                    "mixed_scenario_tests": []
                }
            }
        }
    
    def run_single_result_tests(self, parallel: bool = False) -> List[TestResult]:
        """运行单个结果测试"""
        print("\n=== 运行单个结果测试 ===")
        
        test_cases = self.test_scenarios.get("test_scenarios", {}).get("test_cases", {}).get("single_result_tests", [])
        
        if not test_cases:
            # 如果没有配置测试用例，生成默认测试用例
            test_cases = self._generate_default_single_tests()
        
        if parallel:
            return self._run_tests_parallel(test_cases, self._execute_single_result_test)
        else:
            return self._run_tests_sequential(test_cases, self._execute_single_result_test)
    
    def _generate_default_single_tests(self) -> List[Dict[str, Any]]:
        """生成默认单个结果测试用例"""
        scenarios = ["excellent", "good", "moderate", "significant", "severe"]
        test_cases = []
        
        for scenario in scenarios:
            test_cases.append({
                "name": f"{scenario}_test",
                "scenario": scenario,
                "user_id": f"test_user_{scenario}",
                "expected_outcome": {
                    "is_deviation": scenario in ["moderate", "significant", "severe"],
                    "alert_triggered": scenario in ["significant", "severe"]
                }
            })
        
        return test_cases
    
    def _execute_single_result_test(self, test_case: Dict[str, Any]) -> TestResult:
        """执行单个结果测试"""
        start_time = time.time()
        
        try:
            # 创建测试环境
            mock_dm = MockJSONDataManager()
            tracker = DeviationTracker(data_manager=mock_dm)
            
            # 生成测试数据
            result = self.mock_generator.generate_single_result(
                test_case["scenario"], test_case["user_id"]
            )
            
            # 记录结果
            initial_alerts = len(tracker.alerts)
            tracker.record_analysis_result(result)
            final_alerts = len(tracker.alerts)
            
            # 分析实际结果
            actual_outcome = {
                "is_deviation": result.is_deviation,
                "score": result.score,
                "completion_rate": result.completion_rate,
                "grade": result.get_grade(),
                "alert_triggered": final_alerts > initial_alerts,
                "alerts_count": final_alerts - initial_alerts
            }
            
            # 验证结果
            expected = test_case["expected_outcome"]
            success = (
                actual_outcome["is_deviation"] == expected["is_deviation"] and
                actual_outcome["alert_triggered"] == expected.get("alert_triggered", False)
            )
            
            execution_time = time.time() - start_time
            
            return TestResult(
                test_name=test_case["name"],
                test_type="single_result",
                user_id=test_case["user_id"],
                scenario=test_case["scenario"],
                expected_outcome=expected,
                actual_outcome=actual_outcome,
                success=success,
                execution_time=execution_time
            )
            
        except Exception as e:
            execution_time = time.time() - start_time
            return TestResult(
                test_name=test_case["name"],
                test_type="single_result",
                user_id=test_case["user_id"],
                scenario=test_case["scenario"],
                expected_outcome=test_case["expected_outcome"],
                actual_outcome={},
                success=False,
                execution_time=execution_time,
                error_message=str(e)
            )
    
    def run_continuous_deviation_tests(self) -> List[TestResult]:
        """运行连续偏离测试"""
        print("\n=== 运行连续偏离测试 ===")
        
        test_cases = self.test_scenarios.get("test_scenarios", {}).get("test_cases", {}).get("continuous_deviation_tests", [])
        
        if not test_cases:
            test_cases = self._generate_default_continuous_tests()
        
        return self._run_tests_sequential(test_cases, self._execute_continuous_deviation_test)
    
    def _generate_default_continuous_tests(self) -> List[Dict[str, Any]]:
        """生成默认连续偏离测试用例"""
        return [
            {
                "name": "continuous_2_days",
                "scenario": "moderate",
                "user_id": "test_continuous_2",
                "duration_days": 2,
                "expected_outcome": {"continuous_alert": False}
            },
            {
                "name": "continuous_3_days",
                "scenario": "significant",
                "user_id": "test_continuous_3",
                "duration_days": 3,
                "expected_outcome": {"continuous_alert": True}
            },
            {
                "name": "continuous_5_days",
                "scenario": "severe",
                "user_id": "test_continuous_5",
                "duration_days": 5,
                "expected_outcome": {"continuous_alert": True}
            }
        ]
    
    def _execute_continuous_deviation_test(self, test_case: Dict[str, Any]) -> TestResult:
        """执行连续偏离测试"""
        start_time = time.time()
        
        try:
            # 创建测试环境
            mock_dm = MockJSONDataManager()
            tracker = DeviationTracker(data_manager=mock_dm)
            
            # 生成连续偏离数据
            results = self.mock_generator.generate_continuous_deviation_scenario(
                test_case["user_id"],
                test_case["duration_days"],
                test_case["scenario"]
            )
            
            # 记录所有结果
            initial_alerts = len(tracker.alerts)
            for result in results:
                tracker.record_analysis_result(result)
            final_alerts = len(tracker.alerts)
            
            # 检查连续偏离预警
            continuous_alerts = [
                alert for alert in tracker.alerts[initial_alerts:]
                if alert.alert_type == 'continuous_deviation'
            ]
            
            actual_outcome = {
                "continuous_alert": len(continuous_alerts) > 0,
                "alerts_count": len(continuous_alerts),
                "total_alerts": final_alerts - initial_alerts,
                "deviation_days": test_case["duration_days"]
            }
            
            # 验证结果
            expected = test_case["expected_outcome"]
            success = actual_outcome["continuous_alert"] == expected["continuous_alert"]
            
            execution_time = time.time() - start_time
            
            return TestResult(
                test_name=test_case["name"],
                test_type="continuous_deviation",
                user_id=test_case["user_id"],
                scenario=test_case["scenario"],
                expected_outcome=expected,
                actual_outcome=actual_outcome,
                success=success,
                execution_time=execution_time
            )
            
        except Exception as e:
            execution_time = time.time() - start_time
            return TestResult(
                test_name=test_case["name"],
                test_type="continuous_deviation",
                user_id=test_case["user_id"],
                scenario=test_case["scenario"],
                expected_outcome=test_case["expected_outcome"],
                actual_outcome={},
                success=False,
                execution_time=execution_time,
                error_message=str(e)
            )
    
    def run_pattern_change_tests(self) -> List[TestResult]:
        """运行模式变化测试"""
        print("\n=== 运行模式变化测试 ===")
        
        test_cases = self.test_scenarios.get("test_scenarios", {}).get("test_cases", {}).get("pattern_change_tests", [])
        
        if not test_cases:
            test_cases = self._generate_default_pattern_tests()
        
        return self._run_tests_sequential(test_cases, self._execute_pattern_change_test)
    
    def _generate_default_pattern_tests(self) -> List[Dict[str, Any]]:
        """生成默认模式变化测试用例"""
        return [
            {
                "name": "excellent_to_severe",
                "user_id": "test_pattern_1",
                "pattern": [
                    {"day": 1, "scenario": "excellent"},
                    {"day": 2, "scenario": "excellent"},
                    {"day": 3, "scenario": "severe"},
                    {"day": 4, "scenario": "severe"}
                ],
                "expected_outcome": {"pattern_change_alert": True}
            },
            {
                "name": "stable_good",
                "user_id": "test_pattern_2",
                "pattern": [
                    {"day": 1, "scenario": "good"},
                    {"day": 2, "scenario": "good"},
                    {"day": 3, "scenario": "excellent"},
                    {"day": 4, "scenario": "good"}
                ],
                "expected_outcome": {"pattern_change_alert": False}
            }
        ]
    
    def _execute_pattern_change_test(self, test_case: Dict[str, Any]) -> TestResult:
        """执行模式变化测试"""
        start_time = time.time()
        
        try:
            # 创建测试环境
            mock_dm = MockJSONDataManager()
            tracker = DeviationTracker(data_manager=mock_dm)
            
            # 生成模式变化数据
            results = []
            base_date = date.today() - timedelta(days=len(test_case["pattern"]))
            
            for day_info in test_case["pattern"]:
                result = self.mock_generator.generate_single_result(
                    day_info["scenario"], test_case["user_id"]
                )
                result.analysis_date = (base_date + timedelta(days=day_info["day"] - 1)).isoformat()
                results.append(result)
            
            # 记录所有结果
            initial_alerts = len(tracker.alerts)
            for result in results:
                tracker.record_analysis_result(result)
            final_alerts = len(tracker.alerts)
            
            # 检查模式变化预警
            pattern_alerts = [
                alert for alert in tracker.alerts[initial_alerts:]
                if alert.alert_type == 'pattern_change'
            ]
            
            actual_outcome = {
                "pattern_change_alert": len(pattern_alerts) > 0,
                "alerts_count": len(pattern_alerts),
                "total_alerts": final_alerts - initial_alerts,
                "pattern_length": len(test_case["pattern"])
            }
            
            # 验证结果
            expected = test_case["expected_outcome"]
            success = actual_outcome["pattern_change_alert"] == expected["pattern_change_alert"]
            
            execution_time = time.time() - start_time
            
            return TestResult(
                test_name=test_case["name"],
                test_type="pattern_change",
                user_id=test_case["user_id"],
                scenario="mixed",
                expected_outcome=expected,
                actual_outcome=actual_outcome,
                success=success,
                execution_time=execution_time
            )
            
        except Exception as e:
            execution_time = time.time() - start_time
            return TestResult(
                test_name=test_case["name"],
                test_type="pattern_change",
                user_id=test_case["user_id"],
                scenario="mixed",
                expected_outcome=test_case["expected_outcome"],
                actual_outcome={},
                success=False,
                execution_time=execution_time,
                error_message=str(e)
            )
    
    def run_mixed_scenario_tests(self) -> List[TestResult]:
        """运行混合场景测试"""
        print("\n=== 运行混合场景测试 ===")
        
        test_cases = self.test_scenarios.get("test_scenarios", {}).get("test_cases", {}).get("mixed_scenario_tests", [])
        
        if not test_cases:
            test_cases = self._generate_default_mixed_tests()
        
        results = []
        for test_case in test_cases:
            results.extend(self._execute_mixed_scenario_test(test_case))
        
        return results
    
    def _generate_default_mixed_tests(self) -> List[Dict[str, Any]]:
        """生成默认混合场景测试用例"""
        return [
            {
                "name": "multi_user_mixed",
                "description": "多用户混合场景测试",
                "users": [
                    {
                        "user_id": "mixed_user_1",
                        "timeline": [
                            {"day": 1, "scenario": "excellent"},
                            {"day": 2, "scenario": "good"},
                            {"day": 3, "scenario": "moderate"}
                        ]
                    },
                    {
                        "user_id": "mixed_user_2",
                        "timeline": [
                            {"day": 1, "scenario": "significant"},
                            {"day": 2, "scenario": "significant"},
                            {"day": 3, "scenario": "significant"}
                        ]
                    }
                ],
                "expected_outcomes": {
                    "mixed_user_1": {"continuous_alerts": 0},
                    "mixed_user_2": {"continuous_alerts": 1}
                }
            }
        ]
    
    def _execute_mixed_scenario_test(self, test_case: Dict[str, Any]) -> List[TestResult]:
        """执行混合场景测试"""
        results = []
        
        # 创建测试环境
        mock_dm = MockJSONDataManager()
        tracker = DeviationTracker(data_manager=mock_dm)
        
        # 处理每个用户的时间线
        for user_info in test_case["users"]:
            start_time = time.time()
            
            try:
                user_id = user_info["user_id"]
                timeline = user_info["timeline"]
                
                # 生成用户数据
                user_results = []
                base_date = date.today() - timedelta(days=len(timeline))
                
                for day_info in timeline:
                    result = self.mock_generator.generate_single_result(
                        day_info["scenario"], user_id
                    )
                    result.analysis_date = (base_date + timedelta(days=day_info["day"] - 1)).isoformat()
                    user_results.append(result)
                
                # 记录用户结果
                initial_alerts = len(tracker.alerts)
                for result in user_results:
                    tracker.record_analysis_result(result)
                final_alerts = len(tracker.alerts)
                
                # 分析用户预警
                user_alerts = tracker.alerts[initial_alerts:]
                continuous_alerts = [a for a in user_alerts if a.alert_type == 'continuous_deviation']
                pattern_alerts = [a for a in user_alerts if a.alert_type == 'pattern_change']
                high_score_alerts = [a for a in user_alerts if a.alert_type == 'high_score']
                
                actual_outcome = {
                    "continuous_alerts": len(continuous_alerts),
                    "pattern_change_alerts": len(pattern_alerts),
                    "high_score_alerts": len(high_score_alerts),
                    "total_alerts": len(user_alerts)
                }
                
                # 验证结果
                expected = test_case["expected_outcomes"].get(user_id, {})
                success = True
                for key, expected_value in expected.items():
                    if actual_outcome.get(key, 0) != expected_value:
                        success = False
                        break
                
                execution_time = time.time() - start_time
                
                results.append(TestResult(
                    test_name=f"{test_case['name']}_{user_id}",
                    test_type="mixed_scenario",
                    user_id=user_id,
                    scenario="mixed",
                    expected_outcome=expected,
                    actual_outcome=actual_outcome,
                    success=success,
                    execution_time=execution_time
                ))
                
            except Exception as e:
                execution_time = time.time() - start_time
                results.append(TestResult(
                    test_name=f"{test_case['name']}_{user_info['user_id']}",
                    test_type="mixed_scenario",
                    user_id=user_info["user_id"],
                    scenario="mixed",
                    expected_outcome=test_case["expected_outcomes"].get(user_info["user_id"], {}),
                    actual_outcome={},
                    success=False,
                    execution_time=execution_time,
                    error_message=str(e)
                ))
        
        return results
    
    def _run_tests_sequential(self, test_cases: List[Dict[str, Any]], executor_func) -> List[TestResult]:
        """顺序运行测试"""
        results = []
        for i, test_case in enumerate(test_cases, 1):
            print(f"  运行测试 {i}/{len(test_cases)}: {test_case.get('name', 'unnamed')}")
            result = executor_func(test_case)
            results.append(result)
            
            # 打印测试结果
            status = "✓" if result.success else "✗"
            print(f"    {status} {result.test_name} ({result.execution_time:.3f}s)")
            if not result.success and result.error_message:
                print(f"      错误: {result.error_message}")
        
        return results
    
    def _run_tests_parallel(self, test_cases: List[Dict[str, Any]], executor_func, max_workers: int = 4) -> List[TestResult]:
        """并行运行测试"""
        results = []
        
        with ThreadPoolExecutor(max_workers=max_workers) as executor:
            # 提交所有任务
            future_to_test = {executor.submit(executor_func, test_case): test_case for test_case in test_cases}
            
            # 收集结果
            for i, future in enumerate(as_completed(future_to_test), 1):
                test_case = future_to_test[future]
                try:
                    result = future.result()
                    results.append(result)
                    
                    # 打印测试结果
                    status = "✓" if result.success else "✗"
                    print(f"  {status} {result.test_name} ({result.execution_time:.3f}s) [{i}/{len(test_cases)}]")
                    
                except Exception as e:
                    print(f"  ✗ {test_case.get('name', 'unnamed')} - 执行异常: {e}")
        
        return results
    
    def run_all_tests(self, parallel: bool = False) -> BatchTestSummary:
        """运行所有测试"""
        print("\n" + "="*60)
        print("开始批量偏离检测测试")
        print("="*60)
        
        start_time = time.time()
        all_results = []
        
        # 运行各类测试
        all_results.extend(self.run_single_result_tests(parallel))
        all_results.extend(self.run_continuous_deviation_tests())
        all_results.extend(self.run_pattern_change_tests())
        all_results.extend(self.run_mixed_scenario_tests())
        
        total_time = time.time() - start_time
        
        # 生成汇总报告
        summary = self._generate_summary(all_results, total_time)
        
        # 打印汇总结果
        self._print_summary(summary)
        
        return summary
    
    def _generate_summary(self, results: List[TestResult], total_time: float) -> BatchTestSummary:
        """生成测试汇总"""
        total_tests = len(results)
        passed_tests = sum(1 for r in results if r.success)
        failed_tests = total_tests - passed_tests
        success_rate = passed_tests / total_tests if total_tests > 0 else 0
        avg_time = total_time / total_tests if total_tests > 0 else 0
        
        # 统计预警类型
        alert_stats = {"continuous_deviation": 0, "pattern_change": 0, "high_score": 0}
        
        # 统计场景结果
        scenario_stats = {}
        
        for result in results:
            # 统计场景
            scenario = result.scenario
            if scenario not in scenario_stats:
                scenario_stats[scenario] = {"total": 0, "passed": 0, "failed": 0}
            
            scenario_stats[scenario]["total"] += 1
            if result.success:
                scenario_stats[scenario]["passed"] += 1
            else:
                scenario_stats[scenario]["failed"] += 1
            
            # 统计预警（从实际结果中提取）
            actual = result.actual_outcome
            if isinstance(actual, dict):
                for alert_type in alert_stats.keys():
                    if actual.get(f"{alert_type}_alerts", 0) > 0 or actual.get(f"{alert_type}_alert", False):
                        alert_stats[alert_type] += 1
        
        return BatchTestSummary(
            total_tests=total_tests,
            passed_tests=passed_tests,
            failed_tests=failed_tests,
            success_rate=success_rate,
            total_execution_time=total_time,
            average_execution_time=avg_time,
            test_results=results,
            alert_statistics=alert_stats,
            scenario_statistics=scenario_stats
        )
    
    def _print_summary(self, summary: BatchTestSummary):
        """打印测试汇总"""
        print("\n" + "="*60)
        print("批量测试汇总报告")
        print("="*60)
        
        print(f"总测试数量: {summary.total_tests}")
        print(f"通过测试: {summary.passed_tests}")
        print(f"失败测试: {summary.failed_tests}")
        print(f"成功率: {summary.success_rate:.1%}")
        print(f"总执行时间: {summary.total_execution_time:.2f}秒")
        print(f"平均执行时间: {summary.average_execution_time:.3f}秒")
        
        print("\n场景统计:")
        for scenario, stats in summary.scenario_statistics.items():
            success_rate = stats["passed"] / stats["total"] if stats["total"] > 0 else 0
            print(f"  {scenario}: {stats['passed']}/{stats['total']} ({success_rate:.1%})")
        
        print("\n预警统计:")
        for alert_type, count in summary.alert_statistics.items():
            print(f"  {alert_type}: {count}")
        
        if summary.failed_tests > 0:
            print("\n失败测试详情:")
            for result in summary.test_results:
                if not result.success:
                    print(f"  ✗ {result.test_name} ({result.test_type})")
                    if result.error_message:
                        print(f"    错误: {result.error_message}")
                    else:
                        print(f"    预期: {result.expected_outcome}")
                        print(f"    实际: {result.actual_outcome}")
    
    def save_results(self, summary: BatchTestSummary, output_file: str = "batch_test_results.json"):
        """保存测试结果"""
        results_data = {
            "metadata": {
                "generated_at": datetime.now().isoformat(),
                "test_type": "batch_deviation_detection",
                "config_file": self.config_file
            },
            "summary": {
                "total_tests": summary.total_tests,
                "passed_tests": summary.passed_tests,
                "failed_tests": summary.failed_tests,
                "success_rate": summary.success_rate,
                "total_execution_time": summary.total_execution_time,
                "average_execution_time": summary.average_execution_time,
                "alert_statistics": summary.alert_statistics,
                "scenario_statistics": summary.scenario_statistics
            },
            "detailed_results": [
                {
                    "test_name": r.test_name,
                    "test_type": r.test_type,
                    "user_id": r.user_id,
                    "scenario": r.scenario,
                    "success": r.success,
                    "execution_time": r.execution_time,
                    "expected_outcome": r.expected_outcome,
                    "actual_outcome": r.actual_outcome,
                    "error_message": r.error_message
                }
                for r in summary.test_results
            ]
        }
        
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(results_data, f, ensure_ascii=False, indent=2)
        
        print(f"\n测试结果已保存到: {output_file}")


def main():
    """主函数"""
    parser = argparse.ArgumentParser(description="偏离检测批量测试运行器")
    parser.add_argument("--config", default="tests/test_scenarios.json", help="测试场景配置文件")
    parser.add_argument("--parallel", action="store_true", help="启用并行测试")
    parser.add_argument("--output", default="batch_test_results.json", help="结果输出文件")
    parser.add_argument("--test-type", choices=["single", "continuous", "pattern", "mixed", "all"], 
                       default="all", help="指定测试类型")
    
    args = parser.parse_args()
    
    # 创建测试运行器
    runner = BatchTestRunner(args.config)
    
    # 运行指定类型的测试
    if args.test_type == "single":
        results = runner.run_single_result_tests(args.parallel)
        summary = runner._generate_summary(results, 0)
    elif args.test_type == "continuous":
        results = runner.run_continuous_deviation_tests()
        summary = runner._generate_summary(results, 0)
    elif args.test_type == "pattern":
        results = runner.run_pattern_change_tests()
        summary = runner._generate_summary(results, 0)
    elif args.test_type == "mixed":
        results = runner.run_mixed_scenario_tests()
        summary = runner._generate_summary(results, 0)
    else:
        summary = runner.run_all_tests(args.parallel)
    
    # 保存结果
    runner.save_results(summary, args.output)
    
    # 返回退出码
    return 0 if summary.success_rate == 1.0 else 1


if __name__ == "__main__":
    exit(main())