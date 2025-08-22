#!/usr/bin/env python3
"""
简单修复缺失回复
"""

import asyncio
from src.clients.github_client import GitHubClient
from src.clients.glm_client import GLMClient
from src.config import Config

async def simple_fix():
    """
    简单修复
    """
    config = Config()
    github_client = GitHubClient(config.github)
    glm_client = GLMClient(config.glm)
    
    print("=" * 60)
    print("简单修复缺失回复")
    print("=" * 60)
    
    # 目标信息
    discussion_number = 62
    comment_id = "DC_kwDOPMm80c4A2EJS"
    
    # 日计划内容（从诊断结果中获取）
    daily_plan_content = """# 日计划 （8月22日）
1. 招聘工具需求PRD整理，包括JD分析、简历分析、面试提问建议、面试报告
2. 翻译工具本地化文本优化
3. 团队考核和管理复盘"""
    
    # 周计划内容（假设为空或使用通用内容）
    weekly_plan_content = ""
    
    try:
        print(f"📋 目标讨论: #{discussion_number}")
        print(f"📝 目标评论: {comment_id}")
        print(f"📊 日计划内容: {daily_plan_content}")
        
        # 1. 生成日计划分析
        print(f"\n🔄 生成日计划分析...")
        analysis = await glm_client.analyze_daily_plan_content(
            daily_plan=daily_plan_content,
            weekly_plan=weekly_plan_content
        )
        
        if not analysis or analysis.startswith("## ❌"):
            print(f"❌ 分析生成失败: {analysis[:100] if analysis else 'None'}...")
            return
            
        print(f"✅ 分析生成成功，长度: {len(analysis)} 字符")
        print(f"📝 分析预览: {analysis[:300]}...")
        
        # 2. 发布分析回复
        print(f"\n📤 发布分析回复...")
        success = await github_client.post_analysis_comment(
            discussion_number=discussion_number,
            analysis_content=analysis,
            reply_to_comment_id=comment_id,
            content_type='daily_plan'
        )
        
        if success:
            print(f"🎉 分析回复发布成功！")
        else:
            print(f"❌ 分析回复发布失败")
            
    except Exception as e:
        print(f"❌ 修复过程中发生错误: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(simple_fix())