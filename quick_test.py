#!/usr/bin/env python3
"""
快速测试脚本 - 验证GitHub组织级别Discussions访问
"""

import os
import sys
from datetime import date

# 简单测试配置加载
def test_config():
    print("🔧 测试配置加载...")
    
    # 加载环境变量
    try:
        from dotenv import load_dotenv
        load_dotenv()
    except ImportError:
        print("❌ 无法导入python-dotenv")
        return False
    
    # 检查环境变量
    github_token = os.getenv('GITHUB_TOKEN')
    github_org = os.getenv('GITHUB_ORG')
    glm_api_key = os.getenv('GLM_API_KEY')
    
    print(f"GitHub Token: {'✅ 已配置' if github_token else '❌ 未配置'}")
    print(f"GitHub组织: {github_org if github_org else '❌ 未配置'}")
    print(f"GLM API Key: {'✅ 已配置' if glm_api_key else '❌ 未配置'}")
    
    return bool(github_token and github_org and glm_api_key)

def test_imports():
    print("\n📦 测试依赖包...")
    
    try:
        import requests
        print("✅ requests")
    except ImportError:
        print("❌ requests - 需要安装: pip install requests")
        return False
    
    try:
        import yaml
        print("✅ PyYAML")
    except ImportError:
        print("❌ PyYAML - 需要安装: pip install PyYAML")
        return False
    
    try:
        from dotenv import load_dotenv
        print("✅ python-dotenv")
    except ImportError:
        print("❌ python-dotenv - 需要安装: pip install python-dotenv")
        return False
    
    try:
        from github import Github
        print("✅ PyGithub")
    except ImportError:
        print("❌ PyGithub - 需要安装: pip install PyGithub")
        return False
    
    try:
        import zhipuai
        print("✅ zhipuai")
    except ImportError:
        print("❌ zhipuai - 需要安装: pip install zhipuai")
        return False
    
    return True

def test_github_connection():
    print("\n🐙 测试GitHub连接...")
    
    from dotenv import load_dotenv
    load_dotenv()
    
    try:
        from github import Github
        
        github_token = os.getenv('GITHUB_TOKEN')
        github_org = os.getenv('GITHUB_ORG')
        
        if not github_token or not github_org:
            print("❌ 缺少GitHub配置")
            return False
        
        # 创建GitHub客户端
        g = Github(github_token)
        
        # 测试组织访问
        org = g.get_organization(github_org)
        print(f"✅ 组织访问成功: {org.login}")
        
        # 测试Discussions访问
        discussions = list(org.get_discussions())
        print(f"✅ Discussions访问成功，找到 {len(discussions)} 个讨论")
        
        # 查找"2 - 日结"分类
        categories = set()
        target_category = "2 - 日结"
        found_target = False
        
        for disc in discussions[:10]:  # 只检查前10个
            categories.add(disc.category.name)
            if disc.category.name == target_category:
                found_target = True
        
        print(f"📁 找到分类: {', '.join(sorted(categories))}")
        
        if found_target:
            print(f"✅ 找到目标分类: {target_category}")
        else:
            print(f"⚠️ 未找到目标分类: {target_category}")
            print("可用分类:", ', '.join(sorted(categories)))
        
        # 查找测试讨论 #52
        test_discussion = None
        for disc in discussions:
            if disc.number == 52:
                test_discussion = disc
                break
        
        if test_discussion:
            print(f"✅ 找到测试讨论 #{test_discussion.number}: {test_discussion.title}")
            print(f"   📅 更新时间: {test_discussion.updated_at}")
            print(f"   📁 分类: {test_discussion.category.name}")
            print(f"   💬 评论数: {test_discussion.comments}")
        else:
            print("⚠️ 未找到讨论 #52")
        
        return True
        
    except Exception as e:
        print(f"❌ GitHub连接失败: {e}")
        return False

def test_glm_connection():
    print("\n🤖 测试GLM连接...")
    
    try:
        import zhipuai
        from dotenv import load_dotenv
        load_dotenv()
        
        api_key = os.getenv('GLM_API_KEY')
        if not api_key:
            print("❌ 缺少GLM API密钥")
            return False
        
        client = zhipuai.ZhipuAI(api_key=api_key)
        
        # 测试简单调用
        response = client.chat.completions.create(
            model="glm-4-flash",
            messages=[
                {"role": "system", "content": "你是一个测试助手。"},
                {"role": "user", "content": "请回复'连接测试成功'。"}
            ],
            temperature=0.1,
            max_tokens=50
        )
        
        result = response.choices[0].message.content
        print(f"✅ GLM连接成功: {result}")
        return True
        
    except Exception as e:
        print(f"❌ GLM连接失败: {e}")
        return False

def main():
    print("🚀 GitHub Discussions 自动化分析服务 - 快速测试")
    print("="*60)
    
    # 加载环境变量
    try:
        from dotenv import load_dotenv
        load_dotenv()
        print("✅ 环境变量加载成功")
    except ImportError:
        print("❌ 无法导入python-dotenv，请安装: pip install python-dotenv")
        return False
    
    # 测试步骤
    tests = [
        ("配置检查", test_config),
        ("依赖包检查", test_imports),
        ("GitHub连接", test_github_connection),
        ("GLM连接", test_glm_connection),
    ]
    
    results = []
    for test_name, test_func in tests:
        try:
            success = test_func()
            results.append((test_name, success))
        except Exception as e:
            print(f"❌ {test_name}测试异常: {e}")
            results.append((test_name, False))
    
    # 显示测试总结
    print("\n" + "="*60)
    print("📊 测试总结")
    print("="*60)
    
    passed = sum(1 for _, success in results if success)
    total = len(results)
    
    for test_name, success in results:
        status = "✅ 通过" if success else "❌ 失败"
        print(f"{status} {test_name}")
    
    print(f"\n🎯 总体结果: {passed}/{total} 项测试通过")
    
    if passed == total:
        print("🎉 所有测试通过！可以运行完整服务。")
        print("\n下一步:")
        print("1. 测试特定讨论解析: python scripts/test_daily_structure.py discuss 52")
        print("2. 生成分析预览: python scripts/manual_analysis.py discuss 52 --preview")
        print("3. 启动定时服务: python src/main.py")
    else:
        print("⚠️ 部分测试失败，请检查上述错误信息。")
    
    return passed == total

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)

