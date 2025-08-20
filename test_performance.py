#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
性能测试脚本
测试GitHub API和GLM API的响应时间和稳定性
"""

import asyncio
import time
import sys
from pathlib import Path

# 添加项目根目录到Python路径
sys.path.append(str(Path(__file__).parent))

from src.config import Config
from src.clients.github_client import GitHubClient
from src.clients.glm_client import GLMClient


async def test_github_performance(github_client: GitHubClient, rounds: int = 3):
    """测试GitHub API性能"""
    print("📊 测试GitHub API响应时间...")
    
    times = []
    for i in range(rounds):
        try:
            start_time = time.time()
            rate_limit = await github_client.check_api_rate_limit()
            response_time = time.time() - start_time
            times.append(response_time)
            
            print(f"  第{i+1}轮: {response_time:.2f}秒")
            if i == 0:  # 只在第一轮显示详细信息
                print(f"  📈 剩余请求数: {rate_limit.get('remaining', '未知')}")
                print(f"  🔄 重置时间: {rate_limit.get('reset_time', '未知')}")
                
        except Exception as e:
            print(f"  ❌ 第{i+1}轮失败: {e}")
            return None
    
    avg_time = sum(times) / len(times)
    min_time = min(times)
    max_time = max(times)
    
    print(f"✅ GitHub API性能统计:")
    print(f"  平均响应时间: {avg_time:.2f}秒")
    print(f"  最快响应时间: {min_time:.2f}秒")
    print(f"  最慢响应时间: {max_time:.2f}秒")
    
    return {
        'average': avg_time,
        'min': min_time,
        'max': max_time,
        'times': times
    }


async def test_glm_performance(glm_client: GLMClient, rounds: int = 3):
    """测试GLM API性能"""
    print("\n🤖 测试GLM API响应时间...")
    
    test_daily_summary = "今天完成了代码测试工作，遇到了一些API调用问题但已解决。"
    test_daily_plan = "明天计划继续优化代码性能，完成文档编写。"
    test_weekly_plan = "本周目标是完成项目的核心功能开发和测试。"
    
    times = []
    for i in range(rounds):
        try:
            start_time = time.time()
            response = await glm_client.generate_comprehensive_analysis(
                daily_summary=test_daily_summary,
                daily_plan=test_daily_plan,
                weekly_plan=test_weekly_plan
            )
            response_time = time.time() - start_time
            times.append(response_time)
            
            print(f"  第{i+1}轮: {response_time:.2f}秒")
            if i == 0:  # 只在第一轮显示响应长度
                print(f"  📝 响应长度: {len(response)}字符")
                
        except Exception as e:
            print(f"  ❌ 第{i+1}轮失败: {e}")
            return None
    
    avg_time = sum(times) / len(times)
    min_time = min(times)
    max_time = max(times)
    
    print(f"✅ GLM API性能统计:")
    print(f"  平均响应时间: {avg_time:.2f}秒")
    print(f"  最快响应时间: {min_time:.2f}秒")
    print(f"  最慢响应时间: {max_time:.2f}秒")
    
    return {
        'average': avg_time,
        'min': min_time,
        'max': max_time,
        'times': times
    }


async def main():
    """主测试函数"""
    print("🚀 开始API性能测试...")
    print("=" * 50)
    
    try:
        # 初始化配置和客户端
        config = Config()
        github_client = GitHubClient(config.github)
        glm_client = GLMClient(config.glm)
        
        total_start_time = time.time()
        
        # 测试GitHub API
        github_results = await test_github_performance(github_client)
        
        # 测试GLM API
        glm_results = await test_glm_performance(glm_client)
        
        total_time = time.time() - total_start_time
        
        # 输出总结
        print("\n" + "=" * 50)
        print("📊 性能测试总结:")
        print(f"⏱️ 总测试时间: {total_time:.2f}秒")
        
        if github_results:
            print(f"🐙 GitHub API平均响应: {github_results['average']:.2f}秒")
            if github_results['average'] < 2.0:
                print("  ✅ GitHub API响应速度良好")
            elif github_results['average'] < 5.0:
                print("  ⚠️ GitHub API响应速度一般")
            else:
                print("  ❌ GitHub API响应速度较慢")
        
        if glm_results:
            print(f"🤖 GLM API平均响应: {glm_results['average']:.2f}秒")
            if glm_results['average'] < 5.0:
                print("  ✅ GLM API响应速度良好")
            elif glm_results['average'] < 10.0:
                print("  ⚠️ GLM API响应速度一般")
            else:
                print("  ❌ GLM API响应速度较慢")
        
        # 稳定性评估
        if github_results and glm_results:
            github_stability = (github_results['max'] - github_results['min']) / github_results['average']
            glm_stability = (glm_results['max'] - glm_results['min']) / glm_results['average']
            
            print(f"\n📈 稳定性评估:")
            print(f"🐙 GitHub API稳定性: {(1-github_stability)*100:.1f}%")
            print(f"🤖 GLM API稳定性: {(1-glm_stability)*100:.1f}%")
            
            if github_stability < 0.2 and glm_stability < 0.3:
                print("✅ 整体API稳定性良好")
            else:
                print("⚠️ API响应时间波动较大，建议检查网络环境")
        
    except Exception as e:
        print(f"❌ 性能测试失败: {e}")
        return False
    
    return True


if __name__ == "__main__":
    success = asyncio.run(main())
    if success:
        print("\n🎉 性能测试完成!")
    else:
        print("\n💥 性能测试失败!")
        sys.exit(1)