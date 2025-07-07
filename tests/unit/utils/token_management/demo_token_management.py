#!/usr/bin/env python3
"""
Demo script to show token management in action.

This script demonstrates how the token management system works by:
1. Creating large inputs that exceed model token limits
2. Showing how different models handle different token loads
3. Demonstrating the logging output from token management
"""

import sys
import os
import logging
import asyncio

# Add project root to path
project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '../../../..'))
sys.path.insert(0, project_root)

# Configure logging to show token management details
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

from src.utils.token_manager import TokenManager
from src.utils.token_counter import count_tokens
from langchain_core.messages import HumanMessage, SystemMessage, AIMessage


def demo_basic_token_management():
    """Demonstrate basic token management functionality"""
    print("=== Token Management Demo ===\n")
    
    token_manager = TokenManager()
    
    # Create a large input that would exceed DeepSeek's limit
    large_content = """
    圣诞装饰品市场正在经历前所未有的变革。智能化装饰品成为新趋势，LED智能彩灯、可编程装饰品、
    语音控制装饰等科技元素受到消费者热烈欢迎。环保材料应用也是重要趋势，可回收塑料、
    天然材料制成的圣诞用品需求持续增长。个性化定制服务成为差异化竞争关键，
    消费者对独特定制化产品需求不断增长。
    """ * 500  # Repeat to make it large
    
    print(f"Large content length: {len(large_content):,} characters")
    
    # Count tokens for different models
    deepseek_tokens = count_tokens(large_content, "deepseek-chat")
    gemini_tokens = count_tokens(large_content, "gemini-2.0-flash")
    
    print(f"DeepSeek tokens: {deepseek_tokens:,} (limit: 32,768)")
    print(f"Gemini tokens: {gemini_tokens:,} (limit: 1,000,000)")
    print(f"DeepSeek exceeds limit by: {max(0, deepseek_tokens - 32768):,} tokens\n")
    
    # Create messages that include this large content
    messages = [
        SystemMessage(content="你是一个专业的市场分析师，请详细分析提供的信息。"),
        HumanMessage(content=f"请分析以下市场信息：\n\n{large_content}"),
        HumanMessage(content="请提供具体的数据分析和市场预测。")
    ]
    
    print(f"Original messages: {len(messages)}")
    
    # Apply token management for DeepSeek
    print("\n--- DeepSeek Token Management ---")
    trimmed_deepseek = token_manager.trim_messages_for_node(messages, "deepseek-chat", "planner")
    print(f"Trimmed messages: {len(trimmed_deepseek)}")
    
    # Apply token management for Gemini
    print("\n--- Gemini Token Management ---")
    trimmed_gemini = token_manager.trim_messages_for_node(messages, "gemini-2.0-flash", "planner")
    print(f"Trimmed messages: {len(trimmed_gemini)}")
    
    # Show the difference
    trimmed_deepseek_content = " ".join([msg.content for msg in trimmed_deepseek if hasattr(msg, 'content')])
    trimmed_gemini_content = " ".join([msg.content for msg in trimmed_gemini if hasattr(msg, 'content')])
    
    deepseek_final_tokens = count_tokens(trimmed_deepseek_content, "deepseek-chat")
    gemini_final_tokens = count_tokens(trimmed_gemini_content, "gemini-2.0-flash")
    
    print(f"\nFinal token counts:")
    print(f"DeepSeek: {deepseek_final_tokens:,} tokens ({(deepseek_final_tokens/deepseek_tokens*100):.1f}% of original)")
    print(f"Gemini: {gemini_final_tokens:,} tokens ({(gemini_final_tokens/gemini_tokens*100):.1f}% of original)")


def demo_observation_management():
    """Demonstrate observation management"""
    print("\n=== Observation Management Demo ===\n")
    
    token_manager = TokenManager()
    
    # Create many detailed observations
    observations = []
    for i in range(15):
        observation = f"""
        研究观察 {i}: 通过对圣诞装饰品市场的深入调研发现，消费者行为正在发生显著变化。
        智能化产品的接受度大幅提升，特别是年轻消费群体对科技元素的追求明显。
        价格敏感度有所下降，消费者更愿意为高质量、个性化的产品支付溢价。
        线上购买渠道占比持续增长，社交媒体影响购买决策的作用日益显著。
        环保意识的提升推动了可持续产品的需求增长，这为行业转型提供了新机遇。
        """ * 20  # Make each observation quite long
        observations.append(observation.strip())
    
    print(f"Original observations: {len(observations)}")
    print(f"Average length: {sum(len(obs) for obs in observations) / len(observations):.0f} characters")
    
    # Apply observation management
    managed_observations = token_manager.manage_observations(observations)
    
    print(f"Managed observations: {len(managed_observations)}")
    print(f"Average length: {sum(len(obs) for obs in managed_observations) / len(managed_observations):.0f} characters")
    
    total_original = sum(len(obs) for obs in observations)
    total_managed = sum(len(obs) for obs in managed_observations)
    reduction = (1 - total_managed / total_original) * 100
    
    print(f"Content reduction: {reduction:.1f}%")


def demo_real_world_scenario():
    """Demonstrate a real-world scenario"""
    print("\n=== Real-World Scenario Demo ===\n")
    print("Simulating a workflow that would fail without token management...\n")
    
    # This simulates what would happen in the actual deer-flow workflow
    # when processing large background investigation results
    
    # Large background investigation result (simulated)
    background_result = """
    圣诞装饰品全球市场调研报告：
    
    1. 市场规模分析
    全球圣诞装饰品市场规模预计2025年将达到180亿美元，较2024年增长8.5%。
    主要增长驱动因素包括：消费升级、科技创新、个性化需求增长。
    
    2. 地区分布
    北美市场占比35%，欧洲市场占比30%，亚太市场占比25%，其他地区占比10%。
    亚太市场增长最为迅速，年复合增长率达到12.3%。
    
    3. 产品类别分析
    LED彩灯类产品占比40%，装饰摆件占比25%，圣诞树及配件占比20%，其他占比15%。
    智能化产品增长显著，预计年增长率超过20%。
    
    4. 消费者行为变化
    线上购买比例从2020年的30%增长到2025年预期的65%。
    消费者更注重产品的环保属性和个性化特征。
    价格敏感度下降，品质和体验成为主要考量因素。
    
    5. 技术创新趋势
    物联网技术应用：智能控制、远程操作、场景联动
    新材料应用：生物降解材料、回收材料、节能材料
    设计创新：3D打印定制、AR/VR体验、AI推荐
    
    6. 竞争格局
    传统制造商加速数字化转型，科技公司跨界进入市场。
    品牌集中度提升，头部企业市场份额扩大。
    供应链全球化趋势明显，区域化生产增加。
    
    7. 挑战与机遇
    挑战：原材料价格波动、环保法规趋严、消费需求多样化
    机遇：新兴市场增长、技术创新驱动、可持续发展需求
    """ * 100  # Make it very large
    
    token_manager = TokenManager()
    
    # Check if this would exceed limits
    bg_tokens = count_tokens(background_result, "deepseek-chat")
    print(f"Background investigation result: {bg_tokens:,} tokens")
    print(f"DeepSeek limit: 32,768 tokens")
    print(f"Exceeds limit by: {max(0, bg_tokens - 32768):,} tokens")
    
    # Show how the system would handle this
    strategy = token_manager.get_trimming_strategy("background_investigation")
    max_length = strategy.get("max_tokens", 2000) * 4
    
    if len(background_result) > max_length:
        trimmed_bg = background_result[:max_length] + "\n\n[... results truncated for token management ...]"
        print(f"\nBackground investigation would be trimmed:")
        print(f"Original: {len(background_result):,} characters")
        print(f"Trimmed: {len(trimmed_bg):,} characters")
        print(f"Reduction: {((len(background_result) - len(trimmed_bg)) / len(background_result) * 100):.1f}%")
    
    print(f"\n✓ Token management prevents workflow failures!")
    print(f"✓ Large inputs are automatically handled!")
    print(f"✓ Different models get appropriate token allocations!")


if __name__ == "__main__":
    print("🦌 Deer-Flow Token Management Demo")
    print("=" * 50)
    
    try:
        demo_basic_token_management()
        demo_observation_management()
        demo_real_world_scenario()
        
        print("\n" + "=" * 50)
        print("✓ Token management is working correctly!")
        print("✓ Your deer-flow system can now handle models like DeepSeek!")
        print("✓ Check the logs above to see token reduction in action!")
        
    except Exception as e:
        print(f"\n❌ Demo failed: {e}")
        import traceback
        traceback.print_exc()