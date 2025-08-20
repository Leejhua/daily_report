import asyncio
from src.clients.github_client import GitHubClient
from src.config import Config

async def test_discussions():
    config = Config()
    client = GitHubClient(config.github)
    
    print(f"配置: 组织={config.github.organization}, 仓库={config.github.repository}")
    print(f"使用组织级别Discussions: {config.github.use_org_discussions}")
    
    try:
        discussions = await client._get_repo_discussions()
        print(f"\n找到 {len(discussions)} 个讨论:")
        
        for i, d in enumerate(discussions[:10]):
            print(f"- #{d.number}: {d.title} (分类: {d.category.name})")
            
        if discussions:
            print(f"\n可以使用讨论编号 #{discussions[0].number} 进行测试")
        else:
            print("\n仓库中没有找到任何讨论")
            
    except Exception as e:
        print(f"获取讨论失败: {e}")

if __name__ == "__main__":
    asyncio.run(test_discussions())