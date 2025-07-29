"""测试数据库调查节点的LLM分析功能"""

import asyncio
import logging
from src.graph.nodes_database import database_investigation_node
from src.graph.types import State
from langchain_core.runnables import RunnableConfig

# 设置日志
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

async def test_database_investigation():
    """测试数据库调查节点"""
    
    # 测试场景
    test_queries = [
        "分析沃尔玛2024年的销售趋势",
        "请根据沃尔玛Walmart 2024年的主题和在售商品，结合当下市场流行趋势，做一份圣诞产品的推荐",
        "比较不同品类商品的价格分布",
        "找出最受欢迎的产品类别"
    ]
    
    for i, query in enumerate(test_queries):
        print(f"\n{'='*60}")
        print(f"测试场景 {i+1}: {query}")
        print('='*60)
        
        # 创建状态
        state = State()
        state['research_topic'] = query
        
        # 创建配置
        config = RunnableConfig()
        
        try:
            # 调用节点
            result = await database_investigation_node(state, config)
            
            # 显示结果
            print("\n返回的键:")
            for key in result.keys():
                print(f"  - {key}")
            
            # 显示调查结果
            investigation_results = result.get('database_investigation_results', '')
            if investigation_results:
                print(f"\n调查结果长度: {len(investigation_results)} 字符")
                
                # 检查是否包含LLM分析
                if "LLM数据分析建议" in investigation_results:
                    print("\n✓ 包含LLM数据分析建议")
                else:
                    print("\n✗ 未包含LLM数据分析建议")
                
                # 分页显示完整结果
                print("\n调查结果完整内容:")
                print("-" * 50)
                
                # 每页显示10k字符
                page_size = 10000
                total_length = len(investigation_results)
                current_pos = 0
                
                while current_pos < total_length:
                    end_pos = min(current_pos + page_size, total_length)
                    page_content = investigation_results[current_pos:end_pos]
                    
                    print(f"\n--- 页面 {current_pos//page_size + 1} (字符 {current_pos+1}-{end_pos}) ---")
                    print(page_content)
                    
                    current_pos = end_pos
                    
                    # 如果还有更多内容，询问是否继续
                    if current_pos < total_length:
                        remaining = total_length - current_pos
                        print(f"\n--- 还有 {remaining} 个字符未显示 ---")
                        user_input = input("按回车键继续，输入'q'退出: ")
                        if user_input.lower() == 'q':
                            print("显示已终止")
                            break
                
                print("-" * 50)
            
        except Exception as e:
            logger.error(f"测试失败: {str(e)}", exc_info=True)
        
        # 暂停一下，避免API速率限制
        if i < len(test_queries) - 1:
            print("\n等待3秒后继续下一个测试...")
            await asyncio.sleep(3)
    
    print("\n" + "="*60)
    print("所有测试完成！")
    print("="*60)

if __name__ == "__main__":
    asyncio.run(test_database_investigation())