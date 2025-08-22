import sys
sys.path.append('D:\\cursor_glm')

from src.config import Config
from src.analyzers.daily_analyzer import DailyAnalyzer
from datetime import date

async def debug_analysis_process():
    """调试分析过程，看看到底发生了什么"""
    print("🔍 调试2025-08-22的分析过程...")
    
    config = Config()
    analyzer = DailyAnalyzer(config)
    
    target_date = date(2025, 8, 22)
    
    # 1. 获取当日讨论
    print("\n📋 步骤1: 获取当日讨论")
    discussions = await analyzer.github_client.get_daily_discussions(target_date)
    print(f"找到 {len(discussions)} 个讨论:")
    
    for disc in discussions:
        print(f"  #{disc.number}: {disc.title}")
    
    # 2. 找到讨论#57
    discussion_57 = None
    for disc in discussions:
        if disc.number == 57:
            discussion_57 = disc
            break
    
    if not discussion_57:
        print("❌ 未找到讨论#57")
        return
    
    print(f"\n✅ 找到讨论#57: {discussion_57.title}")
    
    # 3. 提取内容
    print("\n📋 步骤2: 提取内容")
    content_data = await analyzer.github_client.extract_daily_content(discussion_57)
    
    daily_summary = content_data.get('daily_summary', '')
    daily_plan = content_data.get('daily_plan', '')
    
    print(f"日报内容长度: {len(daily_summary)}")
    print(f"日计划内容长度: {len(daily_plan)}")
    
    if daily_summary:
        print(f"日报内容预览: {daily_summary[:100]}...")
    if daily_plan:
        print(f"日计划内容预览: {daily_plan[:100]}...")
    
    # 4. 检查是否已有回复
    print("\n📋 步骤3: 检查现有回复")
    
    if daily_summary:
        # 查找日报评论ID
        daily_summary_comment_id = await analyzer._find_content_comment_id(
            discussion_57.number, 'daily_summary'
        )
        print(f"日报评论ID: {daily_summary_comment_id}")
        
        if daily_summary_comment_id:
            already_replied = await analyzer.github_client.check_already_replied(
                discussion_57.number, daily_summary_comment_id, 'daily_report'
            )
            print(f"日报是否已有回复: {already_replied}")
    
    if daily_plan:
        # 查找日计划评论ID
        daily_plan_comment_id = await analyzer._find_content_comment_id(
            discussion_57.number, 'daily_plan'
        )
        print(f"日计划评论ID: {daily_plan_comment_id}")
        
        if daily_plan_comment_id:
            already_replied = await analyzer.github_client.check_already_replied(
                discussion_57.number, daily_plan_comment_id, 'daily_plan'
            )
            print(f"日计划是否已有回复: {already_replied}")
    
    # 5. 测试分析过程
    print("\n📋 步骤4: 执行完整分析")
    result = await analyzer._analyze_single_discussion(discussion_57)
    
    print(f"分析结果: {result}")

if __name__ == "__main__":
    import asyncio
    asyncio.run(debug_analysis_process())