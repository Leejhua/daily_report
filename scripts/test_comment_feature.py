#!/usr/bin/env python3
"""
评论功能测试脚本
专门测试GitHub Discussions评论发布功能
"""

import asyncio
import sys
import json
from pathlib import Path
from datetime import datetime

# 添加项目根目录到Python路径
sys.path.append(str(Path(__file__).parent.parent))

from src.config import Config
from src.analyzers.daily_analyzer import DailyAnalyzer
from src.clients.github_client import GitHubClient


async def test_comment_posting():
    """测试评论发布功能"""
    print("💬 测试评论发布功能...")
    
    test_results = {
        'timestamp': datetime.now().isoformat(),
        'tests': [],
        'overall_success': True
    }
    
    try:
        config = Config()
        github_client = GitHubClient(config.github)
        
        # 测试1: 验证GitHub连接
        print("\n1️⃣ 验证GitHub连接...")
        try:
            github_connected = await github_client.test_connection()
            
            test_results['tests'].append({
                'name': 'GitHub连接测试',
                'success': github_connected,
                'details': '连接正常' if github_connected else '连接失败'
            })
            
            if github_connected:
                print("✅ GitHub连接正常")
            else:
                print("❌ GitHub连接失败")
                test_results['overall_success'] = False
                return test_results
                
        except Exception as e:
            print(f"❌ GitHub连接测试失败: {e}")
            test_results['tests'].append({
                'name': 'GitHub连接测试',
                'success': False,
                'details': f'连接异常: {e}'
            })
            test_results['overall_success'] = False
            return test_results
        
        # 测试2: 设置测试讨论
        print("\n2️⃣ 设置测试讨论...")
        try:
            # 使用已知存在的讨论编号进行测试
            discussion_number = 60  # 使用实际存在的讨论编号
            
            test_results['tests'].append({
                'name': '设置测试讨论',
                'success': True,
                'details': f'将使用讨论 #{discussion_number} 进行评论测试'
            })
            
            print(f"✅ 将使用讨论 #{discussion_number} 进行评论测试")
                
        except Exception as e:
            print(f"❌ 设置测试讨论失败: {e}")
            test_results['tests'].append({
                'name': '设置测试讨论',
                'success': False,
                'details': f'设置异常: {e}'
            })
            test_results['overall_success'] = False
            return test_results
        
        # 测试3: 生成测试分析内容
        print("\n3️⃣ 生成测试分析内容...")
        try:
            # 使用模拟的分析内容进行测试
            analysis_content = f"""## 📊 日结分析报告

### 📅 分析概览
- **分析时间**: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
- **讨论编号**: #{discussion_number}
- **分析类型**: 评论功能测试

### 🎯 执行情况分析
**今日完成度**: 85%

**主要成果**:
1. ✅ 完成了核心功能开发
2. ✅ 进行了单元测试
3. ⚠️ 文档更新待完善

### 📈 偏离度分析
**偏离度评分**: 0.15 (低偏离)

**分析结果**: 整体执行情况良好，与计划基本一致。

### 💡 清晰度分析
**清晰度评分**: 0.82 (良好)

**建议**: 建议在描述技术细节时增加更多具体信息。

### 🔄 一致性分析
**一致性评分**: 0.78 (良好)

**分析**: 日报内容与周计划保持较好的一致性。

### 📝 改进建议
1. 建议完善技术文档
2. 增加代码注释的详细程度
3. 考虑添加更多的测试用例

---
*本报告由 Cursor GLM 自动生成*"""
            
            test_results['tests'].append({
                'name': '生成分析内容',
                'success': True,
                'details': f'模拟分析内容长度: {len(analysis_content)} 字符'
            })
            
            print(f"✅ 生成模拟分析内容成功，长度: {len(analysis_content)} 字符")
                
        except Exception as e:
            print(f"❌ 生成分析内容异常: {e}")
            test_results['tests'].append({
                'name': '生成分析内容',
                'success': False,
                'details': f'生成异常: {e}'
            })
            test_results['overall_success'] = False
            return test_results
        
        # 测试4: 发布测试评论（实际发布）
        print("\n4️⃣ 发布测试评论...")
        print("⚠️  注意：这将在GitHub上实际发布一条测试评论")
        
        # 添加测试标识
        test_analysis_content = f"""## 🧪 评论功能测试

> **这是一条自动化测试评论，用于验证系统的评论发布功能**
> 
> 测试时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}

---

{analysis_content}

---

*本评论由Cursor GLM自动化测试系统生成*"""
        
        try:
            comment_success = await github_client.post_analysis_comment(
                discussion_number, 
                test_analysis_content
            )
            
            if comment_success:
                print("✅ 评论发布成功！")
                test_results['tests'].append({
                    'name': '发布评论',
                    'success': True,
                    'details': f'成功在讨论 #{discussion_number} 发布测试评论'
                })
                
            else:
                print("❌ 评论发布失败")
                test_results['tests'].append({
                    'name': '发布评论',
                    'success': False,
                    'details': '评论发布失败，未知原因'
                })
                test_results['overall_success'] = False
                
        except Exception as e:
            print(f"❌ 评论发布异常: {e}")
            test_results['tests'].append({
                'name': '发布评论',
                'success': False,
                'details': f'发布异常: {e}'
            })
            test_results['overall_success'] = False
        
        # 测试5: 验证评论是否成功发布
        print("\n5️⃣ 验证评论发布结果...")
        try:
            # 获取讨论的最新评论
            comments = await github_client.get_discussion_comments(discussion_number)
            
            # 检查最新评论是否包含测试标识
            latest_comment = comments[-1] if comments else None
            
            if latest_comment and "评论功能测试" in latest_comment.body:
                print("✅ 评论验证成功，测试评论已正确发布")
                test_results['tests'].append({
                    'name': '验证评论发布',
                    'success': True,
                    'details': f'确认测试评论已发布，评论ID: {latest_comment.id}'
                })
                
            else:
                print("❌ 评论验证失败，未找到测试评论")
                test_results['tests'].append({
                    'name': '验证评论发布',
                    'success': False,
                    'details': '未找到测试评论或评论内容不匹配'
                })
                test_results['overall_success'] = False
                
        except Exception as e:
            print(f"❌ 评论验证异常: {e}")
            test_results['tests'].append({
                'name': '验证评论发布',
                'success': False,
                'details': f'验证异常: {e}'
            })
            test_results['overall_success'] = False
        
        return test_results
        
    except Exception as e:
        print(f"❌ 评论功能测试失败: {e}")
        test_results['overall_success'] = False
        test_results['error'] = str(e)
        return test_results


async def main():
    """主函数"""
    print("🚀 开始评论功能测试")
    print("="*50)
    
    # 运行评论功能测试
    results = await test_comment_posting()
    
    # 输出测试结果
    print("\n" + "="*50)
    print("📊 测试结果汇总")
    print("="*50)
    
    success_count = sum(1 for test in results['tests'] if test['success'])
    total_count = len(results['tests'])
    success_rate = (success_count / total_count * 100) if total_count > 0 else 0
    
    print(f"✅ 成功测试: {success_count}/{total_count}")
    print(f"📈 成功率: {success_rate:.1f}%")
    print(f"🎯 整体状态: {'通过' if results['overall_success'] else '失败'}")
    
    # 详细测试结果
    print("\n📋 详细测试结果:")
    for i, test in enumerate(results['tests'], 1):
        status = "✅" if test['success'] else "❌"
        print(f"{i}. {status} {test['name']}: {test['details']}")
    
    # 保存测试报告
    report_file = Path(__file__).parent.parent / "comment_test_report.json"
    with open(report_file, 'w', encoding='utf-8') as f:
        json.dump(results, f, ensure_ascii=False, indent=2)
    
    print(f"\n📄 测试报告已保存到: {report_file}")
    
    # 返回退出码
    return 0 if results['overall_success'] else 1


if __name__ == "__main__":
    exit_code = asyncio.run(main())
    sys.exit(exit_code)