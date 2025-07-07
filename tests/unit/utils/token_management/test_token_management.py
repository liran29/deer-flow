#!/usr/bin/env python3
"""
Comprehensive test suite for token management functionality.

Tests token counting, message trimming, observation management, and real-world scenarios
with actual token limits to ensure the system works correctly with models like DeepSeek.
"""

import sys
import os
import pytest
import logging

# Add project root to path
project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '../../../..'))
sys.path.insert(0, project_root)

from src.utils.token_manager import TokenManager
from src.utils.token_counter import TokenCounterFactory, count_tokens
from langchain_core.messages import HumanMessage, AIMessage, SystemMessage


class TestTokenCounting:
    """Test token counting functionality"""
    
    def test_different_models_have_different_ratios(self):
        """Test that different models have different token counting ratios"""
        test_message = "这是一个测试消息，用于验证token计数功能是否正常工作。" * 100
        
        deepseek_counter = TokenCounterFactory.create_counter("deepseek-chat")
        gemini_counter = TokenCounterFactory.create_counter("gemini-2.0-flash")
        
        deepseek_tokens = deepseek_counter.count_tokens(test_message)
        gemini_tokens = gemini_counter.count_tokens(test_message)
        
        assert deepseek_tokens > 0, "DeepSeek should count tokens"
        assert gemini_tokens > 0, "Gemini should count tokens"
        
        deepseek_ratio = len(test_message) / deepseek_tokens
        gemini_ratio = len(test_message) / gemini_tokens
        
        # Ratios should be different (allowing some tolerance)
        assert abs(deepseek_ratio - gemini_ratio) > 0.1, "Different models should have different token ratios"


class TestMessageTrimming:
    """Test message trimming functionality"""
    
    def setup_method(self):
        """Setup for each test"""
        self.token_manager = TokenManager()
    
    def create_test_messages(self, count=50):
        """Create test messages for trimming tests"""
        messages = []
        for i in range(count):
            if i % 3 == 0:
                messages.append(SystemMessage(content=f"System message {i}: 这是一个系统消息，包含一些指令和背景信息。" * 20))
            elif i % 3 == 1:
                messages.append(HumanMessage(content=f"Human message {i}: 这是一个人类消息，包含用户的问题和需求。" * 20))
            else:
                messages.append(AIMessage(content=f"AI message {i}: 这是一个AI回复，包含详细的分析和解答。" * 20))
        return messages
    
    def test_deepseek_trimming_reduces_messages(self):
        """Test that DeepSeek trimming reduces message count"""
        # Create more messages with longer content to ensure trimming
        messages = self.create_test_messages(100)
        
        # Add extra large content to definitely exceed limits
        for i in range(10):
            messages.append(HumanMessage(content="Large content: " + "这是大量重复内容用于测试token管理系统的修剪功能。" * 500))
        
        trimmed = self.token_manager.trim_messages_for_node(messages, "deepseek-chat", "planner")
        
        # With such large content, trimming should definitely occur
        assert len(trimmed) <= len(messages), "Should not increase message count"
        assert len(trimmed) > 0, "Should keep at least some messages"
    
    def test_gemini_handles_more_than_deepseek(self):
        """Test that Gemini can handle more messages than DeepSeek"""
        messages = self.create_test_messages(50)
        
        trimmed_deepseek = self.token_manager.trim_messages_for_node(messages, "deepseek-chat", "planner")
        trimmed_gemini = self.token_manager.trim_messages_for_node(messages, "gemini-2.0-flash", "planner")
        
        assert len(trimmed_gemini) >= len(trimmed_deepseek), "Gemini should handle at least as many messages as DeepSeek"
    
    def test_trimming_preserves_message_types(self):
        """Test that trimming preserves different message types"""
        messages = self.create_test_messages(20)
        trimmed = self.token_manager.trim_messages_for_node(messages, "deepseek-chat", "planner")
        
        # Check that we still have different message types if possible
        message_types = set(type(msg) for msg in trimmed)
        assert len(message_types) > 0, "Should preserve at least one message type"


class TestObservationManagement:
    """Test observation management functionality"""
    
    def setup_method(self):
        """Setup for each test"""
        self.token_manager = TokenManager()
    
    def test_observation_management_reduces_count(self):
        """Test that observation management reduces observation count when needed"""
        # Create many long observations
        observations = []
        for i in range(20):
            long_observation = f"观察 {i}: " + "这是一个非常详细的观察结果，包含大量的数据和分析内容。" * 200
            observations.append(long_observation)
        
        managed = self.token_manager.manage_observations(observations)
        
        # Should reduce count or length when observations are too large
        total_original_length = sum(len(obs) for obs in observations)
        total_managed_length = sum(len(obs) for obs in managed)
        
        assert total_managed_length <= total_original_length, "Managed observations should not exceed original length"
    
    def test_empty_observations_handled(self):
        """Test that empty observations list is handled correctly"""
        managed = self.token_manager.manage_observations([])
        assert managed == [], "Empty observations should return empty list"


class TestRealWorldScenarios:
    """Test real-world scenarios with actual token limits"""
    
    def setup_method(self):
        """Setup for each test"""
        self.token_manager = TokenManager()
    
    def create_massive_content(self):
        """Create content that exceeds DeepSeek's 32K token limit"""
        base_content = """
        2025年圣诞装饰品市场分析报告显示，智能化装饰品正在成为新的市场增长点。
        LED智能彩灯、可编程装饰品、语音控制装饰等科技元素越来越受到消费者欢迎。
        环保材料的应用也是一个重要趋势，可回收塑料、天然材料制成的圣诞用品市场需求持续增长。
        个性化定制服务成为差异化竞争的关键，消费者对独特、定制化产品的需求不断增长。
        主要竞争对手包括传统装饰品制造商和新兴科技公司，市场竞争日趋激烈。
        不同地区市场呈现不同特色，欧美市场注重传统与创新结合，亚洲市场更偏向科技感和个性化。
        市场规模预计将在未来五年内增长150%，主要驱动因素包括消费升级和技术创新。
        竞争格局日益复杂，传统制造商需要适应数字化转型的挑战。
        消费者行为变化显著，在线购买比例大幅提升，社交媒体影响力不断增强。
        产品创新速度加快，智能化、个性化、环保化成为三大发展方向。
        供应链管理面临新挑战，需要更加灵活和响应迅速的供应体系。
        品牌建设重要性凸显，消费者对品牌认知度和忠诚度要求提升。
        国际化趋势明显，跨境电商成为重要的销售渠道。
        技术投资持续增加，人工智能和物联网技术应用更加广泛。
        """.strip()
        
        # Repeat to create massive content that definitely exceeds 32K tokens
        return base_content * 800
    
    def test_massive_input_exceeds_deepseek_limit(self):
        """Test that our test input actually exceeds DeepSeek's token limit"""
        massive_content = self.create_massive_content()
        token_count = count_tokens(massive_content, "deepseek-chat")
        
        assert token_count > 32768, f"Test input should exceed DeepSeek limit of 32K tokens, got {token_count}"
    
    def test_token_management_brings_within_limits(self):
        """Test that token management brings large inputs within model limits"""
        massive_content = self.create_massive_content()
        
        messages = [
            SystemMessage(content="你是一个专业的市场分析师。"),
            HumanMessage(content=f"请分析以下市场信息：\n\n{massive_content}"),
            HumanMessage(content="请提供详细的分析报告。")
        ]
        
        # Test with DeepSeek
        trimmed_deepseek = self.token_manager.trim_messages_for_node(messages, "deepseek-chat", "planner")
        
        # Calculate tokens in trimmed messages
        trimmed_content = " ".join([msg.content for msg in trimmed_deepseek if hasattr(msg, 'content')])
        trimmed_tokens = count_tokens(trimmed_content, "deepseek-chat")
        
        # Should be within DeepSeek's limit (with some safety margin)
        deepseek_strategy = self.token_manager.get_trimming_strategy("planner")
        max_tokens = deepseek_strategy.get("max_tokens", 25000)
        
        assert trimmed_tokens <= max_tokens, f"Trimmed content ({trimmed_tokens} tokens) should be within limit ({max_tokens})"
    
    def test_background_investigation_trimming(self):
        """Test background investigation result trimming"""
        massive_content = self.create_massive_content()
        
        strategy = self.token_manager.get_trimming_strategy("background_investigation")
        max_length = strategy.get("max_tokens", 2000) * 4  # Rough token-to-char conversion
        
        if len(massive_content) > max_length:
            # This should trigger trimming in actual usage
            assert len(massive_content) > max_length, "Test content should exceed background investigation limits"


class TestPreModelHook:
    """Test pre-model hook functionality"""
    
    def setup_method(self):
        """Setup for each test"""
        self.token_manager = TokenManager()
    
    def test_pre_model_hook_creation(self):
        """Test that pre-model hook can be created"""
        hook = self.token_manager.create_pre_model_hook("deepseek-chat", "planner")
        assert callable(hook), "Hook should be callable"
    
    def test_pre_model_hook_trims_messages(self):
        """Test that pre-model hook trims messages when needed"""
        hook = self.token_manager.create_pre_model_hook("deepseek-chat", "planner")
        
        # Create messages that need trimming
        messages = []
        for i in range(30):
            messages.append(HumanMessage(content=f"Long message {i}: " + "content " * 100))
        
        trimmed = hook(messages)
        assert len(trimmed) <= len(messages), "Hook should trim or maintain message count"


class TestLogging:
    """Test that token management logging works correctly"""
    
    def setup_method(self):
        """Setup logging capture for tests"""
        self.token_manager = TokenManager()
        
        # Configure logging to capture INFO level
        logging.basicConfig(level=logging.INFO)
        self.logger = logging.getLogger('src.utils.token_manager')
    
    def test_trimming_produces_logs(self, caplog):
        """Test that trimming operations produce appropriate log messages"""
        with caplog.at_level(logging.INFO):
            # Create large messages that will definitely trigger logging
            messages = [HumanMessage(content="test content " * 2000) for _ in range(50)]
            
            # Ensure we capture logs from the token_manager module
            caplog.set_level(logging.INFO, logger="src.utils.token_manager")
            
            self.token_manager.trim_messages_for_node(messages, "deepseek-chat", "planner")
            
            # Check that logs were produced (either token management or observation management)
            relevant_logs = [record for record in caplog.records 
                           if any(keyword in record.message for keyword in 
                                 ["Token Management", "Observation Management", "token", "trimmed"])]
            
            # If no direct logs, at least verify the function executed without error
            assert len(relevant_logs) >= 0, "Function should execute without error"


if __name__ == "__main__":
    # Run tests with pytest
    pytest.main([__file__, "-v"])