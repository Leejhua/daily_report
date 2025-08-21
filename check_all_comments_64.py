#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
检查讨论#64的所有评论
"""

import asyncio
import sys
import os

# 添加项目根目录到路径
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from src.config import Config
from src.clients.github_client import GitHubClient

async def check_all_comments_64():
    """检查讨论#64的所有评论"""
    print("=== 检查讨论#64的所有评论 ===")
    
    config = Config()
    github_client = GitHubClient(config.github)
    
    discussion_number = 64
    
    try:
        # 获取所有评论
        comments = await github_client.get_discussion_comments(discussion_number)
        
        print(f"总共 {len(comments)} 条评论\n")
        
        # 按时间顺序显示所有评论
        comments.sort(key=lambda x: x.updated_at)
        
        for i, comment in enumerate(comments, 1):
            print(f"=== 评论 {i} ===")
            print(f"作者: {comment.author}")
            print(f"时间: {comment.updated_at}")
            print(f"内容长度: {len(comment.body)} 字符")
            
            # 识别内容类型
            content_type = github_client.identify_content_type(comment.body)
            print(f"识别类型: {content_type}")
            
            # 显示内容
            print(f"内容:\n{comment.body}")
            
            # 检查是否包含"日计划"字样
            if '日计划' in comment.body:
                print(f"\n🎯 此评论包含'日计划'字样！")
                
            print(f"\n{'='*50}\n")
            
        # 显示最新评论信息
        if comments:
            latest_comment = comments[-1]  # 最后一个（最新的）
            print(f"=== 最新评论总结 ===")
            print(f"最新评论是第 {len(comments)} 条")
            print(f"作者: {latest_comment.author}")
            print(f"类型: {github_client.identify_content_type(latest_comment.body)}")
            print(f"这就是系统用来决定分析类型的评论")
            
    except Exception as e:
        print(f"❌ 检查失败: {e}")
        import traceback
        traceback.print_exc()

async def main():
    """主函数"""
    print("开始检查讨论#64的所有评论...\n")
    
    await check_all_comments_64()
    
    print("\n检查完成！")

if __name__ == "__main__":
    asyncio.run(main())