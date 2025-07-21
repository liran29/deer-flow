# Copyright (c) 2025 Bytedance Ltd. and/or its affiliates
# SPDX-License-Identifier: MIT

import logging
from typing import Dict, Any

from src.llms.llm import get_llm_by_type
from src.prompts.template import apply_prompt_template

logger = logging.getLogger(__name__)


def llm_summarize_search_result(content_item: Dict[str, Any], query: str) -> str:
    """使用LLM对单个搜索结果进行智能摘要
    
    Args:
        content_item: 搜索结果项，包含title、content等字段
        query: 原始查询字符串
        
    Returns:
        摘要后的内容字符串
    """
    try:
        # 检查是否是图片结果，如果是则跳过摘要
        if content_item.get('type') == 'image':
            logger.info("跳过图片结果的摘要")
            # 返回结构化结果，标记为无效
            return {"is_valid": False, "reason": "Image content"}
        # 准备模板变量
        title = content_item.get('title', '')
        content = content_item.get('content', '')
        
        # 调试输出模板变量
        logger.info(f"模板变量 - query: '{query}', title: '{title[:50]}...', content: '{content[:50]}...'")
        
        # 创建一个模拟的state用于模板渲染
        fake_state = {
            "messages": [],
            "query": query,
            "title": title,
            "content": content
        }
        
        # 使用apply_prompt_template函数渲染模板
        messages = apply_prompt_template("search_summarizer", fake_state)
        prompt = messages[0]["content"]  # 获取system prompt内容
        
        # 输出原始内容和提示词用于调试
        logger.info(f"准备摘要文章: {content_item.get('title', '')}")
        logger.info(f"原始内容长度: {len(content_item.get('content', ''))} 字符")
        logger.info(f"原始内容预览: {content_item.get('content', '')[:200]}...")
        logger.info(f"搜索结果所有字段: {list(content_item.keys())}")
        logger.info(f"原始内容URL: {content_item.get('url', '')}")
        logger.info(f"完整摘要提示词: {prompt}")  # 输出完整提示词
        
        # 调用LLM生成摘要
        response = get_llm_by_type("basic").invoke([
            {"role": "user", "content": prompt}
        ])
        
        response_text = response.content.strip()
        logger.info(f"LLM响应长度: {len(response_text)} 字符")
        logger.debug(f"LLM原始响应: {response_text[:200]}...")
        
        # 检查是否标记为无效内容
        if response_text.startswith("[INVALID]"):
            reason = response_text[9:].strip()  # 移除 "[INVALID]" 前缀
            logger.info(f"内容被标记为无效: {reason}")
            return {"is_valid": False, "reason": reason}
        else:
            # 内容有效，直接使用响应作为摘要
            logger.info(f"内容有效，摘要长度: {len(response_text)} 字符")
            return {"is_valid": True, "summary": response_text}
        
    except Exception as e:
        logger.error(f"LLM摘要失败: {str(e)}", exc_info=True)
        # 降级处理：返回截断的原始内容
        fallback_content = content_item.get('content', '')[:500]
        if len(content_item.get('content', '')) > 500:
            fallback_content += "..."
        logger.info(f"使用降级方案，返回截断内容: {len(fallback_content)} 字符")
        return {"is_valid": True, "summary": fallback_content}


def format_summarized_result(content_item: Dict[str, Any], summary: str) -> str:
    """格式化摘要后的搜索结果
    
    Args:
        content_item: 原始搜索结果项
        summary: 摘要内容
        
    Returns:
        格式化后的结果字符串
    """
    result_parts = [f"## {content_item.get('title', '未知标题')}"]
    result_parts.append(summary)
    
    # 添加图片信息
    if content_item.get('images'):
        result_parts.append(f"[包含 {len(content_item['images'])} 张相关图片]")
    
    # 添加来源信息
    if content_item.get('url'):
        result_parts.append(f"来源：{content_item['url']}")
    
    formatted_result = "\n\n".join(result_parts)
    
    # 调试输出
    logger.info(f"格式化结果长度: {len(formatted_result)} 字符")
    logger.debug(f"格式化结果预览: {formatted_result[:300]}...")
    
    return formatted_result