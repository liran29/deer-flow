#!/usr/bin/env python3
"""
测试 Token 扩展分析功能
"""

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent))

from src.utils.token_manager import TokenManager
from langchain_core.messages import HumanMessage, AIMessage, SystemMessage
import logging

# Configure logging to see detailed analysis
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

def create_test_scenarios():
    """创建不同的测试场景来触发 token 扩展"""
    
    scenarios = []
    
    # Scenario 1: Simple messages (baseline)
    scenarios.append({
        "name": "基础场景",
        "messages": [
            SystemMessage(content="You are helpful."),
            HumanMessage(content="Hi"),
            AIMessage(content="Hello!")
        ]
    })
    
    # Scenario 2: Messages with observations (like reporter node)
    scenarios.append({
        "name": "包含观察数据",
        "messages": [
            SystemMessage(content="Generate report based on findings."),
            HumanMessage(content="Research findings:\n<finding>\nTensorFlow performance data...\n</finding>"),
            AIMessage(content="Based on the observations, here is the analysis...")
        ]
    })
    
    # Scenario 3: Messages with metadata
    messages_with_metadata = [
        SystemMessage(content="System prompt"),
        HumanMessage(content="Query with additional info")
    ]
    # Add metadata to simulate real workflow
    messages_with_metadata[1].additional_kwargs = {"source": "user", "timestamp": "2025-01-01"}
    messages_with_metadata[1].response_metadata = {"processing_time": 0.5}
    
    scenarios.append({
        "name": "包含元数据",
        "messages": messages_with_metadata
    })
    
    # Scenario 4: Structured content
    scenarios.append({
        "name": "结构化内容",
        "messages": [
            SystemMessage(content="Process structured data"),
            HumanMessage(content='{"task": "analysis", "data": {"frameworks": ["TensorFlow", "PyTorch", "JAX"]}}'),
            AIMessage(content="## Analysis Results\n\n**Key Findings:**\n- Framework comparison\n- Performance metrics")
        ]
    })
    
    return scenarios

def test_expansion_analysis():
    """测试扩展分析功能"""
    
    print("\n" + "="*80)
    print("🔍 Token 扩展分析测试")
    print("="*80)
    
    token_manager = TokenManager()
    scenarios = create_test_scenarios()
    
    for i, scenario in enumerate(scenarios, 1):
        print(f"\n📋 测试场景 {i}: {scenario['name']}")
        print("-" * 60)
        
        messages = scenario['messages']
        
        # Test with reporter node (which showed expansion in logs)
        try:
            result = token_manager.trim_messages_for_node(
                messages, "deepseek-chat", "reporter"
            )
            
            print(f"✅ 处理完成: {len(messages)} → {len(result)} 消息")
            
        except Exception as e:
            print(f"❌ 错误: {e}")

def simulate_reporter_expansion():
    """专门模拟 reporter 节点的 token 扩展情况"""
    
    print("\n" + "="*80)
    print("🎯 模拟 Reporter 节点扩展场景")
    print("="*80)
    
    token_manager = TokenManager()
    
    # Create a scenario similar to what might cause expansion in reporter
    messages = [
        SystemMessage(content="Generate a comprehensive research report based on the collected findings."),
        HumanMessage(content="""
# Research Findings Summary

## Finding 1: Performance Benchmarks
TensorFlow shows superior performance in distributed training scenarios.

## Finding 2: Architecture Analysis  
PyTorch provides more flexible distributed training APIs.

## Finding 3: Ecosystem Comparison
JAX demonstrates excellent performance but has limited ecosystem.
        """),
        AIMessage(content="I'll analyze these findings to create a comprehensive report."),
        HumanMessage(content="Please include detailed performance metrics and recommendations."),
        AIMessage(content="Based on the research findings, I'll structure the report as follows..."),
        HumanMessage(content="Also compare the frameworks' ease of use and learning curves.")
    ]
    
    print(f"📝 输入消息数: {len(messages)}")
    print("🔄 执行 token 管理...")
    
    # This should trigger detailed expansion analysis if it occurs
    result = token_manager.trim_messages_for_node(
        messages, "deepseek-chat", "reporter"
    )
    
    print(f"✅ 输出消息数: {len(result)}")
    print("\n💡 检查上方日志中的详细分析信息")

def main():
    """主函数"""
    print("\n🧪 Token 扩展深度分析系统")
    print("=" * 80)
    print("这个测试将帮助我们理解为什么会出现 token 扩展")
    print("新增的分析功能将提供详细的诊断信息")
    
    test_expansion_analysis()
    simulate_reporter_expansion()
    
    print("\n" + "="*80)
    print("📊 分析总结")
    print("="*80)
    print("✅ 新增了详细的 token 扩展分析功能")
    print("✅ 能够检测多种可能的扩展原因:")
    print("   - 消息格式转换")
    print("   - 元数据添加")
    print("   - 结构化数据处理")
    print("   - 观察数据整合")
    print("   - Markdown 格式化")
    print("💡 下次出现扩展时，日志将提供详细的诊断信息")
    print("="*80 + "\n")

if __name__ == "__main__":
    main()