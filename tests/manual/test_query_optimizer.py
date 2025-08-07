#!/usr/bin/env python3
"""
测试查询优化功能
验证中文查询翻译、关键词提取和多查询搜索策略
"""

import sys
from pathlib import Path

# 添加src目录到系统路径
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from src.utils.query_optimizer import (
    optimize_query_for_search,
    translate_to_english, 
    extract_search_keywords,
    multi_query_search,
    evaluate_query_optimization_effect
)
from src.tools.search import get_web_search_tool

def test_translation():
    """测试中文到英文翻译功能"""
    print("=== 测试中文翻译功能 ===")
    
    test_queries = [
        "沃尔玛在线商城最近推出了哪些新的热门圣诞节装饰品商品类别？",
        "亚马逊2024年最受欢迎的电子产品有哪些？",
        "苹果公司最新iPhone的技术规格和价格信息"
    ]
    
    for i, query in enumerate(test_queries, 1):
        print(f"\n--- 测试 {i} ---")
        print(f"原查询: {query}")
        try:
            translated = translate_to_english(query)
            print(f"翻译结果: {translated}")
        except Exception as e:
            print(f"翻译失败: {e}")

def test_keyword_extraction():
    """测试关键词提取功能"""
    print("\n=== 测试关键词提取功能 ===")
    
    test_queries = [
        "Walmart Christmas decorations new categories 2024",
        "Amazon popular electronics 2024",
        "Apple iPhone latest specifications and pricing"
    ]
    
    for i, query in enumerate(test_queries, 1):
        print(f"\n--- 测试 {i} ---")
        print(f"英文查询: {query}")
        try:
            keywords = extract_search_keywords(query, max_keywords=4)
            print(f"提取的关键词组合:")
            for j, keyword in enumerate(keywords, 1):
                print(f"  {j}. {keyword}")
        except Exception as e:
            print(f"关键词提取失败: {e}")

def test_full_optimization():
    """测试完整的查询优化流程"""
    print("\n=== 测试完整查询优化流程 ===")
    
    original_query = "沃尔玛在线商城最近推出了哪些新的热门圣诞节装饰品商品类别？"
    
    print(f"原始查询: {original_query}")
    
    try:
        # 完整优化
        optimized_queries = optimize_query_for_search(original_query, max_queries=4)
        
        print(f"\n优化后的查询数量: {len(optimized_queries)}")
        print("优化查询列表:")
        for i, query in enumerate(optimized_queries, 1):
            print(f"  {i}. {query}")
        
        # 生成分析报告
        analysis = evaluate_query_optimization_effect(original_query, optimized_queries)
        
        print(f"\n=== 优化分析报告 ===")
        print(f"包含翻译: {analysis['has_translation']}")
        print(f"添加时间上下文: {analysis['time_context_added']}")
        print(f"优化查询数量: {analysis['optimization_count']}")
        
        print(f"\n关键词密度分析:")
        for word, count in sorted(analysis['keyword_density'].items(), key=lambda x: x[1], reverse=True)[:10]:
            print(f"  {word}: {count}")
            
        return optimized_queries
        
    except Exception as e:
        print(f"完整优化失败: {e}")
        return []

def test_multi_query_search():
    """测试多查询搜索策略"""
    print("\n=== 测试多查询搜索策略 ===")
    
    # 先获取优化查询
    optimized_queries = test_full_optimization()
    
    if not optimized_queries:
        print("无法进行搜索测试，优化查询失败")
        return
    
    print(f"\n开始测试多查询搜索...")
    
    try:
        # 创建搜索函数
        search_tool = get_web_search_tool(max_search_results=3)
        search_func = lambda q: search_tool.invoke(q)
        
        # 执行多查询搜索
        results = multi_query_search(search_func, optimized_queries, max_results_per_query=3)
        
        print(f"\n搜索结果分析:")
        print(f"总结果数量: {len(results)}")
        
        # 分析域名分布
        domains = {}
        valid_results = 0
        
        for result in results:
            if isinstance(result, dict) and result.get('url'):
                valid_results += 1
                from urllib.parse import urlparse
                domain = urlparse(result['url']).netloc
                domains[domain] = domains.get(domain, 0) + 1
        
        print(f"有效结果数量: {valid_results}")
        print(f"域名分布:")
        for domain, count in sorted(domains.items(), key=lambda x: x[1], reverse=True):
            print(f"  {domain}: {count} 个结果")
        
        # 显示前3个结果
        print(f"\n前3个搜索结果:")
        for i, result in enumerate(results[:3], 1):
            if isinstance(result, dict):
                print(f"\n结果 {i}:")
                print(f"  标题: {result.get('title', 'N/A')}")
                print(f"  URL: {result.get('url', 'N/A')}")
                print(f"  内容长度: {len(result.get('content', ''))} 字符")
                
    except Exception as e:
        print(f"多查询搜索失败: {e}")

def test_comparison():
    """对比优化前后的搜索效果"""
    print("\n=== 对比优化前后搜索效果 ===")
    
    original_query = "沃尔玛在线商城最近推出了哪些新的热门圣诞节装饰品商品类别？"
    
    try:
        search_tool = get_web_search_tool(max_search_results=5)
        
        print("--- 优化前（直接搜索原查询） ---")
        original_results = search_tool.invoke(original_query)
        print(f"原查询结果数量: {len(original_results) if isinstance(original_results, list) else 0}")
        
        print("\n--- 优化后（多查询搜索） ---")
        optimized_queries = optimize_query_for_search(original_query, max_queries=3)
        search_func = lambda q: search_tool.invoke(q) 
        optimized_results = multi_query_search(search_func, optimized_queries, max_results_per_query=2)
        print(f"优化查询结果数量: {len(optimized_results) if isinstance(optimized_results, list) else 0}")
        
        # 简单的相关性分析
        def analyze_relevance(results, target_keywords=["walmart", "christmas", "decoration"]):
            if not isinstance(results, list):
                return 0
            
            relevant_count = 0
            for result in results:
                if isinstance(result, dict):
                    content = f"{result.get('title', '')} {result.get('content', '')}".lower()
                    if any(keyword in content for keyword in target_keywords):
                        relevant_count += 1
            return relevant_count
        
        original_relevant = analyze_relevance(original_results)
        optimized_relevant = analyze_relevance(optimized_results)
        
        print(f"\n相关性分析:")
        print(f"原查询相关结果: {original_relevant}")  
        print(f"优化查询相关结果: {optimized_relevant}")
        print(f"改进效果: {'+' if optimized_relevant > original_relevant else '='}{abs(optimized_relevant - original_relevant)}")
        
    except Exception as e:
        print(f"对比测试失败: {e}")

def main():
    """主测试函数"""
    print("=== 查询优化功能测试 ===")
    
    # 分步测试
    test_translation()
    test_keyword_extraction()
    test_multi_query_search() 
    test_comparison()
    
    print("\n=== 测试完成 ===")

if __name__ == "__main__":
    main()