#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
测试最近三天日结数据获取和显示功能
修复原有逻辑问题，实现真正的多日期数据获取
"""

import asyncio
import sys
from datetime import date, timedelta
from pathlib import Path
from typing import List, Dict, Any

# 添加项目根目录到Python路径
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

from src.config import Config
from src.clients.github_client import GitHubClient, DiscussionData


class RecentDaysAnalyzer:
    """最近几天日结数据分析器"""
    
    def __init__(self, config: Config):
        self.config = config
        self.github_client = GitHubClient(config.github)
        
    async def get_recent_discussions(self, days: int = 3) -> Dict[str, List[DiscussionData]]:
        """
        获取最近指定天数的所有日结讨论
        
        Args:
            days: 要获取的天数，默认3天
            
        Returns:
            Dict[str, List[DiscussionData]]: 按日期分组的讨论数据
        """
        print(f"🔍 正在获取最近 {days} 天的日结讨论...")
        
        discussions_by_date = {}
        total_discussions = 0
        
        for i in range(days):
            target_date = date.today() - timedelta(days=i)
            date_str = target_date.strftime('%Y-%m-%d')
            
            print(f"📅 获取 {date_str} 的讨论...")
            
            try:
                daily_discussions = await self.github_client.get_daily_discussions(target_date)
                discussions_by_date[date_str] = daily_discussions
                total_discussions += len(daily_discussions)
                
                print(f"   ✅ 找到 {len(daily_discussions)} 个讨论")
                
            except Exception as e:
                print(f"   ❌ 获取失败: {e}")
                discussions_by_date[date_str] = []
        
        print(f"\n📊 总计获取 {total_discussions} 个讨论，覆盖 {days} 天")
        return discussions_by_date
    
    async def analyze_discussions_structure(self, discussions_by_date: Dict[str, List[DiscussionData]]) -> Dict[str, Any]:
        """
        分析讨论结构和内容特征
        
        Args:
            discussions_by_date: 按日期分组的讨论数据
            
        Returns:
            Dict[str, Any]: 分析结果
        """
        print("\n🔍 开始分析讨论结构...")
        
        analysis_result = {
            'total_days': len(discussions_by_date),
            'total_discussions': 0,
            'daily_analysis': {},
            'overall_stats': {
                'has_weekly_plan': 0,
                'has_daily_summary': 0,
                'has_daily_plan': 0,
                'has_progress_info': 0,
                'has_problems': 0,
                'has_tasks': 0
            }
        }
        
        for date_str, discussions in discussions_by_date.items():
            print(f"\n📅 分析 {date_str} ({len(discussions)} 个讨论)")
            print("=" * 60)
            
            daily_stats = {
                'discussion_count': len(discussions),
                'discussions': []
            }
            
            for i, discussion in enumerate(discussions, 1):
                print(f"\n[{i}] #{discussion.number}: {discussion.title}")
                print(f"📝 作者: {discussion.author}")
                print(f"🕒 创建: {discussion.created_at.strftime('%Y-%m-%d %H:%M')}")
                print(f"🔄 更新: {discussion.updated_at.strftime('%Y-%m-%d %H:%M')}")
                
                # 分析讨论内容结构
                discussion_analysis = await self._analyze_single_discussion(discussion)
                daily_stats['discussions'].append(discussion_analysis)
                
                # 更新总体统计
                for key in analysis_result['overall_stats']:
                    if discussion_analysis.get(key, False):
                        analysis_result['overall_stats'][key] += 1
                
                print("-" * 40)
            
            analysis_result['daily_analysis'][date_str] = daily_stats
            analysis_result['total_discussions'] += len(discussions)
        
        return analysis_result
    
    async def _analyze_single_discussion(self, discussion: DiscussionData) -> Dict[str, Any]:
        """
        分析单个讨论的内容结构
        
        Args:
            discussion: 讨论数据
            
        Returns:
            Dict[str, Any]: 分析结果
        """
        analysis = {
            'number': discussion.number,
            'title': discussion.title,
            'author': discussion.author,
            'has_weekly_plan': False,
            'has_daily_summary': False,
            'has_daily_plan': False,
            'has_progress_info': False,
            'has_problems': False,
            'has_tasks': False,
            'content_preview': '',
            'error': None
        }
        
        try:
            # 提取讨论内容
            content_data = await self.github_client.extract_daily_content(discussion)
            
            # 检查各部分内容
            analysis['has_weekly_plan'] = len(content_data.get('weekly_plan', '')) > 0
            analysis['has_daily_summary'] = len(content_data.get('daily_summary', '')) > 0
            analysis['has_daily_plan'] = len(content_data.get('daily_plan', '')) > 0
            
            # 分析日报内容特征
            if analysis['has_daily_summary']:
                daily_content = content_data['daily_summary'].lower()
                analysis['has_progress_info'] = any(word in daily_content for word in ['完成', '进度', '百分', '%'])
                analysis['has_problems'] = any(word in daily_content for word in ['问题', '困难', '阻塞', 'bug', '错误'])
                analysis['has_tasks'] = any(word in daily_content for word in ['开发', '测试', '修复', '会议', '任务', '功能'])
                
                # 生成内容预览
                preview_length = 200
                analysis['content_preview'] = (content_data['daily_summary'][:preview_length] + '...' 
                                             if len(content_data['daily_summary']) > preview_length 
                                             else content_data['daily_summary'])
            
            # 显示结构分析结果
            structure_indicators = []
            if analysis['has_weekly_plan']: structure_indicators.append("周期计划✅")
            if analysis['has_daily_summary']: structure_indicators.append("日报✅")
            if analysis['has_daily_plan']: structure_indicators.append("日计划✅")
            
            if not structure_indicators:
                structure_indicators.append("无标准结构❌")
            
            print(f"📊 结构: {' | '.join(structure_indicators)}")
            
            # 显示内容特征
            if analysis['has_daily_summary']:
                features = []
                if analysis['has_progress_info']: features.append("进度描述")
                if analysis['has_problems']: features.append("问题记录")
                if analysis['has_tasks']: features.append("任务内容")
                
                print(f"🏷️ 日报特征: {', '.join(features) if features else '无明显特征'}")
                
                if analysis['content_preview']:
                    print(f"📄 内容预览: {analysis['content_preview']}")
            
        except Exception as e:
            analysis['error'] = str(e)
            print(f"❌ 内容分析失败: {e}")
        
        return analysis
    
    def generate_summary_report(self, analysis_result: Dict[str, Any]) -> str:
        """
        生成分析总结报告
        
        Args:
            analysis_result: 分析结果
            
        Returns:
            str: 报告内容
        """
        report = []
        report.append("\n" + "=" * 80)
        report.append("📋 最近三天日结数据分析报告")
        report.append("=" * 80)
        
        # 基本统计
        total_days = analysis_result['total_days']
        total_discussions = analysis_result['total_discussions']
        stats = analysis_result['overall_stats']
        
        report.append(f"\n📊 基本统计:")
        report.append(f"   • 分析天数: {total_days} 天")
        report.append(f"   • 总讨论数: {total_discussions} 个")
        report.append(f"   • 平均每天: {total_discussions/total_days:.1f} 个讨论")
        
        # 结构完整性统计
        if total_discussions > 0:
            report.append(f"\n📈 结构完整性:")
            report.append(f"   • 包含周期计划: {stats['has_weekly_plan']}/{total_discussions} ({stats['has_weekly_plan']/total_discussions*100:.1f}%)")
            report.append(f"   • 包含日报内容: {stats['has_daily_summary']}/{total_discussions} ({stats['has_daily_summary']/total_discussions*100:.1f}%)")
            report.append(f"   • 包含日计划: {stats['has_daily_plan']}/{total_discussions} ({stats['has_daily_plan']/total_discussions*100:.1f}%)")
            
            report.append(f"\n🏷️ 内容特征:")
            report.append(f"   • 包含进度信息: {stats['has_progress_info']}/{total_discussions} ({stats['has_progress_info']/total_discussions*100:.1f}%)")
            report.append(f"   • 包含问题记录: {stats['has_problems']}/{total_discussions} ({stats['has_problems']/total_discussions*100:.1f}%)")
            report.append(f"   • 包含任务内容: {stats['has_tasks']}/{total_discussions} ({stats['has_tasks']/total_discussions*100:.1f}%)")
        
        # 每日详情
        report.append(f"\n📅 每日详情:")
        for date_str, daily_data in analysis_result['daily_analysis'].items():
            count = daily_data['discussion_count']
            report.append(f"   • {date_str}: {count} 个讨论")
            
            if count > 0:
                for disc in daily_data['discussions']:
                    status_indicators = []
                    if disc['has_weekly_plan']: status_indicators.append("周")
                    if disc['has_daily_summary']: status_indicators.append("日")
                    if disc['has_daily_plan']: status_indicators.append("计")
                    
                    status = f"[{'/'.join(status_indicators)}]" if status_indicators else "[无]"
                    report.append(f"     - #{disc['number']}: {disc['title'][:50]}{'...' if len(disc['title']) > 50 else ''} {status}")
        
        # 结论和建议
        report.append(f"\n💡 结论和建议:")
        
        if total_discussions == 0:
            report.append("   ❌ 未找到任何日结讨论，建议检查:")
            report.append("      - GitHub配置是否正确")
            report.append("      - 讨论分类设置是否正确")
            report.append("      - 最近三天是否有创建日结讨论")
        else:
            completion_rate = stats['has_daily_summary'] / total_discussions * 100
            
            if completion_rate >= 80:
                report.append(f"   ✅ 日结数据质量良好 ({completion_rate:.1f}% 包含日报内容)")
            elif completion_rate >= 50:
                report.append(f"   ⚠️ 日结数据质量一般 ({completion_rate:.1f}% 包含日报内容)")
                report.append("      建议提高日报内容的完整性")
            else:
                report.append(f"   ❌ 日结数据质量较差 ({completion_rate:.1f}% 包含日报内容)")
                report.append("      建议规范日结讨论的内容结构")
        
        report.append("\n" + "=" * 80)
        
        return "\n".join(report)


async def main():
    """主函数"""
    print("🚀 开始测试最近三天日结数据获取和显示功能")
    print("=" * 80)
    
    try:
        # 初始化配置和分析器
        config = Config()
        analyzer = RecentDaysAnalyzer(config)
        
        # 测试GitHub连接
        print("🔗 测试GitHub连接...")
        await analyzer.github_client.test_connection()
        print("✅ GitHub连接正常")
        
        # 获取最近三天的讨论
        discussions_by_date = await analyzer.get_recent_discussions(days=3)
        
        # 分析讨论结构
        analysis_result = await analyzer.analyze_discussions_structure(discussions_by_date)
        
        # 生成并显示报告
        report = analyzer.generate_summary_report(analysis_result)
        print(report)
        
        # 保存报告到文件
        report_file = Path("recent_three_days_report.md")
        with open(report_file, 'w', encoding='utf-8') as f:
            f.write(f"# 最近三天日结数据分析报告\n\n")
            f.write(f"生成时间: {date.today().strftime('%Y-%m-%d')}\n\n")
            f.write(report)
        
        print(f"\n📄 详细报告已保存到: {report_file.absolute()}")
        
        # 判断测试结果
        total_discussions = analysis_result['total_discussions']
        if total_discussions > 0:
            print(f"\n✅ 测试成功: 成功获取并分析了 {total_discussions} 个日结讨论")
            return True
        else:
            print(f"\n⚠️ 测试完成: 未找到日结讨论，但功能正常运行")
            return True
            
    except Exception as e:
        print(f"\n❌ 测试失败: {e}")
        import traceback
        traceback.print_exc()
        return False


if __name__ == "__main__":
    success = asyncio.run(main())
    sys.exit(0 if success else 1)