#!/usr/bin/env python3
"""
测试背景调查域名过滤配置功能
"""

import sys
from pathlib import Path

# 添加src目录到系统路径
sys.path.insert(0, str(Path(__file__).parent))

from src.config.loader import load_yaml_config
from src.tools.search import get_search_config

def test_config_loading():
    """测试配置加载"""
    print("=== 测试配置加载 ===")
    
    # 加载完整配置
    config = load_yaml_config('conf.yaml')
    enhanced_features = config.get('ENHANCED_FEATURES', {})
    
    print(f"enhanced_background_investigation: {enhanced_features.get('enhanced_background_investigation', False)}")
    print(f"background_investigation_use_domain_filter: {enhanced_features.get('background_investigation_use_domain_filter', True)}")
    
    # 加载搜索配置
    search_config = get_search_config()
    include_domains = search_config.get('include_domains', [])
    print(f"配置的域名数量: {len(include_domains)}")
    
    return enhanced_features

def test_domain_filter_behavior(use_domain_filter: bool):
    """测试域名过滤行为"""
    print(f"\n=== 测试域名过滤 (use_domain_filter={use_domain_filter}) ===")
    
    from src.tools.search import LoggedTavilySearch, get_web_search_tool
    from urllib.parse import urlparse
    
    query = "retail market analysis trends"
    max_results = 5
    
    if use_domain_filter:
        print("使用 get_web_search_tool (带域名过滤)")
        search_tool = get_web_search_tool(max_results)
        results = search_tool.invoke(query)
    else:
        print("使用 LoggedTavilySearch (无域名过滤)")
        results = LoggedTavilySearch(
            max_results=max_results,
            include_raw_content=True,
            include_images=True,
        ).invoke(query)
    
    # 分析结果域名
    if isinstance(results, list):
        domains = []
        for result in results:
            if isinstance(result, dict) and 'url' in result:
                domain = urlparse(result['url']).netloc
                domains.append(domain)
        
        unique_domains = list(set(domains))
        print(f"结果数量: {len(results)}")
        print(f"唯一域名数量: {len(unique_domains)}")
        print("发现的域名:")
        for domain in sorted(unique_domains):
            print(f"  - {domain}")
        
        return unique_domains
    else:
        print(f"意外的结果类型: {type(results)}")
        return []

def main():
    """主测试函数"""
    print("=== 背景调查域名过滤配置测试 ===")
    
    # 测试配置加载
    enhanced_features = test_config_loading()
    
    # 测试两种模式
    print("\n" + "="*50)
    domains_with_filter = test_domain_filter_behavior(True)
    
    print("\n" + "="*50)  
    domains_without_filter = test_domain_filter_behavior(False)
    
    # 对比结果
    print("\n=== 对比结果 ===")
    print(f"使用域名过滤的域名数量: {len(domains_with_filter)}")
    print(f"不使用域名过滤的域名数量: {len(domains_without_filter)}")
    
    # 查找违规域名
    search_config = get_search_config()
    allowed_domains = set(search_config.get('include_domains', []))
    
    violations_with = []
    violations_without = []
    
    for domain in domains_with_filter:
        clean_domain = domain.replace('www.', '')
        is_allowed = any(clean_domain == allowed or clean_domain.endswith('.' + allowed) 
                        for allowed in allowed_domains)
        if not is_allowed:
            violations_with.append(domain)
    
    for domain in domains_without_filter:
        clean_domain = domain.replace('www.', '')
        is_allowed = any(clean_domain == allowed or clean_domain.endswith('.' + allowed) 
                        for allowed in allowed_domains)
        if not is_allowed:
            violations_without.append(domain)
    
    print(f"使用域名过滤的违规域名: {len(violations_with)} 个")
    if violations_with:
        for domain in violations_with:
            print(f"  - {domain}")
    
    print(f"不使用域名过滤的违规域名: {len(violations_without)} 个")
    if violations_without:
        for domain in violations_without:
            print(f"  - {domain}")
    
    # 总结
    print(f"\n=== 测试总结 ===")
    print(f"配置功能: {'✅ 正常' if len(violations_with) == 0 and len(violations_without) > 0 else '❌ 异常'}")
    print(f"域名过滤: {'✅ 生效' if len(violations_with) < len(violations_without) else '❌ 无效'}")

if __name__ == "__main__":
    main()