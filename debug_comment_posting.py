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
        
        print("\n3. 获取讨论#62的内容...")
        discussions = await github_client.get_daily_discussions()
        target_discussion = None
        for discussion in discussions:
            if discussion.number == 62:
                target_discussion = discussion
                break
        
        if not target_discussion:
            print("未找到讨论#62")
            return
        
        print(f"找到讨论: #{target_discussion.number} - {target_discussion.title}")
        
        # 提取内容
        content_data = await github_client.extract_daily_content(target_discussion)
        print(f"\n提取的内容:")
        print(f"- 日报: {len(content_data['daily_summary'])} 字符")
        print(f"- 日计划: {len(content_data['daily_plan'])} 字符")
        print(f"- 周计划: {len(content_data['weekly_plan'])} 字符")
        
        print("\n4. 测试生成分析内容...")
        
        # 获取讨论评论
        print("\n4. 获取讨论评论...")
        comments = await github_client.get_discussion_comments(target_discussion.number)
        print(f"找到 {len(comments)} 条评论")
        
        # 查找特定的评论ID: DC_kwDOPMm80c4A2IFa
        target_comment = None
        for comment in comments:
            author_name = comment.author.login if hasattr(comment.author, 'login') else comment.author
            if comment.id == "DC_kwDOPMm80c4A2IFa" and author_name == "goudaren0528":
                target_comment = comment
                break
        
        if target_comment:
            print(f"\n🎯 找到目标评论 DC_kwDOPMm80c4A2IFa")
            author_name = target_comment.author.login if hasattr(target_comment.author, 'login') else target_comment.author
            print(f"   作者: {author_name}")
            print(f"   时间: {target_comment.created_at}")
            
            # 检查是否已有回复
            has_target_reply = await github_client.check_already_replied(
                62, target_comment.id, 'daily_summary'
            )
            print(f"   已有分析回复: {has_target_reply}")
            
            if not has_target_reply:
                print(f"\n🧪 为目标评论发布日报分析...")
                test_content = "## 📊 日报分析\n\n【内容问题】\n- 日报中提到'已经实现了简历筛选能力和其他页面'，但没有具体说明实现了哪些功能或页面，缺乏具体细节。\n- 日报中提到'还停留在思考阶段，还没开始梳理文档'，对于预计完成时间'下周一完成'缺乏具体的计划或步骤说明。\n\n【偏离判断】\n- 从日报内容来看，工作进度与计划存在一定程度的偏离。原计划中第二项任务'把翻译工具的界面本地化文本测试后发布'已经完成，但第三项任务'整理团队项目清单和下一周期考核目标'仍在思考阶段，进度较慢。"
                
                success = await github_client.post_analysis_comment(
                    62, test_content, target_comment.id, 'daily_summary'
                )
                
                if success:
                    print("✅ 目标评论分析回复发布成功！")
                else:
                    print("❌ 目标评论分析回复发布失败")
            else:
                print("⚠️  目标评论已有分析回复")
        else:
            print("❌ 未找到目标评论 DC_kwDOPMm80c4A2IFa")
        
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