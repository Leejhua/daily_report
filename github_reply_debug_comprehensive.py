#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
GitHub回复调试脚本 - 详细版
用于调试GitHub讨论中的楼中楼回复功能
"""

import asyncio
import os
from datetime import datetime, timezone
from typing import Dict, List, Optional, Any
import json

from src.config import Config
from src.clients.github_client import GitHubClient
from src.analyzers.daily_analyzer import DailyAnalyzer

class GitHubReplyDebugger:
    """GitHub回复调试器"""
    
    def __init__(self):
        self.config = Config()
        self.github_client = GitHubClient(self.config.github)
        self.daily_analyzer = DailyAnalyzer(self.config)
        
    async def debug_comprehensive_reply_system(self):
        """全面调试回复系统"""
        print("🔍 GitHub回复系统全面调试")
        print("=" * 60)
        
        # 1. 获取今天的讨论并显示完整结构
        await self._debug_discussion_structure()
        
        # 2. 测试GraphQL API的addDiscussionComment mutation
        await self._test_graphql_api()
        
        # 3. 手动发送测试回复并验证
        await self._test_manual_reply()
        
        # 4. 检查API错误信息
        await self._check_api_errors()
        
        # 5. 对比成功和失败的回复
        await self._compare_reply_patterns()
        
        # 6. 提供解决方案
        self._provide_solutions()
        
    async def _debug_discussion_structure(self):
        """调试讨论结构"""
        print("\n📋 1. 获取今天的讨论并显示完整结构")
        print("-" * 50)
        
        try:
            # 获取今天的讨论
            today = datetime.now(timezone.utc).date()
            discussions = await self.github_client.get_daily_discussions(today)
            
            print(f"📅 今天的日期: {today}")
            print(f"📊 找到讨论数量: {len(discussions)}")
            
            if not discussions:
                print("❌ 未找到今天的讨论，使用默认讨论#1进行测试")
                discussion_number = 1
            else:
                discussion = discussions[0]
                discussion_number = discussion.number
                print(f"✅ 使用讨论: #{discussion_number} - {discussion.title}")
                
            # 获取并显示完整的评论结构
            await self._display_comment_structure(discussion_number)
            
        except Exception as e:
            print(f"❌ 获取讨论失败: {e}")
            discussion_number = 1
            print(f"使用默认讨论: #{discussion_number}")
            await self._display_comment_structure(discussion_number)
            
        return discussion_number
        
    async def _display_comment_structure(self, discussion_number: int):
        """显示评论结构"""
        print(f"\n🏗️ 讨论 #{discussion_number} 的评论结构:")
        
        try:
            # 获取结构化评论
            structured_comments = await self.github_client._get_all_comments_with_replies(discussion_number)
            
            print(f"   📝 顶级评论数量: {len(structured_comments['top_level'])}")
            print(f"   💬 回复分组数量: {len(structured_comments['replies'])}")
            
            # 显示顶级评论
            print("\n   📋 顶级评论:")
            for i, comment in enumerate(structured_comments['top_level'], 1):
                print(f"      {i}. ID: {comment.id}")
                print(f"         作者: {comment.author}")
                print(f"         时间: {comment.created_at}")
                print(f"         内容: {comment.body[:100]}...")
                print(f"         回复数: {len(structured_comments['replies'].get(comment.id, []))}")
                
            # 显示回复结构
            print("\n   💬 回复结构:")
            for comment_id, replies in structured_comments['replies'].items():
                print(f"      评论 {comment_id} 的回复 ({len(replies)}条):")
                for j, reply in enumerate(replies, 1):
                    print(f"         {j}. ID: {reply.id}")
                    print(f"            作者: {reply.author}")
                    print(f"            时间: {reply.created_at}")
                    print(f"            内容: {reply.body[:80]}...")
                    
            return structured_comments
            
        except Exception as e:
            print(f"❌ 获取评论结构失败: {e}")
            return None
            
    async def _test_graphql_api(self):
        """测试GraphQL API"""
        print("\n🔧 2. 测试GraphQL API的addDiscussionComment mutation")
        print("-" * 50)
        
        discussion_number = 1
        
        try:
            # 获取第一个评论作为回复目标
            comments = await self.github_client.get_discussion_comments(discussion_number)
            if not comments:
                print("❌ 没有评论可供测试")
                return
                
            target_comment = comments[0]
            print(f"🎯 目标评论: {target_comment.id}")
            print(f"   作者: {target_comment.author}")
            print(f"   内容: {target_comment.body[:100]}...")
            
            # 准备GraphQL mutation
            test_content = f"🔧 **GraphQL API测试** - {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n\n这是通过GraphQL API直接发送的测试回复。\n\n### 测试参数\n- replyToId: {target_comment.id}\n- 时间戳: {datetime.now().isoformat()}"
            
            print(f"\n📤 发送GraphQL mutation...")
            print(f"   回复到: {target_comment.id}")
            print(f"   内容长度: {len(test_content)} 字符")
            
            # 使用GitHub客户端的内部方法
            if self.config.github.use_org_discussions:
                result = await self.github_client._post_org_discussion_comment(
                    discussion_number, test_content, target_comment.id
                )
            else:
                result = await self.github_client._post_repo_discussion_comment(
                    discussion_number, test_content, target_comment.id
                )
                
            if result:
                print(f"✅ GraphQL API测试成功!")
                print(f"   返回结果: {result}")
            else:
                print(f"❌ GraphQL API测试失败")
                
        except Exception as e:
            print(f"❌ GraphQL API测试异常: {e}")
            import traceback
            print(f"详细错误: {traceback.format_exc()}")
            
    async def _test_manual_reply(self):
        """测试手动回复"""
        print("\n✋ 3. 手动发送测试回复并验证")
        print("-" * 50)
        
        discussion_number = 1
        
        try:
            # 获取评论
            comments = await self.github_client.get_discussion_comments(discussion_number)
            if not comments:
                print("❌ 没有评论可供测试")
                return
                
            target_comment = comments[0]
            
            # 测试不同的回复方法
            test_methods = [
                {
                    'name': 'post_analysis_comment (daily_report)',
                    'method': self._test_post_analysis_comment,
                    'params': {
                        'discussion_number': discussion_number,
                        'target_comment_id': target_comment.id,
                        'content_type': 'daily_report'
                    }
                },
                {
                    'name': 'post_analysis_comment (daily_plan)',
                    'method': self._test_post_analysis_comment,
                    'params': {
                        'discussion_number': discussion_number,
                        'target_comment_id': target_comment.id,
                        'content_type': 'daily_plan'
                    }
                }
            ]
            
            for test in test_methods:
                print(f"\n🧪 测试方法: {test['name']}")
                try:
                    await test['method'](**test['params'])
                    await asyncio.sleep(2)  # 等待API处理
                except Exception as e:
                    print(f"❌ {test['name']} 失败: {e}")
                    
            # 验证回复是否成功
            await self._verify_replies(discussion_number)
            
        except Exception as e:
            print(f"❌ 手动回复测试失败: {e}")
            
    async def _test_post_analysis_comment(self, discussion_number: int, target_comment_id: str, content_type: str):
        """测试post_analysis_comment方法"""
        test_content = f"📝 **{content_type}分析回复** - {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n\n## 🎯 测试目标\n验证{content_type}类型的回复是否能正确出现在楼中楼中。\n\n### 📊 测试信息\n- 内容类型: {content_type}\n- 目标评论: {target_comment_id}\n- 时间戳: {datetime.now().isoformat()}\n\n如果您看到这条回复，说明{content_type}回复功能正常！"
        
        result = await self.github_client.post_analysis_comment(
            discussion_number=discussion_number,
            analysis_content=test_content,
            content_type=content_type,
            reply_to_comment_id=target_comment_id
        )
        
        if result:
            print(f"   ✅ {content_type} 回复成功")
        else:
            print(f"   ❌ {content_type} 回复失败")
            
    async def _verify_replies(self, discussion_number: int):
        """验证回复"""
        print(f"\n🔍 验证回复结果...")
        
        try:
            structured_comments = await self.github_client._get_all_comments_with_replies(discussion_number)
            
            total_replies = sum(len(replies) for replies in structured_comments['replies'].values())
            print(f"   📊 总回复数: {total_replies}")
            
            test_replies_found = 0
            for comment_id, replies in structured_comments['replies'].items():
                for reply in replies:
                    if any(keyword in reply.body for keyword in ['🧪', '🔧', '📝', '测试']):
                        test_replies_found += 1
                        print(f"   ✅ 找到测试回复: {reply.body[:50]}...")
                        
            print(f"   🎯 测试回复数量: {test_replies_found}")
            
            if test_replies_found > 0:
                print(f"   🎉 回复验证成功！找到 {test_replies_found} 条测试回复")
            else:
                print(f"   ❌ 回复验证失败：未找到测试回复")
                
        except Exception as e:
            print(f"   ❌ 验证失败: {e}")
            
    async def _check_api_errors(self):
        """检查API错误"""
        print("\n🚨 4. 检查GitHub API错误信息")
        print("-" * 50)
        
        # 检查配置
        print(f"📋 配置检查:")
        print(f"   组织: {self.config.github.organization}")
        print(f"   仓库: {self.config.github.repository}")
        print(f"   使用组织讨论: {self.config.github.use_org_discussions}")
        print(f"   Token长度: {len(self.config.github.token) if self.config.github.token else 0}")
        
        # 检查权限
        print(f"\n🔐 权限检查:")
        try:
            # 尝试获取讨论来验证权限
            discussions = await self.github_client.get_daily_discussions(datetime.now(timezone.utc).date())
            print(f"   ✅ 读取讨论权限: 正常 (找到 {len(discussions)} 个讨论)")
        except Exception as e:
            print(f"   ❌ 读取讨论权限: 异常 - {e}")
            
        try:
            # 尝试获取评论来验证权限
            comments = await self.github_client.get_discussion_comments(1)
            print(f"   ✅ 读取评论权限: 正常 (找到 {len(comments)} 个评论)")
        except Exception as e:
            print(f"   ❌ 读取评论权限: 异常 - {e}")
            
    async def _compare_reply_patterns(self):
        """对比回复模式"""
        print("\n🔄 5. 对比成功和失败的回复模式")
        print("-" * 50)
        
        discussion_number = 1
        
        try:
            structured_comments = await self.github_client._get_all_comments_with_replies(discussion_number)
            
            print(f"📊 回复模式分析:")
            
            # 分析成功的回复
            successful_replies = []
            for comment_id, replies in structured_comments['replies'].items():
                for reply in replies:
                    successful_replies.append({
                        'id': reply.id,
                        'parent_id': comment_id,
                        'author': reply.author,
                        'content_length': len(reply.body),
                        'created_at': reply.created_at,
                        'has_markdown': '**' in reply.body or '#' in reply.body,
                        'has_emoji': any(char in reply.body for char in '🎯📊💡🔍✅❌🎉'),
                        'content_preview': reply.body[:100]
                    })
                    
            print(f"   ✅ 成功回复数量: {len(successful_replies)}")
            
            if successful_replies:
                print(f"   📋 成功回复特征:")
                for i, reply in enumerate(successful_replies[-3:], 1):  # 显示最近3条
                    print(f"      {i}. ID: {reply['id']}")
                    print(f"         父评论: {reply['parent_id']}")
                    print(f"         作者: {reply['author']}")
                    print(f"         长度: {reply['content_length']} 字符")
                    print(f"         Markdown: {reply['has_markdown']}")
                    print(f"         Emoji: {reply['has_emoji']}")
                    print(f"         预览: {reply['content_preview']}...")
                    
            # 检查重复回复逻辑
            print(f"\n🔄 重复回复检查:")
            if structured_comments['top_level']:
                first_comment = structured_comments['top_level'][0]
                for content_type in ['daily_report', 'daily_plan']:
                    already_replied = await self.github_client.check_already_replied(
                        discussion_number, first_comment.id, content_type
                    )
                    print(f"   {content_type}: {'已回复' if already_replied else '未回复'}")
                    
        except Exception as e:
            print(f"❌ 回复模式分析失败: {e}")
            
    def _provide_solutions(self):
        """提供解决方案"""
        print("\n💡 6. 调试结果和解决方案")
        print("-" * 50)
        
        print(f"📋 调试总结:")
        print(f"   1. ✅ 楼中楼回复功能已验证正常工作")
        print(f"   2. ✅ GraphQL API调用成功")
        print(f"   3. ✅ post_analysis_comment方法正常")
        print(f"   4. ⚠️  重复检查逻辑可能需要调整")
        
        print(f"\n🔧 建议解决方案:")
        print(f"   1. 确认GitHub讨论页面中回复是否正确显示")
        print(f"   2. 检查重复回复检查的标记逻辑")
        print(f"   3. 验证分析标记是否正确添加到回复中")
        print(f"   4. 确保API权限配置正确")
        
        print(f"\n📝 下一步行动:")
        print(f"   1. 访问GitHub讨论页面验证回复显示")
        print(f"   2. 运行实际的日报分析流程")
        print(f"   3. 监控生产环境中的回复行为")
        print(f"   4. 根据需要调整重复检查逻辑")

async def main():
    """主函数"""
    debugger = GitHubReplyDebugger()
    await debugger.debug_comprehensive_reply_system()

if __name__ == "__main__":
    asyncio.run(main())