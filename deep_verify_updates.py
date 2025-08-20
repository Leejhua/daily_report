#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
深度验证最近三天的更新情况
检查讨论本身和评论的更新时间
考虑时区差异和评论活动
"""

import asyncio
import os
from datetime import date, timedelta, datetime
from dotenv import load_dotenv
import requests
import pytz

# 加载环境变量
load_dotenv()

def check_comprehensive_updates():
    """全面检查讨论和评论的更新情况"""
    
    print("🔍 深度验证最近三天的更新情况")
    print("=" * 60)
    
    # GitHub配置
    token = os.getenv('GITHUB_TOKEN')
    org = os.getenv('GITHUB_ORG', 'LambdaTheory')
    repo = os.getenv('GITHUB_REPO', 'main')
    target_category = "2 - 日结"
    
    print(f"📋 配置信息:")
    print(f"   组织: {org}")
    print(f"   仓库: {repo}")
    print(f"   目标分类: {target_category}")
    print()
    
    # 计算日期范围（考虑时区）
    utc_now = datetime.now(pytz.UTC)
    local_now = datetime.now()
    
    print(f"🕐 时间信息:")
    print(f"   本地时间: {local_now.strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"   UTC时间: {utc_now.strftime('%Y-%m-%d %H:%M:%S')}")
    print()
    
    # 扩展检查范围到7天，以防时区问题
    today = date.today()
    check_dates = [today - timedelta(days=i) for i in range(7)]
    
    print(f"📅 检查日期范围: {check_dates[-1]} 到 {check_dates[0]}")
    print()
    
    try:
        # 获取讨论列表
        url = f"https://api.github.com/repos/{org}/{repo}/discussions"
        headers = {
            'Authorization': f'token {token}',
            'Accept': 'application/vnd.github.v3+json',
            'X-GitHub-Api-Version': '2022-11-28'
        }
        
        print(f"🌐 获取讨论列表...")
        response = requests.get(url, headers=headers, timeout=30)
        response.raise_for_status()
        
        discussions = response.json()
        print(f"📊 获取到 {len(discussions)} 个讨论")
        print()
        
        # 筛选目标分类的讨论
        target_discussions = []
        for discussion in discussions:
            category_name = discussion.get('category', {}).get('name', '')
            if category_name == target_category:
                target_discussions.append(discussion)
        
        print(f"🏷️ 目标分类讨论: {len(target_discussions)} 个")
        print()
        
        # 详细检查每个讨论
        recent_activity = []
        
        for discussion in target_discussions:
            number = discussion.get('number')
            title = discussion.get('title', '')
            
            print(f"🔍 检查讨论 #{number}: {title}")
            
            # 解析讨论更新时间
            disc_updated_str = discussion.get('updated_at', '')
            disc_created_str = discussion.get('created_at', '')
            
            if disc_updated_str:
                disc_updated = datetime.fromisoformat(disc_updated_str.replace('Z', '+00:00'))
                disc_created = datetime.fromisoformat(disc_created_str.replace('Z', '+00:00'))
                
                print(f"   📅 讨论创建: {disc_created.strftime('%Y-%m-%d %H:%M:%S')}")
                print(f"   🔄 讨论更新: {disc_updated.strftime('%Y-%m-%d %H:%M:%S')}")
                
                # 检查讨论更新是否在最近几天
                disc_updated_date = disc_updated.date()
                if disc_updated_date in check_dates[:3]:  # 最近3天
                    recent_activity.append({
                        'type': 'discussion',
                        'number': number,
                        'title': title,
                        'updated_at': disc_updated,
                        'updated_date': disc_updated_date
                    })
                    print(f"   ✅ 讨论在最近3天内更新!")
            
            # 获取讨论的评论
            try:
                comments_url = f"https://api.github.com/repos/{org}/{repo}/discussions/{number}/comments"
                print(f"   💬 获取评论...")
                
                comments_response = requests.get(comments_url, headers=headers, timeout=30)
                if comments_response.status_code == 200:
                    comments = comments_response.json()
                    print(f"   📝 找到 {len(comments)} 个评论")
                    
                    # 检查评论更新时间
                    for comment in comments:
                        comment_updated_str = comment.get('updated_at', '')
                        if comment_updated_str:
                            comment_updated = datetime.fromisoformat(comment_updated_str.replace('Z', '+00:00'))
                            comment_updated_date = comment_updated.date()
                            
                            if comment_updated_date in check_dates[:3]:  # 最近3天
                                recent_activity.append({
                                    'type': 'comment',
                                    'number': number,
                                    'title': title,
                                    'updated_at': comment_updated,
                                    'updated_date': comment_updated_date,
                                    'comment_id': comment.get('id'),
                                    'comment_author': comment.get('user', {}).get('login', '')
                                })
                                print(f"   ✅ 评论在最近3天内更新: {comment_updated.strftime('%Y-%m-%d %H:%M:%S')}")
                                print(f"      👤 评论作者: {comment.get('user', {}).get('login', '')}")
                
                elif comments_response.status_code == 404:
                    print(f"   ⚠️ 评论API不可用 (404)")
                else:
                    print(f"   ❌ 获取评论失败: {comments_response.status_code}")
                    
            except Exception as e:
                print(f"   ❌ 评论检查失败: {e}")
            
            print()
        
        # 汇总结果
        print("📊 最近3天活动汇总:")
        print("=" * 40)
        
        if recent_activity:
            print(f"✅ 找到 {len(recent_activity)} 个最近3天的活动:")
            print()
            
            # 按日期分组
            for i in range(3):
                check_date = today - timedelta(days=i)
                day_activities = [a for a in recent_activity if a['updated_date'] == check_date]
                
                print(f"📅 {check_date} ({check_date.strftime('%A')}): {len(day_activities)} 个活动")
                
                for activity in day_activities:
                    if activity['type'] == 'discussion':
                        print(f"   🗣️ 讨论更新: #{activity['number']} - {activity['title']}")
                        print(f"      🕐 {activity['updated_at'].strftime('%H:%M:%S')}")
                    else:
                        print(f"   💬 评论更新: #{activity['number']} - {activity['title']}")
                        print(f"      👤 {activity['comment_author']} 🕐 {activity['updated_at'].strftime('%H:%M:%S')}")
                print()
            
            print("🎯 结论: 用户说得对！最近3天确实有活动")
            print("❗ 系统可能只检查了讨论本身的更新时间，忽略了评论活动")
            
        else:
            print("❌ 确实没有找到最近3天的任何活动")
            print("✅ 系统查询结果是正确的")
            
            # 显示最近的活动时间
            print("\n📋 最近的活动时间:")
            all_times = []
            
            for discussion in target_discussions:
                updated_str = discussion.get('updated_at', '')
                if updated_str:
                    updated = datetime.fromisoformat(updated_str.replace('Z', '+00:00'))
                    all_times.append((discussion.get('number'), updated, 'discussion'))
            
            all_times.sort(key=lambda x: x[1], reverse=True)
            
            for number, updated, activity_type in all_times[:5]:
                days_ago = (datetime.now(pytz.UTC) - updated).days
                print(f"   #{number}: {updated.strftime('%Y-%m-%d %H:%M:%S')} ({days_ago} 天前)")
            
    except Exception as e:
        print(f"❌ 检查失败: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    check_comprehensive_updates()