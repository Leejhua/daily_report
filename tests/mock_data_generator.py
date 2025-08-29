"""Mock数据生成器
用于生成不同偏离程度的测试数据，测试偏离检测功能
"""

import random
from datetime import datetime, date, timedelta
from typing import List, Dict, Any, Optional
from dataclasses import dataclass
import json
import os

# 添加项目根目录到路径
import sys
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.models.data_models import DeviationAnalysisResult


@dataclass
class MockScenario:
    """Mock测试场景"""
    name: str
    description: str
    expected_score_range: tuple  # (min, max)
    expected_completion_rate_range: tuple  # (min, max)
    expected_is_deviation: bool
    sample_reasons: List[str]
    sample_additional_work: List[str]
    sample_suggestions: List[str]


class MockDataGenerator:
    """Mock数据生成器"""
    
    def __init__(self):
        self.scenarios = self._define_scenarios()
        self.user_ids = ["user001", "user002", "user003", "user004", "user005"]
        
    def _define_scenarios(self) -> Dict[str, MockScenario]:
        """定义测试场景"""
        return {
            "excellent": MockScenario(
                name="优秀完成",
                description="完全按计划执行，质量优秀",
                expected_score_range=(0.0, 2.0),
                expected_completion_rate_range=(0.95, 1.0),
                expected_is_deviation=False,
                sample_reasons=[],
                sample_additional_work=[
                    "优化了代码性能",
                    "添加了额外的测试用例",
                    "完善了文档说明"
                ],
                sample_suggestions=[
                    "继续保持当前的工作节奏",
                    "可以考虑分享经验给团队"
                ]
            ),
            "good": MockScenario(
                name="良好完成",
                description="基本按计划执行，有小幅调整",
                expected_score_range=(2.1, 4.0),
                expected_completion_rate_range=(0.85, 0.94),
                expected_is_deviation=False,
                sample_reasons=[
                    "部分功能实现方式有调整",
                    "时间安排略有偏差"
                ],
                sample_additional_work=[
                    "处理了一些意外的技术问题",
                    "增加了错误处理逻辑"
                ],
                sample_suggestions=[
                    "建议提前识别潜在风险",
                    "可以优化时间规划"
                ]
            ),
            "moderate": MockScenario(
                name="中等偏离",
                description="有明显偏离但在可接受范围内",
                expected_score_range=(4.1, 6.0),
                expected_completion_rate_range=(0.70, 0.84),
                expected_is_deviation=True,
                sample_reasons=[
                    "需求理解有偏差",
                    "技术方案选择不当",
                    "时间估算不准确"
                ],
                sample_additional_work=[
                    "重新设计了部分功能",
                    "修复了多个bug",
                    "调整了架构设计"
                ],
                sample_suggestions=[
                    "建议加强需求澄清",
                    "提高技术方案评估能力",
                    "改进时间估算方法"
                ]
            ),
            "significant": MockScenario(
                name="显著偏离",
                description="偏离程度较大，需要关注",
                expected_score_range=(6.1, 8.0),
                expected_completion_rate_range=(0.50, 0.69),
                expected_is_deviation=True,
                sample_reasons=[
                    "需求变更频繁",
                    "技术难度超出预期",
                    "资源配置不足",
                    "外部依赖延迟"
                ],
                sample_additional_work=[
                    "重新实现了核心功能",
                    "处理了大量技术债务",
                    "协调了多个团队的工作",
                    "学习了新的技术栈"
                ],
                sample_suggestions=[
                    "需要重新评估项目范围",
                    "建议增加技术预研时间",
                    "加强项目风险管理",
                    "考虑寻求技术支持"
                ]
            ),
            "severe": MockScenario(
                name="严重偏离",
                description="严重偏离计划，需要紧急干预",
                expected_score_range=(8.1, 10.0),
                expected_completion_rate_range=(0.20, 0.49),
                expected_is_deviation=True,
                sample_reasons=[
                    "项目目标不明确",
                    "技术方案完全错误",
                    "团队沟通严重不足",
                    "关键资源缺失",
                    "外部环境发生重大变化"
                ],
                sample_additional_work=[
                    "重新制定了项目计划",
                    "完全重写了核心模块",
                    "进行了大量的需求调研",
                    "重新搭建了开发环境",
                    "处理了紧急的生产问题"
                ],
                sample_suggestions=[
                    "立即重新评估项目可行性",
                    "建议暂停当前工作进行复盘",
                    "需要高级管理层介入",
                    "考虑重新分配资源",
                    "建议寻求外部专业咨询"
                ]
            )
        }
    
    def generate_single_result(self, scenario_type: str, user_id: str, 
                             analysis_date: Optional[str] = None,
                             discussion_number: Optional[int] = None) -> DeviationAnalysisResult:
        """生成单个分析结果"""
        if scenario_type not in self.scenarios:
            raise ValueError(f"未知的场景类型: {scenario_type}")
        
        scenario = self.scenarios[scenario_type]
        
        # 生成随机数据
        score = round(random.uniform(*scenario.expected_score_range), 1)
        completion_rate = round(random.uniform(*scenario.expected_completion_rate_range), 2)
        confidence = round(random.uniform(0.7, 0.95), 2)
        
        # 随机选择原因、额外工作和建议
        num_reasons = random.randint(0, min(3, len(scenario.sample_reasons)))
        deviation_reasons = random.sample(scenario.sample_reasons, num_reasons) if scenario.sample_reasons else []
        
        num_additional = random.randint(1, min(3, len(scenario.sample_additional_work)))
        additional_work = random.sample(scenario.sample_additional_work, num_additional)
        
        num_suggestions = random.randint(1, min(3, len(scenario.sample_suggestions)))
        suggestions = random.sample(scenario.sample_suggestions, num_suggestions)
        
        # 生成摘要
        summary = f"{scenario.description}。偏离评分: {score}, 完成率: {completion_rate*100:.0f}%"
        
        # 生成原始分析文本
        raw_analysis = f"""## 工作执行分析报告

**偏离评分**: {score}/10
**完成率**: {completion_rate*100:.1f}%
**评级**: {self._get_grade(score)}

### 分析详情
{scenario.description}

### 偏离原因
{chr(10).join([f"- {reason}" for reason in deviation_reasons]) if deviation_reasons else "无明显偏离"}

### 额外工作
{chr(10).join([f"- {work}" for work in additional_work])}

### 改进建议
{chr(10).join([f"- {suggestion}" for suggestion in suggestions])}
"""
        
        return DeviationAnalysisResult(
            score=score,
            completion_rate=completion_rate,
            deviation_reasons=deviation_reasons,
            additional_work=additional_work,
            suggestions=suggestions,
            summary=summary,
            confidence=confidence,
            user_id=user_id,
            analysis_date=analysis_date or date.today().isoformat(),
            discussion_number=discussion_number or random.randint(1000, 9999),
            is_deviation=scenario.expected_is_deviation,
            raw_analysis_text=raw_analysis
        )
    
    def _get_grade(self, score: float) -> str:
        """获取评级"""
        if score <= 2:
            return "优秀"
        elif score <= 4:
            return "良好"
        elif score <= 6:
            return "一般"
        elif score <= 8:
            return "需改进"
        else:
            return "较差"
    
    def generate_user_timeline(self, user_id: str, days: int, 
                             scenario_distribution: Optional[Dict[str, float]] = None) -> List[DeviationAnalysisResult]:
        """生成用户的时间线数据"""
        if scenario_distribution is None:
            # 默认分布：大部分是良好的，少量偏离
            scenario_distribution = {
                "excellent": 0.2,
                "good": 0.4,
                "moderate": 0.25,
                "significant": 0.1,
                "severe": 0.05
            }
        
        results = []
        start_date = date.today() - timedelta(days=days-1)
        
        for i in range(days):
            current_date = start_date + timedelta(days=i)
            
            # 根据分布随机选择场景
            scenario_type = self._weighted_random_choice(scenario_distribution)
            
            result = self.generate_single_result(
                scenario_type=scenario_type,
                user_id=user_id,
                analysis_date=current_date.isoformat(),
                discussion_number=1000 + i
            )
            
            results.append(result)
        
        return results
    
    def _weighted_random_choice(self, weights: Dict[str, float]) -> str:
        """根据权重随机选择"""
        choices = list(weights.keys())
        weights_list = list(weights.values())
        return random.choices(choices, weights=weights_list)[0]
    
    def generate_continuous_deviation_scenario(self, user_id: str, 
                                             deviation_days: int = 3,
                                             severity: str = "moderate") -> List[DeviationAnalysisResult]:
        """生成连续偏离场景"""
        results = []
        start_date = date.today() - timedelta(days=deviation_days-1)
        
        # 根据严重程度选择场景类型
        scenario_mapping = {
            "moderate": "moderate",
            "significant": "significant", 
            "severe": "severe"
        }
        
        scenario_type = scenario_mapping.get(severity, "moderate")
        
        for i in range(deviation_days):
            current_date = start_date + timedelta(days=i)
            
            result = self.generate_single_result(
                scenario_type=scenario_type,
                user_id=user_id,
                analysis_date=current_date.isoformat(),
                discussion_number=2000 + i
            )
            
            results.append(result)
        
        return results
    
    def generate_pattern_change_scenario(self, user_id: str) -> List[DeviationAnalysisResult]:
        """生成模式变化场景"""
        results = []
        
        # 前4天：良好表现
        for i in range(4):
            current_date = date.today() - timedelta(days=6-i)
            result = self.generate_single_result(
                scenario_type="good",
                user_id=user_id,
                analysis_date=current_date.isoformat(),
                discussion_number=3000 + i
            )
            results.append(result)
        
        # 后3天：显著恶化
        for i in range(3):
            current_date = date.today() - timedelta(days=2-i)
            result = self.generate_single_result(
                scenario_type="significant",
                user_id=user_id,
                analysis_date=current_date.isoformat(),
                discussion_number=3004 + i
            )
            results.append(result)
        
        return results
    
    def generate_test_dataset(self, output_file: str = "mock_test_data.json") -> Dict[str, Any]:
        """生成完整的测试数据集"""
        dataset = {
            "metadata": {
                "generated_at": datetime.now().isoformat(),
                "generator_version": "1.0",
                "description": "偏离检测功能测试数据集"
            },
            "scenarios": {},
            "test_cases": {
                "single_results": [],
                "continuous_deviation": [],
                "pattern_change": [],
                "user_timelines": []
            }
        }
        
        # 添加场景定义
        for name, scenario in self.scenarios.items():
            dataset["scenarios"][name] = {
                "name": scenario.name,
                "description": scenario.description,
                "expected_score_range": scenario.expected_score_range,
                "expected_completion_rate_range": scenario.expected_completion_rate_range,
                "expected_is_deviation": scenario.expected_is_deviation
            }
        
        # 生成单个结果测试用例
        for scenario_type in self.scenarios.keys():
            for user_id in self.user_ids[:2]:  # 只用前两个用户
                result = self.generate_single_result(scenario_type, user_id)
                dataset["test_cases"]["single_results"].append({
                    "scenario_type": scenario_type,
                    "result": result.to_dict()
                })
        
        # 生成连续偏离测试用例
        for severity in ["moderate", "significant", "severe"]:
            results = self.generate_continuous_deviation_scenario(
                "user_continuous", deviation_days=3, severity=severity
            )
            dataset["test_cases"]["continuous_deviation"].append({
                "severity": severity,
                "results": [r.to_dict() for r in results]
            })
        
        # 生成模式变化测试用例
        results = self.generate_pattern_change_scenario("user_pattern_change")
        dataset["test_cases"]["pattern_change"] = [r.to_dict() for r in results]
        
        # 生成用户时间线测试用例
        for user_id in self.user_ids:
            timeline = self.generate_user_timeline(user_id, days=14)
            dataset["test_cases"]["user_timelines"].append({
                "user_id": user_id,
                "timeline": [r.to_dict() for r in timeline]
            })
        
        # 保存到文件
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(dataset, f, ensure_ascii=False, indent=2)
        
        return dataset
    
    def get_scenario_info(self) -> Dict[str, Any]:
        """获取场景信息"""
        info = {}
        for name, scenario in self.scenarios.items():
            info[name] = {
                "name": scenario.name,
                "description": scenario.description,
                "score_range": scenario.expected_score_range,
                "completion_rate_range": scenario.expected_completion_rate_range,
                "is_deviation": scenario.expected_is_deviation
            }
        return info


if __name__ == "__main__":
    # 示例用法
    generator = MockDataGenerator()
    
    print("=== Mock数据生成器 ===")
    print("\n可用场景:")
    for name, info in generator.get_scenario_info().items():
        print(f"  {name}: {info['name']} (评分: {info['score_range']}, 偏离: {info['is_deviation']})")
    
    print("\n生成测试数据集...")
    dataset = generator.generate_test_dataset()
    
    print(f"\n数据集生成完成!")
    print(f"- 场景数量: {len(dataset['scenarios'])}")
    print(f"- 单个结果测试用例: {len(dataset['test_cases']['single_results'])}")
    print(f"- 连续偏离测试用例: {len(dataset['test_cases']['continuous_deviation'])}")
    print(f"- 模式变化测试用例: {len(dataset['test_cases']['pattern_change'])}")
    print(f"- 用户时间线: {len(dataset['test_cases']['user_timelines'])}")
    
    print("\n示例 - 生成连续偏离场景:")
    continuous_results = generator.generate_continuous_deviation_scenario(
        "test_user", deviation_days=3, severity="significant"
    )
    for result in continuous_results:
        print(f"  日期: {result.analysis_date}, 评分: {result.score}, 偏离: {result.is_deviation}")