# Copyright (c) 2025 Bytedance Ltd. and/or its affiliates
# SPDX-License-Identifier: MIT

import logging
from langgraph.prebuilt import create_react_agent
from langchain_core.messages import RemoveMessage
from langchain_core.messages.utils import trim_messages
from langgraph.graph.message import REMOVE_ALL_MESSAGES

from src.prompts import apply_prompt_template
from src.llms.llm import get_llm_by_type
from src.config.agents import AGENT_LLM_MAP
from src.utils.token_manager import TokenManager

logger = logging.getLogger(__name__)


# Create agents using configured LLM types
def create_agent(agent_name: str, agent_type: str, tools: list, prompt_template: str):
    """Factory function to create agents with consistent configuration."""
    
    def pre_model_hook(state):
        """Apply token management before each LLM call in the agent."""
        messages = state.get("messages", [])
        
        # Get TokenManager instance
        token_manager = TokenManager()
        
        # Check if token management is enabled
        if not token_manager.config.get("TOKEN_MANAGEMENT", {}).get("enabled", False):
            return {}
        
        # Get the LLM model for this agent type
        llm_model = get_llm_by_type(AGENT_LLM_MAP[agent_type])
        model_name = getattr(llm_model, 'model_name', 'default')
        
        # Apply token management using the existing strategy
        trimmed_messages = token_manager.trim_messages_for_node(
            messages=messages,
            model_name=model_name,
            node_name=agent_name
        )
        
        # 🎯 改进：避免过度修剪导致上下文丢失
        # 如果修剪后消息太少，保留最小上下文
        min_messages = 2  # 至少保留系统消息和一个用户消息
        if len(trimmed_messages) < min_messages and len(messages) >= min_messages:
            # 保留最重要的消息：系统消息 + 最后的用户消息
            important_messages = []
            
            # 保留系统消息
            for msg in messages:
                if hasattr(msg, '__class__') and msg.__class__.__name__ == 'SystemMessage':
                    important_messages.append(msg)
            
            # 保留最后的用户消息
            for msg in reversed(messages):
                if hasattr(msg, '__class__') and msg.__class__.__name__ == 'HumanMessage':
                    important_messages.append(msg)
                    break
            
            trimmed_messages = important_messages
            logger.warning(f"🔧 {agent_name}: Applied minimum context preservation ({len(trimmed_messages)} messages)")
        
        # If trimming occurred, update the state
        if len(trimmed_messages) != len(messages):
            # Remove all existing messages and replace with trimmed ones
            return {"messages": [RemoveMessage(REMOVE_ALL_MESSAGES)] + trimmed_messages}
        
        return {}
    
    return create_react_agent(
        name=agent_name,
        model=get_llm_by_type(AGENT_LLM_MAP[agent_type]),
        tools=tools,
        prompt=lambda state: apply_prompt_template(prompt_template, state),
        pre_model_hook=pre_model_hook,
    )
