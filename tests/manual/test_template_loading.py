#!/usr/bin/env python3
"""
测试模板加载功能
验证查询优化中的模板是否正确加载
"""

import sys
from pathlib import Path

# 添加src目录到系统路径
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from src.prompts.template import apply_prompt_template

def test_query_translator_template():
    """测试查询翻译模板"""
    print("=== 测试查询翻译模板 ===")
    
    template_state = {
        "chinese_query": "测试查询",
        "messages": []
    }
    
    try:
        messages = apply_prompt_template("query_translator", template_state)
        print(f"模板加载成功")
        print(f"系统提示词长度: {len(messages[0]['content'])} 字符")
        print(f"系统提示词前100字符: {messages[0]['content'][:100]}...")
        return True
    except Exception as e:
        print(f"模板加载失败: {e}")
        return False

def test_keyword_extractor_template():
    """测试关键词提取模板"""
    print("\n=== 测试关键词提取模板 ===")
    
    template_state = {
        "query": "test query",
        "max_keywords": 4,
        "current_year": 2025,
        "current_month": 8,
        "recent_years_str": "2024 2025",
        "messages": []
    }
    
    try:
        messages = apply_prompt_template("keyword_extractor", template_state)
        print(f"模板加载成功")
        print(f"系统提示词长度: {len(messages[0]['content'])} 字符")
        print(f"系统提示词前100字符: {messages[0]['content'][:100]}...")
        return True
    except Exception as e:
        print(f"模板加载失败: {e}")
        return False

def main():
    """主测试函数"""
    print("=== 模板加载测试 ===")
    
    success_count = 0
    
    if test_query_translator_template():
        success_count += 1
    
    if test_keyword_extractor_template():
        success_count += 1
    
    print(f"\n=== 测试结果 ===")
    print(f"成功: {success_count}/2")
    print(f"状态: {'通过' if success_count == 2 else '失败'}")

if __name__ == "__main__":
    main()