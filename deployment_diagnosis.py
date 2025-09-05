#!/usr/bin/env python3
"""
部署环境诊断脚本
用于检查GitHub Discussions自动化分析服务的部署状态和配置问题
"""

import os
import sys
import json
import asyncio
import logging
from pathlib import Path
from datetime import datetime
from typing import Dict, List, Any

# 添加项目根目录到Python路径
sys.path.append(str(Path(__file__).parent))

try:
    from src.config import Config
    from src.clients.github_client import GitHubClient
    from src.utils.logger import setup_logging
except ImportError as e:
    print(f"❌ 导入模块失败: {e}")
    print("请确保在项目根目录运行此脚本")
    sys.exit(1)


class DeploymentDiagnostic:
    """部署诊断器"""
    
    def __init__(self):
        self.logger = logging.getLogger(__name__)
        self.issues = []
        self.warnings = []
        self.success_items = []
        
    def add_issue(self, message: str):
        """添加问题"""
        self.issues.append(message)
        self.logger.error(f"❌ {message}")
        
    def add_warning(self, message: str):
        """添加警告"""
        self.warnings.append(message)
        self.logger.warning(f"⚠️ {message}")
        
    def add_success(self, message: str):
        """添加成功项"""
        self.success_items.append(message)
        self.logger.info(f"✅ {message}")
        
    def check_python_environment(self) -> bool:
        """检查Python环境"""
        self.logger.info("🐍 检查Python环境...")
        
        # 检查Python版本
        python_version = sys.version_info
        if python_version.major == 3 and python_version.minor >= 8:
            self.add_success(f"Python版本: {python_version.major}.{python_version.minor}.{python_version.micro}")
        else:
            self.add_issue(f"Python版本过低: {python_version.major}.{python_version.minor}.{python_version.micro}，需要3.8+")
            return False
            
        # 检查必要的模块
        required_modules = [
            'asyncio', 'aiohttp', 'croniter', 'pydantic', 'pyyaml'
        ]
        
        for module in required_modules:
            try:
                __import__(module)
                self.add_success(f"模块 {module} 已安装")
            except ImportError:
                self.add_issue(f"缺少必要模块: {module}")
                return False
                
        return True
        
    def check_project_structure(self) -> bool:
        """检查项目结构"""
        self.logger.info("📁 检查项目结构...")
        
        required_files = [
            'src/main.py',
            'src/config.py',
            'src/scheduler.py',
            'config/config.yaml',
            'requirements.txt'
        ]
        
        missing_files = []
        for file_path in required_files:
            if not Path(file_path).exists():
                missing_files.append(file_path)
            else:
                self.add_success(f"文件存在: {file_path}")
                
        if missing_files:
            for file_path in missing_files:
                self.add_issue(f"缺少必要文件: {file_path}")
            return False
            
        return True
        
    def check_configuration(self) -> bool:
        """检查配置文件"""
        self.logger.info("⚙️ 检查配置文件...")
        
        try:
            config = Config()
            self.add_success("配置文件加载成功")
            
            # 检查GitHub配置
            if not config.github.organization:
                self.add_issue("GitHub组织名称未配置")
                return False
            else:
                self.add_success(f"GitHub组织: {config.github.organization}")
                
            if not config.github.discussion_category:
                self.add_issue("Discussion分类未配置")
                return False
            else:
                self.add_success(f"Discussion分类: {config.github.discussion_category}")
                
            # 检查use_org_discussions配置
            if config.github.use_org_discussions:
                if not config.github.repository:
                    self.add_success("使用组织级Discussions")
                else:
                    self.add_warning("配置了use_org_discussions=true但同时设置了repository")
            else:
                if not config.github.repository:
                    self.add_issue("use_org_discussions=false但未配置repository")
                    return False
                else:
                    self.add_success(f"使用仓库级Discussions: {config.github.repository}")
                    
            # 检查调度器配置
            if not config.scheduler.cron_expression:
                self.add_issue("调度器Cron表达式未配置")
                return False
            else:
                self.add_success(f"调度器Cron: {config.scheduler.cron_expression}")
                
            # 检查内容检查配置
            if hasattr(config, 'daily_content_check') and config.daily_content_check.enabled:
                if not config.daily_content_check.content_check_cron:
                    self.add_issue("内容检查Cron表达式未配置")
                    return False
                if not config.daily_content_check.analysis_cron:
                    self.add_issue("日常分析Cron表达式未配置")
                    return False
                self.add_success("内容检查配置正确")
            else:
                self.add_warning("内容检查功能未启用")
                
            return True
            
        except Exception as e:
            self.add_issue(f"配置文件加载失败: {e}")
            return False
            
    def check_environment_variables(self) -> bool:
        """检查环境变量"""
        self.logger.info("🌍 检查环境变量...")
        
        required_env_vars = {
            'GITHUB_TOKEN': '必需，用于GitHub API访问',
            'GLM_API_KEY': '必需，用于GLM模型访问'
        }
        
        optional_env_vars = {
            'GITHUB_ORG': '可选，GitHub组织名称',
            'GITHUB_REPO': '可选，GitHub仓库名称',
            'USE_ORG_DISCUSSIONS': '可选，是否使用组织级Discussions',
            'GLM_BASE_URL': '可选，GLM API基础URL',
            'LOG_LEVEL': '可选，日志级别'
        }
        
        missing_required = []
        for var, desc in required_env_vars.items():
            value = os.getenv(var)
            if not value:
                missing_required.append(f"{var} ({desc})")
            else:
                # 隐藏敏感信息
                display_value = value[:8] + '...' if len(value) > 8 else value
                self.add_success(f"环境变量 {var}: {display_value}")
                
        if missing_required:
            for var in missing_required:
                self.add_issue(f"缺少必需的环境变量: {var}")
            return False
            
        # 检查可选环境变量
        for var, desc in optional_env_vars.items():
            value = os.getenv(var)
            if value:
                self.add_success(f"环境变量 {var}: {value}")
            else:
                self.add_warning(f"未设置可选环境变量: {var} ({desc})")
                
        return True
        
    async def check_github_connectivity(self) -> bool:
        """检查GitHub连接"""
        self.logger.info("🔗 检查GitHub连接...")
        
        try:
            config = Config()
            github_client = GitHubClient(config.github)
            
            # 测试基本连接
            if config.github.use_org_discussions:
                discussions = await github_client.get_daily_discussions()
            else:
                discussions = await github_client.get_daily_discussions()
                
            self.add_success(f"GitHub连接正常，获取到 {len(discussions)} 个讨论")
            return True
            
        except Exception as e:
            self.add_issue(f"GitHub连接失败: {e}")
            return False
            
    def check_deployment_files(self) -> bool:
        """检查部署文件"""
        self.logger.info("🚀 检查部署文件...")
        
        deployment_files = {
            'Dockerfile': '用于Docker部署',
            'docker-compose.yml': '用于Docker Compose部署',
            'deploy/deploy.sh': '部署脚本',
            '.env.example': '环境变量示例文件'
        }
        
        for file_path, desc in deployment_files.items():
            if Path(file_path).exists():
                self.add_success(f"部署文件存在: {file_path} ({desc})")
            else:
                self.add_warning(f"部署文件缺失: {file_path} ({desc})")
                
        # 检查.env文件
        if Path('.env').exists():
            self.add_success("环境变量文件 .env 存在")
        else:
            self.add_warning("环境变量文件 .env 不存在，请从 .env.example 复制并配置")
            
        return True
        
    def check_log_directories(self) -> bool:
        """检查日志目录"""
        self.logger.info("📝 检查日志目录...")
        
        log_dirs = ['logs', 'data', 'reports']
        
        for dir_name in log_dirs:
            dir_path = Path(dir_name)
            if dir_path.exists():
                if dir_path.is_dir():
                    self.add_success(f"目录存在: {dir_name}")
                else:
                    self.add_issue(f"{dir_name} 存在但不是目录")
                    return False
            else:
                try:
                    dir_path.mkdir(exist_ok=True)
                    self.add_success(f"创建目录: {dir_name}")
                except Exception as e:
                    self.add_issue(f"无法创建目录 {dir_name}: {e}")
                    return False
                    
        return True
        
    def generate_report(self) -> Dict[str, Any]:
        """生成诊断报告"""
        report = {
            'timestamp': datetime.now().isoformat(),
            'summary': {
                'total_checks': len(self.success_items) + len(self.warnings) + len(self.issues),
                'success_count': len(self.success_items),
                'warning_count': len(self.warnings),
                'issue_count': len(self.issues),
                'overall_status': 'PASS' if len(self.issues) == 0 else 'FAIL'
            },
            'details': {
                'success_items': self.success_items,
                'warnings': self.warnings,
                'issues': self.issues
            }
        }
        
        return report
        
    def print_summary(self):
        """打印诊断摘要"""
        print("\n" + "=" * 60)
        print("📋 部署诊断摘要")
        print("=" * 60)
        
        print(f"✅ 成功项: {len(self.success_items)}")
        print(f"⚠️ 警告项: {len(self.warnings)}")
        print(f"❌ 问题项: {len(self.issues)}")
        
        if self.issues:
            print("\n🚨 需要解决的问题:")
            for i, issue in enumerate(self.issues, 1):
                print(f"  {i}. {issue}")
                
        if self.warnings:
            print("\n⚠️ 警告信息:")
            for i, warning in enumerate(self.warnings, 1):
                print(f"  {i}. {warning}")
                
        overall_status = "通过" if len(self.issues) == 0 else "失败"
        print(f"\n🎯 总体状态: {overall_status}")
        
        if len(self.issues) == 0:
            print("\n🎉 恭喜！部署环境检查通过，可以正常运行服务。")
        else:
            print("\n🔧 请解决上述问题后重新运行诊断。")
            
    async def run_full_diagnosis(self) -> bool:
        """运行完整诊断"""
        print("🔍 开始部署环境诊断...")
        print("=" * 60)
        
        checks = [
            ('Python环境', self.check_python_environment),
            ('项目结构', self.check_project_structure),
            ('配置文件', self.check_configuration),
            ('环境变量', self.check_environment_variables),
            ('日志目录', self.check_log_directories),
            ('部署文件', self.check_deployment_files),
            ('GitHub连接', self.check_github_connectivity)
        ]
        
        all_passed = True
        for check_name, check_func in checks:
            try:
                if asyncio.iscoroutinefunction(check_func):
                    result = await check_func()
                else:
                    result = check_func()
                    
                if not result:
                    all_passed = False
                    
            except Exception as e:
                self.add_issue(f"{check_name}检查失败: {e}")
                all_passed = False
                
        return all_passed


async def main():
    """主函数"""
    # 设置日志
    setup_logging()
    
    # 创建诊断器
    diagnostic = DeploymentDiagnostic()
    
    try:
        # 运行诊断
        success = await diagnostic.run_full_diagnosis()
        
        # 打印摘要
        diagnostic.print_summary()
        
        # 生成报告文件
        report = diagnostic.generate_report()
        report_file = Path('deployment_diagnosis_report.json')
        
        with open(report_file, 'w', encoding='utf-8') as f:
            json.dump(report, f, ensure_ascii=False, indent=2)
            
        print(f"\n📄 详细报告已保存到: {report_file}")
        
        # 返回适当的退出码
        sys.exit(0 if success else 1)
        
    except KeyboardInterrupt:
        print("\n⏹️ 诊断被用户中断")
        sys.exit(1)
    except Exception as e:
        print(f"\n💥 诊断过程中发生错误: {e}")
        sys.exit(1)


if __name__ == "__main__":
    asyncio.run(main())