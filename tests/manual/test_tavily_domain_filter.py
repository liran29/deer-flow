#!/usr/bin/env python3
"""
测试Tavily域名过滤功能
验证配置的include_domains是否正常工作
"""

import os
import sys
import logging
from pathlib import Path

# 添加src目录到系统路径
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from src.tools.search import get_web_search_tool, get_search_config
from src.config import SELECTED_SEARCH_ENGINE, SearchEngine

# 设置日志级别
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def test_search_config():
    """测试搜索配置是否正确加载"""
    print("\n=== 测试搜索配置 ===")
    config = get_search_config()
    print(f"搜索引擎: {config.get('engine', 'default')}")
    print(f"Include domains数量: {len(config.get('include_domains', []))}")
    print(f"Include domains列表:")
    for domain in config.get('include_domains', []):
        print(f"  - {domain}")
    return config

def test_tavily_search(query: str):
    """测试Tavily搜索功能"""
    print(f"\n=== 测试搜索: '{query}' ===")
    
    if SELECTED_SEARCH_ENGINE != SearchEngine.TAVILY.value:
        print(f"警告: 当前搜索引擎是 {SELECTED_SEARCH_ENGINE}, 不是 Tavily")
        return
    
    try:
        # 获取搜索工具
        search_tool = get_web_search_tool(max_search_results=10)
        print(f"搜索工具已创建: {search_tool.name}")
        
        # 执行搜索
        results = search_tool.invoke(query)
        
        # 分析结果
        if isinstance(results, list):
            print(f"\n搜索结果数量: {len(results)}")
            
            # 统计各域名的结果数量
            domain_count = {}
            for result in results:
                if isinstance(result, dict) and 'url' in result:
                    url = result['url']
                    # 提取域名
                    from urllib.parse import urlparse
                    domain = urlparse(url).netloc
                    domain_count[domain] = domain_count.get(domain, 0) + 1
                    
            print("\n各域名结果统计:")
            for domain, count in sorted(domain_count.items(), key=lambda x: x[1], reverse=True):
                print(f"  {domain}: {count} 个结果")
                
            # 显示前3个结果
            print("\n前3个搜索结果:")
            for i, result in enumerate(results[:3], 1):
                if isinstance(result, dict):
                    print(f"\n结果 {i}:")
                    print(f"  标题: {result.get('title', 'N/A')}")
                    print(f"  URL: {result.get('url', 'N/A')}")
                    print(f"  内容: {result.get('content', 'N/A')[:200]}...")
        else:
            print(f"意外的结果类型: {type(results)}")
            print(f"结果内容: {results}")
            
    except Exception as e:
        print(f"搜索出错: {str(e)}")
        import traceback
        traceback.print_exc()

def main():
    """主测试函数"""
    print("=== Tavily域名过滤测试 ===")
    print(f"当前搜索引擎: {SELECTED_SEARCH_ENGINE}")
    
    # 测试配置
    config = test_search_config()
    
    # 测试查询
    test_queries = [
        "Walmart online marketplace popular products",
        "Amazon best selling items 2024",
        "retail market analysis trends",
        "e-commerce statistics 2024"
    ]
    
    for query in test_queries:
        test_tavily_search(query)
        print("\n" + "="*60 + "\n")
    
    # 验证域名过滤是否生效
    print("\n=== 域名过滤验证总结 ===")
    include_domains = config.get('include_domains', [])
    if include_domains:
        print(f"配置的域名过滤列表包含 {len(include_domains)} 个域名")
        print("如果过滤正常工作，所有搜索结果应该只来自这些域名。")
    else:
        print("警告：没有配置include_domains，域名过滤未启用。")

if __name__ == "__main__":
    main()