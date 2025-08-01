#!/usr/bin/env python3
"""测试 walmart_orders 表的数据"""

import asyncio
import json
from src.tools.mindsdb_mcp import MindsDBMCPTool

async def test_walmart_orders():
    """测试 walmart_orders 表的样本数据"""
    
    tool = MindsDBMCPTool()
    
    print("🔍 检查 walmart_orders 表...")
    print("=" * 80)
    
    try:
        # 1. 表结构信息
        print("\n📋 1. 表结构信息:")
        table_info = await tool.get_table_info("htinfo_db", "walmart_orders")
        if table_info.get("success"):
            print(f"字段数: {len(table_info.get('data', []))}")
            for field in table_info.get("data", [])[:10]:  # 显示前10个字段
                print(f"  - {field}")
        else:
            print(f"获取表结构失败: {table_info.get('error')}")
        
        # 2. 样本数据
        print("\n📊 2. 样本数据 (前3行):")
        sample_result = await tool.query_database(
            "htinfo_db",
            "SELECT * FROM walmart_orders LIMIT 3"
        )
        if sample_result.get("success"):
            columns = sample_result.get("columns", [])
            data = sample_result.get("data", [])
            print(f"列: {columns}")
            print(f"数据行数: {len(data)}")
            for i, row in enumerate(data):
                print(f"行 {i+1}: {row}")
        else:
            print(f"查询失败: {sample_result.get('error')}")
        
        # 3. 数据总量
        print("\n📈 3. 数据总量统计:")
        count_result = await tool.query_database(
            "htinfo_db",
            "SELECT COUNT(*) as total_rows FROM walmart_orders"
        )
        if count_result.get("success") and count_result.get("data"):
            print(f"总行数: {count_result['data'][0]}")
        
        # 4. 检查字段内容
        print("\n🔍 4. 检查关键字段:")
        
        # 检查是否有 order_date 字段
        date_check = await tool.query_database(
            "htinfo_db",
            "SELECT * FROM walmart_orders WHERE 1=0"  # 只获取列名
        )
        if date_check.get("success"):
            columns = date_check.get("columns", [])
            print(f"表的所有列: {columns}")
            
            if "order_date" in columns:
                print("\n✅ 存在 order_date 字段")
                # 检查 order_date 的数据
                date_sample = await tool.query_database(
                    "htinfo_db",
                    "SELECT order_date FROM walmart_orders LIMIT 5"
                )
                if date_sample.get("success"):
                    print("order_date 样本数据:")
                    for row in date_sample.get("data", []):
                        print(f"  - {row}")
            else:
                print("\n❌ 不存在 order_date 字段")
                
            # 检查是否有 year 字段
            if "year" in columns:
                print("\n✅ 存在 year 字段")
                year_sample = await tool.query_database(
                    "htinfo_db",
                    "SELECT DISTINCT year FROM walmart_orders ORDER BY year"
                )
                if year_sample.get("success"):
                    print("year 字段的值:")
                    for row in year_sample.get("data", []):
                        print(f"  - {row}")
                        
            # 检查是否有其他日期相关字段
            date_related_columns = [col for col in columns if 'date' in col.lower() or 'time' in col.lower() or 'year' in col.lower()]
            if date_related_columns:
                print(f"\n📅 日期相关字段: {date_related_columns}")
        
        # 5. 检查2024年数据
        print("\n📆 5. 检查2024年数据:")
        
        # 尝试不同的查询方式
        queries = [
            ("使用 year 字段", "SELECT COUNT(*) FROM walmart_orders WHERE year = 2024"),
            ("使用 LIKE 匹配", "SELECT COUNT(*) FROM walmart_orders WHERE CAST(year AS CHAR) LIKE '2024%'"),
            ("查看所有年份", "SELECT year, COUNT(*) as count FROM walmart_orders GROUP BY year ORDER BY year")
        ]
        
        for desc, query in queries:
            print(f"\n{desc}: {query}")
            result = await tool.query_database("htinfo_db", query)
            if result.get("success"):
                print(f"结果: {result.get('data')}")
            else:
                print(f"查询失败: {result.get('error')}")
                
    except Exception as e:
        print(f"\n❌ 错误: {e}")
        import traceback
        traceback.print_exc()
    
    print("\n" + "=" * 80)
    print("测试完成!")

if __name__ == "__main__":
    asyncio.run(test_walmart_orders())