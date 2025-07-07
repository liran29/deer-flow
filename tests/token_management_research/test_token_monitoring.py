#!/usr/bin/env python3
"""
测试改进后的 Token 管理监控
"""

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent))

from src.utils.token_manager import TokenManager
from langchain_core.messages import HumanMessage, AIMessage, SystemMessage
import logging

# Configure logging to see all token management activities
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

def test_improved_monitoring():
    """测试改进后的 Token 管理监控"""
    
    print("\n" + "="*80)
    print("🔧 测试改进后的 Token 管理监控")
    print("="*80 + "\n")
    
    token_manager = TokenManager()
    
    # Test Case 1: Normal scenario (should show NO_TRIM)
    print("📋 测试案例 1: 正常场景 (少量消息)")
    print("-" * 50)
    
    small_messages = [
        SystemMessage(content="You are a helpful assistant."),
        HumanMessage(content="简单问题"),
        AIMessage(content="简单回答")
    ]
    
    result1 = token_manager.trim_messages_for_node(
        small_messages, "deepseek-chat", "planner"
    )
    print(f"结果: {len(small_messages)} → {len(result1)} 条消息")
    
    # Test Case 2: Large scenario (should show TRIMMED)
    print("\n📋 测试案例 2: 大量消息场景 (应该裁剪)")
    print("-" * 50)
    
    large_messages = [SystemMessage(content="You are a helpful assistant.")]
    
    # Add many large messages
    for i in range(150):
        large_messages.append(HumanMessage(content=f"大量问题 {i}: " + "内容" * 200))
        large_messages.append(AIMessage(content=f"大量回答 {i}: " + "详细回答" * 300))
    
    result2 = token_manager.trim_messages_for_node(
        large_messages, "deepseek-chat", "planner"
    )
    print(f"结果: {len(large_messages)} → {len(result2)} 条消息")
    
    # Test Case 3: Different nodes
    print("\n📋 测试案例 3: 不同节点的配置")
    print("-" * 50)
    
    test_nodes = ["planner", "reporter", "researcher", "background_investigation"]
    
    for node in test_nodes:
        print(f"\n🔍 测试节点: {node}")
        result = token_manager.trim_messages_for_node(
            large_messages[:50], "deepseek-chat", node  # Use subset for different effects
        )
        strategy = token_manager.get_trimming_strategy(node)
        print(f"   配置的 max_tokens: {strategy.get('max_tokens', 'N/A')}")
        print(f"   实际结果: {len(large_messages[:50])} → {len(result)} 条消息")
    
    # Test Case 4: Model limits
    print("\n📋 测试案例 4: 不同模型限制")
    print("-" * 50)
    
    test_models = ["deepseek-chat", "gemini-2.0-flash", "gpt-4"]
    
    for model in test_models:
        limit = token_manager.get_model_limit(model)
        print(f"🤖 {model}: {limit:,} tokens")
        
        result = token_manager.trim_messages_for_node(
            large_messages[:30], model, "planner"
        )
        print(f"   处理结果: {len(large_messages[:30])} → {len(result)} 条消息")
    
    print("\n" + "="*80)
    print("✅ Token 管理监控测试完成!")
    print("🔍 请检查上方的详细监控日志")
    print("="*80 + "\n")

if __name__ == "__main__":
    test_improved_monitoring()