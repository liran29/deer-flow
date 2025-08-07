#!/usr/bin/env python3
"""
测试查询优化基本功能（不调用LLM）
验证中文检测和模板加载
"""

import sys
import re
from pathlib import Path

# 添加src目录到系统路径
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

def test_chinese_detection():
    """测试中文检测"""
    print("=== 测试中文检测功能 ===")
    
    test_cases = [
        ("沃尔玛在线商城最近推出了哪些新的热门圣诞节装饰品商品类别？", True),
        ("Walmart Christmas decorations", False),
        ("mixed text 中文混合", True),
        ("pure English text", False)
    ]
    
    success_count = 0
    for query, expected in test_cases:
        contains_chinese = bool(re.search(r'[\u4e00-\u9fff]', query))
        result = "通过" if contains_chinese == expected else "失败"
        print(f"查询: '{query}' -> 中文: {contains_chinese} ({result})")
        if contains_chinese == expected:
            success_count += 1
    
    print(f"中文检测测试: {success_count}/{len(test_cases)} 通过")
    return success_count == len(test_cases)

def test_template_variables():
    """测试模板变量生成"""
    print("\n=== 测试模板变量生成 ===")
    
    from src.utils.query_optimizer import get_current_time_context
    
    try:
        time_context = get_current_time_context()
        print(f"当前年份: {time_context['current_year']}")
        print(f"当前月份: {time_context['current_month']}")
        print(f"近两年: {time_context['recent_years']}")
        print(f"是否准备季: {time_context['is_preparation_season']}")
        
        # 生成recent_years_str
        recent_years_str = " ".join(map(str, time_context["recent_years"]))
        print(f"年份字符串: '{recent_years_str}'")
        
        return True
    except Exception as e:
        print(f"时间上下文生成失败: {e}")
        return False

def main():
    """主测试函数"""
    print("=== 查询优化基本功能测试 ===")
    
    tests_passed = []
    
    # 中文检测测试
    tests_passed.append(test_chinese_detection())
    
    # 模板变量测试
    tests_passed.append(test_template_variables())
    
    success_count = sum(tests_passed)
    
    print(f"\n=== 最终结果 ===")
    print(f"测试通过: {success_count}/{len(tests_passed)}")
    print(f"状态: {'全部通过' if success_count == len(tests_passed) else '部分失败'}")

if __name__ == "__main__":
    main()