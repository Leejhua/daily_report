#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
读取GitHub讨论的完整结构，包括评论和回复的层级关系
"""

import os
import sys
from datetime import datetime
from typing import List, Dict, Any

# 添加项目根目录到Python路径
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.clients.github_client import GitHubClient
from src.config import Config

def format_content_preview(content: str, max_length: int = 100) -> str:
    """格式化内容预览"""
    if not content:
        return "[空内容]"
    
    # 移除多余的空白字符
    content = ' '.join(content.split())
    
    if len(content) <= max_length:
        return content
    
    return content[:max_length] + "..."

def has_analysis_marker(content: str) -> tuple[bool, str]:
    """检查内容是否包含分析标记"""
    analysis_markers = [
        "## 📊 日报分析",
        "## 📋 日计划分析", 
        "## 📅 周计划分析",
        "## 🔍 内容分析"
    ]
    
    for marker in analysis_markers:
        if marker in content:
            return True, marker
    
    return False, ""

async def get_discussion_info(github_client, discussion_number: int):
    """获取讨论的基本信息"""
    try:
        # 使用GraphQL查询获取讨论的详细信息
        discussion_query = """
        query($owner: String!, $name: String!, $number: Int!) {
            repository(owner: $owner, name: $name) {
                discussion(number: $number) {
                    id
                    title
                    body
                    createdAt
                    updatedAt
                    author {
                        login
                    }
                    category {
                        name
                    }
                }
            }
        }
        """
        
        query_variables = {
            "owner": github_client.config.organization,
            "name": github_client.config.repository,
            "number": discussion_number
        }
        
        headers = {
            "Authorization": f"Bearer {github_client.config.token}",
            "Content-Type": "application/json"
        }
        
        import requests
        response = requests.post(
            "https://api.github.com/graphql",
            headers=headers,
            json={"query": discussion_query, "variables": query_variables},
            timeout=github_client.config.timeout
        )
        response.raise_for_status()
        
        result = response.json()
        
        if "errors" in result:
            print(f"GraphQL查询错误: {result['errors']}")
            return None
            
        data = result.get("data", {})
        repository = data.get("repository")
        if not repository:
            return None
            
        discussion = repository.get("discussion")
        return discussion
        
    except Exception as e:
        print(f"获取讨论信息失败: {e}")
        return None

async def print_discussion_structure(discussion_number: int):
    """打印指定讨论的完整结构"""
    try:
        # 初始化配置和GitHub客户端
        config = Config()
        github_client = GitHubClient(config.github)
        
        # 获取讨论基本信息
        discussion_info = await get_discussion_info(github_client, discussion_number)
        
        # 获取讨论的所有评论和回复
        result = await github_client._get_all_comments_with_replies(discussion_number)
        
        top_level_comments = result.get("top_level", [])
        replies_by_parent = result.get("replies", {})
        
        print(f"\n=== 讨论 #{discussion_number} 结构分析 ===")
        
        # 打印讨论基本信息
        print("\n📋 讨论信息:")
        if discussion_info:
            print(f"   标题: {discussion_info.get('title', 'N/A')}")
            author = discussion_info.get('author')
            print(f"   作者: {author.get('login', 'N/A') if author else 'N/A'}")
            print(f"   创建时间: {discussion_info.get('createdAt', 'N/A')}")
            print(f"   更新时间: {discussion_info.get('updatedAt', 'N/A')}")
            category = discussion_info.get('category')
            print(f"   分类: {category.get('name', 'N/A') if category else 'N/A'}")
            print(f"   首楼内容预览: {format_content_preview(discussion_info.get('body', ''))}")
        else:
            print("   标题: N/A")
            print("   作者: N/A")
            print("   创建时间: N/A")
            print("   更新时间: N/A")
            print("   分类: N/A")
            print("   首楼内容预览: [无法获取]")
        
        print(f"\n💬 评论总数: {len(top_level_comments)}")
        
        # 统计变量
        total_replies = 0
        analysis_comments = 0
        analysis_replies = 0
        
        # 遍历所有顶级评论
        for i, comment in enumerate(top_level_comments, 1):
            print(f"\n📝 评论 #{i}:")
            print(f"   ID: {comment.id}")
            print(f"   作者: {comment.user.login}")
            print(f"   创建时间: {comment.created_at.strftime('%Y-%m-%d %H:%M:%S')}")
            print(f"   内容预览: {format_content_preview(comment.body)}")
            
            # 检查是否包含分析标记
            if has_analysis_marker(comment.body):
                analysis_comments += 1
                print("   🔍 [包含分析标记]")
            
            # 获取该评论的回复
            comment_replies = replies_by_parent.get(comment.id, [])
            if comment_replies:
                print(f"   📨 回复数: {len(comment_replies)}")
                total_replies += len(comment_replies)
                
                for j, reply in enumerate(comment_replies, 1):
                    print(f"      └─ 回复 #{j}:")
                    print(f"         ID: {reply.id}")
                    print(f"         作者: {reply.user.login}")
                    print(f"         创建时间: {reply.created_at.strftime('%Y-%m-%d %H:%M:%S')}")
                    print(f"         内容预览: {format_content_preview(reply.body)}")
                    
                    # 检查回复是否包含分析标记
                    if has_analysis_marker(reply.body):
                        analysis_replies += 1
                        print("         🔍 [包含分析标记]")
            else:
                print("   📨 回复数: 0")
        
        # 打印统计信息
        print(f"\n📊 统计信息:")
        print(f"   总评论数: {len(top_level_comments)}")
        print(f"   总回复数: {total_replies}")
        print(f"   包含分析标记的评论: {analysis_comments}")
        print(f"   包含分析标记的回复: {analysis_replies}")
        
    except Exception as e:
        print(f"❌ 获取讨论结构失败: {e}")
        import traceback
        traceback.print_exc()

async def main():
    """主函数"""
    if len(sys.argv) != 2:
        print("用法: python read_discussion_structure.py <讨论号>")
        print("示例: python read_discussion_structure.py 70")
        sys.exit(1)
    
    try:
        discussion_number = int(sys.argv[1])
        await print_discussion_structure(discussion_number)
    except ValueError:
        print("❌ 讨论号必须是数字")
        sys.exit(1)

if __name__ == "__main__":
    import asyncio
    asyncio.run(main())