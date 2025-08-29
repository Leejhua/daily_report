#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
简化的回复测试脚本
"""

import asyncio
import os
from datetime import datetime, timezone
from typing import Dict, List, Optional, Any
import json

from src.config import Config
from src.clients.github_client import GitHubClient

class SimpleReplyTester:
    """简化回复测试器"""
    
    def __init__(self):
        self.config = Config()
        self.github_client = GitHubClient(self.config.github)
        
    async def test_simple_reply(self):
        """测试简单回复功能"""
        print("🔍 简化回复测试")
        print("=" * 50)
        
        discussion_number = 1
        
        print(f"📋 测试讨论: #{discussion_number}")
        print(f"配置: {self.config.github.organization}/{self.config.github.repository}")
        print(f"使用组织讨论: {self.config.github.use_org_discussions}")
        
        # 1. 获取评论
        print("\n📝 获取评论...")
        try:
            comments = await self.github_client.get_discussion_comments(discussion_number)
            print(f"✅ 评论数量: {len(comments)}")
            
            if not comments:
                print("❌ 没有评论可供测试")
                return
                
            first_comment = comments[0]
            print(f"\n第一个评论:")
            print(f"   ID: {first_comment.id}")
            print(f"   作者: {first_comment.author}")
            print(f"   内容: {first_comment.body[:100]}...")
            
        except Exception as e:
            print(f"❌ 获取评论失败: {e}")
            return
            
        # 2. 测试post_analysis_comment
        print("\n📤 测试post_analysis_comment...")
        try:
            test_content = f"🧪 **测试分析回复** - {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n\n## 📊 测试分析\n\n这是一个测试分析回复，用于验证楼中楼回复功能。\n\n### 🎯 测试目标\n- 验证回复是否出现在楼中楼\n- 检查回复格式是否正确\n\n### 💡 测试结果\n如果您看到这条回复，说明楼中楼回复功能正常工作！"
            
            print(f"回复到评论: {first_comment.id}")
            print(f"回复内容长度: {len(test_content)} 字符")
            
            result = await self.github_client.post_analysis_comment(
                discussion_number=discussion_number,
                analysis_content=test_content,
                content_type='daily_report',  # 使用已知的内容类型
                reply_to_comment_id=first_comment.id
            )
            
            if result:
                print(f"✅ post_analysis_comment 成功!")
            else:
                print(f"❌ post_analysis_comment 失败")
                
        except Exception as e:
            print(f"❌ post_analysis_comment 异常: {e}")
            
        # 3. 等待并验证
        print("\n⏳ 等待3秒后验证...")
        await asyncio.sleep(3)
        
        try:
            # 重新获取结构化评论
            structured_comments = await self.github_client._get_all_comments_with_replies(discussion_number)
            print(f"\n📊 验证结果:")
            print(f"   顶级评论数量: {len(structured_comments['top_level'])}")
            print(f"   回复分组数量: {len(structured_comments['replies'])}")
            
            # 检查回复
            found_test_reply = False
            for comment_id, replies in structured_comments['replies'].items():
                print(f"\n评论 {comment_id} 的回复:")
                print(f"   回复数量: {len(replies)}")
                
                for i, reply in enumerate(replies):
                    print(f"   回复 {i+1}: {reply.body[:50]}...")
                    if '🧪 **测试分析回复**' in reply.body:
                        print(f"      ✅ 找到测试回复!")
                        found_test_reply = True
                        
            if found_test_reply:
                print(f"\n🎉 成功! 测试回复已出现在楼中楼中!")
            else:
                print(f"\n❌ 未找到测试回复")
                
        except Exception as e:
            print(f"❌ 验证失败: {e}")
            
        # 4. 检查重复回复逻辑
        print("\n🔄 测试重复回复检查...")
        try:
            already_replied = await self.github_client.check_already_replied(
                discussion_number, first_comment.id, 'daily_report'
            )
            print(f"重复检查结果: {already_replied}")
            
            if already_replied:
                print("✅ 重复检查正常工作 - 检测到已有回复")
            else:
                print("❌ 重复检查可能有问题 - 未检测到回复")
                
        except Exception as e:
            print(f"❌ 重复检查失败: {e}")
            
        print("\n🎯 测试总结")
        print("-" * 40)
        print("1. 如果看到 '🎉 成功!' 消息，说明楼中楼回复功能正常")
        print("2. 如果重复检查返回True，说明防重复逻辑正常")
        print("3. 请检查GitHub讨论页面确认回复是否正确显示")

async def main():
    """主函数"""
    tester = SimpleReplyTester()
    await tester.test_simple_reply()

if __name__ == "__main__":
    asyncio.run(main())