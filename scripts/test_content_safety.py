#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
内容安全处理机制测试脚本
使用真实的引起 Content Exists Risk 的内容来验证处理机制
"""

import asyncio
import logging
import sys
import os
from typing import Dict, Any
from openai import BadRequestError

# 添加项目路径
sys.path.append('/mnt/d/HT/market-assistant/deer-flow')

from src.utils.content_safety_handler import content_safety_handler, ContentSafetyError
from src.config import load_yaml_config
from src.llms.llm import get_llm_by_type

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# 从日志中提取的实际引起 Content Exists Risk 的内容
RISK_CONTENT = """# Current Task

## Title

医疗领域的应用现状与技术挑战

## Description

收集大语言模型在医疗领域的最新应用案例，包括诊疗效率提升、医疗服务质量改善等方面的具体实例。同时，分析医疗数据安全、隐私保护、模型泛化能力等技术挑战。

## 医疗大模型发展现状

2024年底国产开源语言大模型DeepSeek的爆发，极大加速了市场教育，将大模型在医疗场景的应用迫切度推至历史高点。

### 技术演进与性能突破

医疗大模型的发展历经从规则驱动到数据驱动、单模态到多模态融合的演进过程。例如DeepSeek-V3模型凭借6710亿参数与混合专家架构，训练成本仅557.6万美元（不足GPT-4的1/10），却在基准测试中性能媲美闭源模型，推动医疗大模型进入"生成+推理"新阶段。

### 应用场景拓展

医疗大模型在以下方面取得突破：
- 临床专病辅助决策
- 预问诊系统
- 病历辅助生成
- 医学影像辅助诊断
- 药物研发加速
- 中医药现代化

### 商业化进程

当前医疗大模型市场呈现爆发式增长态势。2025年截至5月1日，国内已发布133个医疗大模型，远超2024年全年的94个、2023年的61个。市场规模预计在2028年突破百亿元。

## Locale

zh-CN"""

class MockBadRequestError(BadRequestError):
    """模拟 BadRequestError 用于测试"""
    def __init__(self, message: str):
        # 创建一个最小的 mock response 对象
        class MockRequest:
            def __init__(self):
                self.method = "POST"
                self.url = "https://api.deepseek.com/chat/completions"
        
        class MockResponse:
            def __init__(self):
                self.request = MockRequest()
                self.status_code = 400
                self.headers = {}
                
            def json(self):
                return {
                    "error": {
                        "message": "Content Exists Risk",
                        "type": "invalid_request_error",
                        "param": None,
                        "code": "invalid_request_error"
                    }
                }
        
        # 调用父类构造函数
        mock_response = MockResponse()
        super().__init__(
            message=message,
            response=mock_response,
            body=None
        )

async def test_content_safety_with_real_content():
    """使用真实的引起风险的内容测试内容安全机制"""
    
    logger.info("🧪 开始测试内容安全处理机制")
    logger.info("=" * 60)
    
    # 1. 测试内容安全错误检测
    logger.info("📝 测试1: 内容安全错误检测")
    
    # 模拟真实的 Content Exists Risk 错误
    mock_error = MockBadRequestError("Error code: 400 - {'error': {'message': 'Content Exists Risk', 'type': 'invalid_request_error', 'param': None, 'code': 'invalid_request_error'}}")
    
    # 测试错误检测
    is_safety_error = content_safety_handler.is_content_safety_error(mock_error)
    logger.info(f"   ✅ 错误检测结果: {is_safety_error}")
    
    # 2. 测试错误详情提取
    logger.info("📝 测试2: 错误详情提取")
    error_details = content_safety_handler.extract_error_details(mock_error)
    logger.info(f"   ✅ 错误详情: {error_details}")
    
    # 3. 测试内容安全处理
    logger.info("📝 测试3: 内容安全错误处理")
    
    context = {
        "agent_name": "researcher",
        "step_title": "医疗领域的应用现状与技术挑战",
        "content_preview": RISK_CONTENT[:200] + "...",
        "message_count": 3,
        "error_time": "2025-07-10 测试时间"
    }
    
    # 处理内容安全错误
    action = await content_safety_handler.handle_content_safety_error(
        mock_error,
        context,
        auto_continue_timeout=5  # 5秒测试超时
    )
    
    logger.info(f"   ✅ 处理结果: {action}")
    logger.info(f"   ✅ 错误历史记录数: {len(content_safety_handler.error_history)}")
    
    # 4. 测试配置加载
    logger.info("📝 测试4: 配置验证")
    config = content_safety_handler.config
    logger.info(f"   ✅ 内容安全处理启用: {config.get('enabled', False)}")
    logger.info(f"   ✅ 自动过滤: {config.get('auto_filter', False)}")
    logger.info(f"   ✅ 显示警告: {config.get('show_warning', False)}")
    logger.info(f"   ✅ 记录事件: {config.get('log_incidents', False)}")
    
    # 5. 测试错误历史查看
    logger.info("📝 测试5: 错误历史记录")
    if content_safety_handler.error_history:
        latest_error = content_safety_handler.error_history[-1]
        logger.info(f"   ✅ 最新错误时间: {latest_error['timestamp']}")
        logger.info(f"   ✅ 错误类型: {latest_error['error']['type']}")
        logger.info(f"   ✅ 错误消息: {latest_error['error']['message']}")
    
    logger.info("=" * 60)
    logger.info("🎉 内容安全处理机制测试完成！")
    
    return action == "continue"

async def test_llm_integration():
    """测试与实际LLM的集成（可选，需要谨慎）"""
    
    logger.info("\n🔗 测试LLM集成（模拟场景）")
    logger.info("=" * 60)
    
    try:
        # 加载配置
        config = load_yaml_config("conf.yaml")
        model_name = config.get("BASIC_MODEL", {}).get("model", "deepseek-chat")
        
        logger.info(f"📡 当前配置模型: {model_name}")
        
        # 注意：这里不实际调用LLM，只是展示如何集成
        logger.info("   ⚠️  集成提示: 在实际的 nodes.py 中，当 LLM 调用失败时：")
        logger.info("   1. 捕获 BadRequestError")
        logger.info("   2. 检查是否为内容安全错误")
        logger.info("   3. 调用 content_safety_handler.handle_content_safety_error()")
        logger.info("   4. 返回安全响应消息并继续执行")
        
        logger.info("=" * 60)
        logger.info("🔗 LLM集成测试完成（模拟）")
        
    except Exception as e:
        logger.error(f"❌ LLM集成测试失败: {e}")

def create_test_prompt_with_risk_content():
    """创建包含风险内容的测试提示"""
    
    test_prompt = f"""
请分析以下医疗领域大模型应用的内容：

{RISK_CONTENT}

请对以上内容进行深入分析，包括：
1. 技术发展趋势
2. 市场机会分析  
3. 潜在风险评估
4. 未来发展建议

注意：这是一个测试提示，用于验证内容安全处理机制。
"""
    
    return test_prompt

async def main():
    """主测试函数"""
    
    print("🚀 启动内容安全处理机制验证测试")
    print("=" * 80)
    
    try:
        # 执行核心测试
        success = await test_content_safety_with_real_content()
        
        if success:
            print("\n✅ 核心测试通过！内容安全处理机制工作正常")
        else:
            print("\n❌ 核心测试失败！")
            
        # 执行集成测试
        await test_llm_integration()
        
        # 显示测试提示内容（用于手动测试）
        print("\n📋 风险内容测试样本（用于手动验证）:")
        print("-" * 50)
        test_prompt = create_test_prompt_with_risk_content()
        print(test_prompt[:500] + "...")
        
        print("\n💡 手动测试建议:")
        print("   1. 使用上述内容在研究系统中发起查询")
        print("   2. 观察是否触发 Content Exists Risk 错误")
        print("   3. 验证系统是否显示安全警告并继续执行")
        print("   4. 检查日志中的安全事件记录")
        
    except Exception as e:
        logger.error(f"❌ 测试执行失败: {e}")
        import traceback
        logger.error(f"错误详情: {traceback.format_exc()}")
    
    print("\n" + "=" * 80)
    print("🏁 测试完成")

if __name__ == "__main__":
    asyncio.run(main())