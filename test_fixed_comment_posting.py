#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
测试修复后的评论发布功能

这个脚本用于测试修复后的评论发布功能，
确保分析评论能作为顶级评论正确发布。
"""

import asyncio
import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.config import Config
from src.clients.github_client import GitHubClient
from src.clients.glm_client import GLMClient
from src.utils.logger import get_logger

async def test_fixed_comment_posting():
    """
    测试修复后的评论发布功能
    """
    print("=" * 80)
    print("测试修复后的评论发布功能")
    print("=" * 80)
    
    try:
        # 初始化配置和客户端
        config = Config()
        github_client = GitHubClient(config.github)
        glm_client = GLMClient(config.glm)
        logger = get_logger(__name__)
        
        print("\n1. 测试连接...")
        github_ok = await github_client.test_connection()
        glm_ok = await glm_client.test_connection()
        
        if not github_ok or not glm_ok:
            print(f"连接测试失败 - GitHub: {github_ok}, GLM: {glm_ok}")
            return
        
        print("✅ 连接测试成功")
        
        print("\n2. 获取讨论#64的内容...")
        discussions = await github_client.get_daily_discussions()
        target_discussion = None
        
        for discussion in discussions:
            if discussion.number == 64:
                target_discussion = discussion
                break
        
        if not target_discussion:
            print("❌ 未找到讨论#64")
            return
        
        print(f"✅ 找到讨论#64: {target_discussion.title}")
        
        print("\n3. 提取内容...")
        content_data = await github_client.extract_daily_content(target_discussion)
        
        daily_summary = content_data.get('daily_summary', '')
        daily_plan = content_data.get('daily_plan', '')
        weekly_plan = content_data.get('weekly_plan', '')
        
        print(f"   日报内容: {len(daily_summary)} 字符")
        print(f"   日计划内容: {len(daily_plan)} 字符")
        print(f"   周计划内容: {len(weekly_plan)} 字符")
        
        if not daily_summary and not daily_plan:
            print("❌ 未提取到有效内容")
            return
        
        print("\n4. 生成测试分析评论...")
        test_analysis = f"""## 🧪 测试分析评论

**测试时间**: {asyncio.get_event_loop().time()}
**测试目的**: 验证修复后的评论发布功能

### 修复内容
- 将分析评论改为顶级评论发布
- 移除了replyToId参数
- 用户现在可以直接看到分析评论

### 测试结果
如果您能看到这条评论作为独立的顶级评论出现在讨论中，说明修复成功！

---
*本测试评论由系统自动生成*
"""
        
        print("\n5. 发布测试评论...")
        comment_success = await github_client.post_analysis_comment(
            target_discussion.number,
            test_analysis
        )
        
        if comment_success:
            print("✅ 测试评论发布成功！")
            print("\n请检查GitHub讨论页面，确认评论是否作为顶级评论显示")
        else:
            print("❌ 测试评论发布失败")
        
        print("\n6. 检查最新评论...")
        comments = await github_client.get_discussion_comments(target_discussion.number)
        
        if comments:
            latest_comment = comments[0]  # 最新评论
            print(f"\n最新评论信息:")
            print(f"   作者: {latest_comment.author}")
            print(f"   时间: {latest_comment.created_at}")
            print(f"   内容长度: {len(latest_comment.body)} 字符")
            
            # 检查是否是我们刚发布的测试评论
            if "🧪 测试分析评论" in latest_comment.body:
                print("✅ 确认：测试评论已成功发布为顶级评论")
            else:
                print("⚠️  最新评论不是我们刚发布的测试评论")
        else:
            print("❌ 未获取到任何评论")
        
        print("\n" + "=" * 80)
        print("测试完成")
        print("=" * 80)
        
        print("\n📋 测试总结:")
        print(f"- 评论发布: {'成功' if comment_success else '失败'}")
        print(f"- 评论类型: 顶级评论（不再是回复）")
        print(f"- 用户可见性: 应该可以直接在讨论页面看到")
        
        if comment_success:
            print("\n🎉 修复成功！用户现在应该能够直接看到分析评论了。")
        else:
            print("\n❌ 修复可能存在问题，需要进一步调试。")
        
    except Exception as e:
        print(f"\n测试过程中出错: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(test_fixed_comment_posting())