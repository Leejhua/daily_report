import sys
sys.path.append('.')
from datetime import date
from src.clients.github_client import GitHubClient
from src.config import Config
import asyncio

async def check_discussions():
    try:
        config = Config()
        client = GitHubClient(config.github)
        
        # 检查2025-08-28的讨论
        target_date = date(2025, 8, 28)
        discussions = await client.get_daily_discussions(target_date)
        
        print(f"找到 {len(discussions)} 个讨论 for {target_date}")
        
        # 显示最近的几个讨论
        print("\n最近的讨论:")
        for i, discussion in enumerate(discussions[:5]):
            print(f"{i+1}. #{discussion['number']} - {discussion['title']}")
            print(f"   更新时间: {discussion['updatedAt']}")
            print(f"   分类: {discussion.get('category', {}).get('name', 'N/A')}")
            print()
            
        # 检查是否有日报分类的讨论
        daily_report_discussions = [d for d in discussions if d.get('category', {}).get('name') == '2 - 日结']
        print(f"\n日报分类讨论数量: {len(daily_report_discussions)}")
        
    except Exception as e:
        print(f"GitHub客户端初始化失败: {e}")

if __name__ == '__main__':
    asyncio.run(check_discussions())