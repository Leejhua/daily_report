#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
真实飞书通知发送测试 (使用API模式)
展示改进后的个人通知和管理层通知的实际效果

注意: 此脚本使用飞书API而非Webhook发送通知
- 个人通知: 使用 send_text_message API 发送到指定用户
- 管理层通知: 使用 send_management_notification API 发送到配置的管理层用户
- 需要配置: app_id, app_secret, 用户open_id等API凭证
"""

import asyncio
import sys
import os
from datetime import datetime

# 添加项目根目录到Python路径
sys.path.append(os.path.dirname(__file__))

from src.config import Config
from src.generators.report_generator import ReportGenerator
from src.clients.glm_client import GLMClient
from src.clients.enhanced_feishu_client import EnhancedFeishuClient, FeishuClientWrapper


def count_chinese_chars(text: str) -> int:
    """计算中文字符数量"""
    return len([char for char in text if '\u4e00' <= char <= '\u9fff']) + len([char for char in text if not ('\u4e00' <= char <= '\u9fff')])


async def test_real_feishu_notifications():
    """测试真实的飞书通知发送"""
    print("🚀 开始真实飞书通知发送测试")
    print("=" * 60)
    
    try:
        # 加载配置
        config = Config()
        print("✅ 配置加载成功")
        
        # 创建GLM客户端
        glm_client = GLMClient(config.glm)
        print("✅ GLM客户端创建成功")
        
        # 创建增强飞书客户端 (使用API而非webhook)
        enhanced_feishu_client = EnhancedFeishuClient(config.feishu.api)
        feishu_client = FeishuClientWrapper(enhanced_feishu_client)
        print("✅ 飞书API客户端创建成功")
        
        # 测试API连接
        if enhanced_feishu_client.test_connection():
            print("✅ 飞书API连接测试成功")
        else:
            print("❌ 飞书API连接测试失败，请检查配置")
        
        # 创建报告生成器
        report_generator = ReportGenerator(config)
        print("✅ 报告生成器创建成功")
        
        # 创建测试数据
        test_data = [
            {
                "date": "2025-01-28",
                "user": "张三",
                "planned_tasks": ["完成项目文档", "代码审查", "团队会议"],
                "completed_tasks": ["完成项目文档"],
                "deviation_score": 7.5,
                "completion_rate": 0.33,
                "deviation_reasons": ["任务优先级调整", "突发需求处理"],
                "suggestions": ["提前规划任务优先级", "预留缓冲时间"]
            }
        ]
        
        print("\n📊 测试数据准备完成")
        print(f"用户: {test_data[0]['user']}")
        print(f"偏离度评分: {test_data[0]['deviation_score']}")
        print(f"完成率: {test_data[0]['completion_rate']:.0%}")
        
        # 生成个人通知
        print("\n" + "=" * 60)
        print("🧑‍💼 生成个人通知")
        print("=" * 60)
        
        personal_report = report_generator.generate_llm_report(
            user_name="张三",
            analyses=test_data,
            report_type="personal"
        )
        
        if personal_report["success"]:
            personal_content = personal_report["content"]
            personal_char_count = count_chinese_chars(personal_content)
            
            print(f"📝 个人通知内容:")
            print("-" * 40)
            print(personal_content)
            print("-" * 40)
            print(f"📏 字符统计: {personal_char_count} 字")
            print(f"🎯 长度控制: {'✅ 符合要求' if personal_char_count <= 200 else '❌ 超出限制'}")
            
            # 发送个人通知到飞书 (使用API)
            print("\n📤 发送个人通知到飞书API...")
            try:
                # 使用API发送文本消息到指定用户 (LEEJHUA的真实open_id)
                # 注意: 使用LEEJHUA的真实飞书用户ID进行测试
                personal_send_result = enhanced_feishu_client.send_text_message(
                    receive_id="ou_c9cf0adee8b20877a1bb793df7a364bb",  # LEEJHUA的飞书用户ID
                    text=personal_report['content'],
                    receive_id_type="open_id"
                )
                print("📝 API调用说明: 使用 send_text_message 方法发送到指定用户")
                
                if personal_send_result:
                    print("✅ 个人通知API发送成功")
                else:
                    print("❌ 个人通知API发送失败")
            except Exception as e:
                print(f"❌ 个人通知API发送异常: {e}")
                personal_send_result = False
        else:
            print(f"❌ 个人通知生成失败: {personal_report.get('error', '未知错误')}")
        
        # 等待一下，避免发送过快
        await asyncio.sleep(2)
        
        # 生成管理层通知
        print("\n" + "=" * 60)
        print("👔 生成管理层通知")
        print("=" * 60)
        
        management_report = report_generator.generate_llm_report(
            user_name="张三",
            analyses=test_data,
            report_type="management"
        )
        
        if management_report["success"]:
            management_content = management_report["content"]
            management_char_count = count_chinese_chars(management_content)
            
            print(f"📝 管理层通知内容:")
            print("-" * 40)
            print(management_content)
            print("-" * 40)
            print(f"📏 字符统计: {management_char_count} 字")
            print(f"🎯 长度控制: {'✅ 符合要求' if management_char_count <= 150 else '❌ 超出限制'}")
            
            # 发送管理层通知到飞书 (使用API)
            print("\n📤 发送管理层通知到飞书API...")
            try:
                # 使用API发送管理层通知 (读取配置文件中的管理层用户ID)
                management_send_result = feishu_client.send_management_notification(
                    message_content=management_report['content']
                )
                print("📝 API调用说明: 使用 send_management_notification 方法发送到配置的管理层用户")
                
                if management_send_result:
                    print("✅ 管理层通知API发送成功")
                else:
                    print("❌ 管理层通知API发送失败")
            except Exception as e:
                print(f"❌ 管理层通知API发送异常: {e}")
                management_send_result = False
        else:
            print(f"❌ 管理层通知生成失败: {management_report.get('error', '未知错误')}")
        
        # 内容对比分析
        if personal_report["success"] and management_report["success"]:
            print("\n" + "=" * 60)
            print("🔍 内容对比分析")
            print("=" * 60)
            
            # 分析关键词差异
            personal_keywords = ["温暖", "鼓励", "建议", "改进", "加油", "相信"]
            management_keywords = ["风险", "影响", "行动", "评估", "资源", "管理"]
            
            personal_matches = sum(1 for keyword in personal_keywords if keyword in personal_content)
            management_matches = sum(1 for keyword in management_keywords if keyword in management_content)
            
            print(f"👤 个人通知关键词匹配: {personal_matches}/{len(personal_keywords)}")
            print(f"👔 管理层通知关键词匹配: {management_matches}/{len(management_keywords)}")
            
            # 分析语调差异
            encouraging_words = ["加油", "相信", "一定能", "努力", "坚持"]
            business_words = ["评估", "决策", "资源", "风险", "管理"]
            
            personal_tone = sum(1 for word in encouraging_words if word in personal_content)
            management_tone = sum(1 for word in business_words if word in management_content)
            
            print(f"😊 个人通知鼓励性语调: {personal_tone} 个相关词汇")
            print(f"💼 管理层通知商务语调: {management_tone} 个相关词汇")
            
            if personal_matches < management_matches and personal_tone > 0:
                print("\n✅ 内容区分度: 良好")
            else:
                print("\n⚠️ 内容区分度: 需要改进")
        
        # 测试总结
        print("\n" + "=" * 60)
        print("📊 测试总结")
        print("=" * 60)
        
        success_count = 0
        total_tests = 4
        
        if personal_report.get("success"):
            success_count += 1
            print("✅ 个人通知生成: 成功")
        else:
            print("❌ 个人通知生成: 失败")
        
        if management_report.get("success"):
            success_count += 1
            print("✅ 管理层通知生成: 成功")
        else:
            print("❌ 管理层通知生成: 失败")
        
        # 检查发送结果
        if 'personal_send_result' in locals() and personal_send_result:
            success_count += 1
            print("✅ 个人通知发送: 成功")
        else:
            print("❌ 个人通知发送: 失败 (需要配置飞书API凭证和用户ID)")
        
        if 'management_send_result' in locals() and management_send_result:
            success_count += 1
            print("✅ 管理层通知发送: 成功")
        else:
            print("❌ 管理层通知发送: 失败 (需要配置飞书API凭证和管理层用户ID)")
        
        print(f"\n🎯 测试通过率: {success_count}/{total_tests} ({success_count/total_tests*100:.1f}%)")
        
        if success_count == total_tests:
            print("🎉 所有测试通过！真实飞书通知发送成功！")
        else:
            print("⚠️ 部分测试失败，请检查配置和网络连接")
        
        print("\n🏁 真实飞书通知测试完成")
        print("\n💡 提示: 要实际发送到飞书，请在配置文件中设置有效的飞书API凭证 (app_id, app_secret) 和用户ID")
        
    except Exception as e:
        print(f"❌ 测试过程中发生错误: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    asyncio.run(test_real_feishu_notifications())