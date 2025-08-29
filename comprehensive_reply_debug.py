#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
全面的GitHub回复调试脚本
用于诊断楼中楼回复失败的原因
"""

import asyncio
import os
from datetime import datetime, timezone
from typing import Dict, List, Optional, Any
import json

from src.config import Config
from src.clients.github_client import GitHubClient
from src.analyzers.daily_analyzer import DailyAnalyzer

class ComprehensiveReplyDebugger:
    """全面的回复调试器"""
    
    def __init__(self):
        self.config = Config()
        self.github_client = GitHubClient(self.config.github)
        self.daily_analyzer = DailyAnalyzer(self.config)
        
    async def debug_reply_flow(self):
        """调试完整的回复流程"""
        print("🔍 开始全面回复流程调试")
        print("=" * 60)
        
        # 使用固定的讨论编号进行测试
        # 这里使用一个已知的讨论编号，可以根据实际情况修改
        discussion_number = 1  # 替换为实际存在的讨论编号
        print(f"📋 使用固定讨论编号: #{discussion_number} 进行测试")
        
        # 2. 显示讨论的完整结构
        await self.show_discussion_structure(discussion_number)
        
        # 3. 测试_find_content_comment_id方法
        await self.test_find_comment_id(discussion_number)
        
        # 4. 测试check_already_replied方法
        await self.test_duplicate_check(discussion_number)
        
        # 5. 测试实际的post_analysis_comment方法
        await self.test_post_analysis_comment(discussion_number)
        
        # 6. 手动测试GraphQL回复
        await self.test_manual_graphql_reply(discussion_number)
        
        # 7. 对比分析
        await self.analyze_differences(discussion_number)
        
    async def get_today_discussion(self):
        """获取今天的讨论"""
        try:
            discussions = await self.github_client.get_daily_discussions()
            today = datetime.now().strftime("%Y-%m-%d")
            
            for discussion in discussions:
                if today in discussion.title:
                    return discussion
            return None
        except Exception as e:
            print(f"❌ 获取讨论失败: {e}")
            return None
            
    async def show_discussion_structure(self, discussion_number: int):
        """显示讨论的完整结构"""
        print("\n📊 讨论结构分析")
        print("-" * 40)
        
        try:
            # 获取结构化评论
            structured_comments = await self.github_client._get_all_comments_with_replies(discussion_number)
            
            print(f"顶级评论数量: {len(structured_comments['top_level'])}")
            
            for i, comment in enumerate(structured_comments['top_level']):
                print(f"\n📝 顶级评论 {i+1}:")
                print(f"   ID: {comment.id}")
                print(f"   作者: {comment.author.login if comment.author else '未知'}")
                print(f"   时间: {comment.created_at}")
                print(f"   内容预览: {comment.body[:100]}...")
                
                # 检查是否有回复
                if comment.id in structured_comments['replies']:
                    replies = structured_comments['replies'][comment.id]
                    print(f"   📬 回复数量: {len(replies)}")
                    
                    for j, reply in enumerate(replies):
                        print(f"      └─ 回复 {j+1}: {reply.author.login if reply.author else '未知'} - {reply.body[:50]}...")
                        
                        # 检查是否是分析回复
                        analysis_markers = [
                            '本分析由GLM-4.5自动生成', '📋 日报分析', '📋 日计划分析',
                            '## 📊', '## ✅', '## ❌', 'AI分析'
                        ]
                        is_analysis = any(marker in reply.body for marker in analysis_markers)
                        if is_analysis:
                            print(f"         🤖 这是一个分析回复!")
                else:
                    print(f"   📭 无回复")
                    
        except Exception as e:
            print(f"❌ 获取讨论结构失败: {e}")
            
    async def test_find_comment_id(self, discussion_number: int):
        """测试查找评论ID的方法"""
        print("\n🔍 测试查找评论ID")
        print("-" * 40)
        
        try:
            # 测试查找日报评论ID
            daily_report_id = await self.daily_analyzer._find_content_comment_id(discussion_number, 'daily_report')
            print(f"日报评论ID: {daily_report_id}")
            
            # 测试查找日计划评论ID
            daily_plan_id = await self.daily_analyzer._find_content_comment_id(discussion_number, 'daily_plan')
            print(f"日计划评论ID: {daily_plan_id}")
            
            return daily_report_id, daily_plan_id
            
        except Exception as e:
            print(f"❌ 查找评论ID失败: {e}")
            return None, None
            
    async def test_duplicate_check(self, discussion_number: int):
        """测试重复检查逻辑"""
        print("\n🔄 测试重复检查逻辑")
        print("-" * 40)
        
        try:
            # 获取评论ID
            daily_report_id, daily_plan_id = await self.test_find_comment_id(discussion_number)
            
            # 测试日报重复检查
            if daily_report_id:
                already_replied_report = await self.github_client.check_already_replied(
                    discussion_number, daily_report_id, 'daily_report'
                )
                print(f"日报已回复检查: {already_replied_report}")
                
            # 测试日计划重复检查
            if daily_plan_id:
                already_replied_plan = await self.github_client.check_already_replied(
                    discussion_number, daily_plan_id, 'daily_plan'
                )
                print(f"日计划已回复检查: {already_replied_plan}")
                
            # 测试顶级评论重复检查
            already_replied_top = await self.github_client.check_already_replied(
                discussion_number, None, 'daily_report'
            )
            print(f"顶级评论已回复检查: {already_replied_top}")
            
        except Exception as e:
            print(f"❌ 重复检查失败: {e}")
            
    async def test_post_analysis_comment(self, discussion_number: int):
        """测试post_analysis_comment方法"""
        print("\n📝 测试post_analysis_comment方法")
        print("-" * 40)
        
        try:
            # 获取评论ID
            daily_report_id, daily_plan_id = await self.test_find_comment_id(discussion_number)
            
            test_content = "🧪 **测试分析回复**\n\n这是一个测试回复，用于验证楼中楼功能。\n\n---\n*测试时间: {}*".format(
                datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S UTC")
            )
            
            # 测试回复日报
            if daily_report_id:
                print(f"\n尝试回复日报评论 {daily_report_id}...")
                success = await self.github_client.post_analysis_comment(
                    discussion_number, test_content, daily_report_id, 'daily_report'
                )
                print(f"日报回复结果: {'✅ 成功' if success else '❌ 失败'}")
                
            # 测试回复日计划
            if daily_plan_id:
                print(f"\n尝试回复日计划评论 {daily_plan_id}...")
                success = await self.github_client.post_analysis_comment(
                    discussion_number, test_content, daily_plan_id, 'daily_plan'
                )
                print(f"日计划回复结果: {'✅ 成功' if success else '❌ 失败'}")
                
        except Exception as e:
            print(f"❌ 测试post_analysis_comment失败: {e}")
            
    async def test_manual_graphql_reply(self, discussion_number: int):
        """手动测试GraphQL回复"""
        print("\n🔧 手动测试GraphQL回复")
        print("-" * 40)
        
        try:
            # 获取评论ID
            daily_report_id, daily_plan_id = await self.test_find_comment_id(discussion_number)
            
            test_content = "🔧 **手动GraphQL测试回复**\n\n这是直接使用GraphQL API的测试回复。\n\n---\n*测试时间: {}*".format(
                datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S UTC")
            )
            
            # 直接使用_post_repo_discussion_comment方法
            if daily_report_id:
                print(f"\n直接回复日报评论 {daily_report_id}...")
                success = await self.github_client._post_repo_discussion_comment(
                    discussion_number, test_content, daily_report_id
                )
                print(f"直接GraphQL回复结果: {'✅ 成功' if success else '❌ 失败'}")
                
        except Exception as e:
            print(f"❌ 手动GraphQL测试失败: {e}")
            
    async def analyze_differences(self, discussion_number: int):
        """分析差异和提供解决方案"""
        print("\n🔍 差异分析和解决方案")
        print("-" * 40)
        
        print("\n📋 可能的问题原因:")
        print("1. check_already_replied方法误判已经回复过")
        print("2. 评论ID格式不正确或已失效")
        print("3. GraphQL API权限问题")
        print("4. 网络或超时问题")
        
        print("\n💡 建议解决方案:")
        print("1. 在post_analysis_comment中添加详细日志")
        print("2. 验证check_already_replied的逻辑")
        print("3. 确保评论ID的有效性")
        print("4. 检查GitHub API权限和配额")
        print("5. 考虑添加重试机制")
        
        # 检查当前配置
        print("\n⚙️ 当前配置:")
        print(f"组织: {self.config.github.organization}")
        print(f"仓库: {self.config.github.repository}")
        print(f"使用组织讨论: {self.config.github.use_org_discussions}")
        print(f"Token配置: {'✅ 已配置' if self.config.github.token else '❌ 未配置'}")

async def main():
    """主函数"""
    debugger = ComprehensiveReplyDebugger()
    await debugger.debug_reply_flow()

if __name__ == "__main__":
    asyncio.run(main())