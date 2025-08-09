# Copyright (c) 2025 Bytedance Ltd. and/or its affiliates
# SPDX-License-Identifier: MIT

"""
选择性爬取工具
基于搜索概览结果选择性地爬取特定URL的内容
专门用于researcher的"先概览后爬取"流程
"""

import logging
from typing import Annotated, Dict, Optional
from langchain_core.tools import tool

from src.crawler import Crawler

logger = logging.getLogger(__name__)


@tool
def selective_crawl_tool(
    url: Annotated[str, "The URL to crawl, selected from search overview results"],
    max_content_length: Annotated[Optional[int], "Maximum content length to return (default: 5000 chars)"] = 5000,
) -> Dict[str, str]:
    """
    Selectively crawl a specific URL based on search overview analysis.
    
    This tool is designed for the 'analyze first, crawl selectively' workflow:
    1. First use search_overview to get lightweight results
    2. Analyze which URLs are most relevant
    3. Use this tool to crawl ONLY the 2-3 most relevant URLs
    
    Returns a dictionary with:
    - url: The crawled URL
    - title: Page title
    - content: Crawled content (truncated to max_content_length)
    - status: Success or error message
    """
    try:
        logger.info(f"Selective crawl initiated for: {url}")
        
        # 验证URL
        if not url or not url.startswith(('http://', 'https://')):
            error_msg = f"Invalid URL: {url}. Must be a complete URL starting with http:// or https://"
            logger.error(error_msg)
            return {
                "url": url,
                "status": "error",
                "error": error_msg
            }
        
        # 执行爬取
        crawler = Crawler()
        article = crawler.crawl(url)
        
        # 获取内容并限制长度
        content = article.to_markdown()
        if max_content_length and len(content) > max_content_length:
            logger.info(f"Truncating content from {len(content)} to {max_content_length} chars")
            content = content[:max_content_length] + "\n\n[Content truncated for token optimization]"
        
        logger.info(f"Selective crawl successful for: {url}, content length: {len(content)}")
        
        return {
            "url": url,
            "title": article.title if hasattr(article, 'title') else "No title",
            "content": content,
            "status": "success",
            "content_length": len(content)
        }
        
    except Exception as e:
        error_msg = f"Failed to crawl {url}: {repr(e)}"
        logger.error(error_msg)
        return {
            "url": url,
            "status": "error",
            "error": error_msg
        }


@tool
def batch_selective_crawl_tool(
    urls: Annotated[list, "List of URLs to crawl (maximum 3 URLs)"],
    max_content_length_per_url: Annotated[Optional[int], "Maximum content length per URL (default: 3000 chars)"] = 3000,
) -> Dict[str, any]:
    """
    Batch crawl multiple URLs selected from search overview.
    
    IMPORTANT: Only crawl 2-3 most relevant URLs to optimize token usage.
    This tool enforces a maximum of 3 URLs per batch.
    
    Returns a dictionary with:
    - results: List of crawl results for each URL
    - total_crawled: Number of URLs successfully crawled
    - total_content_length: Combined content length
    """
    try:
        # 限制URL数量
        if len(urls) > 3:
            logger.warning(f"Too many URLs ({len(urls)}), limiting to first 3 for token optimization")
            urls = urls[:3]
        
        results = []
        total_content_length = 0
        successful_crawls = 0
        
        for url in urls:
            logger.info(f"Batch crawling URL {len(results)+1}/{len(urls)}: {url}")
            
            # 使用selective_crawl_tool爬取单个URL
            result = selective_crawl_tool.invoke({
                "url": url,
                "max_content_length": max_content_length_per_url
            })
            
            results.append(result)
            
            if result.get("status") == "success":
                successful_crawls += 1
                total_content_length += result.get("content_length", 0)
        
        logger.info(f"Batch crawl completed: {successful_crawls}/{len(urls)} successful, total content: {total_content_length} chars")
        
        return {
            "results": results,
            "total_crawled": successful_crawls,
            "total_urls": len(urls),
            "total_content_length": total_content_length,
            "optimization_note": "Content limited for token optimization"
        }
        
    except Exception as e:
        error_msg = f"Batch crawl failed: {repr(e)}"
        logger.error(error_msg)
        return {
            "results": [],
            "error": error_msg
        }