#!/usr/bin/env python3
"""
Token Management Validation Script

This script tests the token management system in real deer-flow workflows
to ensure it properly handles large inputs that would exceed model token limits.
"""

import sys
import os
import logging
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

# Configure logging to see token management in action
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

logger = logging.getLogger(__name__)

def create_large_background_content():
    """Create background content that definitely exceeds token limits."""
    base_content = """
    深度市场分析报告：全球AI芯片产业发展趋势与竞争格局分析
    
    一、产业概述
    人工智能芯片作为AI技术落地的核心硬件支撑，近年来市场需求爆发式增长。
    全球AI芯片市场规模从2020年的130亿美元增长到2024年的超过500亿美元，
    预计到2030年将达到2000亿美元，年复合增长率超过25%。
    
    二、技术发展趋势
    1. 架构创新：从传统CPU/GPU到专用AI加速器
    - 神经网络处理器(NPU)成为主流
    - 可重构计算架构兴起
    - 存算一体化技术突破
    - 光子计算开始商业化探索
    
    2. 制程工艺：先进制程竞争激烈
    - 5nm制程量产，3nm制程即将普及
    - 先进封装技术创新，如2.5D、3D封装
    - 新材料应用，如化合物半导体
    - 量子计算芯片技术突破
    
    3. 应用场景多样化
    - 云端训练：大模型训练需求暴增
    - 边缘推理：移动设备AI计算能力提升
    - 自动驾驶：车载AI芯片市场快速增长
    - 数据中心：AI服务器渗透率持续提升
    
    三、竞争格局分析
    1. 全球头部厂商
    - NVIDIA：在AI训练芯片领域占据绝对领先地位，H100、A100系列产品需求火爆
    - AMD：通过收购Xilinx增强FPGA实力，MI系列GPU对标NVIDIA
    - Intel：收购Habana Labs进军AI训练，推出Ponte Vecchio架构
    - Google：TPU系列在自家云服务中大规模部署
    - Apple：M系列芯片集成Neural Engine，在移动AI领域创新
    
    2. 中国厂商崛起
    - 华为：昇腾系列AI芯片技术不断突破，生态逐步完善
    - 寒武纪：思元系列覆盖云边端全场景
    - 地平线：在汽车智能芯片领域占据重要地位
    - 比特大陆：从挖矿芯片转向AI推理芯片
    - 燧原科技：专注于AI训练芯片，邃思系列性能优异
    
    四、市场细分
    1. 训练芯片市场
    - 大模型训练需求推动高端芯片需求
    - 算力密度和能效比成为关键指标
    - 多芯片互联技术重要性凸显
    - 软件生态和开发工具链决定竞争力
    
    2. 推理芯片市场
    - 边缘计算需求推动低功耗芯片发展
    - 实时性要求推动专用架构创新
    - 成本敏感性促进芯片标准化
    - 量产规模决定市场地位
    
    五、产业链分析
    1. 上游：设计工具和IP
    - EDA工具被国外厂商垄断，成为产业发展瓶颈
    - IP核授权费用持续上涨
    - 开源RISC-V架构提供新选择
    
    2. 中游：芯片设计与制造
    - 设计能力分化加剧
    - 先进制程产能稀缺
    - 封装测试环节竞争激烈
    
    3. 下游：系统集成与应用
    - 云服务商成为重要客户
    - OEM厂商需求多样化
    - 垂直行业应用快速增长
    
    六、投资机会分析
    1. 长期看好领域
    - 大模型训练基础设施
    - 边缘AI芯片
    - 汽车智能化芯片
    - 机器人控制芯片
    
    2. 关键技术方向
    - 存算一体化架构
    - 光电融合计算
    - 量子计算芯片
    - 脑机接口芯片
    
    七、风险因素
    1. 技术风险
    - 摩尔定律放缓
    - 新架构不确定性
    - 良率控制难度
    
    2. 市场风险
    - 需求波动性大
    - 竞争加剧
    - 替代技术威胁
    
    3. 政策风险
    - 贸易限制
    - 技术出口管制
    - 产业政策变化
    
    八、发展建议
    1. 对企业
    - 加强技术创新投入
    - 完善产业生态建设
    - 重视人才培养
    - 深化国际合作
    
    2. 对投资者
    - 关注技术领先企业
    - 重视生态建设能力
    - 考虑产业链完整性
    - 评估可持续发展能力
    """
    
    # Repeat to create massive content (should exceed 32K tokens for DeepSeek)
    return base_content * 100

def create_large_observations():
    """Create large observations list that exceeds memory limits."""
    observations = []
    
    for i in range(20):
        obs = f"""
        调研观察 {i+1}: 
        
        通过对全球AI芯片市场的深入调研，发现了以下重要市场动态和技术趋势：
        
        技术发展方面：
        - 新一代7nm制程AI芯片开始量产，相比上一代产品性能提升40%，能耗降低30%
        - 存算一体化架构取得重大突破，内存带宽利用率提升至传统架构的5倍
        - 多模态AI芯片成为新热点，支持视觉、语言、音频等多种AI任务的统一处理
        - 光子计算技术在部分场景下展现出巨大潜力，计算速度理论上可提升1000倍
        
        市场竞争格局：
        - NVIDIA继续在高端AI训练芯片市场保持领先，但在推理芯片市场面临更多挑战
        - 中国本土AI芯片厂商在特定细分领域开始展现竞争优势
        - 云服务商自研芯片趋势明显，亚马逊、谷歌、阿里云等都在加大投入
        - 汽车智能化推动车载AI芯片需求爆发，预计未来5年市场规模增长10倍
        
        供应链动态：
        - 先进制程产能依然紧张，台积电5nm产线排期已到2025年
        - 封装材料成本上涨，推动芯片厂商寻求新的封装解决方案
        - 地缘政治因素对产业链稳定性影响加大，企业开始布局多元化供应策略
        
        应用场景拓展：
        - 大语言模型训练需求推动超大规模AI集群建设
        - 边缘计算场景下的AI芯片需求快速增长
        - 工业物联网、智慧城市等新兴应用为AI芯片提供新的增长点
        - 科学计算、药物发现等领域开始大规模采用AI加速器
        
        投资热点分析：
        - 私募股权投资重点关注初创AI芯片公司
        - 上市公司通过并购整合产业链资源
        - 政府产业基金加大对本土AI芯片企业的支持力度
        - 国际资本对中国AI芯片企业的投资趋于谨慎
        
        技术标准化进展：
        - IEEE、ISO等国际组织推动AI芯片标准制定
        - 开源硬件架构RISC-V在AI芯片领域应用增多
        - 软件框架标准化有助于降低开发成本
        - 安全标准和隐私保护要求日益严格
        
        未来发展趋势预测：
        - 专用AI芯片将在更多垂直领域出现
        - 量子计算与经典计算的混合架构成为研究热点
        - 生物启发的神经形态芯片技术逐步成熟
        - 可重构计算架构为AI芯片提供更大灵活性
        """ * 50  # Make each observation very long
        
        observations.append(obs.strip())
    
    return observations

def test_planner_node_integration():
    """Test planner node with large input that exceeds token limits."""
    logger.info("🧪 Testing Planner Node Token Management...")
    
    try:
        from src.graph.nodes import planner_node
        from src.graph.types import State
        from langchain_core.messages import HumanMessage
        from langchain_core.runnables import RunnableConfig
        
        # Create large background content
        large_content = create_large_background_content()
        logger.info(f"Created background content: {len(large_content):,} characters")
        
        # Create state with large message history
        messages = [
            HumanMessage(content="请分析全球AI芯片产业的发展趋势"),
            HumanMessage(content=f"背景信息：{large_content}"),
            HumanMessage(content="请提供详细的市场分析和投资建议")
        ]
        
        state = State(
            messages=messages,
            research_topic="AI芯片产业分析"
        )
        
        # Create proper RunnableConfig
        config = RunnableConfig(
            configurable={
                "max_plan_iterations": 1,
                "max_step_num": 3,
                "max_search_results": 3
            }
        )
        
        logger.info(f"Testing planner with {len(messages)} messages...")
        
        # This should trigger token management
        result = planner_node(state, config)
        
        logger.info("✅ Planner node completed successfully with token management")
        logger.info(f"Result plan length: {len(str(result.get('plan', '')))}")
        
        return True
        
    except Exception as e:
        logger.error(f"❌ Planner node test failed: {e}")
        return False

def test_reporter_node_integration():
    """Test reporter node with large observations."""
    logger.info("🧪 Testing Reporter Node Token Management...")
    
    try:
        from src.graph.nodes import reporter_node
        from src.graph.types import State
        from langchain_core.messages import HumanMessage
        from langchain_core.runnables import RunnableConfig
        
        # Create large observations
        large_observations = create_large_observations()
        logger.info(f"Created {len(large_observations)} observations")
        
        state = State(
            messages=[HumanMessage(content="请根据调研结果生成报告")],
            research_topic="AI芯片产业分析",
            observations=large_observations
        )
        
        # Create proper RunnableConfig
        config = RunnableConfig(
            configurable={
                "max_plan_iterations": 1,
                "max_step_num": 3,
                "max_search_results": 3,
                "report_style": "academic"
            }
        )
        
        logger.info("Testing reporter with large observations...")
        
        # This should trigger observation management
        result = reporter_node(state, config)
        
        logger.info("✅ Reporter node completed successfully with token management")
        logger.info(f"Generated report length: {len(str(result.get('final_report', '')))}")
        
        return True
        
    except Exception as e:
        logger.error(f"❌ Reporter node test failed: {e}")
        return False

def test_background_investigation_integration():
    """Test background investigation with large result."""
    logger.info("🧪 Testing Background Investigation Token Management...")
    
    try:
        from src.graph.nodes import background_investigation_node
        from src.graph.types import State
        from langchain_core.messages import HumanMessage
        from langchain_core.runnables import RunnableConfig
        
        # Create state for background investigation
        state = State(
            messages=[HumanMessage(content="请调研全球AI芯片产业的最新发展情况")],
            research_topic="AI芯片产业发展调研",
            enable_background_investigation=True
        )
        
        # Create proper RunnableConfig
        config = RunnableConfig(
            configurable={
                "max_plan_iterations": 1,
                "max_step_num": 3,
                "max_search_results": 3
            }
        )
        
        logger.info("Testing background investigation...")
        
        # This should trigger token management if the investigation result is large
        result = background_investigation_node(state, config)
        
        logger.info("✅ Background investigation completed successfully")
        logger.info(f"Investigation result length: {len(str(result.get('background_investigation_results', '')))}")
        
        return True
        
    except Exception as e:
        logger.error(f"❌ Background investigation test failed: {e}")
        return False

def test_token_manager_directly():
    """Test TokenManager directly with large inputs."""
    logger.info("🧪 Testing TokenManager Directly...")
    
    try:
        from src.utils.token_manager import TokenManager
        from src.utils.token_counter import count_tokens
        from langchain_core.messages import HumanMessage, SystemMessage
        
        token_manager = TokenManager()
        
        # Create large content
        large_content = create_large_background_content()
        
        messages = [
            SystemMessage(content="你是一个专业的产业分析师"),
            HumanMessage(content=f"请分析以下信息：{large_content}"),
            HumanMessage(content="请提供详细的分析报告")
        ]
        
        # Test with DeepSeek model
        original_tokens = sum(count_tokens(msg.content, "deepseek-chat") for msg in messages)
        logger.info(f"Original content tokens: {original_tokens:,}")
        
        # Apply token management
        trimmed_messages = token_manager.trim_messages_for_node(messages, "deepseek-chat", "planner")
        trimmed_tokens = sum(count_tokens(msg.content, "deepseek-chat") for msg in trimmed_messages)
        
        logger.info(f"Trimmed content tokens: {trimmed_tokens:,}")
        logger.info(f"Token reduction: {((original_tokens - trimmed_tokens) / original_tokens * 100):.1f}%")
        
        # Verify it's within DeepSeek limits
        deepseek_limit = 32768
        if trimmed_tokens <= deepseek_limit:
            logger.info("✅ Token management successfully kept content within DeepSeek limits")
            return True
        else:
            logger.error(f"❌ Token management failed: {trimmed_tokens} > {deepseek_limit}")
            return False
            
    except Exception as e:
        logger.error(f"❌ Direct TokenManager test failed: {e}")
        return False

def main():
    """Run all validation tests."""
    logger.info("🦌 Starting Token Management Validation Tests")
    logger.info("=" * 60)
    
    tests = [
        ("Direct TokenManager Test", test_token_manager_directly),
        ("Planner Node Integration", test_planner_node_integration),
        ("Reporter Node Integration", test_reporter_node_integration),
        ("Background Investigation Integration", test_background_investigation_integration),
    ]
    
    results = {}
    
    for test_name, test_func in tests:
        logger.info(f"\n🔍 Running: {test_name}")
        logger.info("-" * 40)
        
        try:
            results[test_name] = test_func()
        except Exception as e:
            logger.error(f"❌ {test_name} crashed: {e}")
            results[test_name] = False
    
    # Summary
    logger.info("\n" + "=" * 60)
    logger.info("📊 VALIDATION RESULTS SUMMARY")
    logger.info("=" * 60)
    
    passed = sum(1 for result in results.values() if result)
    total = len(results)
    
    for test_name, result in results.items():
        status = "✅ PASSED" if result else "❌ FAILED"
        logger.info(f"{status} - {test_name}")
    
    logger.info(f"\n🎯 Overall: {passed}/{total} tests passed")
    
    if passed == total:
        logger.info("🎉 All token management validations PASSED!")
        logger.info("🚀 Your deer-flow system is ready for production with DeepSeek!")
    else:
        logger.info("⚠️  Some validations failed. Review the logs above.")
    
    return passed == total

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)