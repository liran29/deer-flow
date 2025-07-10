# Copyright (c) 2025 Bytedance Ltd. and/or its affiliates
# SPDX-License-Identifier: MIT

"""
用户交互处理器
支持前端交互和配置驱动的混合模式
"""

import asyncio
import logging
from typing import Dict, Any, Optional, Literal
from datetime import datetime

logger = logging.getLogger(__name__)


class UserInteractionHandler:
    """处理用户交互，支持前端通信和自动决策"""
    
    def __init__(self):
        self.pending_decisions: Dict[str, Dict[str, Any]] = {}
        self.user_responses: Dict[str, str] = {}
        
    async def request_user_decision(
        self,
        decision_id: str,
        decision_data: Dict[str, Any],
        timeout: int = 30
    ) -> str:
        """
        请求用户决策
        
        Args:
            decision_id: 决策ID
            decision_data: 决策相关数据
            timeout: 超时时间（秒）
            
        Returns:
            用户决策结果
        """
        
        # 存储待决策的信息
        self.pending_decisions[decision_id] = {
            "data": decision_data,
            "timestamp": datetime.now(),
            "timeout": timeout
        }
        
        # 发送到前端（通过WebSocket/SSE）
        await self._notify_frontend(decision_id, decision_data, timeout)
        
        # 等待用户响应或超时
        try:
            return await self._wait_for_response(decision_id, timeout)
        except asyncio.TimeoutError:
            # 超时后使用默认行为
            default_action = decision_data.get("default_action", "continue")
            logger.info(f"⏰ 用户决策超时，使用默认行为: {default_action}")
            return default_action
        finally:
            # 清理
            self.pending_decisions.pop(decision_id, None)
            self.user_responses.pop(decision_id, None)
    
    async def _notify_frontend(
        self, 
        decision_id: str, 
        decision_data: Dict[str, Any], 
        timeout: int
    ):
        """通知前端需要用户决策"""
        
        notification = {
            "type": "user_decision_required",
            "decision_id": decision_id,
            "data": decision_data,
            "timeout": timeout,
            "timestamp": datetime.now().isoformat()
        }
        
        # TODO: 通过WebSocket或SSE发送到前端
        # 例如：
        # await websocket_manager.broadcast(notification)
        # 或者：
        # await sse_manager.send_event("decision_required", notification)
        
        # 目前只记录日志
        logger.info(f"📢 通知前端用户决策请求: {decision_id}")
        logger.debug(f"决策数据: {decision_data}")
    
    async def _wait_for_response(self, decision_id: str, timeout: int) -> str:
        """等待用户响应"""
        
        for _ in range(timeout):
            # 检查是否有用户响应
            if decision_id in self.user_responses:
                response = self.user_responses[decision_id]
                logger.info(f"✅ 收到用户决策: {decision_id} -> {response}")
                return response
            
            # 等待1秒
            await asyncio.sleep(1)
        
        # 超时
        raise asyncio.TimeoutError(f"等待用户决策超时: {decision_id}")
    
    def provide_user_response(self, decision_id: str, response: str):
        """接收用户响应（通过API调用）"""
        if decision_id in self.pending_decisions:
            self.user_responses[decision_id] = response
            logger.info(f"📝 记录用户响应: {decision_id} -> {response}")
        else:
            logger.warning(f"⚠️ 收到无效决策ID的响应: {decision_id}")


# 全局实例
user_interaction_handler = UserInteractionHandler()


# 用于服务器端API的响应接收函数
async def handle_user_decision_response(decision_id: str, action: str):
    """处理前端发送的用户决策响应"""
    user_interaction_handler.provide_user_response(decision_id, action)
    return {"status": "success", "decision_id": decision_id, "action": action}