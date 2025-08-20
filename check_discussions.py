#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
检查GitHub仓库中的实际讨论情况
"""

import os
import sys
import requests
import json
from datetime import datetime, timedelta
from dotenv import load_dotenv

# 添加src目录到Python路径
sys.path.append(os.path.join(os.path.dirname(__file__), 'src'))

from config import Config

def main():
    # 加载环境变量
    load_dotenv()
    
    print("🔍 检查GitHub仓库讨论情况")
    print("=" * 50)
    
    try:
        # 初始化配置
        config = Config()
        
        print(f"📋 仓库: {config.github.organization}/{config.github.repository}")
        print(f"🏷️ 目标分类: {config.github.discussion_category}")
        print(f"🔧 使用组织讨论: {config.github.use_org_discussions}")
        print()
        
        # 计算最近三天的日期范围
        today = datetime.now().date()
        three_days_ago = today - timedelta(days=2)
        
        print(f"📅 检查时间范围: {three_days_ago} 到 {today}")
        print()
        
        # 获取分类信息
        print("📥 获取所有可用分类...")
        try:
            query = """
            query($owner: String!, $name: String!) {
                repository(owner: $owner, name: $name) {
                    discussionCategories(first: 20) {
                        nodes {
                            name
                            description
                        }
                    }
                    discussions(first: 50, orderBy: {field: UPDATED_AT, direction: DESC}) {
                        nodes {
                            number
                            title
                            createdAt
                            updatedAt
                            category {
                                name
                            }
                        }
                    }
                }
            }
            """
            
            variables = {
                "owner": config.github.organization,
                "name": config.github.repository
            }
            
            headers = {
                "Authorization": f"Bearer {config.github.token}",
                "Content-Type": "application/json"
            }
            
            payload = {
                "query": query,
                "variables": variables
            }
            
            response = requests.post(
                "https://api.github.com/graphql",
                headers=headers,
                json=payload,
                timeout=30
            )
            
            if response.status_code != 200:
                print(f"❌ HTTP错误: {response.status_code}")
                print(f"   响应: {response.text}")
                return
                
            result = response.json()
            
            if 'data' in result and result['data']['repository']:
                repo_data = result['data']['repository']
                
                # 显示所有分类
                categories = []
                if 'discussionCategories' in repo_data:
                    for category in repo_data['discussionCategories']['nodes']:
                        categories.append(category['name'])
                
                print("🏷️ 所有分类:")
                for category in sorted(categories):
                    mark = "✅" if category == config.github.discussion_category else "  "
                    print(f"   {mark} {category}")
                print()
                
                # 分析讨论
                discussions = repo_data.get('discussions', {}).get('nodes', [])
                total_discussions = len(discussions)
                category_discussions = 0
                recent_discussions = 0
                
                print(f"📊 总讨论数: {total_discussions}")
                print()
                
                for discussion in discussions:
                    category_name = discussion['category']['name']
                    
                    # 检查分类
                    if category_name == config.github.discussion_category:
                        category_discussions += 1
                        
                        # 解析时间
                        updated_at = datetime.fromisoformat(discussion['updatedAt'].replace('Z', '+00:00'))
                        created_at = datetime.fromisoformat(discussion['createdAt'].replace('Z', '+00:00'))
                        updated_date = updated_at.date()
                        created_date = created_at.date()
                        
                        # 检查更新时间
                        if three_days_ago <= updated_date <= today:
                            recent_discussions += 1
                            
                            print(f"✅ 找到近期讨论: #{discussion['number']} - {discussion['title']}")
                            print(f"   📅 创建: {created_date}, 更新: {updated_date}")
                            print(f"   🏷️ 分类: {category_name}")
                            print()
                
                # 输出统计结果
                print("📊 统计结果:")
                print(f"   总讨论数: {total_discussions}")
                print(f"   目标分类讨论数: {category_discussions}")
                print(f"   近三天更新的目标分类讨论数: {recent_discussions}")
                print()
                
                if recent_discussions == 0:
                    print("❌ 未找到近三天更新的目标分类讨论")
                    print("💡 可能的原因:")
                    print(f"   1. 分类名称不匹配 (当前设置: '{config.github.discussion_category}')")
                    print("   2. 近三天确实没有更新的讨论")
                    print("   3. GitHub访问权限问题")
                    
                    if category_discussions > 0:
                        print(f"   ℹ️ 注意: 找到了 {category_discussions} 个目标分类的讨论，但都不在近三天内更新")
                else:
                    print(f"✅ 找到 {recent_discussions} 个近三天更新的目标分类讨论")
                    
            else:
                print("❌ 无法获取仓库数据")
                print(f"   响应内容: {result}")
                
        except Exception as e:
            print(f"❌ GraphQL查询失败: {e}")
            import traceback
            traceback.print_exc()
            
    except Exception as e:
        print(f"❌ 错误: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main()