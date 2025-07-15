# Copyright (c) 2025 Bytedance Ltd. and/or its affiliates
# SPDX-License-Identifier: MIT

import logging
from typing import Dict, Any

from src.llms.llm import get_llm_by_type
from src.prompts.template import get_prompt_template
from jinja2 import Environment, Template

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
        # 获取摘要提示词模板
        template_str = get_prompt_template("search_summarizer")
        template = Template(template_str)
        
        # 渲染提示词
        prompt = template.render(
            query=query,
            title=content_item.get('title', ''),
            content=content_item.get('content', '')
        )
        
        # 调用LLM生成摘要
        response = get_llm_by_type("basic").invoke([
            {"role": "user", "content": prompt}
        ])
        
        summary = response.content.strip()
        logger.debug(f"搜索结果摘要成功: {content_item.get('title', '')[:50]}...")
        
        return summary
        
    except Exception as e:
        logger.error(f"LLM摘要失败: {str(e)}", exc_info=True)
        # 降级处理：返回截断的原始内容
        fallback_content = content_item.get('content', '')[:500]
        if len(content_item.get('content', '')) > 500:
            fallback_content += "..."
        logger.info(f"使用降级方案，返回截断内容: {len(fallback_content)} 字符")
        return fallback_content


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
    
    return "\n\n".join(result_parts)