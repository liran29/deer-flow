# Copyright (c) 2025 Bytedance Ltd. and/or its affiliates
# SPDX-License-Identifier: MIT

"""
Production-grade token counting utilities for various LLM models.

This module provides robust token counting with fallback mechanisms,
caching, and comprehensive error handling.
"""

import json
import logging
from abc import ABC, abstractmethod
from functools import lru_cache
from typing import Dict, List, Optional, Union

logger = logging.getLogger(__name__)


class TokenCounterBase(ABC):
    """Base class for token counters."""
    
    @abstractmethod
    def count_tokens(self, text: str) -> int:
        """Count tokens in the given text."""
        pass
    
    @abstractmethod
    def count_messages_tokens(self, messages: List[Dict[str, str]]) -> int:
        """Count tokens in a list of messages."""
        pass


class ApproximateTokenCounter(TokenCounterBase):
    """Fallback token counter using character-based approximation."""
    
    def __init__(self, chars_per_token: float = 4.0):
        """
        Initialize with average characters per token.
        
        Args:
            chars_per_token: Average number of characters per token.
                           Default 4.0 is conservative for most models.
        """
        self.chars_per_token = chars_per_token
        logger.info(f"Initialized ApproximateTokenCounter with {chars_per_token} chars/token")
    
    def count_tokens(self, text: str) -> int:
        """Count tokens using character approximation."""
        if not text:
            return 0
        
        # Add overhead for special tokens and formatting
        overhead = 5
        return max(1, int(len(text) / self.chars_per_token) + overhead)
    
    def count_messages_tokens(self, messages: List[Dict[str, str]]) -> int:
        """Count tokens in messages with role overhead."""
        if not messages:
            return 0
        
        total_tokens = 0
        for message in messages:
            # Add tokens for role specification
            role_overhead = 3
            content = message.get("content", "")
            total_tokens += self.count_tokens(content) + role_overhead
        
        # Add overhead for message structure
        structure_overhead = len(messages) * 2
        return total_tokens + structure_overhead


class TiktokenCounter(TokenCounterBase):
    """Token counter using tiktoken library."""
    
    def __init__(self, model_name: str):
        """
        Initialize with tiktoken encoding for the specified model.
        
        Args:
            model_name: Name of the model to get encoding for.
        """
        self.model_name = model_name
        self.encoding = None
        
        try:
            import tiktoken
            self.encoding = tiktoken.encoding_for_model(model_name)
            logger.info(f"Initialized TiktokenCounter for model: {model_name}")
        except ImportError:
            logger.warning("tiktoken not available, falling back to approximation")
            raise ImportError("tiktoken package is required for accurate token counting")
        except Exception as e:
            logger.warning(f"Failed to get encoding for {model_name}: {e}")
            raise ValueError(f"Unsupported model for tiktoken: {model_name}")
    
    @lru_cache(maxsize=1000)
    def count_tokens(self, text: str) -> int:
        """Count tokens using tiktoken (cached)."""
        if not text:
            return 0
        
        try:
            return len(self.encoding.encode(text))
        except Exception as e:
            logger.error(f"Error counting tokens with tiktoken: {e}")
            # Fallback to approximation
            return ApproximateTokenCounter().count_tokens(text)
    
    def count_messages_tokens(self, messages: List[Dict[str, str]]) -> int:
        """Count tokens in messages using OpenAI's message format."""
        if not messages:
            return 0
        
        try:
            # Convert messages to the format expected by the model
            formatted_text = self._format_messages_for_counting(messages)
            return self.count_tokens(formatted_text)
        except Exception as e:
            logger.error(f"Error counting message tokens: {e}")
            # Fallback to approximation
            return ApproximateTokenCounter().count_messages_tokens(messages)
    
    def _format_messages_for_counting(self, messages: List[Dict[str, str]]) -> str:
        """Format messages as they would appear to the model."""
        formatted_parts = []
        for message in messages:
            role = message.get("role", "user")
            content = message.get("content", "")
            formatted_parts.append(f"<|im_start|>{role}\n{content}<|im_end|>")
        return "\n".join(formatted_parts)


class TokenCounterFactory:
    """Factory for creating appropriate token counters."""
    
    # Model name mappings for tiktoken
    TIKTOKEN_MODEL_MAPPING = {
        "gpt-4": "gpt-4",
        "gpt-4-turbo": "gpt-4",
        "gpt-3.5-turbo": "gpt-3.5-turbo",
        "text-davinci-003": "text-davinci-003",
        # Add more mappings as needed
    }
    
    # Default characters per token for different model families
    CHARS_PER_TOKEN_MAPPING = {
        "gemini": 3.5,
        "deepseek": 4.0,
        "claude": 3.8,
        "qwen": 4.2,
        "llama": 4.0,
        "default": 4.0,
    }
    
    @classmethod
    def create_counter(cls, model_name: str) -> TokenCounterBase:
        """
        Create the most appropriate token counter for the given model.
        
        Args:
            model_name: Name of the LLM model.
            
        Returns:
            TokenCounterBase: The best available token counter.
        """
        logger.info(f"Creating token counter for model: {model_name}")
        
        # Try tiktoken first for supported models
        tiktoken_model = cls._get_tiktoken_model(model_name)
        if tiktoken_model:
            try:
                return TiktokenCounter(tiktoken_model)
            except (ImportError, ValueError) as e:
                logger.warning(f"Failed to create TiktokenCounter: {e}")
        
        # Fallback to approximation with model-specific scaling
        chars_per_token = cls._get_chars_per_token(model_name)
        return ApproximateTokenCounter(chars_per_token)
    
    @classmethod
    def _get_tiktoken_model(cls, model_name: str) -> Optional[str]:
        """Get tiktoken model name if supported."""
        model_lower = model_name.lower()
        
        # Direct mapping
        if model_name in cls.TIKTOKEN_MODEL_MAPPING:
            return cls.TIKTOKEN_MODEL_MAPPING[model_name]
        
        # Fuzzy matching for model families
        for pattern, tiktoken_model in cls.TIKTOKEN_MODEL_MAPPING.items():
            if pattern in model_lower:
                return tiktoken_model
        
        return None
    
    @classmethod
    def _get_chars_per_token(cls, model_name: str) -> float:
        """Get characters per token for approximation."""
        model_lower = model_name.lower()
        
        for pattern, chars_per_token in cls.CHARS_PER_TOKEN_MAPPING.items():
            if pattern in model_lower:
                return chars_per_token
        
        return cls.CHARS_PER_TOKEN_MAPPING["default"]


# Convenience functions
def count_tokens(text: str, model_name: str) -> int:
    """
    Count tokens in text for the specified model.
    
    Args:
        text: Text to count tokens for.
        model_name: Name of the LLM model.
        
    Returns:
        int: Number of tokens.
    """
    counter = TokenCounterFactory.create_counter(model_name)
    return counter.count_tokens(text)


def count_messages_tokens(messages: List[Dict[str, str]], model_name: str) -> int:
    """
    Count tokens in messages for the specified model.
    
    Args:
        messages: List of message dictionaries with 'role' and 'content' keys.
        model_name: Name of the LLM model.
        
    Returns:
        int: Number of tokens.
    """
    counter = TokenCounterFactory.create_counter(model_name)
    return counter.count_messages_tokens(messages)


def estimate_response_tokens(prompt_tokens: int, model_name: str) -> int:
    """
    Estimate response tokens based on prompt tokens and model.
    
    Args:
        prompt_tokens: Number of tokens in the prompt.
        model_name: Name of the LLM model.
        
    Returns:
        int: Estimated response tokens.
    """
    # Conservative estimation based on typical response patterns
    if "gpt-4" in model_name.lower():
        return min(prompt_tokens * 0.3, 2000)
    elif "gemini" in model_name.lower():
        return min(prompt_tokens * 0.4, 3000)
    elif "deepseek" in model_name.lower():
        return min(prompt_tokens * 0.2, 1500)
    else:
        return min(prompt_tokens * 0.25, 1000)