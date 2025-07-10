# Copyright (c) 2025 Bytedance Ltd. and/or its affiliates
# SPDX-License-Identifier: MIT

"""
内容安全错误处理器
处理LLM API的内容安全检查错误，提供用户交互选项
"""

import logging
import asyncio
from typing import Optional, Dict, Any, Literal
from datetime import datetime
from openai import BadRequestError

logger = logging.getLogger(__name__)


class ContentSafetyError(Exception):
    """内容安全错误"""
    def __init__(self, message: str, original_error: Exception = None):
        super().__init__(message)
        self.original_error = original_error
        self.timestamp = datetime.now()


class ContentSafetyHandler:
    """处理内容安全相关错误"""
    
    def __init__(self):
        self.error_history: list[Dict[str, Any]] = []
        self.user_preferences: Dict[str, str] = {}
        self.config = self._load_config()
    
    def _load_config(self) -> Dict[str, Any]:
        """加载内容安全配置"""
        try:
            from src.config import load_yaml_config
            config = load_yaml_config("conf.yaml")
            return config.get("CONTENT_SAFETY", {
                "enabled": True,
                "default_action": "continue",
                "auto_continue_timeout": 30,
                "notify_user": True,
                "strategies": {}
            })
        except Exception as e:
            logger.warning(f"加载内容安全配置失败: {e}")
            return {
                "enabled": True,
                "default_action": "continue", 
                "auto_continue_timeout": 30,
                "notify_user": True,
                "strategies": {}
            }
        
    def is_content_safety_error(self, error: Exception) -> bool:
        """判断是否为内容安全错误"""
        if isinstance(error, BadRequestError):
            error_message = str(error)
            safety_keywords = [
                "Content Exists Risk",
                "content safety",
                "content moderation",
                "inappropriate content",
                "harmful content"
            ]
            return any(keyword in error_message for keyword in safety_keywords)
        return False
    
    def extract_error_details(self, error: BadRequestError) -> Dict[str, Any]:
        """提取错误详情"""
        try:
            # 尝试从错误响应中提取详细信息
            if hasattr(error, 'response') and hasattr(error.response, 'json'):
                error_data = error.response.json()
                return {
                    "message": error_data.get("error", {}).get("message", "Unknown error"),
                    "type": error_data.get("error", {}).get("type", "unknown"),
                    "code": error_data.get("error", {}).get("code", "unknown"),
                    "raw_error": str(error)
                }
        except:
            pass
        
        # 降级处理
        return {
            "message": str(error),
            "type": "content_safety_error",
            "code": "content_exists_risk",
            "raw_error": str(error)
        }
    
    def log_error(self, error_details: Dict[str, Any], context: Dict[str, Any] = None):
        """记录错误历史"""
        error_record = {
            "timestamp": datetime.now().isoformat(),
            "error": error_details,
            "context": context or {},
        }
        self.error_history.append(error_record)
        
        # 保持历史记录在合理范围内
        if len(self.error_history) > 100:
            self.error_history = self.error_history[-50:]
    
    async def handle_content_safety_error(
        self,
        error: BadRequestError,
        context: Dict[str, Any] = None,
        auto_continue_timeout: Optional[int] = None
    ) -> Literal["continue"]:
        """
        处理内容安全错误，自动继续执行
        
        Args:
            error: 原始错误
            context: 错误上下文（如当前任务、消息等）
            auto_continue_timeout: 保留参数，向后兼容
            
        Returns:
            固定返回 "continue"，自动继续执行
        """
        error_details = self.extract_error_details(error)
        self.log_error(error_details, context)
        
        # 记录详细日志但不需要用户干预
        logger.warning(f"🚨 内容安全检查失败，自动过滤内容: {error_details['message']}")
        if context:
            logger.info(f"错误上下文: {context}")
        
        # 如果内容安全处理被禁用，直接抛出错误
        if not self.config.get("enabled", True):
            raise error
        
        # 记录错误类型用于统计
        error_type = error_details.get("code", "unknown").lower()
        
        # 记录处理信息
        logger.info(f"📝 内容安全处理记录:")
        logger.info(f"   错误类型: {error_type}")
        logger.info(f"   处理方式: 自动过滤并继续")
        logger.info(f"   建议: {self._get_recommendation(error_type)}")
        
        # 固定返回continue，自动继续执行
        return "continue"
    
    def _get_recommendation(self, error_type: str) -> str:
        """获取针对不同错误类型的建议"""
        recommendations = {
            "content_exists_risk": "建议调整查询关键词或换个角度描述问题",
            "inappropriate_content": "请确保内容符合使用规范",
            "harmful_content": "请检查内容是否包含有害信息"
        }
        return recommendations.get(error_type, "请检查内容并重新尝试")


# 全局实例
content_safety_handler = ContentSafetyHandler()


def wrap_with_content_safety(func):
    """装饰器：为函数添加内容安全错误处理"""
    async def wrapper(*args, **kwargs):
        try:
            return await func(*args, **kwargs)
        except BadRequestError as e:
            if content_safety_handler.is_content_safety_error(e):
                # 提取上下文信息
                context = {
                    "function": func.__name__,
                    "args": str(args)[:200],  # 限制长度
                    "kwargs": str(kwargs)[:200]
                }
                
                # 处理错误并获取用户决策
                action = await content_safety_handler.handle_content_safety_error(
                    e,
                    context,
                    auto_continue_timeout=30  # 30秒后自动继续
                )
                
                if action == "continue":
                    # 返回一个安全的默认响应
                    return {
                        "content": "由于内容安全限制，此部分内容无法处理。请调整查询内容后重试。",
                        "error": "content_safety_filtered"
                    }
                elif action == "retry":
                    # 重试逻辑（需要修改内容）
                    # TODO: 实现内容修改逻辑
                    raise e
                else:  # stop
                    raise ContentSafetyError("用户选择停止任务", e)
            else:
                raise
        except Exception as e:
            # 非内容安全错误，直接抛出
            raise
    
    return wrapper if asyncio.iscoroutinefunction(func) else func