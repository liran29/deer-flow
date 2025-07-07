#!/usr/bin/env python3
"""
简单测试 token 管理系统
"""

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent))

from src.config.configuration import Configuration
from src.utils.token_manager import TokenManager
from langchain_core.messages import HumanMessage, AIMessage, SystemMessage
import logging

# Configure logging to see token management logs
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

def test_token_management():
    """测试 token 管理功能"""
    
    print("\n" + "="*80)
    print("🧪 Token 管理系统简单测试")
    print("="*80 + "\n")
    
    # Initialize token manager
    token_manager = TokenManager()
    
    # Check configuration
    print(f"✅ Token 管理系统已初始化")
    print(f"📊 测试模型: deepseek-chat (32K tokens)")
    
    # Create test messages
    messages = [
        SystemMessage(content="You are a helpful AI assistant."),
        HumanMessage(content="Hello, I need help with a complex research task."),
        AIMessage(content="I'll help you with your research. What would you like to know?"),
    ]
    
    # Add many messages to simulate a long conversation
    print("\n🔄 生成大量测试消息...")
    for i in range(100):
        messages.append(HumanMessage(content=f"Question {i}: " + "x" * 500))
        messages.append(AIMessage(content=f"Answer {i}: " + "y" * 1000))
    
    # Test trimming for different nodes
    test_cases = [
        ("planner", "deepseek-chat"),
        ("reporter", "deepseek-chat"),
        ("background_investigation", "deepseek-chat"),
    ]
    
    print(f"\n📋 原始消息数量: {len(messages)}")
    
    for node_name, model_name in test_cases:
        print(f"\n{'='*60}")
        print(f"🔍 测试节点: {node_name}")
        print(f"🤖 模型: {model_name}")
        print(f"{'='*60}")
        
        # Apply token management
        trimmed = token_manager.trim_messages_for_node(
            messages, model_name, node_name
        )
        
        print(f"✅ 消息裁剪完成!")
        print(f"   - 裁剪后消息数: {len(trimmed)}")
        
        # Check if extreme trimming happened
        if len(trimmed) == 0:
            print(f"⚠️  警告: 所有消息都被裁剪了!")
        elif len(trimmed) == 1:
            print(f"⚠️  注意: 只保留了系统消息")
        
    print("\n" + "="*80)
    print("✅ 测试完成! 检查上面的日志了解详细的 token 使用情况")
    print("="*80 + "\n")

if __name__ == "__main__":
    test_token_management()