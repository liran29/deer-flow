# Copyright (c) 2025 Bytedance Ltd. and/or its affiliates
# SPDX-License-Identifier: MIT

"""
查询优化工具模块

提供通用的搜索查询优化功能，包括：
1. 中文到英文翻译
2. 问句到关键词提取  
3. 时效性年份处理
4. 多查询策略生成

设计为通用组件，可在background_investigation和researcher等节点中复用。
"""

import logging
import re
from datetime import datetime
from typing import List, Dict, Optional, Any
from urllib.parse import urlparse

from src.llms.llm import get_llm_by_type
from src.prompts.template import apply_prompt_template

logger = logging.getLogger(__name__)


def get_current_time_context() -> Dict[str, Any]:
    """获取当前时间上下文"""
    current_year = datetime.now().year
    current_month = datetime.now().month
    
    return {
        "current_year": current_year,
        "current_month": current_month,
        "recent_years": [current_year, current_year - 1],
        "is_preparation_season": current_month >= 8  # 8月开始是下年度准备季
    }


def optimize_query_unified(query: str, max_queries: int = 4) -> List[str]:
    """统一的查询优化 - 一次LLM调用处理翻译和关键词提取"""
    try:
        time_context = get_current_time_context()
        recent_years_str = " ".join(map(str, time_context["recent_years"]))
        
        # 创建用于模板渲染的状态
        template_state = {
            "query": query,
            "max_queries": max_queries,
            "current_year": time_context["current_year"],
            "current_month": time_context["current_month"],
            "recent_years_str": recent_years_str,
            "messages": []  # apply_prompt_template需要这个字段
        }
        
        # 使用统一的优化模板
        messages = apply_prompt_template("query_optimizer", template_state)
        prompt = messages[0]["content"]
        
        llm = get_llm_by_type("basic")
        response = llm.invoke([{"role": "user", "content": prompt}])
        
        # 解析响应，提取优化后的查询
        lines = response.content.strip().split('\n')
        optimized_queries = []
        
        for line in lines:
            line = line.strip()
            if line and not line.startswith(('Example', 'Output', 'Guidelines', 'Your task')):
                # 移除序号和项目符号
                cleaned_line = re.sub(r'^\d+[.)\s]*', '', line)
                cleaned_line = re.sub(r'^[-*•]\s*', '', cleaned_line)
                cleaned_line = cleaned_line.strip('"\'')  # 移除引号
                
                if cleaned_line and len(cleaned_line.split()) <= 8:  # 限制长度
                    optimized_queries.append(cleaned_line)
        
        # 确保返回指定数量的查询
        optimized_queries = optimized_queries[:max_queries]
        
        if not optimized_queries:
            # 降级处理：返回原查询
            logger.warning("LLM查询优化失败，使用原查询")
            optimized_queries = [query.replace('？', '').replace('?', '')]
        
        logger.info(f"查询优化: '{query}' -> {optimized_queries}")
        return optimized_queries
        
    except Exception as e:
        logger.error(f"查询优化失败: {str(e)}")
        # 降级处理：返回原查询
        return [query]


def optimize_query_for_search(user_query: str, max_queries: int = 4) -> List[str]:
    """优化用户查询为搜索关键词组合
    
    Args:
        user_query: 用户的原始查询
        max_queries: 最大生成的查询数量
        
    Returns:
        优化后的搜索关键词列表
    """
    logger.info(f"开始统一查询优化: '{user_query}'")
    
    # 使用统一的优化函数
    optimized_queries = optimize_query_unified(user_query, max_queries)
    
    logger.info(f"查询优化完成，生成了{len(optimized_queries)}个优化查询")
    return optimized_queries


def multi_query_search(search_func, queries: List[str], max_results_per_query: int = 3) -> List[Dict]:
    """执行多查询搜索策略
    
    Args:
        search_func: 搜索函数（如Tavily search tool的invoke方法）
        queries: 优化后的查询列表
        max_results_per_query: 每个查询的最大结果数
        
    Returns:
        合并并去重后的搜索结果
    """
    all_results = []
    
    logger.info(f"开始执行多查询搜索，共{len(queries)}个查询")
    
    for i, query in enumerate(queries, 1):
        try:
            logger.info(f"执行第{i}个查询: '{query}'")
            results = search_func(query)
            
            if isinstance(results, list):
                logger.info(f"第{i}个查询返回{len(results)}个结果")
                all_results.extend(results)
            else:
                logger.warning(f"第{i}个查询返回异常格式: {type(results)}")
                
        except Exception as e:
            logger.error(f"第{i}个查询执行失败: {str(e)}")
            continue
    
    # 去重处理（基于URL）
    unique_results = remove_duplicate_results(all_results)
    
    logger.info(f"多查询搜索完成，去重前{len(all_results)}个结果，去重后{len(unique_results)}个结果")
    return unique_results


def remove_duplicate_results(results: List[Dict]) -> List[Dict]:
    """去除重复的搜索结果（基于URL）"""
    seen_urls = set()
    unique_results = []
    
    for result in results:
        if not isinstance(result, dict):
            continue
            
        url = result.get('url', '')
        if not url:
            # 没有URL的结果也保留，但用title作为去重标准
            title = result.get('title', '')
            if title and title not in seen_urls:
                seen_urls.add(title)
                unique_results.append(result)
        else:
            # 标准化URL进行去重
            normalized_url = normalize_url(url)
            if normalized_url not in seen_urls:
                seen_urls.add(normalized_url)
                unique_results.append(result)
    
    return unique_results


def normalize_url(url: str) -> str:
    """标准化URL用于去重"""
    try:
        parsed = urlparse(url)
        
        # 对于YouTube等视频网站，保留视频ID参数
        if 'youtube.com' in parsed.netloc or 'youtu.be' in parsed.netloc:
            # 保留v参数（视频ID）
            if parsed.query:
                import urllib.parse
                params = urllib.parse.parse_qs(parsed.query)
                if 'v' in params:
                    video_id = params['v'][0]
                    normalized = f"{parsed.scheme}://{parsed.netloc}{parsed.path}?v={video_id}"
                    return normalized.lower()
        
        # 对于其他网站，移除查询参数但保留路径
        normalized = f"{parsed.scheme}://{parsed.netloc}{parsed.path}"
        return normalized.lower()
    except:
        return url.lower()


def evaluate_query_optimization_effect(original_query: str, optimized_queries: List[str]) -> Dict[str, Any]:
    """评估查询优化效果（用于调试和监控）"""
    
    analysis = {
        "original_query": original_query,
        "optimized_queries": optimized_queries,
        "optimization_count": len(optimized_queries),
        "has_translation": bool(re.search(r'[\u4e00-\u9fff]', original_query)),
        "keyword_density": {},
        "time_context_added": any("2024" in q or "2025" in q for q in optimized_queries)
    }
    
    # 分析关键词密度
    for query in optimized_queries:
        words = query.lower().split()
        for word in words:
            if len(word) > 2:  # 忽略短词
                analysis["keyword_density"][word] = analysis["keyword_density"].get(word, 0) + 1
    
    return analysis


# 为了方便测试，提供一个完整的优化和搜索流程
def optimize_and_search(search_func, user_query: str, max_queries: int = 4, max_results_per_query: int = 3) -> tuple:
    """完整的查询优化和搜索流程
    
    Returns:
        (optimized_queries, search_results, analysis)
    """
    # 优化查询
    optimized_queries = optimize_query_for_search(user_query, max_queries)
    
    # 执行搜索
    search_results = multi_query_search(search_func, optimized_queries, max_results_per_query)
    
    # 生成分析报告
    analysis = evaluate_query_optimization_effect(user_query, optimized_queries)
    
    return optimized_queries, search_results, analysis