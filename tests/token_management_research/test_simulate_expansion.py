#!/usr/bin/env python3
"""
模拟真实的 Token 扩展场景
"""

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent))

from src.utils.token_manager import TokenManager
from langchain_core.messages import HumanMessage, AIMessage, SystemMessage
from langchain_core.messages.utils import trim_messages
import logging

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

def create_expansion_scenario():
    """创建一个可能导致 token 扩展的场景"""
    
    # 模拟 reporter 节点收到的消息格式
    messages = [
        SystemMessage(content="Generate comprehensive research report."),
        HumanMessage(content="Research Topic: Framework Comparison"),
        AIMessage(content="I'll analyze the frameworks based on collected data."),
        HumanMessage(content="""
# Existing Research Findings

## Finding 1: Performance Data
TensorFlow: 95% efficiency in distributed training
PyTorch: 87% efficiency, better debugging
JAX: 99% efficiency, limited ecosystem

## Finding 2: Architecture Analysis  
- TensorFlow: Static graph optimization
- PyTorch: Dynamic computation graphs
- JAX: Functional programming approach

## Finding 3: Community Support
TensorFlow: 180k GitHub stars
PyTorch: 150k GitHub stars  
JAX: 25k GitHub stars
        """),
        AIMessage(content="Based on this data, I need to process observations."),
        HumanMessage(content="Include performance benchmarks and user experience analysis.")
    ]
    
    return messages

def test_manual_token_expansion():
    """手动测试可能导致扩展的操作"""
    
    print("\n" + "="*80)
    print("🧪 手动模拟 Token 扩展测试")
    print("="*80)
    
    messages = create_expansion_scenario()
    token_manager = TokenManager()
    
    print(f"📝 原始消息数: {len(messages)}")
    
    # 1. 首先计算原始 token 数
    from src.utils.token_counter import TokenCounterFactory
    counter = TokenCounterFactory.create_counter("deepseek-chat")
    
    # Convert to dict format for counting
    orig_dicts = []
    for msg in messages:
        if hasattr(msg, '__class__'):
            msg_type = msg.__class__.__name__
            if msg_type == 'SystemMessage':
                role = 'system'
            elif msg_type == 'HumanMessage':
                role = 'user'
            elif msg_type == 'AIMessage':
                role = 'assistant'
            else:
                role = 'user'
        
        orig_dicts.append({
            'role': role,
            'content': str(msg.content)
        })
    
    orig_tokens = counter.count_messages_tokens(orig_dicts)
    print(f"🔢 原始 tokens: {orig_tokens:,}")
    
    # 2. 使用 trim_messages 处理
    print("\n🔄 使用 trim_messages 处理...")
    
    def test_token_counter(messages_list):
        # Same conversion logic as in TokenManager
        message_dicts = []
        for msg in messages_list:
            if hasattr(msg, 'content'):
                if hasattr(msg, '__class__'):
                    msg_type = msg.__class__.__name__
                    if msg_type == 'SystemMessage':
                        role = 'system'
                    elif msg_type == 'HumanMessage':
                        role = 'user' 
                    elif msg_type == 'AIMessage':
                        role = 'assistant'
                    else:
                        role = 'user'
                else:
                    role = 'user'
                
                message_dicts.append({
                    'role': role,
                    'content': str(msg.content)
                })
        
        return counter.count_messages_tokens(message_dicts)
    
    # Apply trim_messages directly
    trimmed = trim_messages(
        messages=messages,
        max_tokens=12000,  # reporter limit
        strategy="last",
        token_counter=test_token_counter
    )
    
    # Count trimmed tokens
    trimmed_tokens = test_token_counter(trimmed)
    
    print(f"📊 处理结果:")
    print(f"   消息数: {len(messages)} → {len(trimmed)}")
    print(f"   Tokens: {orig_tokens:,} → {trimmed_tokens:,}")
    print(f"   变化: {((trimmed_tokens - orig_tokens) / orig_tokens * 100):+.1f}%")
    
    # 3. 现在用 TokenManager 处理看是否有差异
    print(f"\n🔄 使用 TokenManager 处理...")
    
    result = token_manager.trim_messages_for_node(
        messages, "deepseek-chat", "reporter"
    )
    
    print(f"🎯 TokenManager 结果: {len(messages)} → {len(result)} 消息")
    
    # 4. 检查消息内容是否有变化
    print(f"\n🔍 内容分析:")
    
    # 比较第一条和最后一条消息
    if messages and result:
        orig_first_len = len(str(messages[0].content))
        trim_first_len = len(str(result[0].content))
        print(f"   第一条消息长度: {orig_first_len} → {trim_first_len}")
        
        if len(messages) > 1 and len(result) > 1:
            orig_last_len = len(str(messages[-1].content))
            trim_last_len = len(str(result[-1].content))
            print(f"   最后一条消息长度: {orig_last_len} → {trim_last_len}")
    
    # 5. 检查是否有新的内容添加
    orig_content = " ".join(str(msg.content) for msg in messages)
    trim_content = " ".join(str(msg.content) for msg in result)
    
    print(f"   总内容长度: {len(orig_content)} → {len(trim_content)}")
    
    if len(trim_content) > len(orig_content):
        print("⚠️  检测到内容增加，可能的原因:")
        
        # 检查是否有新的格式化
        if "##" in trim_content and "##" not in orig_content:
            print("     - 添加了 Markdown 标题格式")
        
        if "<finding>" in trim_content and "<finding>" not in orig_content:
            print("     - 添加了结构化标签")
            
        if "observation" in trim_content.lower() and "observation" not in orig_content.lower():
            print("     - 添加了观察数据标识")

def main():
    """主函数"""
    print("\n🔬 Token 扩展深度分析实验")
    print("=" * 80)
    print("目标: 理解并重现 token 扩展现象")
    
    test_manual_token_expansion()
    
    print("\n" + "="*80)
    print("📋 实验总结")
    print("="*80)
    print("✅ 通过直接对比 trim_messages 的输入输出")
    print("✅ 分析了可能导致扩展的具体原因")
    print("✅ 增强了监控和诊断能力")
    print("💡 下次在生产环境中遇到扩展时，将获得详细的分析报告")
    print("="*80 + "\n")

if __name__ == "__main__":
    main()