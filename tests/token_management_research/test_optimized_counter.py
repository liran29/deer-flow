#!/usr/bin/env python3
"""
测试优化后的 Token Counter 性能
"""

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent))

import time
from src.utils.token_manager import TokenManager
from langchain_core.messages import HumanMessage, AIMessage, SystemMessage
import logging

# Configure logging
logging.basicConfig(
    level=logging.WARNING,  # Only show warnings to reduce noise
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

def test_counter_performance():
    """测试优化后的性能"""
    
    print("\n" + "="*80)
    print("⚡ Token Counter 性能测试")
    print("="*80)
    
    token_manager = TokenManager()
    
    # Create test messages
    messages = [
        SystemMessage(content="You are a helpful assistant."),
        HumanMessage(content="Test question " * 100),
        AIMessage(content="Test answer " * 150),
    ]
    
    print(f"📝 测试消息数: {len(messages)}")
    print(f"🤖 测试模型: deepseek-chat")
    
    # Test multiple calls to see caching effect
    print("\n🔄 执行多次 token 管理调用...")
    
    start_time = time.time()
    
    for i in range(10):
        result = token_manager.trim_messages_for_node(
            messages, "deepseek-chat", "planner"
        )
        if i == 0:
            print(f"   第1次: {len(messages)} → {len(result)} 消息")
        elif i == 9:
            print(f"   第10次: {len(messages)} → {len(result)} 消息")
    
    end_time = time.time()
    total_time = end_time - start_time
    
    print(f"\n📊 性能结果:")
    print(f"   总耗时: {total_time:.3f} 秒")
    print(f"   平均每次: {total_time/10:.3f} 秒")
    print(f"   每秒处理: {10/total_time:.1f} 次")
    
    # Test cache effectiveness
    print(f"\n🧠 缓存状态:")
    print(f"   缓存的计数器: {list(token_manager._token_counters.keys())}")
    print(f"   缓存大小: {len(token_manager._token_counters)}")
    
    print("\n" + "="*80)
    print("✅ 性能测试完成!")
    print("💡 现在每个模型的 token counter 只创建一次，后续调用复用缓存")
    print("="*80 + "\n")

if __name__ == "__main__":
    test_counter_performance()