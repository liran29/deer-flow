#!/usr/bin/env python3
"""
快速测试 token 管理在实际节点中的应用
"""

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent))

from src.graph.nodes import planner_node
from src.graph.types import State
from langchain_core.runnables import RunnableConfig
from langchain_core.messages import HumanMessage, AIMessage
import logging

# Configure logging to see token management logs
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

def test_planner_token_management():
    """测试 planner 节点的 token 管理"""
    
    print("\n" + "="*80)
    print("🧪 快速测试 Planner 节点的 Token 管理")
    print("="*80 + "\n")
    
    # Create a state with many messages to trigger token management
    messages = [
        HumanMessage(content="什么是机器学习？"),
    ]
    
    # Add many historical messages to exceed token limit
    for i in range(200):  # Increased to ensure we exceed the limit
        messages.append(AIMessage(content=f"这是历史消息 {i}: " + "x" * 1000))  # Longer messages
        messages.append(HumanMessage(content=f"继续讨论 {i}: " + "y" * 500))
    
    state = State(
        messages=messages,
        next="planner",
        plan=[],
        plan_step_results={},
        plan_steps_taken=0
    )
    
    config = RunnableConfig()
    
    print(f"📊 输入消息数量: {len(messages)}")
    print("🚀 调用 planner_node...\n")
    
    try:
        # This should trigger token management logs
        result = planner_node(state, config)
        print(f"\n✅ Planner 节点执行成功!")
        print(f"📋 生成的计划步骤数: {len(result.get('plan', []))}")
    except Exception as e:
        print(f"\n❌ 错误: {str(e)}")
        import traceback
        traceback.print_exc()
    
    print("\n" + "="*80)
    print("💡 请查看上方日志中的 'Token Management' 输出")
    print("="*80 + "\n")

if __name__ == "__main__":
    test_planner_token_management()