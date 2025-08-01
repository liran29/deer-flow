#!/usr/bin/env python3
"""测试正确的查询方式"""

import asyncio
from src.tools.mindsdb_mcp import MindsDBMCPTool

async def test_correct_queries():
    """测试walmart_orders表的正确查询方式"""
    
    tool = MindsDBMCPTool()
    
    print("🧪 测试正确的查询方式...")
    print("=" * 80)
    
    # 测试查询列表
    test_queries = [
        {
            "desc": "1. 按类别统计2024年销售",
            "query": "SELECT category, SUM(nums) as total_quantity, SUM(UnitRetail * nums) as total_sales, COUNT(*) as product_count FROM walmart_orders WHERE year = 2024 GROUP BY category ORDER BY total_sales DESC"
        },
        {
            "desc": "2. 2024年销量最高的产品",
            "query": "SELECT ItemDescription, category, nums as quantity_sold, UnitRetail, (UnitRetail * nums) as total_revenue FROM walmart_orders WHERE year = 2024 AND nums > 0 ORDER BY nums DESC LIMIT 10"
        },
        {
            "desc": "3. 各年份销售趋势",
            "query": "SELECT year, COUNT(*) as product_count, SUM(nums) as total_quantity, SUM(UnitRetail * nums) as total_sales FROM walmart_orders GROUP BY year ORDER BY year"
        },
        {
            "desc": "4. 2024年价格分布",
            "query": "SELECT category, MIN(UnitRetail) as min_price, MAX(UnitRetail) as max_price, AVG(UnitRetail) as avg_price, COUNT(*) as product_count FROM walmart_orders WHERE year = 2024 GROUP BY category"
        },
        {
            "desc": "5. 检查是否有月份数据",
            "query": "SELECT DISTINCT year FROM walmart_orders ORDER BY year"
        }
    ]
    
    for test in test_queries:
        print(f"\n{test['desc']}")
        print(f"查询: {test['query']}")
        print("-" * 80)
        
        try:
            result = await tool.query_database("htinfo_db", test['query'])
            
            if result.get("success"):
                data = result.get("data", [])
                columns = result.get("columns", [])
                
                print(f"✅ 查询成功")
                print(f"列: {columns}")
                print(f"返回行数: {len(data)}")
                
                if data:
                    print("数据样本:")
                    for i, row in enumerate(data[:3]):  # 显示前3行
                        print(f"  行{i+1}: {row}")
                else:
                    print("❌ 没有返回数据")
            else:
                print(f"❌ 查询失败: {result.get('error')}")
                
        except Exception as e:
            print(f"❌ 执行错误: {e}")
    
    print("\n" + "=" * 80)
    print("✅ 测试完成！")
    
    # 总结
    print("\n📋 查询策略总结:")
    print("1. 使用实际存在的表名: walmart_orders")
    print("2. 使用实际存在的字段: category, ItemDescription, nums, UnitRetail, year")
    print("3. 年份过滤使用: WHERE year = 2024")
    print("4. 销售额计算: UnitRetail * nums")
    print("5. 没有月份字段，只能按年份和类别分析")

if __name__ == "__main__":
    asyncio.run(test_correct_queries())