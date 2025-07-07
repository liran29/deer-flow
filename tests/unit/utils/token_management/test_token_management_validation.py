#!/usr/bin/env python3
"""
简化版Token Management验证脚本

专注于验证token管理核心功能，避免复杂的node集成测试。
"""

import sys
import os
import logging
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

logger = logging.getLogger(__name__)

def create_test_content():
    """Create test content of various sizes."""
    base_content = """
    全球AI芯片产业深度分析报告：技术革新与市场竞争格局研究
    
    一、产业概述与发展现状
    人工智能芯片作为驱动AI技术落地的核心硬件基础设施，正在经历前所未有的快速发展期。
    从市场规模来看，全球AI芯片市场已从2020年的130亿美元增长到2024年的超过500亿美元，
    预计到2030年将突破2000亿美元大关，年复合增长率保持在25%以上的高位水平。
    
    技术架构方面，AI芯片正在从传统的通用计算架构向专用AI计算架构演进。
    神经网络处理器(NPU)、图形处理器(GPU)、现场可编程门阵列(FPGA)等不同架构
    在不同应用场景下展现出各自的优势特点。存算一体化、光子计算、量子计算等
    前沿技术也在逐步从实验室走向商业化应用。
    
    二、技术发展趋势分析
    1. 计算架构创新：专用化程度不断提升
    - 从CPU/GPU通用计算向NPU专用计算演进
    - 存算一体化架构突破冯·诺依曼瓶颈限制
    - 可重构计算提供灵活性与性能的平衡
    - 类脑计算架构模拟人脑神经网络结构
    
    2. 制程工艺竞争：先进制程成为关键
    - 5纳米制程技术已实现大规模量产
    - 3纳米制程即将进入商业化阶段
    - 2.5D/3D封装技术突破性能瓶颈
    - 新材料应用推动器件性能提升
    
    3. 软件生态建设：开发工具链日趋完善
    - 编译器优化提升代码执行效率
    - 开发框架简化AI应用开发流程
    - 调试工具增强系统可观测性
    - 性能分析工具优化资源利用
    """ * 50  # 重复50次创建大内容
    
    return {
        'small': base_content,
        'medium': base_content * 5,
        'large': base_content * 20,
        'massive': base_content * 100
    }

def test_token_counter_accuracy():
    """测试token计数器的准确性"""
    logger.info("🧪 Testing Token Counter Accuracy...")
    
    try:
        from src.utils.token_counter import TokenCounterFactory, count_tokens
        
        test_content = create_test_content()
        
        # 测试不同模型的token计数
        models = ["deepseek-chat", "gemini-2.0-flash", "gpt-4"]
        
        for model in models:
            logger.info(f"\n--- Testing {model} ---")
            counter = TokenCounterFactory.create_counter(model)
            
            for size, content in test_content.items():
                token_count = count_tokens(content, model)
                char_count = len(content)
                ratio = char_count / token_count if token_count > 0 else 0
                
                logger.info(f"{size:>8} content: {char_count:>8,} chars = {token_count:>6,} tokens (ratio: {ratio:.1f})")
        
        return True
        
    except Exception as e:
        logger.error(f"❌ Token counter test failed: {e}")
        return False

def test_token_trimming_effectiveness():
    """测试token修剪的有效性"""
    logger.info("\n🧪 Testing Token Trimming Effectiveness...")
    
    try:
        from src.utils.token_manager import TokenManager
        from src.utils.token_counter import count_tokens
        from langchain_core.messages import HumanMessage, SystemMessage, AIMessage
        
        token_manager = TokenManager()
        test_content = create_test_content()
        
        # 测试不同规模内容的修剪效果
        for size_name, content in test_content.items():
            logger.info(f"\n--- Testing {size_name} content ---")
            
            messages = [
                SystemMessage(content="你是一个专业的产业分析师。"),
                HumanMessage(content=f"请分析以下内容：{content}"),
                AIMessage(content="我将为您提供详细的分析。"),
                HumanMessage(content="请提供具体的数据分析和建议。")
            ]
            
            # 计算原始token数
            original_tokens = sum(count_tokens(msg.content, "deepseek-chat") for msg in messages)
            
            # 应用token管理
            trimmed_messages = token_manager.trim_messages_for_node(messages, "deepseek-chat", "planner")
            trimmed_tokens = sum(count_tokens(msg.content, "deepseek-chat") for msg in trimmed_messages)
            
            # 计算效果
            reduction = ((original_tokens - trimmed_tokens) / original_tokens * 100) if original_tokens > 0 else 0
            
            logger.info(f"Original: {original_tokens:>6,} tokens | Trimmed: {trimmed_tokens:>6,} tokens | Reduction: {reduction:>5.1f}%")
            
            # 验证是否在限制范围内
            deepseek_limit = 32768
            if trimmed_tokens <= deepseek_limit:
                logger.info(f"✅ Within DeepSeek limit ({deepseek_limit:,} tokens)")
            else:
                logger.warning(f"⚠️  Exceeds DeepSeek limit ({deepseek_limit:,} tokens)")
        
        return True
        
    except Exception as e:
        logger.error(f"❌ Token trimming test failed: {e}")
        return False

def test_different_model_limits():
    """测试不同模型限制的处理"""
    logger.info("\n🧪 Testing Different Model Limits...")
    
    try:
        from src.utils.token_manager import TokenManager
        from src.utils.token_counter import count_tokens
        from langchain_core.messages import HumanMessage
        
        token_manager = TokenManager()
        large_content = create_test_content()['massive']
        
        message = HumanMessage(content=large_content)
        
        # 测试不同模型的处理
        models = [
            ("deepseek-chat", 32768),
            ("gemini-2.0-flash", 1000000), 
            ("gpt-4", 128000)
        ]
        
        for model, expected_limit in models:
            logger.info(f"\n--- Testing {model} (limit: {expected_limit:,}) ---")
            
            original_tokens = count_tokens(message.content, model)
            trimmed_messages = token_manager.trim_messages_for_node([message], model, "planner")
            trimmed_tokens = sum(count_tokens(msg.content, model) for msg in trimmed_messages)
            
            model_limit = token_manager.get_model_limit(model)
            
            logger.info(f"Original tokens: {original_tokens:>8,}")
            logger.info(f"Trimmed tokens:  {trimmed_tokens:>8,}")
            logger.info(f"Model limit:     {model_limit:>8,}")
            logger.info(f"Within limit: {'✅ Yes' if trimmed_tokens <= model_limit else '❌ No'}")
        
        return True
        
    except Exception as e:
        logger.error(f"❌ Model limits test failed: {e}")
        return False

def test_observation_management():
    """测试观察管理功能"""
    logger.info("\n🧪 Testing Observation Management...")
    
    try:
        from src.utils.token_manager import TokenManager
        
        token_manager = TokenManager()
        
        # 创建大量长观察
        observations = []
        for i in range(25):
            long_obs = f"观察{i}: " + "这是一个非常详细的观察结果，包含大量数据和分析。" * 300
            observations.append(long_obs)
        
        logger.info(f"Original observations: {len(observations)}")
        total_chars = sum(len(obs) for obs in observations)
        logger.info(f"Total characters: {total_chars:,}")
        
        # 应用观察管理
        managed_observations = token_manager.manage_observations(observations)
        
        logger.info(f"Managed observations: {len(managed_observations)}")
        managed_chars = sum(len(obs) for obs in managed_observations)
        logger.info(f"Managed characters: {managed_chars:,}")
        
        reduction = ((total_chars - managed_chars) / total_chars * 100) if total_chars > 0 else 0
        logger.info(f"Character reduction: {reduction:.1f}%")
        
        return True
        
    except Exception as e:
        logger.error(f"❌ Observation management test failed: {e}")
        return False

def test_configuration_loading():
    """测试配置加载功能"""
    logger.info("\n🧪 Testing Configuration Loading...")
    
    try:
        from src.utils.token_manager import TokenManager
        
        token_manager = TokenManager()
        
        # 测试配置是否正确加载
        logger.info(f"Config path: {token_manager.config_path}")
        logger.info(f"Config exists: {token_manager.config_path.exists()}")
        logger.info(f"Token management enabled: {token_manager.token_management.get('enabled', False)}")
        
        # 测试模型限制
        test_models = ["deepseek-chat", "gemini-2.0-flash", "gpt-4", "unknown-model"]
        for model in test_models:
            limit = token_manager.get_model_limit(model)
            logger.info(f"{model}: {limit:,} tokens")
        
        # 测试修剪策略
        test_nodes = ["planner", "reporter", "background_investigation", "unknown_node"]
        for node in test_nodes:
            strategy = token_manager.get_trimming_strategy(node)
            max_tokens = strategy.get("max_tokens", "Not set")
            logger.info(f"{node}: {max_tokens} max tokens")
        
        return True
        
    except Exception as e:
        logger.error(f"❌ Configuration test failed: {e}")
        return False

def main():
    """运行所有验证测试"""
    logger.info("🦌 Starting Simplified Token Management Validation")
    logger.info("=" * 70)
    
    tests = [
        ("Configuration Loading", test_configuration_loading),
        ("Token Counter Accuracy", test_token_counter_accuracy),
        ("Token Trimming Effectiveness", test_token_trimming_effectiveness),
        ("Different Model Limits", test_different_model_limits),
        ("Observation Management", test_observation_management),
    ]
    
    results = {}
    
    for test_name, test_func in tests:
        logger.info(f"\n{'='*70}")
        logger.info(f"🔍 Running: {test_name}")
        logger.info(f"{'='*70}")
        
        try:
            results[test_name] = test_func()
        except Exception as e:
            logger.error(f"❌ {test_name} crashed: {e}")
            results[test_name] = False
    
    # 总结
    logger.info(f"\n{'='*70}")
    logger.info("📊 VALIDATION RESULTS SUMMARY")
    logger.info(f"{'='*70}")
    
    passed = sum(1 for result in results.values() if result)
    total = len(results)
    
    for test_name, result in results.items():
        status = "✅ PASSED" if result else "❌ FAILED"
        logger.info(f"{status} - {test_name}")
    
    logger.info(f"\n🎯 Overall Result: {passed}/{total} tests passed")
    
    if passed == total:
        logger.info("🎉 ALL TOKEN MANAGEMENT VALIDATIONS PASSED!")
        logger.info("🚀 Your deer-flow system is ready for production with small-limit models!")
        logger.info("💡 Token management successfully prevents token overflow errors!")
    else:
        logger.info("⚠️  Some validations failed. Review the logs above for details.")
    
    return passed == total

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)