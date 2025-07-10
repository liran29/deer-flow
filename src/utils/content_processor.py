# Copyright (c) 2025 Bytedance Ltd. and/or its affiliates
# SPDX-License-Identifier: MIT

"""
智能内容处理器 - 为Researcher提供多层次内容优化
核心理念: 分层提取、智能压缩、语义保留
"""

import logging
import re
import hashlib
from typing import Dict, List, Optional, Tuple
from dataclasses import dataclass
from abc import ABC, abstractmethod

logger = logging.getLogger(__name__)


@dataclass
class ContentLayer:
    """内容层级定义"""
    layer_type: str  # 'summary', 'keywords', 'full'
    content: str
    token_estimate: int
    importance_score: float  # 0-1, 重要性评分


class ContentProcessor:
    """智能内容处理器"""
    
    def __init__(self, max_tokens_per_content: int = 1000):
        self.max_tokens_per_content = max_tokens_per_content
        self.content_cache: Dict[str, List[ContentLayer]] = {}
        
    def process_crawled_content(
        self, 
        url: str, 
        raw_content: str,
        available_tokens: int = None
    ) -> str:
        """
        智能处理爬取内容
        
        策略:
        1. 生成内容指纹进行缓存
        2. 多层次提取: 摘要 -> 关键词 -> 完整内容
        3. 根据可用token动态选择层级
        """
        content_hash = self._generate_content_hash(url, raw_content)
        
        # 检查缓存
        if content_hash in self.content_cache:
            return self._select_optimal_layer(
                self.content_cache[content_hash], 
                available_tokens
            )
        
        # 生成多层次内容
        layers = self._generate_content_layers(raw_content)
        self.content_cache[content_hash] = layers
        
        return self._select_optimal_layer(layers, available_tokens)
    
    def _generate_content_hash(self, url: str, content: str) -> str:
        """生成内容指纹"""
        return hashlib.md5(f"{url}:{content[:100]}".encode()).hexdigest()
    
    def _generate_content_layers(self, content: str) -> List[ContentLayer]:
        """生成多层次内容"""
        layers = []
        
        # Layer 1: 超简摘要 (50-100 tokens)
        summary = self._extract_summary(content, max_length=200)
        layers.append(ContentLayer(
            layer_type="ultra_summary",
            content=summary,
            token_estimate=len(summary) // 4,  # 粗略估算
            importance_score=0.9
        ))
        
        # Layer 2: 关键信息 (200-300 tokens)
        keywords = self._extract_key_information(content, max_length=800)
        layers.append(ContentLayer(
            layer_type="key_info",
            content=keywords,
            token_estimate=len(keywords) // 4,
            importance_score=0.8
        ))
        
        # Layer 3: 结构化摘要 (500-800 tokens)
        structured = self._extract_structured_content(content, max_length=2000)
        layers.append(ContentLayer(
            layer_type="structured",
            content=structured,
            token_estimate=len(structured) // 4,
            importance_score=0.7
        ))
        
        # Layer 4: 完整内容 (限制在max_tokens内)
        truncated_full = content[:self.max_tokens_per_content * 4]
        layers.append(ContentLayer(
            layer_type="full",
            content=truncated_full,
            token_estimate=len(truncated_full) // 4,
            importance_score=0.6
        ))
        
        return layers
    
    def _select_optimal_layer(
        self, 
        layers: List[ContentLayer], 
        available_tokens: Optional[int]
    ) -> str:
        """根据可用token选择最优层级"""
        if available_tokens is None:
            available_tokens = self.max_tokens_per_content
        
        # 选择最详细但不超过限制的层级
        for layer in reversed(layers):  # 从最详细开始
            if layer.token_estimate <= available_tokens:
                logger.debug(f"Selected {layer.layer_type} layer with {layer.token_estimate} tokens")
                return layer.content
        
        # 如果都超限，返回最简摘要
        return layers[0].content
    
    def _extract_summary(self, content: str, max_length: int) -> str:
        """提取超简摘要"""
        # 简单策略: 取前几段并压缩
        paragraphs = content.split('\n\n')[:3]
        summary = ' '.join(paragraphs)
        
        if len(summary) > max_length:
            summary = summary[:max_length] + "..."
        
        return f"📝 **页面摘要**: {summary}"
    
    def _extract_key_information(self, content: str, max_length: int) -> str:
        """提取关键信息"""
        # 提取标题、列表、重要数据
        key_info = []
        
        # 提取标题
        titles = re.findall(r'^#{1,3}\s+(.+)$', content, re.MULTILINE)
        if titles:
            key_info.append(f"🏷️ **主要章节**: {', '.join(titles[:5])}")
        
        # 提取数字和统计
        numbers = re.findall(r'\b\d+(?:,\d{3})*(?:\.\d+)?\s*(?:%|万|亿|billion|million)\b', content)
        if numbers:
            key_info.append(f"📊 **关键数据**: {', '.join(numbers[:10])}")
        
        # 提取列表项
        lists = re.findall(r'^[-*+]\s+(.+)$', content, re.MULTILINE)
        if lists:
            key_info.append(f"📋 **要点**: {', '.join(lists[:5])}")
        
        result = '\n'.join(key_info)
        if len(result) > max_length:
            result = result[:max_length] + "..."
        
        return result
    
    def _extract_structured_content(self, content: str, max_length: int) -> str:
        """提取结构化内容"""
        sections = []
        
        # 按段落分析
        paragraphs = content.split('\n\n')
        for i, para in enumerate(paragraphs[:10]):  # 最多处理10段
            if len(para.strip()) > 50:  # 忽略太短的段落
                # 压缩段落
                compressed = self._compress_paragraph(para)
                sections.append(f"**第{i+1}段**: {compressed}")
        
        result = '\n\n'.join(sections)
        if len(result) > max_length:
            result = result[:max_length] + "..."
        
        return result
    
    def _compress_paragraph(self, paragraph: str) -> str:
        """压缩段落"""
        # 移除冗余词汇和短语
        compressed = paragraph
        
        # 移除常见的填充词
        filler_words = ['的话', '其实', '基本上', '事实上', '一般来说', '总的来说']
        for word in filler_words:
            compressed = compressed.replace(word, '')
        
        # 如果还是太长，取前半部分
        if len(compressed) > 200:
            compressed = compressed[:200] + "..."
        
        return compressed.strip()


class MultimodalContentProcessor(ContentProcessor):
    """多媒体内容处理器"""
    
    def process_with_images(
        self, 
        url: str, 
        content: str, 
        images: List[str],
        available_tokens: int = None
    ) -> Tuple[str, List[str]]:
        """处理包含图片的内容"""
        
        # 处理文本内容
        text_content = self.process_crawled_content(url, content, available_tokens)
        
        # 智能选择图片
        selected_images = self._select_important_images(images, max_count=3)
        
        return text_content, selected_images
    
    def _select_important_images(self, images: List[str], max_count: int) -> List[str]:
        """智能选择重要图片"""
        if len(images) <= max_count:
            return images
        
        # 简单策略: 优先选择可能包含重要信息的图片
        scored_images = []
        for img in images:
            score = self._score_image_importance(img)
            scored_images.append((img, score))
        
        # 按得分排序并选择top N
        scored_images.sort(key=lambda x: x[1], reverse=True)
        return [img for img, _ in scored_images[:max_count]]
    
    def _score_image_importance(self, image_url: str) -> float:
        """为图片重要性评分"""
        score = 0.5  # 基础分数
        
        # 包含chart, graph, diagram等关键词的图片更重要
        important_keywords = ['chart', 'graph', 'diagram', 'data', 'statistics']
        for keyword in important_keywords:
            if keyword in image_url.lower():
                score += 0.2
        
        # 避免广告和装饰性图片
        ad_keywords = ['ads', 'banner', 'logo', 'avatar']
        for keyword in ad_keywords:
            if keyword in image_url.lower():
                score -= 0.3
        
        return max(0.0, min(1.0, score))


# 全局实例
content_processor = ContentProcessor()
multimodal_processor = MultimodalContentProcessor()