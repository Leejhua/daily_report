#!/usr/bin/env python3
"""
评论功能与主系统集成测试
验证DailyAnalyzer能否正常调用评论功能
"""

import asyncio
import sys
from pathlib import Path

# 添加项目根目录到Python路径
sys.path.append(str(Path(__file__).parent))

from src.config import Config
from src.analyzers.daily_analyzer import DailyAnalyzer
from src.utils.logger import setup_logging


async def test_integration():
    """测试评论功能与主系统的集成"""
    print("🔧 开始评论功能集成测试")
    print("=" * 50)
    
    try:
        # 1. 初始化配置和组件
        print("1️⃣ 初始化系统组件...")
        config = Config()
        analyzer = DailyAnalyzer(config)
        print("✅ 系统组件初始化成功")
        
        # 2. 测试分析器能否正常创建
        print("\n2️⃣ 验证分析器组件...")
        print(f"✅ GitHub客户端: {type(analyzer.github_client).__name__}")
        print(f"✅ GLM客户端: {type(analyzer.glm_client).__name__}")
        
        # 3. 测试GitHub连接
        print("\n3️⃣ 测试GitHub连接...")
        discussions = await analyzer.github_client.get_daily_discussions()
        print(f"✅ 成功获取 {len(discussions)} 个讨论")
        
        # 4. 测试分析指定讨论（使用讨论#60）
        print("\n4️⃣ 测试分析指定讨论...")
        test_discussion_number = 60
        
        # 直接通过analyze_specific_discussion方法测试
        try:
            result = await analyzer.analyze_specific_discussion(test_discussion_number)
            if result.get('success'):
                print(f"✅ 讨论 #{test_discussion_number} 分析成功")
                print(f"   - 评论发布: {'成功' if result.get('comment_posted') else '失败'}")
                if result.get('analysis_length'):
                    print(f"   - 分析报告长度: {result['analysis_length']} 字符")
            else:
                print(f"❌ 讨论分析失败: {result.get('error', '未知错误')}")
        except Exception as e:
            print(f"❌ 分析过程出错: {e}")
            
        # 5. 额外测试：直接获取讨论进行内容分析
        print("\n5️⃣ 测试直接讨论分析...")
        
        # 模拟获取讨论数据
        from src.clients.github_client import DiscussionData
        from datetime import datetime
        target_discussion = DiscussionData(
            id="test_id",
            number=test_discussion_number,
            title="测试讨论",
            body="测试内容",
            author="test_user",
            created_at=datetime.now(),
            updated_at=datetime.now(),
            category="日结",
            url="https://github.com/test/test/discussions/60",
            comments_count=0
        )
        
        if target_discussion:
            # 测试评论发布功能
            print("\n6️⃣ 测试评论发布功能...")
            comment_success = await analyzer.github_client.post_analysis_comment(
                target_discussion.number,
                "🧪 **集成测试评论**\n\n这是一条集成测试评论，验证评论功能与主系统的集成是否正常。\n\n测试时间: " + str(asyncio.get_event_loop().time())
            )
            
            if comment_success:
                print("✅ 评论发布成功！")
            else:
                print("❌ 评论发布失败")
        
        print("\n" + "=" * 50)
        print("🎉 集成测试完成")
        
    except Exception as e:
        print(f"\n❌ 集成测试失败: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    # 设置日志
    setup_logging()
    
    # 运行测试
    asyncio.run(test_integration())