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
        self._token_counters = {}  # Cache for token counters to reduce creation overhead
        
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
                """Professional token counter using TokenCounterFactory with caching."""
                # Use cached counter if available
                if model_name not in self._token_counters:
                    self._token_counters[model_name] = TokenCounterFactory.create_counter(model_name)
                counter = self._token_counters[model_name]
                
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
            
            # Calculate token statistics for logging with detailed analysis
            try:
                original_tokens = professional_token_counter(messages)
                trimmed_tokens = professional_token_counter(trimmed_messages)
            except Exception as e:
                logger.warning(f"Token counting failed for {node_name}: {e}. Using estimated counts.")
                # Fallback to simple character-based estimation
                original_tokens = sum(len(str(msg.content)) for msg in messages) // 4
                trimmed_tokens = sum(len(str(msg.content)) for msg in trimmed_messages) // 4
            
            reduction_pct = ((original_tokens - trimmed_tokens) / original_tokens * 100) if original_tokens > 0 else 0
            token_difference = original_tokens - trimmed_tokens
            
            # Always log token management activity for monitoring
            status = "TRIMMED" if len(trimmed_messages) < len(messages) else "NO_TRIM"
            if token_difference < 0:
                status = "EXPANDED"  # This shouldn't happen normally
            
            logger.info(
                f"Token Management [{node_name}] [{status}]: "
                f"Messages: {len(messages)} → {len(trimmed_messages)} | "
                f"Tokens: {original_tokens:,} → {trimmed_tokens:,} | "
                f"Change: {reduction_pct:+.1f}% | "
                f"Model: {model_name} (limit: {self.get_model_limit(model_name):,}) | "
                f"Max allowed: {max_tokens:,}"
            )
            
            # Additional diagnostics for unusual cases
            if token_difference < 0:
                # Deep analysis of token expansion
                expansion_details = self._analyze_token_expansion(
                    messages, trimmed_messages, node_name, model_name
                )
                
                logger.warning(
                    f"Token EXPANSION detected in {node_name}: "
                    f"Tokens increased by {abs(token_difference):,}. "
                    f"Analysis: {expansion_details}"
                )
            elif reduction_pct > 50:
                logger.info(
                    f"Significant token reduction for {node_name}: "
                    f"Saved {token_difference:,} tokens ({reduction_pct:.1f}% reduction)"
                )
            elif len(trimmed_messages) == len(messages) and original_tokens <= max_tokens:
                logger.debug(
                    f"Token Management [{node_name}]: Within limits, no trimming needed "
                    f"({original_tokens:,} tokens ≤ {max_tokens:,} limit)"
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
    
    def _analyze_token_expansion(
        self, 
        original_messages: List[BaseMessage], 
        trimmed_messages: List[BaseMessage], 
        node_name: str, 
        model_name: str
    ) -> str:
        """
        Analyze the cause of token expansion in detail.
        
        Args:
            original_messages: Original message list
            trimmed_messages: Trimmed message list
            node_name: Name of the workflow node
            model_name: Name of the model
            
        Returns:
            Detailed analysis string
        """
        analysis_parts = []
        
        try:
            # 1. Message count analysis
            orig_count = len(original_messages)
            trim_count = len(trimmed_messages)
            analysis_parts.append(f"msg_count:{orig_count}→{trim_count}")
            
            # 2. Content length analysis
            orig_total_chars = sum(len(str(msg.content)) for msg in original_messages)
            trim_total_chars = sum(len(str(msg.content)) for msg in trimmed_messages)
            char_diff = trim_total_chars - orig_total_chars
            analysis_parts.append(f"chars:{orig_total_chars}→{trim_total_chars}({char_diff:+d})")
            
            # 3. Message type distribution
            orig_types = {}
            trim_types = {}
            
            for msg in original_messages:
                msg_type = msg.__class__.__name__
                orig_types[msg_type] = orig_types.get(msg_type, 0) + 1
                
            for msg in trimmed_messages:
                msg_type = msg.__class__.__name__
                trim_types[msg_type] = trim_types.get(msg_type, 0) + 1
            
            if orig_types != trim_types:
                analysis_parts.append(f"types_changed:{orig_types}→{trim_types}")
            
            # 4. Check for metadata differences
            orig_metadata = self._extract_message_metadata(original_messages)
            trim_metadata = self._extract_message_metadata(trimmed_messages)
            
            if orig_metadata != trim_metadata:
                analysis_parts.append(f"metadata_diff:true")
            
            # 5. Content sample comparison (first and last messages)
            if original_messages and trimmed_messages:
                orig_first = str(original_messages[0].content)[:100]
                trim_first = str(trimmed_messages[0].content)[:100]
                
                if orig_first != trim_first:
                    analysis_parts.append(f"first_msg_changed:true")
                
                if len(original_messages) > 1 and len(trimmed_messages) > 1:
                    orig_last = str(original_messages[-1].content)[:100]
                    trim_last = str(trimmed_messages[-1].content)[:100]
                    
                    if orig_last != trim_last:
                        analysis_parts.append(f"last_msg_changed:true")
            
            # 6. Check for specific patterns that might cause expansion
            expansion_patterns = self._detect_expansion_patterns(original_messages, trimmed_messages)
            if expansion_patterns:
                analysis_parts.extend(expansion_patterns)
                
        except Exception as e:
            analysis_parts.append(f"analysis_error:{str(e)}")
        
        return " | ".join(analysis_parts)
    
    def _extract_message_metadata(self, messages: List[BaseMessage]) -> dict:
        """Extract metadata from messages for comparison."""
        metadata = {
            'has_additional_kwargs': any(hasattr(msg, 'additional_kwargs') and msg.additional_kwargs for msg in messages),
            'has_response_metadata': any(hasattr(msg, 'response_metadata') and msg.response_metadata for msg in messages),
            'has_name': any(hasattr(msg, 'name') and msg.name for msg in messages),
            'has_tool_calls': any(hasattr(msg, 'tool_calls') and getattr(msg, 'tool_calls', None) for msg in messages),
        }
        return metadata
    
    def _detect_expansion_patterns(self, original: List[BaseMessage], trimmed: List[BaseMessage]) -> List[str]:
        """Detect specific patterns that might cause token expansion."""
        patterns = []
        
        try:
            # Pattern 1: Observation data processing
            for msg in trimmed:
                content = str(msg.content)
                if 'observation' in content.lower() or 'finding' in content.lower():
                    patterns.append("contains_observations")
                    break
            
            # Pattern 2: JSON or structured data
            for msg in trimmed:
                content = str(msg.content)
                if content.strip().startswith('{') or '<finding>' in content:
                    patterns.append("structured_data_added")
                    break
            
            # Pattern 3: Message role conversion artifacts
            if any('role' in str(msg.content) for msg in trimmed):
                patterns.append("role_conversion_artifacts")
            
            # Pattern 4: Formatting additions
            orig_has_markdown = any('##' in str(msg.content) or '**' in str(msg.content) for msg in original)
            trim_has_markdown = any('##' in str(msg.content) or '**' in str(msg.content) for msg in trimmed)
            
            if not orig_has_markdown and trim_has_markdown:
                patterns.append("markdown_formatting_added")
            
        except Exception as e:
            patterns.append(f"pattern_detection_error:{str(e)}")
        
        return patterns

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