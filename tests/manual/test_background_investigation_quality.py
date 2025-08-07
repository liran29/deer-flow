#!/usr/bin/env python3
"""
测试背景调查搜索结果质量分析
分析搜索结果作为背景调查内容的问题
"""

import sys
import json
from pathlib import Path
from urllib.parse import urlparse

# 添加src目录到系统路径
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from src.tools.search import get_web_search_tool
from src.utils.enhanced_features import is_background_investigation_domain_filter_enabled

def analyze_search_results(results, query):
    """分析搜索结果质量"""
    print(f"\n=== 搜索结果质量分析 ===")
    print(f"查询: {query}")
    print(f"结果数量: {len(results) if isinstance(results, list) else 'N/A'}")
    
    if not isinstance(results, list):
        print(f"❌ 搜索结果格式异常: {type(results)}")
        return
    
    # 分析各种问题
    issues = {
        "内容相关性": [],
        "信息时效性": [],
        "内容质量": [],
        "结构化程度": [],
        "重复内容": [],
        "域名分布": {}
    }
    
    contents = []
    domains = []
    
    for i, result in enumerate(results, 1):
        if not isinstance(result, dict):
            issues["内容质量"].append(f"结果{i}: 非字典格式")
            continue
            
        title = result.get('title', '')
        content = result.get('content', '')
        url = result.get('url', '')
        
        # 域名分析
        if url:
            domain = urlparse(url).netloc
            domains.append(domain)
            issues["域名分布"][domain] = issues["域名分布"].get(domain, 0) + 1
        
        # 内容相关性分析
        if '沃尔玛' not in title and '沃尔玛' not in content and 'walmart' not in title.lower() and 'walmart' not in content.lower():
            issues["内容相关性"].append(f"结果{i}: 与沃尔玛无关 - {title[:50]}...")
        
        if '圣诞' not in title and '圣诞' not in content and 'christmas' not in title.lower() and 'christmas' not in content.lower():
            issues["内容相关性"].append(f"结果{i}: 与圣诞节无关 - {title[:50]}...")
        
        if '装饰' not in title and '装饰' not in content and 'decor' not in title.lower() and 'decor' not in content.lower():
            issues["内容相关性"].append(f"结果{i}: 与装饰品无关 - {title[:50]}...")
        
        # 时效性分析
        if '2024' not in content and '2025' not in content and '最新' not in content and 'recent' not in content.lower():
            issues["信息时效性"].append(f"结果{i}: 缺乏时效性信息 - {title[:50]}...")
        
        # 内容质量分析
        if len(content) < 100:
            issues["内容质量"].append(f"结果{i}: 内容过短({len(content)}字符) - {title[:50]}...")
        
        if len(content) > 2000:
            issues["内容质量"].append(f"结果{i}: 内容过长({len(content)}字符) - {title[:50]}...")
        
        if not title:
            issues["内容质量"].append(f"结果{i}: 缺少标题")
        
        if not content:
            issues["内容质量"].append(f"结果{i}: 缺少内容")
        
        # 检查重复内容
        if content in contents:
            issues["重复内容"].append(f"结果{i}: 与之前结果重复")
        else:
            contents.append(content)
        
        # 结构化程度分析
        if '商品' not in content and 'product' not in content.lower():
            issues["结构化程度"].append(f"结果{i}: 缺乏商品信息结构")
        
        if '类别' not in content and '分类' not in content and 'category' not in content.lower():
            issues["结构化程度"].append(f"结果{i}: 缺乏分类信息结构")
    
    # 输出分析结果
    print(f"\n=== 问题分析报告 ===")
    
    total_issues = 0
    for category, problems in issues.items():
        if category == "域名分布":
            continue
        if problems:
            total_issues += len(problems)
            print(f"\n❌ {category} ({len(problems)} 个问题):")
            for problem in problems[:5]:  # 只显示前5个问题
                print(f"  - {problem}")
            if len(problems) > 5:
                print(f"  ... 还有 {len(problems) - 5} 个问题")
        else:
            print(f"\n✅ {category}: 无问题")
    
    print(f"\n=== 域名分布 ===")
    for domain, count in sorted(issues["域名分布"].items(), key=lambda x: x[1], reverse=True):
        print(f"  {domain}: {count} 个结果")
    
    print(f"\n=== 总结 ===")
    print(f"总问题数: {total_issues}")
    print(f"问题率: {total_issues/len(results)*100:.1f}%")
    
    # 质量评级
    if total_issues == 0:
        grade = "A+ 优秀"
    elif total_issues <= len(results) * 0.2:
        grade = "A 良好"
    elif total_issues <= len(results) * 0.4:
        grade = "B 一般"  
    elif total_issues <= len(results) * 0.6:
        grade = "C 需要改进"
    else:
        grade = "D 质量差"
    
    print(f"背景调查质量: {grade}")
    
    return issues

def analyze_content_for_background_investigation(results, query):
    """分析内容是否适合作为背景调查"""
    print(f"\n=== 背景调查适用性分析 ===")
    
    if not isinstance(results, list):
        return
    
    print(f"分析 {len(results)} 个搜索结果的背景调查价值...")
    
    high_value_results = []
    medium_value_results = []
    low_value_results = []
    
    for i, result in enumerate(results, 1):
        if not isinstance(result, dict):
            continue
            
        title = result.get('title', '')
        content = result.get('content', '')
        url = result.get('url', '')
        
        # 计算背景调查价值分数
        score = 0
        reasons = []
        
        # 相关性评分
        if '沃尔玛' in title or 'walmart' in title.lower():
            score += 30
            reasons.append("标题包含沃尔玛")
        elif '沃尔玛' in content or 'walmart' in content.lower():
            score += 20
            reasons.append("内容包含沃尔玛")
        
        if '圣诞' in title or 'christmas' in title.lower():
            score += 20
            reasons.append("标题包含圣诞")
        elif '圣诞' in content or 'christmas' in content.lower():
            score += 15
            reasons.append("内容包含圣诞")
        
        if '装饰' in title or 'decor' in title.lower():
            score += 15
            reasons.append("包含装饰信息")
        
        # 时效性评分
        if '2024' in content or '2025' in content:
            score += 10
            reasons.append("包含最新年份")
        
        if '最新' in content or 'new' in content.lower() or 'recent' in content.lower():
            score += 5
            reasons.append("包含时效性词汇")
        
        # 信息丰富度评分
        if 200 <= len(content) <= 1000:
            score += 10
            reasons.append("内容长度适中")
        elif len(content) > 1000:
            score += 5
            reasons.append("内容详细")
        
        # 分类评分
        if score >= 70:
            high_value_results.append((i, title, score, reasons, content[:200]))
        elif score >= 40:
            medium_value_results.append((i, title, score, reasons, content[:200]))
        else:
            low_value_results.append((i, title, score, reasons, content[:200]))
    
    print(f"\n高价值结果 ({len(high_value_results)} 个):")
    for i, title, score, reasons, preview in high_value_results:
        print(f"  结果{i} (分数: {score}): {title[:60]}...")
        print(f"    原因: {', '.join(reasons)}")
        print(f"    预览: {preview}...")
        print()
    
    print(f"\n中价值结果 ({len(medium_value_results)} 个):")
    for i, title, score, reasons, preview in medium_value_results[:3]:
        print(f"  结果{i} (分数: {score}): {title[:60]}...")
        print(f"    原因: {', '.join(reasons)}")
    
    print(f"\n低价值结果 ({len(low_value_results)} 个):")
    for i, title, score, reasons, preview in low_value_results[:3]:
        print(f"  结果{i} (分数: {score}): {title[:60]}...")
        print(f"    原因: {', '.join(reasons) if reasons else '无相关性'}")
    
    # 背景调查建议
    print(f"\n=== 背景调查建议 ===")
    if len(high_value_results) >= 3:
        print("✅ 搜索结果质量良好，适合作为背景调查")
    elif len(high_value_results) + len(medium_value_results) >= 3:
        print("⚠️ 搜索结果质量一般，建议优化查询词")
    else:
        print("❌ 搜索结果质量较差，需要重新搜索或调整策略")
    
    if len(low_value_results) > len(high_value_results):
        print("🔧 建议: 过滤掉低价值结果，只保留高价值内容")
    
    return high_value_results, medium_value_results, low_value_results

def main():
    """主测试函数"""
    print("=== 背景调查搜索结果质量测试 ===")
    
    query = "沃尔玛在线商城最近推出了哪些新的热门圣诞节装饰品商品类别？"
    
    print(f"域名过滤状态: {is_background_investigation_domain_filter_enabled()}")
    
    # 执行搜索
    search_tool = get_web_search_tool(max_search_results=10)
    results = search_tool.invoke(query)
    
    # 分析搜索结果质量
    issues = analyze_search_results(results, query)
    
    # 分析背景调查适用性
    high_value, medium_value, low_value = analyze_content_for_background_investigation(results, query)
    
    # 输出详细的搜索结果供人工检查
    print(f"\n=== 详细搜索结果 (供人工检查) ===")
    if isinstance(results, list):
        for i, result in enumerate(results, 1):
            if isinstance(result, dict):
                print(f"\n--- 结果 {i} ---")
                print(f"标题: {result.get('title', 'N/A')}")
                print(f"URL: {result.get('url', 'N/A')}")
                print(f"内容长度: {len(result.get('content', ''))} 字符")
                print(f"内容预览: {result.get('content', '')[:300]}...")
    
    return results, issues, high_value, medium_value, low_value

if __name__ == "__main__":
    main()