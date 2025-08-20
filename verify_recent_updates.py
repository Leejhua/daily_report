#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
验证最近三天的讨论更新情况
检查用户声称的"最近三天有日结更新"是否属实
"""

import asyncio
import os
from datetime import date, timedelta, datetime
from dotenv import load_dotenv
import requests

# 加载环境变量
load_dotenv()

def check_recent_discussions():
    """使用GitHub REST API直接检查最近三天的讨论更新"""
    
    print("🔍 验证最近三天的讨论更新情况")
    print("=" * 50)
    
    # GitHub配置
    token = os.getenv('GITHUB_TOKEN')
    org = os.getenv('GITHUB_ORG', 'LambdaTheory')
    repo = os.getenv('GITHUB_REPO', 'main')
    use_org = os.getenv('USE_ORG_DISCUSSIONS', 'false').lower() == 'true'
    target_category = "2 - 日结"
    
    print(f"📋 配置信息:")
    print(f"   组织: {org}")
    print(f"   仓库: {repo}")
    print(f"   使用组织讨论: {use_org}")
    print(f"   目标分类: {target_category}")
    print()
    
    # 计算日期范围
    today = date.today()
    three_days_ago = today - timedelta(days=2)
    
    print(f"📅 检查时间范围: {three_days_ago} 到 {today}")
    print()
    
    try:
        # 构建API URL
        if use_org:
            # 注意：组织级别的discussions API可能不可用
            print("⚠️ 组织级别的discussions API可能不支持REST调用")
            return
        else:
            url = f"https://api.github.com/repos/{org}/{repo}/discussions"
        
        # 设置请求头
        headers = {
            'Authorization': f'token {token}',
            'Accept': 'application/vnd.github.v3+json',
            'X-GitHub-Api-Version': '2022-11-28'
        }
        
        print(f"🌐 调用API: {url}")
        response = requests.get(url, headers=headers, timeout=30)
        response.raise_for_status()
        
        discussions = response.json()
        print(f"📊 获取到 {len(discussions)} 个讨论")
        print()
        
        # 分析讨论
        target_discussions = []
        recent_updates = []
        
        for discussion in discussions:
            category_name = discussion.get('category', {}).get('name', '')
            
            # 检查分类
            if category_name == target_category:
                target_discussions.append(discussion)
                
                # 解析更新时间
                updated_at_str = discussion.get('updated_at', '')
                if updated_at_str:
                    try:
                        updated_at = datetime.fromisoformat(updated_at_str.replace('Z', '+00:00'))
                        updated_date = updated_at.date()
                        
                        # 检查是否在最近三天内
                        if three_days_ago <= updated_date <= today:
                            recent_updates.append({
                                'number': discussion.get('number'),
                                'title': discussion.get('title'),
                                'updated_at': updated_at,
                                'updated_date': updated_date,
                                'created_at': datetime.fromisoformat(discussion.get('created_at', '').replace('Z', '+00:00')),
                                'author': discussion.get('user', {}).get('login', '')
                            })
                    except Exception as e:
                        print(f"⚠️ 解析时间失败: {e}")
        
        # 输出结果
        print(f"🏷️ 目标分类 '{target_category}' 的讨论: {len(target_discussions)} 个")
        print(f"📅 最近三天更新的目标讨论: {len(recent_updates)} 个")
        print()
        
        if recent_updates:
            print("✅ 找到最近三天的更新:")
            for disc in recent_updates:
                print(f"   #{disc['number']}: {disc['title']}")
                print(f"      👤 作者: {disc['author']}")
                print(f"      📅 更新: {disc['updated_date']} ({disc['updated_at'].strftime('%H:%M:%S')})")
                print(f"      🆕 创建: {disc['created_at'].strftime('%Y-%m-%d %H:%M:%S')}")
                print()
        else:
            print("❌ 未找到最近三天的更新")
            
            if target_discussions:
                print("📋 所有目标分类讨论的更新时间:")
                for disc in target_discussions[:10]:  # 只显示前10个
                    updated_at_str = disc.get('updated_at', '')
                    if updated_at_str:
                        try:
                            updated_at = datetime.fromisoformat(updated_at_str.replace('Z', '+00:00'))
                            print(f"   #{disc.get('number')}: {updated_at.strftime('%Y-%m-%d %H:%M:%S')}")
                        except:
                            print(f"   #{disc.get('number')}: {updated_at_str}")
                print()
        
        # 按日期分组显示
        print("📊 按日期分组的更新统计:")
        for i in range(3):
            check_date = today - timedelta(days=i)
            day_updates = [d for d in recent_updates if d['updated_date'] == check_date]
            print(f"   {check_date} ({check_date.strftime('%A')}): {len(day_updates)} 个更新")
            for disc in day_updates:
                print(f"      └─ #{disc['number']}: {disc['title']}")
        
        print()
        
        # 结论
        if recent_updates:
            print(f"🎯 结论: 用户说得对！最近三天确实有 {len(recent_updates)} 个日结讨论更新")
            print("❗ 系统查询逻辑可能存在问题，需要进一步调试")
        else:
            print("🎯 结论: 最近三天确实没有日结讨论更新")
            print("✅ 系统查询结果是正确的")
            
    except requests.exceptions.RequestException as e:
        print(f"❌ API请求失败: {e}")
    except Exception as e:
        print(f"❌ 处理失败: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    check_recent_discussions()