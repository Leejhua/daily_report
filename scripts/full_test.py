#!/usr/bin/env python3
"""
完整测试脚本
自动化执行所有测试步骤，验证服务的完整功能
"""

import asyncio
import sys
import os
import json
from pathlib import Path
from datetime import date, datetime

# 添加项目根目录到Python路径
sys.path.append(str(Path(__file__).parent.parent))

from src.config import Config
from src.clients.github_client import GitHubClient
from src.clients.glm_client import GLMClient
from src.analyzers.daily_analyzer import DailyAnalyzer
from src.scheduler import AnalysisScheduler


class FullTestSuite:
    """完整测试套件"""
    
    def __init__(self):
        self.test_results = {}
        self.config = None
        self.github_client = None
        self.glm_client = None
        self.analyzer = None
        
    def log_test(self, test_name: str, success: bool, message: str = "", details: dict = None):
        """记录测试结果"""
        self.test_results[test_name] = {
            'success': success,
            'message': message,
            'details': details or {},
            'timestamp': datetime.now().isoformat()
        }
        
        status = "✅ 通过" if success else "❌ 失败"
        print(f"{status} {test_name}: {message}")
        
    async def test_1_environment_setup(self):
        """测试1: 环境配置"""
        print("\n" + "="*60)
        print("🔧 第1步: 环境配置测试")
        print("="*60)
        
        try:
            # 检查.env文件
            env_file = Path(".env")
            if not env_file.exists():
                self.log_test("环境文件检查", False, ".env文件不存在，请先创建配置文件")
                return False
                
            self.log_test("环境文件检查", True, "找到.env配置文件")
            
            # 加载配置
            try:
                self.config = Config()
                self.config.validate()
                self.log_test("配置加载", True, "配置文件加载成功")
            except Exception as e:
                self.log_test("配置加载", False, f"配置验证失败: {e}")
                return False
                
            # 检查必需的环境变量
            required_vars = ['GITHUB_TOKEN', 'GITHUB_ORG', 'GITHUB_REPO', 'GLM_API_KEY']
            missing_vars = []
            
            for var in required_vars:
                if not os.getenv(var):
                    missing_vars.append(var)
                    
            if missing_vars:
                self.log_test("环境变量检查", False, f"缺少必需环境变量: {', '.join(missing_vars)}")
                return False
            else:
                self.log_test("环境变量检查", True, "所有必需环境变量已配置")
                
            return True
            
        except Exception as e:
            self.log_test("环境配置", False, f"环境配置测试失败: {e}")
            return False
    
    async def test_2_github_integration(self):
        """测试2: GitHub集成"""
        print("\n" + "="*60)
        print("🐙 第2步: GitHub集成测试")
        print("="*60)
        
        try:
            # 初始化GitHub客户端
            self.github_client = GitHubClient(self.config.github)
            
            # 测试连接
            connection_ok = await self.github_client.test_connection()
            if not connection_ok:
                self.log_test("GitHub连接", False, "无法连接到GitHub API")
                return False
            
            self.log_test("GitHub连接", True, "GitHub API连接成功")
            
            # 获取API速率限制信息
            rate_limit = await self.github_client.check_api_rate_limit()
            if rate_limit:
                remaining = rate_limit.get('core', {}).get('remaining', 0)
                self.log_test("API限制检查", True, f"剩余API调用: {remaining}")
            
            # 获取Discussion分类
            try:
                daily_discussions = await self.github_client.get_daily_discussions()
                    
                categories = set()
                discussion_count = 0
                
                for discussion in daily_discussions:
                    categories.add(discussion.category)
                    discussion_count += 1
                    if discussion_count >= 10:  # 只检查前10个避免API限制
                        break
                
                self.log_test("Discussion分类", True, f"找到分类: {', '.join(sorted(categories))}")
                
                # 检查目标分类
                target_category = self.config.github.discussion_category
                if target_category in categories:
                    self.log_test("目标分类检查", True, f"找到目标分类: {target_category}")
                else:
                    self.log_test("目标分类检查", False, f"未找到目标分类: {target_category}")
                    
            except Exception as e:
                self.log_test("Discussion访问", False, f"无法访问Discussions: {e}")
                return False
            
            # 获取最近的讨论
            try:
                daily_discussions = await self.github_client.get_daily_discussions()
                count = len(daily_discussions)
                
                if count > 0:
                    self.log_test("日结讨论获取", True, f"找到 {count} 个今日相关讨论")
                    
                    # 显示讨论详情
                    for i, disc in enumerate(daily_discussions[:3], 1):
                        print(f"   [{i}] #{disc.number}: {disc.title}")
                        print(f"       📅 {disc.updated_at.strftime('%Y-%m-%d %H:%M')}")
                        print(f"       👤 {disc.author} | 💬 {disc.comments_count}")
                        
                else:
                    self.log_test("日结讨论获取", False, "未找到今日相关讨论")
                    
            except Exception as e:
                self.log_test("日结讨论获取", False, f"获取讨论失败: {e}")
                return False
                
            return True
            
        except Exception as e:
            self.log_test("GitHub集成", False, f"GitHub集成测试失败: {e}")
            return False
    
    async def test_3_content_parsing(self):
        """测试3: 内容结构解析"""
        print("\n" + "="*60)
        print("📝 第3步: 内容结构解析测试")
        print("="*60)
        
        try:
            # 获取测试讨论
            daily_discussions = await self.github_client.get_daily_discussions()
            
            if not daily_discussions:
                self.log_test("内容解析", False, "没有可用的测试讨论")
                return False
            
            # 测试第一个讨论
            test_discussion = daily_discussions[0]
            print(f"🔍 测试讨论: #{test_discussion.number} - {test_discussion.title}")
            
            # 提取内容
            content_data = await self.github_client.extract_daily_content(test_discussion)
            
            # 检查提取结果
            weekly_plan_len = len(content_data.get('weekly_plan', ''))
            daily_summary_len = len(content_data.get('daily_summary', ''))
            daily_plan_len = len(content_data.get('daily_plan', ''))
            
            self.log_test("周期计划提取", weekly_plan_len > 0, 
                         f"提取长度: {weekly_plan_len} 字符")
            self.log_test("日报内容提取", daily_summary_len > 0, 
                         f"提取长度: {daily_summary_len} 字符")
            self.log_test("日计划提取", daily_plan_len > 0, 
                         f"提取长度: {daily_plan_len} 字符")
            
            # 显示提取的内容预览
            if content_data.get('weekly_plan'):
                preview = content_data['weekly_plan'][:200] + "..." if len(content_data['weekly_plan']) > 200 else content_data['weekly_plan']
                print(f"\n📋 周期计划预览:\n{preview}")
                
            if content_data.get('daily_summary'):
                preview = content_data['daily_summary'][:200] + "..." if len(content_data['daily_summary']) > 200 else content_data['daily_summary']
                print(f"\n🗒️ 日报预览:\n{preview}")
                
            if content_data.get('daily_plan'):
                preview = content_data['daily_plan'][:200] + "..." if len(content_data['daily_plan']) > 200 else content_data['daily_plan']
                print(f"\n📅 日计划预览:\n{preview}")
            
            # 测试多个讨论（如果有的话）
            if len(daily_discussions) > 1:
                print(f"\n🔍 测试其他讨论...")
                for i, disc in enumerate(daily_discussions[1:3], 2):
                    try:
                        content = await self.github_client.extract_daily_content(disc)
                        has_content = any(len(content.get(key, '')) > 0 for key in ['weekly_plan', 'daily_summary', 'daily_plan'])
                        self.log_test(f"讨论#{disc.number}内容提取", has_content, 
                                    f"标题: {disc.title[:30]}...")
                    except Exception as e:
                        self.log_test(f"讨论#{disc.number}内容提取", False, f"提取失败: {e}")
            
            return True
            
        except Exception as e:
            self.log_test("内容解析", False, f"内容解析测试失败: {e}")
            return False
    
    async def test_4_glm_analysis(self):
        """测试4: GLM分析功能"""
        print("\n" + "="*60)
        print("🤖 第4步: GLM分析功能测试")
        print("="*60)
        
        try:
            # 初始化GLM客户端
            self.glm_client = GLMClient(self.config.glm)
            
            # 测试连接
            connection_ok = await self.glm_client.test_connection()
            if not connection_ok:
                self.log_test("GLM连接", False, "无法连接到GLM API")
                return False
                
            self.log_test("GLM连接", True, "GLM API连接成功")
            
            # 准备测试数据
            test_summary = """
            今日工作总结：
            1. 完成了用户认证模块的开发，包括登录和注册功能
            2. 编写了相关的单元测试，覆盖率达到85%
            3. 修复了3个前端UI bug
            4. 参加了项目进度评审会议
            5. 遇到数据库连接超时问题，已联系DBA协助解决
            
            工作进度：认证模块开发完成度90%，预计明天可以完成剩余功能
            """
            
            test_plan = """
            今日计划：
            1. 完成用户认证模块开发
            2. 编写单元测试
            3. 修复已知的UI问题
            4. 参加项目评审会议
            5. 更新API文档
            """
            
            test_weekly_plan = """
            本周计划：
            - 完成用户认证功能模块
            - 实现权限管理系统
            - 完成相关测试和文档
            - 进行代码review和优化
            """
            
            # 测试偏离度分析
            try:
                print("🔍 测试偏离度分析...")
                deviation_result = await self.glm_client.analyze_work_deviation(test_summary, test_plan)
                
                if isinstance(deviation_result, dict) and 'score' in deviation_result:
                    score = deviation_result.get('score', 0)
                    completion_rate = deviation_result.get('completion_rate', 0)
                    self.log_test("偏离度分析", True, 
                                f"评分: {score}/10, 完成率: {completion_rate*100:.1f}%")
                    print(f"   📊 分析摘要: {deviation_result.get('summary', '')}")
                else:
                    self.log_test("偏离度分析", False, "返回结果格式不正确")
                    
            except Exception as e:
                self.log_test("偏离度分析", False, f"分析失败: {e}")
            
            # 测试清晰度分析
            try:
                print("🔍 测试清晰度分析...")
                clarity_result = await self.glm_client.analyze_content_clarity(test_summary)
                
                if isinstance(clarity_result, dict) and 'clarity_score' in clarity_result:
                    clarity_score = clarity_result.get('clarity_score', 0)
                    specificity_score = clarity_result.get('specificity_score', 0)
                    completeness_score = clarity_result.get('completeness_score', 0)
                    self.log_test("清晰度分析", True, 
                                f"清晰度: {clarity_score}/10, 具体性: {specificity_score}/10, 完整性: {completeness_score}/10")
                    print(f"   📝 分析摘要: {clarity_result.get('summary', '')}")
                else:
                    self.log_test("清晰度分析", False, "返回结果格式不正确")
                    
            except Exception as e:
                self.log_test("清晰度分析", False, f"分析失败: {e}")
            
            # 测试一致性分析
            try:
                print("🔍 测试一致性分析...")
                consistency_result = await self.glm_client.analyze_plan_consistency(test_plan, test_weekly_plan)
                
                if isinstance(consistency_result, dict) and 'consistency_score' in consistency_result:
                    consistency_score = consistency_result.get('consistency_score', 0)
                    alignment_level = consistency_result.get('alignment_level', 0)
                    self.log_test("一致性分析", True, 
                                f"一致性: {consistency_score}/10, 对齐度: {alignment_level}/10")
                    print(f"   🔄 分析摘要: {consistency_result.get('summary', '')}")
                else:
                    self.log_test("一致性分析", False, "返回结果格式不正确")
                    
            except Exception as e:
                self.log_test("一致性分析", False, f"分析失败: {e}")
            
            # 测试综合分析报告
            try:
                print("🔍 测试综合分析报告...")
                comprehensive_report = await self.glm_client.generate_comprehensive_analysis(
                    test_summary, test_plan, test_weekly_plan
                )
                
                if comprehensive_report and len(comprehensive_report) > 100:
                    self.log_test("综合分析报告", True, f"报告长度: {len(comprehensive_report)} 字符")
                    print(f"   📋 报告预览: {comprehensive_report[:200]}...")
                else:
                    self.log_test("综合分析报告", False, "报告生成失败或内容过短")
                    
            except Exception as e:
                self.log_test("综合分析报告", False, f"报告生成失败: {e}")
            
            return True
            
        except Exception as e:
            self.log_test("GLM分析", False, f"GLM分析测试失败: {e}")
            return False
    
    async def test_5_end_to_end(self):
        """测试5: 端到端流程"""
        print("\n" + "="*60)
        print("🚀 第5步: 端到端流程测试")
        print("="*60)
        
        try:
            # 初始化分析器
            self.analyzer = DailyAnalyzer(self.config)
            
            # 测试连接
            connections = await self.analyzer.test_connections()
            overall_ok = connections.get('overall', False)
            
            self.log_test("整体连接测试", overall_ok, 
                         f"GitHub: {connections.get('github', False)}, GLM: {connections.get('glm', False)}")
            
            if not overall_ok:
                return False
            
            # 获取可测试的讨论
            daily_discussions = await self.github_client.get_daily_discussions()
            
            if not daily_discussions:
                self.log_test("端到端测试", False, "没有可用的测试讨论")
                return False
            
            # 选择第一个讨论进行测试
            test_discussion = daily_discussions[0]
            print(f"🔍 端到端测试讨论: #{test_discussion.number}")
            
            # 生成分析预览（不发布评论）
            try:
                preview_result = await self.analyzer.get_analysis_preview(test_discussion.number)
                
                if preview_result.get('success', False):
                    report_length = preview_result.get('report_length', 0)
                    self.log_test("分析预览生成", True, f"报告长度: {report_length} 字符")
                    
                    # 显示报告预览
                    report = preview_result.get('analysis_report', '')
                    if report:
                        print(f"\n📋 生成的分析报告预览:")
                        print("-" * 50)
                        preview_text = report[:500] + "..." if len(report) > 500 else report
                        print(preview_text)
                        print("-" * 50)
                    
                else:
                    error = preview_result.get('error', '未知错误')
                    self.log_test("分析预览生成", False, f"预览生成失败: {error}")
                    
            except Exception as e:
                self.log_test("分析预览生成", False, f"预览生成异常: {e}")
            
            return True
            
        except Exception as e:
            self.log_test("端到端测试", False, f"端到端测试失败: {e}")
            return False
    
    async def test_6_scheduler(self):
        """测试6: 定时任务"""
        print("\n" + "="*60)
        print("⏰ 第6步: 定时任务测试")
        print("="*60)
        
        try:
            # 创建调度器
            scheduler = AnalysisScheduler(self.config)
            
            # 获取调度器状态
            status = await scheduler.get_status()
            
            cron_expr = status.get('cron_expression', '')
            timezone = status.get('timezone', '')
            next_run = status.get('next_run_time', '')
            
            self.log_test("调度器配置", True, 
                         f"Cron: {cron_expr}, 时区: {timezone}")
            
            if next_run:
                self.log_test("下次执行时间", True, f"下次运行: {next_run}")
            else:
                self.log_test("下次执行时间", False, "无法计算下次执行时间")
            
            # 测试手动执行（不实际运行完整分析）
            print("🔍 调度器功能验证完成（未执行实际任务以避免重复分析）")
            
            return True
            
        except Exception as e:
            self.log_test("调度器测试", False, f"调度器测试失败: {e}")
            return False
    
    def generate_test_report(self):
        """生成测试报告"""
        print("\n" + "="*80)
        print("📊 测试报告总结")
        print("="*80)
        
        total_tests = len(self.test_results)
        passed_tests = sum(1 for result in self.test_results.values() if result['success'])
        failed_tests = total_tests - passed_tests
        
        print(f"📈 总测试数: {total_tests}")
        print(f"✅ 通过: {passed_tests}")
        print(f"❌ 失败: {failed_tests}")
        print(f"📊 成功率: {(passed_tests/total_tests*100):.1f}%")
        
        print(f"\n📋 详细结果:")
        for test_name, result in self.test_results.items():
            status = "✅" if result['success'] else "❌"
            print(f"{status} {test_name}: {result['message']}")
        
        # 保存测试报告
        report_file = Path("test_report.json")
        with open(report_file, 'w', encoding='utf-8') as f:
            json.dump(self.test_results, f, ensure_ascii=False, indent=2)
        
        print(f"\n💾 详细测试报告已保存到: {report_file}")
        
        return passed_tests == total_tests
    
    async def run_all_tests(self):
        """运行所有测试"""
        print("🧪 开始完整测试流程...")
        print("="*80)
        
        # 按顺序执行所有测试
        test_steps = [
            self.test_1_environment_setup,
            self.test_2_github_integration,
            self.test_3_content_parsing,
            self.test_4_glm_analysis,
            self.test_5_end_to_end,
            self.test_6_scheduler
        ]
        
        for i, test_func in enumerate(test_steps, 1):
            try:
                success = await test_func()
                if not success:
                    print(f"\n⚠️ 第{i}步测试失败，但继续执行后续测试...")
            except Exception as e:
                print(f"\n❌ 第{i}步测试异常: {e}")
        
        # 生成最终报告
        overall_success = self.generate_test_report()
        
        if overall_success:
            print("\n🎉 所有测试通过！服务已准备就绪。")
        else:
            print("\n⚠️ 部分测试失败，请检查配置和网络连接。")
        
        return overall_success


async def main():
    """主函数"""
    print("🚀 GitHub Discussions 自动化分析服务 - 完整测试")
    print("="*80)
    
    # 检查基本环境
    if not Path(".env").exists():
        print("❌ 未找到 .env 配置文件")
        print("\n请先创建 .env 文件并配置以下信息:")
        print("GITHUB_TOKEN=你的GitHub令牌")
        print("GITHUB_ORG=你的GitHub组织")
        print("GITHUB_REPO=你的仓库名")
        print("GLM_API_KEY=你的GLM API密钥")
        print("\n然后重新运行测试。")
        return False
    
    # 创建测试套件并运行
    test_suite = FullTestSuite()
    success = await test_suite.run_all_tests()
    
    return success


if __name__ == "__main__":
    success = asyncio.run(main())
    sys.exit(0 if success else 1)
