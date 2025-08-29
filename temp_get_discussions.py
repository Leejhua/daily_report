import sys
sys.path.append('src')
from clients.github_client import GitHubClient
from config import Config
import json

config = Config('config/config_v2.yaml')
client = GitHubClient(config.github)
discussions = client.get_discussions_for_date('2025-08-27')
print(json.dumps([d.__dict__ for d in discussions], indent=2, ensure_ascii=False, default=str))