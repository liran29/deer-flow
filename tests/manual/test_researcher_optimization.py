#!/usr/bin/env python3
"""
测试researcher节点中的查询优化功能
验证优化搜索工具的工作情况
"""

import sys
from pathlib import Path

# 添加src目录到系统路径
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from src.tools.search import get_web_search_tool
from src.tools.optimized_search import create_optimized_search_tool


def test_optimized_search_tool():
    """测试优化搜索工具"""
    print("=== 测试优化搜索工具 ===")
    
    # 获取基础搜索工具
    base_tool = get_web_search_tool(max_search_results=3)
    print(f"基础工具: {base_tool.name}")
    
    # 创建优化搜索工具
    optimized_tool = create_optimized_search_tool(
        base_tool=base_tool,
        max_queries=3,
        max_results_per_query=2
    )
    print(f"优化工具: {optimized_tool.name}")
    print(f"优化工具描述: {optimized_tool.description[:100]}...")
    
    # 测试查询
    test_queries = [
        "沃尔玛圣诞节装饰品新品",
        "Walmart Christmas decorations",
        "亚马逊最受欢迎的电子产品有哪些？"
    ]
    
    for query in test_queries:
        print(f"\n--- 测试查询: '{query}' ---")
        try:
            # 执行优化搜索
            results = optimized_tool._run(query)
            
            print(f"返回结果数量: {len(results)}")
            
            # 分析结果域名
            domains = {}
            for result in results:
                if isinstance(result, dict) and 'url' in result:
                    from urllib.parse import urlparse
                    domain = urlparse(result['url']).netloc
                    domains[domain] = domains.get(domain, 0) + 1
            
            if domains:
                print("域名分布:")
                for domain, count in sorted(domains.items(), key=lambda x: x[1], reverse=True):
                    print(f"  {domain}: {count}")
            
            # 显示第一个结果
            if results and isinstance(results[0], dict):
                print(f"第一个结果:")
                print(f"  标题: {results[0].get('title', 'N/A')}")
                print(f"  URL: {results[0].get('url', 'N/A')}")
                
        except Exception as e:
            print(f"搜索失败: {e}")


def test_tool_schema():
    """测试工具的schema定义"""
    print("\n=== 测试工具Schema ===")
    
    base_tool = get_web_search_tool(max_search_results=3)
    optimized_tool = create_optimized_search_tool(base_tool)
    
    print(f"工具名称: {optimized_tool.name}")
    print(f"输入Schema: {optimized_tool.args_schema}")
    print(f"描述: {optimized_tool.description}")
    
    # 测试工具调用格式
    print("\n测试工具调用:")
    test_input = {"query": "test query"}
    
    try:
        # 验证输入格式
        validated_input = optimized_tool.args_schema(**test_input)
        print(f"输入验证成功: {validated_input}")
    except Exception as e:
        print(f"输入验证失败: {e}")


def main():
    """主测试函数"""
    print("=== Researcher查询优化测试 ===")
    
    # 测试工具schema
    test_tool_schema()
    
    # 测试优化搜索
    print("\n" + "="*50)
    test_optimized_search_tool()
    
    print("\n=== 测试完成 ===")


if __name__ == "__main__":
    main()