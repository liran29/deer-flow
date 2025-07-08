#!/usr/bin/env python3
"""
诊断 Token 超限问题
分析为什么 researcher 节点会超出 120K tokens
"""

import json
from pathlib import Path
from src.utils.token_manager import TokenManager
from src.utils.token_counter import TokenCounterFactory
from langchain_core.messages import HumanMessage, SystemMessage, AIMessage
import asyncio

def analyze_token_issue():
    """分析 token 超限问题"""
    print("🔍 诊断 Token 超限问题")
    print("="*60)
    
    # 1. 检查配置
    token_manager = TokenManager()
    config = token_manager.token_management
    
    print("\n📋 当前配置:")
    print(f"- Token 管理启用: {config.get('enabled', False)}")
    print(f"- DeepSeek 模型限制: {config.get('model_limits', {}).get('deepseek-chat', 'N/A')} tokens")
    print(f"- Researcher 节点配置:")
    researcher_config = config.get('trimming_strategies', {}).get('researcher', {})
    print(f"  - 最大 tokens: {researcher_config.get('max_tokens', 'N/A')}")
    print(f"  - 策略: {researcher_config.get('strategy', 'N/A')}")
    print(f"  - 输出预留: {researcher_config.get('reserve_for_output', 0)}")
    
    # 2. 模拟问题场景
    print("\n🧪 模拟问题场景:")
    
    # 创建大量消息模拟实际情况
    messages = []
    
    # 系统消息
    messages.append(SystemMessage(content="You are a helpful research assistant. " * 100))
    
    # 用户查询
    messages.append(HumanMessage(content="深入分析大语言模型在医疗、金融、教育三个领域的应用现状、技术挑战和未来发展趋势"))
    
    # 模拟多轮对话和工具调用结果
    for i in range(50):  # 50轮对话
        # 工具调用结果（搜索结果通常很长）
        tool_result = f"搜索结果 {i+1}:\n" + "这是一个非常长的搜索结果内容。" * 500
        messages.append(AIMessage(content=f"让我搜索一下相关信息..."))
        messages.append(HumanMessage(content=tool_result))
    
    # 计算原始 token 数
    counter = TokenCounterFactory.create_counter("deepseek-chat")
    # 转换为字典格式
    message_dicts = []
    for msg in messages:
        if isinstance(msg, SystemMessage):
            message_dicts.append({"role": "system", "content": msg.content})
        elif isinstance(msg, HumanMessage):
            message_dicts.append({"role": "user", "content": msg.content})
        elif isinstance(msg, AIMessage):
            message_dicts.append({"role": "assistant", "content": msg.content})
    original_tokens = counter.count_messages_tokens(message_dicts)
    
    print(f"- 原始消息数: {len(messages)}")
    print(f"- 原始 token 数: {original_tokens:,}")
    
    # 3. 应用 token 管理
    print("\n🔧 应用 Token 管理:")
    try:
        trimmed_messages = token_manager.trim_messages_for_node(
            messages, "deepseek-chat", "researcher"
        )
        
        # 计算修剪后的 token 数
        trimmed_dicts = []
        for msg in trimmed_messages:
            if isinstance(msg, SystemMessage):
                trimmed_dicts.append({"role": "system", "content": msg.content})
            elif isinstance(msg, HumanMessage):
                trimmed_dicts.append({"role": "user", "content": msg.content})
            elif isinstance(msg, AIMessage):
                trimmed_dicts.append({"role": "assistant", "content": msg.content})
        trimmed_tokens = counter.count_messages_tokens(trimmed_dicts)
        
        print(f"- 修剪后消息数: {len(trimmed_messages)}")
        print(f"- 修剪后 token 数: {trimmed_tokens:,}")
        print(f"- 减少: {original_tokens - trimmed_tokens:,} tokens ({(original_tokens - trimmed_tokens) / original_tokens * 100:.1f}%)")
        
        # 分析为什么还是超限
        model_limit = token_manager.get_model_limit("deepseek-chat")
        if trimmed_tokens > model_limit:
            print(f"\n⚠️ 问题: 即使修剪后仍然超出模型限制!")
            print(f"- 模型限制: {model_limit:,} tokens")
            print(f"- 实际需要: {trimmed_tokens:,} tokens")
            print(f"- 超出: {trimmed_tokens - model_limit:,} tokens")
            
            # 分析消息组成
            print("\n📊 消息组成分析:")
            message_types = {}
            for msg in trimmed_messages:
                msg_type = type(msg).__name__
                if msg_type not in message_types:
                    message_types[msg_type] = {"count": 0, "tokens": 0}
                message_types[msg_type]["count"] += 1
                if isinstance(msg, SystemMessage):
                    msg_dict = {"role": "system", "content": msg.content}
                elif isinstance(msg, HumanMessage):
                    msg_dict = {"role": "user", "content": msg.content}
                elif isinstance(msg, AIMessage):
                    msg_dict = {"role": "assistant", "content": msg.content}
                message_types[msg_type]["tokens"] += counter.count_messages_tokens([msg_dict])
            
            for msg_type, stats in message_types.items():
                print(f"- {msg_type}: {stats['count']} 条, {stats['tokens']:,} tokens")
        
    except Exception as e:
        print(f"❌ Token 管理失败: {e}")
        import traceback
        traceback.print_exc()
    
    # 4. 建议解决方案
    print("\n💡 建议解决方案:")
    print("1. 减少 researcher 节点的 max_tokens 配置")
    print("2. 增加更激进的修剪策略")
    print("3. 限制工具调用结果的长度")
    print("4. 使用摘要而不是完整的搜索结果")
    print("5. 考虑分阶段处理，避免累积过多上下文")

def check_actual_logs():
    """检查实际的日志文件"""
    print("\n📁 检查实际日志:")
    log_dir = Path("logs/token_comparisons")
    if log_dir.exists():
        json_files = list(log_dir.glob("*.json"))
        print(f"找到 {len(json_files)} 个比较文件")
        
        # 查找最新的 researcher 相关文件
        researcher_files = [f for f in json_files if "researcher" in f.name]
        if researcher_files:
            latest = max(researcher_files, key=lambda f: f.stat().st_mtime)
            print(f"\n最新的 researcher 比较文件: {latest.name}")
            
            with open(latest, 'r') as f:
                data = json.load(f)
                print(f"- 原始消息数: {data.get('original_message_count', 'N/A')}")
                print(f"- 原始 tokens: {data.get('original_tokens', 'N/A'):,}")
                print(f"- 修剪后消息数: {data.get('trimmed_message_count', 'N/A')}")
                print(f"- 修剪后 tokens: {data.get('trimmed_tokens', 'N/A'):,}")

if __name__ == "__main__":
    analyze_token_issue()
    check_actual_logs()