#!/usr/bin/env python3
"""
测试带有大量历史消息的工作流
"""

import asyncio
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))

from src.graph import build_graph
from src.graph.types import State
from langchain_core.messages import HumanMessage, AIMessage
import logging

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

async def test_workflow_with_history():
    """测试带有大量历史消息的工作流"""
    
    print("\n" + "="*80)
    print("🧪 测试带历史消息的 Token 管理")
    print("="*80 + "\n")
    
    # Build graph
    graph = build_graph()
    
    # Create initial state with many messages
    messages = []
    
    # Add many historical messages to trigger token management
    print("📝 构建大量历史消息...")
    for i in range(100):
        messages.append(HumanMessage(content=f"历史问题 {i}: " + "这是一个很长的问题" * 50))
        messages.append(AIMessage(content=f"历史回答 {i}: " + "这是一个很长的回答" * 100))
    
    # Add the actual query
    messages.append(HumanMessage(content="什么是机器学习？"))
    
    print(f"📊 消息总数: {len(messages)} 条")
    print(f"💾 估计 tokens: ~{sum(len(msg.content) for msg in messages) // 4:,}")
    
    initial_state = {
        "messages": messages,
        "next": "coordinator",
        "plan": [],
        "plan_step_results": {},
        "plan_steps_taken": 0,
    }
    
    config = {
        "configurable": {
            "locale": "zh-CN",
            "researcher": {
                "llm_type": "basic",
                "max_concurrent_searches": 3,
                "search_engines": ["tavily", "crawl"],
                "extra_tools": {
                    "add_to_agents": ["researcher"],
                }
            }
        },
        "recursion_limit": 50,
    }
    
    print("\n🚀 启动工作流...\n")
    print("💡 注意观察 Token Management 日志\n")
    
    try:
        # Run the workflow
        async for s in graph.astream(
            input=initial_state, 
            config=config, 
            stream_mode="values"
        ):
            # Only print key messages
            if isinstance(s, dict) and "messages" in s:
                last_msg = s["messages"][-1] if s["messages"] else None
                if last_msg and hasattr(last_msg, 'name'):
                    print(f"✓ {last_msg.name} 节点已执行")
                    
        print("\n✅ 工作流完成!")
        
    except Exception as e:
        print(f"\n❌ 错误: {str(e)}")
        import traceback
        traceback.print_exc()
    
    print("\n" + "="*80)
    print("💡 检查上方日志中的 Token Management 输出")
    print("="*80 + "\n")

async def main():
    """主函数"""
    await test_workflow_with_history()

if __name__ == "__main__":
    asyncio.run(main())