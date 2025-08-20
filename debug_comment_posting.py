#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
调试评论发布功能

检查为什么分析评论没有真正发布到GitHub讨论中
"""

import asyncio
import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.config import Config
from src.clients.github_client import GitHubClient
from src.clients.glm_client import GLMClient
from src.utils.logger import get_logger

async def debug_comment_posting():
    """
    调试评论发布功能
    """
    print("=" * 80)
    print("调试评论发布功能")
    print("=" * 80)
    
    try:
        # 初始化配置
        config = Config()
        github_client = GitHubClient(config.github)
        glm_client = GLMClient(config.glm)
        
        print("\n1. 检查GitHub连接...")
        github_connected = await github_client.test_connection()
        print(f"GitHub连接状态: {'成功' if github_connected else '失败'}")
        
        if not github_connected:
            print("GitHub连接失败，无法继续测试")
            return
        
        print("\n2. 检查GLM连接...")
        glm_connected = await glm_client.test_connection()
        print(f"GLM连接状态: {'成功' if glm_connected else '失败'}")
        
        if not glm_connected:
            print("GLM连接失败，无法继续测试")
            return
        
        print("\n3. 获取讨论#64的内容...")
        discussions = await github_client.get_daily_discussions()
        target_discussion = None
        for discussion in discussions:
            if discussion.number == 64:
                target_discussion = discussion
                break
        
        if not target_discussion:
            print("未找到讨论#64")
            return
        
        print(f"找到讨论: #{target_discussion.number} - {target_discussion.title}")
        
        # 提取内容
        content_data = await github_client.extract_daily_content(target_discussion)
        print(f"\n提取的内容:")
        print(f"- 日报: {len(content_data['daily_summary'])} 字符")
        print(f"- 日计划: {len(content_data['daily_plan'])} 字符")
        print(f"- 周计划: {len(content_data['weekly_plan'])} 字符")
        
        print("\n4. 测试生成分析内容...")
        
        # 测试日报分析
        if content_data['daily_summary']:
            print("\n生成日报分析...")
            daily_report_analysis = await glm_client.analyze_daily_report_content(
                daily_summary=content_data['daily_summary'],
                daily_plan=content_data['daily_plan']
            )
            print(f"日报分析生成成功: {len(daily_report_analysis)} 字符")
            print(f"分析内容预览: {daily_report_analysis[:200]}...")
            
            # 测试发布评论
            print("\n尝试发布日报分析评论...")
            comment_success = await github_client.post_analysis_comment(
                target_discussion.number, 
                daily_report_analysis
            )
            print(f"评论发布结果: {'成功' if comment_success else '失败'}")
            
            if comment_success:
                print("\n等待3秒后检查最新评论...")
                await asyncio.sleep(3)
                
                # 重新获取评论检查
                comments = await github_client.get_discussion_comments(target_discussion.number)
                if comments:
                    latest_comment = max(comments, key=lambda x: x.updated_at)
                    print(f"最新评论作者: {latest_comment.author}")
                    print(f"最新评论时间: {latest_comment.updated_at}")
                    print(f"最新评论长度: {len(latest_comment.body)} 字符")
                    print(f"最新评论预览: {latest_comment.body[:200]}...")
                    
                    # 检查是否是分析评论
                    is_analysis = any(keyword in latest_comment.body for keyword in [
                        '## 📊 日报分析', '## 📋 日计划分析', '## 📈 综合分析'
                    ])
                    print(f"是否为分析评论: {'是' if is_analysis else '否'}")
                else:
                    print("未找到任何评论")
            else:
                print("评论发布失败，检查错误原因...")
                
                # 检查API限制
                rate_limit = await github_client.check_api_rate_limit()
                print(f"API限制信息: {rate_limit}")
        
        # 测试日计划分析
        if content_data['daily_plan']:
            print("\n\n生成日计划分析...")
            daily_plan_analysis = await glm_client.analyze_daily_plan_content(
                daily_plan=content_data['daily_plan'],
                weekly_plan=content_data['weekly_plan']
            )
            print(f"日计划分析生成成功: {len(daily_plan_analysis)} 字符")
            print(f"分析内容预览: {daily_plan_analysis[:200]}...")
            
            # 不实际发布，只是测试生成
            print("日计划分析生成测试完成（未发布）")
        
        print("\n" + "=" * 80)
        print("调试完成")
        print("=" * 80)
        
    except Exception as e:
        print(f"\n调试过程中出错: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(debug_comment_posting())
