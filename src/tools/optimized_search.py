# Copyright (c) 2025 Bytedance Ltd. and/or its affiliates
# SPDX-License-Identifier: MIT

"""
优化的搜索工具包装器
自动应用查询优化策略，提升搜索质量
"""

import logging
import re
from typing import Any, Dict, List, Optional, Type
from langchain_core.tools import BaseTool
from pydantic import BaseModel, Field

from src.utils.query_optimizer import optimize_query_for_search, multi_query_search

logger = logging.getLogger(__name__)


class OptimizedSearchInput(BaseModel):
    """优化搜索工具的输入模式"""
    query: str = Field(description="The search query")


class OptimizedSearchTool(BaseTool):
    """
    优化的搜索工具包装器
    
    自动检测中文查询并进行翻译和关键词优化，
    执行多查询搜索策略以提升结果质量。
    """
    
    name: str = "optimized_web_search"
    description: str = (
        "Search the web with automatic query optimization. "
        "Automatically translates Chinese queries to English and extracts keywords for better results."
    )
    args_schema: Type[BaseModel] = OptimizedSearchInput
    base_tool: Optional[BaseTool] = None
    max_queries: int = 4
    max_results_per_query: int = 3
    
    def _run(self, query: str) -> List[Dict[str, Any]]:
        """同步执行优化搜索"""
        return self._execute_optimized_search(query)
    
    async def _arun(self, query: str) -> List[Dict[str, Any]]:
        """异步执行优化搜索"""
        # 在异步上下文中执行同步方法
        import asyncio
        loop = asyncio.get_event_loop()
        return await loop.run_in_executor(None, self._execute_optimized_search, query)
    
    def _execute_optimized_search(self, query: str) -> List[Dict[str, Any]]:
        """
        执行优化搜索的核心逻辑
        
        Args:
            query: 原始查询字符串
            
        Returns:
            优化并去重后的搜索结果列表
        """
        try:
            # 检测是否需要优化（包含中文或复杂问句）
            contains_chinese = bool(re.search(r'[\u4e00-\u9fff]', query))
            is_complex_query = len(query.split()) > 5 or '?' in query or '？' in query
            
            if contains_chinese or is_complex_query:
                logger.info(f"优化查询: '{query}' (中文={contains_chinese}, 复杂={is_complex_query})")
                
                # 应用查询优化
                optimized_queries = optimize_query_for_search(query, self.max_queries)
                logger.info(f"生成{len(optimized_queries)}个优化查询")
                
                # 创建搜索函数
                def search_func(q):
                    try:
                        # 调用基础工具的invoke方法
                        result = self.base_tool.invoke({"query": q})
                        # 确保返回列表格式
                        if isinstance(result, list):
                            return result
                        elif isinstance(result, dict):
                            return [result]
                        elif isinstance(result, str):
                            # 如果是字符串，包装为结果字典
                            return [{"content": result}]
                        else:
                            logger.warning(f"搜索返回异常格式: {type(result)}")
                            return []
                    except Exception as e:
                        logger.error(f"搜索执行失败: {e}")
                        return []
                
                # 执行多查询搜索
                results = multi_query_search(
                    search_func, 
                    optimized_queries, 
                    self.max_results_per_query
                )
                
                logger.info(f"优化搜索完成，返回{len(results)}个结果")
                return results
                
            else:
                # 简单查询直接执行
                logger.info(f"直接执行查询: '{query}'")
                result = self.base_tool.invoke({"query": query})
                
                # 统一返回格式
                if isinstance(result, list):
                    return result
                elif isinstance(result, dict):
                    return [result]
                elif isinstance(result, str):
                    return [{"content": result}]
                else:
                    logger.warning(f"搜索返回异常格式: {type(result)}")
                    return []
                    
        except Exception as e:
            logger.error(f"优化搜索失败: {e}，降级到原始搜索")
            # 降级到原始搜索
            try:
                result = self.base_tool.invoke({"query": query})
                if isinstance(result, list):
                    return result
                else:
                    return [result] if result else []
            except Exception as fallback_error:
                logger.error(f"降级搜索也失败: {fallback_error}")
                return []


def create_optimized_search_tool(
    base_tool: BaseTool,
    max_queries: int = 4,
    max_results_per_query: int = 3
) -> OptimizedSearchTool:
    """
    创建优化搜索工具的工厂函数
    
    Args:
        base_tool: 基础搜索工具
        max_queries: 最大优化查询数量
        max_results_per_query: 每个查询的最大结果数
        
    Returns:
        优化后的搜索工具
    """
    # 创建优化工具实例
    tool = OptimizedSearchTool()
    
    # 设置属性
    tool.base_tool = base_tool
    tool.max_queries = max_queries
    tool.max_results_per_query = max_results_per_query
    
    # 继承基础工具的名称和描述
    tool.name = base_tool.name or "optimized_web_search"
    tool.description = (
        f"{base_tool.description}\n"
        "Note: This tool automatically optimizes queries for better results, "
        "including Chinese-to-English translation and keyword extraction."
    )
    
    return tool