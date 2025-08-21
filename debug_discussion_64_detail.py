#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
详细调试讨论#64的日计划识别问题
"""

import asyncio
import sys
import os

# 添加项目根目录到路径
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from src.config import Config
from src.clients.github_client import GitHubClient

async def debug_discussion_64_detail():
    """详细调试讨论#64"""
    print("=== 详细调试讨论#64 ===")
    
    config = Config()
    github_client = GitHubClient(config.github)
    
    discussion_number = 64
    
    try:
        # 1. 获取讨论信息
        discussions = await github_client._get_repo_discussions()
        target_discussion = None
        
        for discussion in discussions:
            if discussion.number == discussion_number:
                target_discussion = discussion
                break
                
        if not target_discussion:
            print(f"未找到讨论#{discussion_number}")
            return
            
        print(f"讨论: #{target_discussion.number} - {target_discussion.title}")
        
        # 2. 获取所有评论并按时间排序
        comments = await github_client.get_discussion_comments(discussion_number)
        comments.sort(key=lambda x: x.updated_at, reverse=True)
        
        print(f"\n总共 {len(comments)} 条评论")
        
        # 3. 分析最新评论（这是系统用来判断楼层类型的）
        if comments:
            latest_comment = comments[0]
            print(f"\n=== 最新评论分析 ===")
            print(f"作者: {latest_comment.author}")
            print(f"时间: {latest_comment.updated_at}")
            print(f"内容长度: {len(latest_comment.body)} 字符")
            
            # 显示完整内容
            print(f"\n完整内容:")
            print(f"{latest_comment.body}")
            
            # 详细分析识别过程
            content = latest_comment.body
            content_lower = content.lower()
            
            # 所有关键词列表
            daily_report_keywords = [
                '日报', '日结', '今日完成', '今日工作', '工作总结', 
                '完成情况', '今天完成', '今天做了', '进度', '遇到问题',
                '今日进展', '工作内容'
            ]
            
            daily_plan_keywords = [
                '日计划', '明日计划', '明天计划', '下一步', '待办',
                '明日安排', '明天安排', '计划完成', '准备'
            ]
            
            work_keywords = ['完成', '开发', '测试', '修复', '问题', '功能', '任务', '会议']
            
            # 计算得分
            daily_report_score = sum(1 for keyword in daily_report_keywords if keyword in content_lower)
            daily_plan_score = sum(1 for keyword in daily_plan_keywords if keyword in content_lower)
            work_score = sum(1 for keyword in work_keywords if keyword in content_lower)
            
            # 长内容工作特征加分
            if len(content) > 50 and work_score >= 2:
                daily_report_score += 1
                
            print(f"\n=== 关键词分析 ===")
            print(f"日报得分: {daily_report_score}")
            print(f"日计划得分: {daily_plan_score}")
            print(f"工作词汇得分: {work_score}")
            
            # 找到匹配的关键词
            matched_report = [kw for kw in daily_report_keywords if kw in content_lower]
            matched_plan = [kw for kw in daily_plan_keywords if kw in content_lower]
            matched_work = [kw for kw in work_keywords if kw in content_lower]
            
            print(f"\n匹配的关键词:")
            print(f"  日报: {matched_report}")
            print(f"  日计划: {matched_plan}")
            print(f"  工作: {matched_work}")
            
            # 系统识别结果
            identified_type = github_client.identify_content_type(content)
            print(f"\n系统识别类型: {identified_type}")
            
            # 分析为什么是这个结果
            max_score = max(daily_report_score, daily_plan_score)
            print(f"\n=== 识别逻辑分析 ===")
            print(f"最高得分: {max_score}")
            
            if max_score == 0:
                print(f"结果: unknown (所有得分都为0)")
            elif daily_report_score == max_score and daily_report_score > daily_plan_score:
                print(f"结果: daily_report (日报得分 {daily_report_score} > 日计划得分 {daily_plan_score})")
            elif daily_plan_score == max_score and daily_plan_score > daily_report_score:
                print(f"结果: daily_plan (日计划得分 {daily_plan_score} > 日报得分 {daily_report_score})")
            elif daily_report_score == daily_plan_score and daily_report_score > 0:
                print(f"结果: daily_report (得分相等时优先选择日报)")
            
            # 检查是否包含"日计划"字样
            if '日计划' in content:
                print(f"\n⚠️  内容明确包含'日计划'字样！")
                # 查找"日计划"在文本中的位置
                import re
                matches = list(re.finditer(r'日计划', content))
                for i, match in enumerate(matches, 1):
                    start, end = match.span()
                    context_start = max(0, start - 20)
                    context_end = min(len(content), end + 20)
                    context = content[context_start:context_end]
                    print(f"  第{i}处: ...{context}...")
        
        # 4. 检查内容提取结果
        print(f"\n=== 内容提取结果 ===")
        content_data = await github_client.extract_daily_content(target_discussion)
        
        print(f"提取到的内容:")
        print(f"  日结: {len(content_data.get('daily_summary', ''))} 字符")
        print(f"  日计划: {len(content_data.get('daily_plan', ''))} 字符")
        print(f"  周计划: {len(content_data.get('weekly_plan', ''))} 字符")
        
        if content_data.get('daily_plan'):
            print(f"\n日计划内容:\n{content_data['daily_plan']}")
            
        if content_data.get('daily_summary'):
            print(f"\n日结内容:\n{content_data['daily_summary']}")
            
    except Exception as e:
        print(f"❌ 调试失败: {e}")
        import traceback
        traceback.print_exc()

async def main():
    """主函数"""
    print("开始详细调试讨论#64...\n")
    
    await debug_discussion_64_detail()
    
    print("\n调试完成！")

if __name__ == "__main__":
    asyncio.run(main())