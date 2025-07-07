#!/usr/bin/env python3
"""
实际测试 token 管理系统在真实工作流中的表现
"""

import asyncio
import sys
from pathlib import Path

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent))

from src.workflow import graph, run_agent_workflow_async
from src.config.configuration import Configuration
from src.utils.token_manager import TokenManager
import logging

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

async def test_real_workflow():
    """测试真实的研究工作流"""
    
    print("\n" + "="*80)
    print("🧪 实际测试 Token 管理系统")
    print("="*80 + "\n")
    
    # Test cases with different complexity levels
    test_queries = [
        {
            "name": "简单查询",
            "query": "什么是机器学习？",
            "expected": "应该快速完成，token 使用较少"
        },
        # 暂时只测试第一个简单查询
        # {
        #     "name": "中等复杂查询",
        #     "query": "分析比较 TensorFlow 和 PyTorch 的优缺点，包括性能、易用性、社区支持等方面",
        #     "expected": "需要多轮搜索和分析，token 使用中等"
        # },
        # {
        #     "name": "复杂深度研究",
        #     "query": "深入研究大语言模型的 token 优化技术，包括量化、剪枝、知识蒸馏等方法的原理和实践，以及在不同场景下的应用效果对比",
        #     "expected": "需要大量搜索和分析，测试 token 管理能力"
        # }
    ]
    
    # Initialize token manager for monitoring
    token_manager = TokenManager()
    
    for test_case in test_queries:
        print(f"\n{'='*60}")
        print(f"📋 测试案例: {test_case['name']}")
        print(f"🔍 查询: {test_case['query']}")
        print(f"📊 预期: {test_case['expected']}")
        print(f"{'='*60}\n")
        
        try:
            # Run the workflow
            print("🚀 启动工作流...\n")
            
            # Use the run_agent_workflow_async function
            # Note: This function doesn't return a value, it prints output directly
            await run_agent_workflow_async(
                user_input=test_case['query'],
                debug=False,
                max_plan_iterations=1,  # Reduced for faster testing
                max_step_num=1,         # Further reduced for faster testing
                enable_background_investigation=False  # Disable to speed up
            )
            
            print(f"\n✅ 工作流完成!")
            print(f"💡 Token 管理日志已在上方输出中显示")
            
        except Exception as e:
            print(f"\n❌ 错误: {str(e)}")
            import traceback
            traceback.print_exc()
        
        # Small delay between tests
        await asyncio.sleep(2)
    
    print("\n" + "="*80)
    print("✅ 所有测试完成!")
    print("="*80 + "\n")

def main():
    """主函数"""
    print("\n🔧 当前配置:")
    print(f"   - Token 管理: 已启用")
    print(f"   - 测试模型: deepseek-chat")
    
    # Run async workflow tests
    asyncio.run(test_real_workflow())

if __name__ == "__main__":
    main()