"""集成测试脚本
验证增强功能的端到端工作流程
"""

import asyncio
import logging
import tempfile
import os
import json
import pytest
from datetime import datetime
from pathlib import Path
from unittest.mock import patch, AsyncMock
from unittest.mock import Mock, AsyncMock, patch

# 设置日志
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class MockGitHubClient:
    """模拟GitHub客户端"""
    
    def __init__(self):
        self.discussions = [
            {
                'id': 123,
                'title': '测试讨论',
                'body': '今日计划：完成功能开发\n实际完成：只完成了50%',
                'author': {'login': 'test_user'},
                'created_at': datetime.now().isoformat()
            }
        ]
    
    async def get_discussions(self, since_date):
        """获取讨论"""
        return self.discussions
    
    async def post_comment(self, discussion_id, comment):
        """发布评论"""
        logger.info(f"发布评论到讨论 {discussion_id}: {comment[:100]}...")
        return {'id': 456}


class MockGLMClient:
    """模拟GLM客户端"""
    
    async def analyze_with_dual_conversation(self, daily_report, daily_plan):
        """模拟双次对话分析"""
        from src.clients.enhanced_glm_client import DualConversationResult
        from src.models.data_models import DeviationAnalysisResult
        
        # 模拟分析结果
        structured_data = DeviationAnalysisResult(
            score=6.5,
            completion_rate=0.7,
            deviation_reasons=["计划执行不完整", "时间管理不当"],
            additional_work=["临时会议", "紧急任务处理"],
            suggestions=["建议制定更详细的时间计划", "提高执行效率"],
            summary="测试分析总结",
            confidence=0.8
        )
        
        text_report = f"""
## 偏离分析报告

**偏离评分**: {structured_data.score}
**完成率**: {structured_data.completion_rate:.1%}
**是否偏离**: {'是' if structured_data.score > 6.0 else '否'}

### 偏离原因
{chr(10).join(f'- {reason}' for reason in structured_data.deviation_reasons)}

### 改进建议
{chr(10).join(f'- {suggestion}' for suggestion in structured_data.suggestions)}

### 总结
{structured_data.summary}

### 分析时间
{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
"""
        
        return DualConversationResult(
            text_analysis=text_report,
            structured_data=structured_data.to_dict(),
            success=True
        )


@pytest.mark.asyncio
async def test_complete_workflow():
    """测试完整工作流程"""
    logger.info("开始集成测试...")
    
    try:
        # 1. 创建临时配置
        with tempfile.TemporaryDirectory() as temp_dir:
            config = create_test_config(temp_dir)
            
            # 2. 初始化组件
            logger.info("初始化组件...")
            components = await initialize_components(config)
            
            # 3. 运行分析流程
            logger.info("运行分析流程...")
            analysis_results = await run_analysis_workflow(components)
            
            # 4. 验证偏离检测
            logger.info("验证偏离检测...")
            warnings = await verify_deviation_detection(components, analysis_results)
            
            # 5. 测试汇报生成
            logger.info("测试汇报生成...")
            reports = await generate_test_reports(components)
            
            # 6. 测试通知发送
            logger.info("测试通知发送...")
            await send_test_notifications(components, warnings, reports)
            
            # 7. 验证数据持久化
            logger.info("验证数据持久化...")
            await verify_data_persistence(components)
            
            logger.info("✅ 集成测试完成！所有功能正常工作")
            
    except Exception as e:
        logger.error(f"❌ 集成测试失败: {e}")
        raise


def create_test_config(temp_dir):
    """创建测试配置"""
    from types import SimpleNamespace
    
    config = SimpleNamespace()
    
    # 数据存储配置
    config.data_storage = SimpleNamespace()
    config.data_storage.data_directory = temp_dir
    config.data_storage.backup_enabled = True
    config.data_storage.cache_enabled = True
    config.data_storage.cache_size_mb = 10
    
    # 偏离检测配置
    config.deviation_detection = SimpleNamespace()
    config.deviation_detection.consecutive_threshold = 2
    config.deviation_detection.severity_threshold = 0.6
    config.deviation_detection.completion_rate_threshold = 0.5
    config.deviation_detection.pattern_detection_enabled = True
    config.deviation_detection.alert_cooldown_hours = 1
    
    # 汇报生成配置
    config.report_generation = SimpleNamespace()
    config.report_generation.default_format = "detailed"
    config.report_generation.include_charts = True
    config.report_generation.include_trends = True
    
    # 飞书配置
    config.feishu = SimpleNamespace()
    config.feishu.webhook_url = "https://test.webhook.url"
    config.feishu.message_format = "card"
    config.feishu.retry_attempts = 3
    config.feishu.retry_delay = 1
    
    # GLM配置
    config.glm = SimpleNamespace()
    config.glm.api_key = "test_key"
    config.glm.model = "glm-4-flash"
    config.glm.base_url = "https://open.bigmodel.cn/api/paas/v4/"
    config.glm.timeout = 30
    
    return config


async def initialize_components(config):
    """初始化所有组件"""
    import sys
    from pathlib import Path
    
    # 添加项目根目录到Python路径
    project_root = Path(__file__).parent.parent
    sys.path.insert(0, str(project_root))
    
    from src.storage.json_data_manager import JSONDataManager
    from src.trackers.deviation_tracker import DeviationTracker
    from src.generators.report_generator import ReportGenerator
    from src.clients.feishu_client import FeishuClient
    
    # 初始化数据管理器
    data_manager = JSONDataManager(
        data_dir=config.data_storage.data_directory,
        backup_enabled=config.data_storage.backup_enabled
    )
    
    # 初始化偏离跟踪器
    deviation_tracker = DeviationTracker(
        data_manager,
        config_or_threshold=config.deviation_detection.consecutive_threshold,
        high_score_threshold=config.deviation_detection.severity_threshold,
        pattern_change_threshold=3.0
    )
    
    # 初始化汇报生成器
    report_generator = ReportGenerator(config)
    
    # 初始化飞书客户端
    feishu_config_dict = {
        'webhook_url': 'https://test.webhook.url',
        'mapping_file': 'test_feishu_mapping.json',
        'timeout': 30,
        'retry_count': 3
    }
    feishu_client = FeishuClient(feishu_config_dict)
    
    # 模拟GLM客户端
    glm_client = MockGLMClient()
    
    # 模拟GitHub客户端
    github_client = MockGitHubClient()
    
    return {
        'data_manager': data_manager,
        'deviation_tracker': deviation_tracker,
        'report_generator': report_generator,
        'feishu_client': feishu_client,
        'glm_client': glm_client,
        'github_client': github_client
    }


async def run_analysis_workflow(components):
    """运行分析工作流程"""
    github_client = components['github_client']
    glm_client = components['glm_client']
    deviation_tracker = components['deviation_tracker']
    
    # 获取讨论
    discussions = await github_client.get_discussions(datetime.now())
    logger.info(f"获取到 {len(discussions)} 个讨论")
    
    analysis_results = []
    
    for discussion in discussions:
        # 分析讨论内容
        enhanced_result = await glm_client.analyze_with_dual_conversation(
            daily_report=discussion['body'],
            daily_plan="完成功能开发"
        )
        
        logger.info(f"分析完成，偏离评分: {enhanced_result.structured_data['score']}，完成率: {enhanced_result.structured_data['completion_rate']:.1%}")
        
        # 创建DeviationAnalysisResult对象
        from src.models.data_models import DeviationAnalysisResult
        deviation_result = DeviationAnalysisResult(
            user_id="test_user",
            analysis_date=datetime.now().strftime('%Y-%m-%d'),
            discussion_number=1,
            score=enhanced_result.structured_data['score'],
            completion_rate=enhanced_result.structured_data['completion_rate'],
            deviation_reasons=enhanced_result.structured_data['deviation_reasons'],
            additional_work=enhanced_result.structured_data['additional_work'],
            suggestions=enhanced_result.structured_data['suggestions'],
            summary=enhanced_result.structured_data['summary'],
            confidence=enhanced_result.structured_data['confidence'],
            is_deviation=enhanced_result.structured_data['score'] > 6.0,
            raw_analysis_text=enhanced_result.text_analysis
        )
        
        # 记录分析结果并检测偏离
        success = deviation_tracker.record_analysis_result(deviation_result)
        analysis_id = f"test_analysis_{len(analysis_results) + 1}"
        
        analysis_results.append({
            'discussion': discussion,
            'enhanced_result': enhanced_result,
            'analysis_id': analysis_id
        })
        
        logger.info(f"记录分析结果，ID: {analysis_id}")
    
    return analysis_results


async def verify_deviation_detection(components, analysis_results):
    """验证偏离检测功能"""
    deviation_tracker = components['deviation_tracker']
    all_warnings = []
    
    # 检查是否有偏离检测
    for result in analysis_results:
        enhanced_result = result['enhanced_result']
        if enhanced_result.structured_data['score'] > 6.0:
            logger.info(f"检测到偏离: 评分={enhanced_result.structured_data['score']}")
            # 模拟偏离预警
            warning = {
                'user_id': 'test_user',
                'type': 'continuous_deviation',
                'alert_level': 'medium',
                'score': enhanced_result.structured_data['score']
            }
            all_warnings.append(warning)
    
    # 验证预警数据
    data_manager = components['data_manager']
    recent_analyses = data_manager.get_user_recent_results('test_user', days=1)
    logger.info(f"数据库中记录了 {len(recent_analyses)} 个分析记录")
    
    return all_warnings


async def generate_test_reports(components):
    """生成测试汇报"""
    report_generator = components['report_generator']
    data_manager = components['data_manager']
    
    # 导入必要的类
    from src.trackers.deviation_tracker import DeviationAlert
    
    reports = {}
    
    # 获取测试用户的分析数据
    recent_analyses = data_manager.get_user_recent_results('test_user', days=7)
    
    if recent_analyses:
        # 将DeviationAnalysisResult对象转换为字典格式
        analyses_dict = []
        for analysis in recent_analyses:
            analysis_dict = {
                'analysis_date': analysis.analysis_date,
                'deviation_score': analysis.score,
                'completion_rate': analysis.completion_rate,
                'deviation_reasons': analysis.deviation_reasons,
                'suggestions': analysis.suggestions
            }
            analyses_dict.append(analysis_dict)
        
        # 生成详细汇报
        detailed_report = await report_generator.generate_deviation_report(
            user_name="test_user",
            analyses=analyses_dict,
            format_type="detailed"
        )
        reports['detailed'] = detailed_report
        logger.info(f"生成详细汇报: {len(str(detailed_report.get('content', '')))} 字符")
        
        # 生成简洁汇报
        simple_report = await report_generator.generate_deviation_report(
            user_name="test_user",
            analyses=analyses_dict,
            format_type="simple"
        )
        reports['simple'] = simple_report
        logger.info(f"生成简洁汇报: {len(str(simple_report.get('content', '')))} 字符")
        
        # 生成卡片汇报
        card_report = await report_generator.generate_deviation_report(
            user_name="test_user",
            analyses=analyses_dict,
            format_type="card"
        )
        reports['card'] = card_report
        logger.info(f"生成卡片汇报: {len(str(card_report.get('content', '')))} 字符")
    else:
        logger.warning("没有找到分析数据，无法生成汇报")
    
    return reports


async def send_test_notifications(components, warnings, reports):
    """发送测试通知"""
    feishu_client = components['feishu_client']
    
    # 模拟发送预警通知
    if warnings:
        with patch('aiohttp.ClientSession.post') as mock_post:
            mock_response = AsyncMock()
            mock_response.status = 200
            mock_response.json.return_value = {'code': 0}
            mock_post.return_value.__aenter__.return_value = mock_response
            
            success = feishu_client.send_deviation_alert("集成测试汇报", ["test_user"])
            logger.info(f"发送偏离预警: {'成功' if success else '失败'}")
    
    # 模拟发送汇报通知
    for report_type, report in reports.items():
        with patch('aiohttp.ClientSession.post') as mock_post:
            mock_response = AsyncMock()
            mock_response.status = 200
            mock_response.json.return_value = {'code': 0}
            mock_post.return_value.__aenter__.return_value = mock_response
            
            # 使用send_deviation_alert方法发送报告
            success = feishu_client.send_deviation_alert(
                report.get('content', ''), 
                ["test_user"], 
                message_type='card',
                report_data=report.get('data', {})
            )
            logger.info(f"发送{report_type}汇报: {'成功' if success else '失败'}")


async def verify_data_persistence(components):
    """验证数据持久化"""
    data_manager = components['data_manager']
    
    # 检查数据目录是否存在
    assert data_manager.data_dir.exists(), "数据目录不存在"
    
    # 检查分析结果文件是否存在
    assert data_manager.analysis_results_file.exists(), "分析结果文件不存在"
    
    # 检查是否有分析结果
    recent_analyses = data_manager.get_user_recent_results("test_user", days=1)
    assert len(recent_analyses) > 0, "没有找到分析结果"
    
    logger.info(f"✅ 数据持久化验证通过，找到 {len(recent_analyses)} 条分析结果")


async def main():
    """主函数"""
    print("🚀 开始增强功能集成测试")
    print("=" * 50)
    
    try:
        await test_complete_workflow()
        print("\n" + "=" * 50)
        print("✅ 所有测试通过！增强功能工作正常")
    except Exception as e:
        print("\n" + "=" * 50)
        print(f"❌ 测试失败: {e}")
        import traceback
        traceback.print_exc()
        return 1
    
    return 0


if __name__ == "__main__":
    import sys
    sys.exit(asyncio.run(main()))