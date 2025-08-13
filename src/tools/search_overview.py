# Copyright (c) 2025 Bytedance Ltd. and/or its affiliates
# SPDX-License-Identifier: MIT

"""
搜索概览工具
提供轻量级的搜索结果概览，不包含完整内容，用于先分析后爬取的流程
"""

import logging
from typing import Any, Dict, List, Optional, Type
from langchain_core.tools import BaseTool
from pydantic import BaseModel, Field

from src.utils.query_optimizer import optimize_query_for_search, multi_query_search
from src.tools.search import get_web_search_tool

logger = logging.getLogger(__name__)


class SearchOverviewInput(BaseModel):
    """搜索概览工具的输入模式"""
    query: str = Field(description="The search query to get an overview of results")


class SearchOverviewTool(BaseTool):
    """
    搜索概览工具
    
    返回搜索结果的轻量级概览，包含标题、摘要和URL，
    但不包含完整的网页内容（raw_content）。
    用于实现"先概览后爬取"的优化流程。
    """
    
    name: str = "search_overview"
    description: str = (
        "Get a lightweight overview of search results without full content. "
        "Returns titles, snippets, and URLs for analysis before selective crawling. "
        "This tool is optimized for the 'analyze first, crawl selectively' workflow."
    )
    args_schema: Type[BaseModel] = SearchOverviewInput
    
    def _run(self, query: str) -> List[Dict[str, Any]]:
        """同步执行搜索概览"""
        return self._execute_search_overview(query)
    
    async def _arun(self, query: str) -> List[Dict[str, Any]]:
        """异步执行搜索概览"""
        import asyncio
        loop = asyncio.get_event_loop()
        return await loop.run_in_executor(None, self._execute_search_overview, query)
    
    def _execute_search_overview(self, query: str) -> List[Dict[str, Any]]:
        """
        执行搜索概览的核心逻辑
        
        Returns:
            搜索结果概览列表，每个结果包含：
            - title: 标题
            - snippet: 内容摘要
            - url: 可爬取的URL
            - relevance_hint: 相关性提示
        """
        try:
            logger.info(f"执行搜索概览: '{query}'")
            
            # 直接使用用户的查询，不做内部优化（优化逻辑在提示词中）
            from src.tools.search import LoggedTavilySearch
            
            # 创建轻量级搜索工具
            light_search = LoggedTavilySearch(
                max_results=6,  # 稍微增加结果数量
                include_raw_content=False,  # 关键：不包含完整内容
                include_images=True,  # 保持图片支持，用户体验重要
                include_image_descriptions=True,  # 图片描述也很有价值
            )
            
            result = light_search.invoke(query)
            all_results = result if isinstance(result, list) else [result]
            
            # 保持结构化数据，但添加可读的摘要
            overview_results = []
            summary_text = f"Found {len(all_results)} results for '{query}':\n\n"
            
            for i, result in enumerate(all_results, 1):
                title = result.get("title", "No title")
                snippet = result.get("content", "")[:500]
                url = result.get("url", "")
                relevance = self._generate_relevance_hint(result, query)
                
                # 结构化数据（便于LLM处理）
                overview_item = {
                    "index": i,
                    "title": title,
                    "snippet": snippet,
                    "url": url,
                    "relevance_hint": relevance
                }
                overview_results.append(overview_item)
                
                # 人类可读的摘要
                summary_text += f"{i}. {title}\n   {url}\n   Relevance: {relevance}\n\n"
            
            logger.info(f"搜索概览完成，返回{len(overview_results)}个结果概览")
            
            # 返回结构化数据 + 可读摘要
            return {
                "overview": overview_results,
                "summary": summary_text,
                "usage": {
                    "hint": "Analyze results and select 2-3 most relevant URLs to crawl",
                    "total_results": len(overview_results)
                }
            }
            
        except Exception as e:
            logger.error(f"搜索概览失败: {e}")
            return f"Search overview failed: {str(e)}"
    
    def _generate_relevance_hint(self, result: Dict, query: str) -> str:
        """生成相关性提示"""
        title = result.get("title", "").lower()
        content = result.get("content", "").lower()
        query_lower = query.lower()
        
        # 简单的关键词匹配评分
        keywords = query_lower.split()
        matches = sum(1 for kw in keywords if kw in title or kw in content)
        
        if matches >= len(keywords) * 0.7:
            return "High relevance - consider crawling"
        elif matches >= len(keywords) * 0.4:
            return "Medium relevance - review snippet first"
        else:
            return "Low relevance - snippet may be sufficient"


def create_search_overview_tool() -> SearchOverviewTool:
    """
    创建搜索概览工具的工厂函数
    
    Returns:
        搜索概览工具实例
    """
    return SearchOverviewTool()