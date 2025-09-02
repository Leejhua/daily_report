#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
通知系统演示脚本

展示不同类型的通知格式和LLM生成的个性化报告内容
"""

import json
from datetime import datetime, timedelta

def print_section_header(title):
    """打印章节标题"""
    print("\n" + "="*60)
    print(f"  {title}")
    print("="*60)

def print_subsection_header(title):
    """打印子章节标题"""
    print("\n" + "-"*40)
    print(f"  {title}")
    print("-"*40)

def demo_personal_notification_traditional():
    """演示传统个人通知格式"""
    user = "张三"
    consecutive_days = 3
    
    message_lines = [
        f"嘿 {user}，",
        f"最近{consecutive_days}天工作好像有点偏离轨道了，咱们聊聊？😊",
        "",
        "我发现了什么：",
        "工作进度跟计划有点不太一样，不过别担心，这种事儿谁都会遇到。",
        "",
        "几个小想法：",
        "• 要不重新整理下任务，看看哪些真的急",
        "• 遇到卡壳的地方就找人聊聊，别一个人硬扛",
        "• 节奏可以调调，有时候慢点反而更稳",
        "• 别给自己太大压力，适当放松一下",
        "",
        "说真的：",
        "状态有起伏很正常，关键是调整过来就行。你平时挺努力的，相信很快就能找回感觉！",
        "",
        "有啥需要帮忙的就说话，咱们一起想办法！加油 🚀"
    ]
    
    return '\n'.join(message_lines)

def demo_personal_notification_llm():
    """演示LLM生成的个人通知格式"""
    return """嘿 张三！👋

最近3天工作好像有点偏离轨道了，咱们聊聊？😊

我发现了什么：
工作进度跟计划有点不太一样，不过别担心，这种事儿谁都会遇到。

几个小想法：
• 要不重新整理下任务，看看哪些真的急
• 遇到卡壳的地方就找人聊聊，别一个人硬扛
• 节奏可以调调，有时候慢点反而更稳
• 别给自己太大压力，适当放松一下

说真的：
状态有起伏很正常，关键是调整过来就行。你平时挺努力的，相信很快就能找回感觉！

有任何困难随时找我聊，一起想办法解决！"""

def demo_management_notification_traditional():
    """演示传统管理层通知格式"""
    affected_users = ["张三", "李四"]
    
    message_lines = [
        "⚠️ 团队状态预警",
        "",
        "异常情况：",
        f"{len(affected_users)}名团队成员工作进度偏离计划",
        "",
        "涉及人员：",
        *[f"• {user}" for user in affected_users],
        "",
        "建议行动：",
        "• 与相关成员一对一沟通，了解具体困难",
        "• 评估是否需要调整任务分配或资源配置",
        "• 必要时重新评估项目时间线",
        "",
        "建议24小时内处理。"
    ]
    
    return '\n'.join(message_lines)

def demo_management_notification_llm():
    """演示LLM生成的管理层通知格式"""
    return """⚠️ **团队状态预警**

**异常成员**：张三
**风险等级**：中等（连续3天偏离）
**影响评估**：可能影响项目进度

**问题分析**：
• 任务优先级不明确，会议过多
• 技术难题阻碍，个人效率下降
• 偏离程度呈上升趋势

**建议行动**：
• 48小时内安排一对一沟通，了解具体困难
• 评估任务分配合理性，必要时调整优先级
• 提供技术支持，优化会议安排
• 考虑暂时减少非核心任务

**管理要点**：
该成员平时表现良好，当前状况可能是外部因素导致。建议以支持态度沟通，重点移除障碍而非施压。

**跟进计划**：本周内每日简短check-in"""

def demo_detailed_report_traditional():
    """演示传统详细报告格式"""
    return """🚨 **工作执行偏离详细报告**

**相关人员**：@张三
**报告时间**：2024-01-15 14:30:00
**预警级别**：中等
**分析周期**：最近3个工作日

**偏离情况概述**：
连续3天出现工作偏离，平均完成率65%，偏离程度呈上升趋势。

**核心问题**：
• 任务优先级不明确，经常在不重要的事情上花费过多时间
• 会议过多，打断了专注工作的时间
• 技术难题遇到阻碍，进度受到影响

**改进建议**：
• 重新梳理任务优先级，使用时间管理工具
• 减少非必要会议，设置专注工作时间段
• 及时寻求技术支持，不要独自钻牛角尖
• 制定每日工作计划，设置明确的完成目标

**风险提示**：
连续偏离表明存在系统性问题，建议管理层重点关注并制定针对性改进措施。如不及时处理，可能影响整体项目进度和团队效率。

**后续跟进**：
建议在3个工作日内制定改进计划，并在一周内开始实施相关措施。"""

def demo_brief_report_traditional():
    """演示传统简洁报告格式"""
    return """📊 **工作状态预警通知**

**相关人员**：@张三
**预警时间**：2024-01-15 14:30:00
**影响程度**：中等

**核心问题**：
• 任务优先级不明确，经常在不重要的事情上花费过多时间
• 会议过多，打断了专注工作的时间
• 技术难题遇到阻碍，进度受到影响

**改进建议**：
• 重新梳理任务优先级，使用时间管理工具
• 减少非必要会议，设置专注工作时间段
• 及时寻求技术支持，不要独自钻牛角尖

**关键数据**：连续3天偏离，平均完成率65%

偏离程度呈上升趋势，请及时关注并采取改进措施。"""

def demo_notification_system_features():
    """演示通知系统的特色功能"""
    print_subsection_header("智能通知系统特色功能")
    
    features = [
        "🤖 **LLM智能生成**：根据具体情况生成个性化通知内容",
        "🎯 **双重通知模式**：个人私聊 + 管理层通知，确保信息传达",
        "⏰ **智能时间控制**：只在工作时间发送，避免打扰",
        "🔄 **防重复机制**：4小时内不重复发送相同类型通知",
        "📊 **多格式支持**：详细、简洁、卡片等多种报告格式",
        "🛡️ **智能降级**：LLM失败时自动使用传统模板",
        "📱 **飞书集成**：支持API和Webhook两种发送方式",
        "📈 **历史追踪**：记录所有通知历史，支持效果分析",
        "🎨 **个性化内容**：根据用户特点和偏离原因定制内容",
        "⚡ **实时触发**：支持定时检查和手动触发两种模式"
    ]
    
    for feature in features:
        print(feature)

def main():
    """主函数"""
    print("🚀 通知系统演示程序")
    print("本程序将展示不同类型的通知格式和LLM生成的个性化报告内容")
    
    # 演示个人通知
    print_section_header("个人通知演示")
    
    print_subsection_header("传统模板 - 个人通知")
    print("📱 个人私聊内容:")
    print(demo_personal_notification_traditional())
    
    print_subsection_header("LLM生成 - 个人通知")
    print("🤖 LLM个性化内容:")
    print(demo_personal_notification_llm())
    
    # 演示管理层通知
    print_section_header("管理层通知演示")
    
    print_subsection_header("传统模板 - 管理层通知")
    print("👔 管理层通知内容:")
    print(demo_management_notification_traditional())
    
    print_subsection_header("LLM生成 - 管理层通知")
    print("🤖 LLM管理层内容:")
    print(demo_management_notification_llm())
    
    # 演示详细报告
    print_section_header("详细报告演示")
    
    print_subsection_header("传统详细报告")
    print(demo_detailed_report_traditional())
    
    print_subsection_header("传统简洁报告")
    print(demo_brief_report_traditional())
    
    # 演示系统特色功能
    print_section_header("系统特色功能")
    demo_notification_system_features()
    
    # 总结
    print_section_header("演示总结")
    print("✅ 所有通知格式演示已完成")
    print("\n📋 **通知系统对比总结**:")
    print("\n🔸 **传统模板通知**:")
    print("  • 优点: 结构化、标准化、稳定可靠")
    print("  • 特点: 格式固定、内容通用、快速生成")
    print("\n🔸 **LLM生成通知**:")
    print("  • 优点: 个性化、智能化、内容丰富")
    print("  • 特点: 根据具体情况定制、语言自然、建议具体")
    print("\n🔸 **智能特性**:")
    print("  • 自动降级: LLM失败时使用传统模板")
    print("  • 双重通知: 个人+管理层，确保信息传达")
    print("  • 防重复: 避免频繁打扰")
    print("  • 时间控制: 只在合适时间发送")
    print("\n🎯 **实际应用价值**:")
    print("  • 提升工作效率监控的智能化水平")
    print("  • 增强团队管理的个性化体验")
    print("  • 减少管理层的人工干预成本")
    print("  • 提高员工接受度和改进意愿")

if __name__ == "__main__":
    main()