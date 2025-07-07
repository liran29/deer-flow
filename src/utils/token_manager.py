"""
Token management utility using LangGraph's built-in trim_messages functionality.

This module provides a centralized way to handle token limits across different LLMs
and nodes in the deer-flow system, preventing token limit exceeded errors.
"""

import logging
import os
from typing import List, Dict, Any, Optional, Union
import yaml
from pathlib import Path

from langchain_core.messages import BaseMessage, SystemMessage, HumanMessage, AIMessage, ToolMessage
from langchain_core.messages.utils import trim_messages

logger = logging.getLogger(__name__)


class TokenManager:
    """
    Manages token limits and message trimming for different LLMs and workflow nodes.
    
    Uses LangGraph's built-in trim_messages functionality with configuration-based
    settings for different models and nodes.
    """
    
    def __init__(self, config_path: str = "conf.yaml"):
        """
        Initialize TokenManager with configuration.
        
        Args:
            config_path: Path to the configuration file containing token management settings
        """
        # If path is relative, make it relative to the project root
        if not os.path.isabs(config_path):
            # Use the same method as llm.py - go to project root (src/utils -> src -> project_root)
            project_root = Path(__file__).parent.parent.parent
            self.config_path = (project_root / config_path).resolve()
        else:
            self.config_path = Path(config_path)
        self.config = self._load_config()
        self.token_management = self.config.get("TOKEN_MANAGEMENT", {})
        
        if not self.token_management.get("enabled", False):
            logger.info("Token management is disabled in configuration")
            
    def _load_config(self) -> Dict[str, Any]:
        """Load configuration from YAML file."""
        try:
            with open(self.config_path, 'r', encoding='utf-8') as f:
                return yaml.safe_load(f)
        except Exception as e:
            logger.error(f"Failed to load configuration from {self.config_path}: {e}")
            logger.warning("Using fallback token management configuration")
            return self._get_fallback_config()
    
    def _get_fallback_config(self) -> Dict[str, Any]:
        """Get fallback configuration when conf.yaml is not available."""
        return {
            "TOKEN_MANAGEMENT": {
                "enabled": True,
                "safety_margin": 0.2,
                "model_limits": {
                    "deepseek-chat": 32768,
                    "gemini-2.0-flash": 1000000,
                    "default": 4096
                },
                "trimming_strategies": {
                    "planner": {
                        "max_tokens": 25000,
                        "strategy": "last"
                    },
                    "reporter": {
                        "max_tokens": 30000,
                        "strategy": "last"
                    },
                    "background_investigation": {
                        "max_tokens": 2000,
                        "strategy": "first"
                    }
                }
            }
        }
    
    def get_model_limit(self, model_name: str) -> int:
        """
        Get the token limit for a specific model.
        
        Args:
            model_name: Name of the model
            
        Returns:
            Token limit for the model
        """
        model_limits = self.token_management.get("model_limits", {})
        return model_limits.get(model_name, model_limits.get("default", 4096))
    
    def get_trimming_strategy(self, node_name: str) -> Dict[str, Any]:
        """
        Get the trimming strategy configuration for a specific node.
        
        Args:
            node_name: Name of the workflow node
            
        Returns:
            Dictionary containing trimming strategy configuration
        """
        trimming_strategies = self.token_management.get("trimming_strategies", {})
        return trimming_strategies.get(node_name, {})
    
    def calculate_available_tokens(self, model_name: str, node_name: str) -> int:
        """
        Calculate available tokens for input after reserving tokens for output.
        
        Args:
            model_name: Name of the model
            node_name: Name of the workflow node
            
        Returns:
            Number of tokens available for input
        """
        model_limit = self.get_model_limit(model_name)
        strategy = self.get_trimming_strategy(node_name)
        
        # Apply safety margin
        safety_margin = self.token_management.get("safety_margin", 0.2)
        effective_limit = int(model_limit * (1 - safety_margin))
        
        # Reserve tokens for output if specified
        reserve_for_output = strategy.get("reserve_for_output", 0)
        available_tokens = effective_limit - reserve_for_output
        
        return max(available_tokens, 1000)  # Minimum 1000 tokens
    
    def trim_messages_for_node(
        self,
        messages: List[BaseMessage],
        model_name: str,
        node_name: str,
        **kwargs
    ) -> List[BaseMessage]:
        """
        Trim messages for a specific node using LangGraph's trim_messages.
        
        Args:
            messages: List of messages to trim
            model_name: Name of the model
            node_name: Name of the workflow node
            **kwargs: Additional arguments to pass to trim_messages
            
        Returns:
            Trimmed list of messages
        """
        if not self.token_management.get("enabled", False):
            return messages
            
        strategy = self.get_trimming_strategy(node_name)
        if not strategy:
            logger.warning(f"No trimming strategy found for node: {node_name}")
            return messages
            
        # Calculate available tokens
        max_tokens = strategy.get("max_tokens")
        if not max_tokens:
            max_tokens = self.calculate_available_tokens(model_name, node_name)
        
        # Prepare trim_messages parameters
        trim_params = {
            "messages": messages,
            "max_tokens": max_tokens,
            "strategy": strategy.get("strategy", "last"),
            "include_system": strategy.get("include_system", True),
            **kwargs
        }
        
        # Add start_on and end_on if specified
        if "start_on" in strategy:
            trim_params["start_on"] = strategy["start_on"]
        if "end_on" in strategy:
            trim_params["end_on"] = strategy["end_on"]
            
        try:
            # Use the proper token counter from our token_counter module
            from .token_counter import TokenCounterFactory
            
            def professional_token_counter(messages):
                """Professional token counter using TokenCounterFactory."""
                counter = TokenCounterFactory.create_counter(model_name)
                
                # Convert BaseMessage objects to dict format for counting
                message_dicts = []
                for msg in messages:
                    if hasattr(msg, 'content'):
                        # Determine role based on message type
                        if hasattr(msg, '__class__'):
                            msg_type = msg.__class__.__name__
                            if msg_type == 'SystemMessage':
                                role = 'system'
                            elif msg_type == 'HumanMessage':
                                role = 'user'
                            elif msg_type == 'AIMessage':
                                role = 'assistant'
                            else:
                                role = 'user'  # fallback
                        else:
                            role = 'user'  # fallback
                        
                        message_dicts.append({
                            'role': role,
                            'content': str(msg.content)
                        })
                
                return counter.count_messages_tokens(message_dicts)
            
            trim_params["token_counter"] = professional_token_counter
            trimmed_messages = trim_messages(**trim_params)
            
            # Calculate token statistics for logging
            original_tokens = professional_token_counter(messages)
            trimmed_tokens = professional_token_counter(trimmed_messages)
            reduction_pct = ((original_tokens - trimmed_tokens) / original_tokens * 100) if original_tokens > 0 else 0
            
            if len(trimmed_messages) < len(messages) or original_tokens != trimmed_tokens:
                logger.info(
                    f"Token Management [{node_name}]: "
                    f"Messages: {len(messages)} → {len(trimmed_messages)} | "
                    f"Tokens: {original_tokens:,} → {trimmed_tokens:,} | "
                    f"Reduction: {reduction_pct:.1f}% | "
                    f"Model: {model_name} (limit: {self.get_model_limit(model_name):,})"
                )
                
                # Log details if significant reduction
                if reduction_pct > 50:
                    logger.info(
                        f"Significant token reduction for {node_name}: "
                        f"Saved {original_tokens - trimmed_tokens:,} tokens"
                    )
            else:
                logger.debug(
                    f"Token Management [{node_name}]: No trimming needed "
                    f"({original_tokens:,} tokens < {max_tokens:,} limit)"
                )
                
            return trimmed_messages
            
        except Exception as e:
            logger.error(f"Failed to trim messages for {node_name}: {e}")
            # Fallback: return recent messages manually
            return self._fallback_trim(messages, max_tokens // 100)  # Rough estimate
    
    def _fallback_trim(self, messages: List[BaseMessage], max_messages: int) -> List[BaseMessage]:
        """
        Fallback trimming method that keeps recent messages.
        
        Args:
            messages: List of messages to trim
            max_messages: Maximum number of messages to keep
            
        Returns:
            Trimmed list of messages
        """
        if len(messages) <= max_messages:
            return messages
            
        # Keep system messages and recent messages
        system_messages = [msg for msg in messages if isinstance(msg, SystemMessage)]
        other_messages = [msg for msg in messages if not isinstance(msg, SystemMessage)]
        
        # Keep the most recent non-system messages
        recent_messages = other_messages[-max_messages:]
        
        return system_messages + recent_messages
    
    def manage_observations(self, observations: List[str]) -> List[str]:
        """
        Manage observation list according to configuration.
        
        Args:
            observations: List of observation strings
            
        Returns:
            Managed list of observations
        """
        if not self.token_management.get("enabled", False):
            return observations
            
        obs_config = self.token_management.get("observation_management", {})
        max_observations = obs_config.get("max_full_observations", 3)
        max_length = obs_config.get("max_observation_length", 5000)
        enable_summarization = obs_config.get("enable_summarization", True)
        summary_target_length = obs_config.get("summary_target_length", 1000)
        
        # Truncate individual observations that are too long
        managed_observations = []
        for obs in observations:
            if len(obs) <= max_length:
                managed_observations.append(obs)
            else:
                if enable_summarization:
                    # Simple summarization: take first and last parts
                    summary = (
                        obs[:summary_target_length//2] + 
                        "\n\n[... content truncated ...]\n\n" +
                        obs[-summary_target_length//2:]
                    )
                    managed_observations.append(summary)
                else:
                    managed_observations.append(obs[:max_length] + "\n\n[... truncated ...]")
        
        # Limit total number of observations
        if len(managed_observations) > max_observations:
            original_count = len(observations)
            if enable_summarization:
                # Keep recent full observations and summarize older ones
                recent_observations = managed_observations[-max_observations:]
                older_count = len(managed_observations) - max_observations
                summary_prefix = f"[{older_count} earlier observations summarized]"
                result = [summary_prefix] + recent_observations
            else:
                result = managed_observations[-max_observations:]
            
            # Log observation management
            logger.info(
                f"Observation Management: {original_count} → {len(result)} observations | "
                f"Strategy: {'summarization' if enable_summarization else 'truncation'} | "
                f"Max allowed: {max_observations}"
            )
            return result
        
        # Log if observations were truncated
        if len(managed_observations) < len(observations):
            logger.info(
                f"Observation Management: Truncated long observations | "
                f"Original: {len(observations)} | Max length: {max_length}"
            )
        
        return managed_observations
    
    def create_pre_model_hook(self, model_name: str, node_name: str):
        """
        Create a pre-model hook function for automatic message trimming.
        
        Args:
            model_name: Name of the model
            node_name: Name of the workflow node
            
        Returns:
            Hook function that can be used with LangGraph
        """
        def pre_model_hook(messages: List[BaseMessage]) -> List[BaseMessage]:
            return self.trim_messages_for_node(messages, model_name, node_name)
        
        return pre_model_hook
    
    def log_token_usage(self, node_name: str, original_count: int, trimmed_count: int):
        """
        Log token usage statistics.
        
        Args:
            node_name: Name of the workflow node
            original_count: Original message/token count
            trimmed_count: Trimmed message/token count
        """
        if original_count > trimmed_count:
            reduction_pct = ((original_count - trimmed_count) / original_count) * 100
            logger.info(
                f"Token management for {node_name}: "
                f"Reduced from {original_count} to {trimmed_count} "
                f"({reduction_pct:.1f}% reduction)"
            )