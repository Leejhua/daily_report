#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
检查讨论的完整评论结构，包括回复

这个脚本用于检查GitHub讨论中的所有评论和回复，
特别是查看分析评论是否作为回复发布了。
"""

import asyncio
import sys
import os
import requests
from datetime import datetime
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.config import Config
from src.utils.logger import get_logger

async def check_discussion_replies():
    """
    检查讨论的完整评论结构
    """
    print("=" * 80)
    print("检查讨论#64的完整评论结构（包括回复）")
    print("=" * 80)
    
    try:
        # 初始化配置
        config = Config()
        
        # 使用GraphQL API获取完整的评论结构
        query = """
        query($owner: String!, $name: String!, $number: Int!) {
            repository(owner: $owner, name: $name) {
                discussion(number: $number) {
                    id
                    title
                    body
                    author {
                        login
                    }
                    createdAt
                    updatedAt
                    comments(first: 50) {
                        totalCount
                        nodes {
                            id
                            body
                            author {
                                login
                            }
                            createdAt
                            updatedAt
                            replies(first: 20) {
                                totalCount
                                nodes {
                                    id
                                    body
                                    author {
                                        login
                                    }
                                    createdAt
                                    updatedAt
                                }
                            }
                        }
                    }
                }
            }
        }
        """
        
        variables = {
            "owner": config.github.organization,
            "name": config.github.repository,
            "number": 64
        }
        
        headers = {
            "Authorization": f"Bearer {config.github.token}",
            "Content-Type": "application/json"
        }
        
        response = requests.post(
            "https://api.github.com/graphql",
            headers=headers,
            json={"query": query, "variables": variables},
            timeout=30
        )
        response.raise_for_status()
        
        result = response.json()
        
        if "errors" in result:
            print(f"GraphQL错误: {result['errors']}")
            return
        
        discussion = result["data"]["repository"]["discussion"]
        if not discussion:
            print("未找到讨论#64")
            return
        
        print(f"\n讨论信息:")
        print(f"标题: {discussion['title']}")
        print(f"作者: {discussion['author']['login']}")
        print(f"创建时间: {discussion['createdAt']}")
        print(f"更新时间: {discussion['updatedAt']}")
        print(f"首楼内容长度: {len(discussion['body'])} 字符")
        
        comments = discussion["comments"]["nodes"]
        total_comments = discussion["comments"]["totalCount"]
        
        print(f"\n评论总数: {total_comments}")
        print(f"获取到的评论数: {len(comments)}")
        
        if not comments:
            print("没有找到任何评论")
            return
        
        print("\n" + "=" * 60)
        print("详细评论结构")
        print("=" * 60)
        
        for i, comment in enumerate(comments, 1):
            print(f"\n评论 {i}:")
            print(f"  ID: {comment['id']}")
            print(f"  作者: {comment['author']['login']}")
            print(f"  创建时间: {comment['createdAt']}")
            print(f"  更新时间: {comment['updatedAt']}")
            print(f"  内容长度: {len(comment['body'])} 字符")
            
            # 检查是否是分析评论
            is_analysis = any(keyword in comment['body'] for keyword in [
                '## 📊 日报分析', '## 📋 日计划分析', '## 📈 综合分析', 
                '本分析由GLM', 'GLM-4.5自动生成'
            ])
            print(f"  是否为分析评论: {'是' if is_analysis else '否'}")
            
            # 显示内容预览
            preview = comment['body'][:200] + "..." if len(comment['body']) > 200 else comment['body']
            print(f"  内容预览: {preview}")
            
            # 检查回复
            replies = comment['replies']['nodes']
            reply_count = comment['replies']['totalCount']
            
            if reply_count > 0:
                print(f"  \n  回复数量: {reply_count}")
                for j, reply in enumerate(replies, 1):
                    print(f"    回复 {j}:")
                    print(f"      ID: {reply['id']}")
                    print(f"      作者: {reply['author']['login']}")
                    print(f"      创建时间: {reply['createdAt']}")
                    print(f"      更新时间: {reply['updatedAt']}")
                    print(f"      内容长度: {len(reply['body'])} 字符")
                    
                    # 检查回复是否是分析评论
                    is_reply_analysis = any(keyword in reply['body'] for keyword in [
                        '## 📊 日报分析', '## 📋 日计划分析', '## 📈 综合分析',
                        '本分析由GLM', 'GLM-4.5自动生成'
                    ])
                    print(f"      是否为分析评论: {'是' if is_reply_analysis else '否'}")
                    
                    # 显示回复内容预览
                    reply_preview = reply['body'][:150] + "..." if len(reply['body']) > 150 else reply['body']
                    print(f"      内容预览: {reply_preview}")
            else:
                print(f"  回复数量: 0")
        
        print("\n" + "=" * 80)
        print("检查完成")
        print("=" * 80)
        
        # 统计分析评论
        analysis_comments = []
        for comment in comments:
            if any(keyword in comment['body'] for keyword in [
                '## 📊 日报分析', '## 📋 日计划分析', '## 📈 综合分析',
                '本分析由GLM', 'GLM-4.5自动生成'
            ]):
                analysis_comments.append(('顶级评论', comment))
            
            for reply in comment['replies']['nodes']:
                if any(keyword in reply['body'] for keyword in [
                    '## 📊 日报分析', '## 📋 日计划分析', '## 📈 综合分析',
                    '本分析由GLM', 'GLM-4.5自动生成'
                ]):
                    analysis_comments.append(('回复', reply))
        
        print(f"\n找到 {len(analysis_comments)} 个分析评论:")
        for comment_type, comment in analysis_comments:
            print(f"- {comment_type}: {comment['author']['login']} 于 {comment['createdAt']} 发布")
            print(f"  内容长度: {len(comment['body'])} 字符")
            preview = comment['body'][:100] + "..." if len(comment['body']) > 100 else comment['body']
            print(f"  预览: {preview}")
        
    except Exception as e:
        print(f"\n检查过程中出错: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(check_discussion_replies())