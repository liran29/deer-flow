"""测试数据库计划节点的计划生成功能"""

import asyncio
import logging
from src.graph.nodes_database import database_investigation_node, database_planner_node
from src.graph.types import State
from langchain_core.runnables import RunnableConfig

# 设置日志
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

async def test_database_planner():
    """测试数据库计划节点完整流程"""
    
    # 测试场景
    test_queries = [
        "分析沃尔玛2024年的销售趋势",
        "请根据沃尔玛Walmart 2024年的主题和在售商品，结合当下市场流行趋势，做一份圣诞产品的推荐",
        "比较不同品类商品的价格分布",
        "找出最受欢迎的产品类别"
    ]
    
    for i, query in enumerate(test_queries):
        print(f"\n{'='*80}")
        print(f"测试场景 {i+1}: {query}")
        print('='*80)
        
        # 创建状态
        state = State(
            messages=[{"role": "user", "content": query}],  # 用户查询放在messages中
            research_topic=query,
            locale='zh-CN'
        )
        
        # 创建配置
        config = RunnableConfig()
        
        try:
            # 步骤1: 先运行数据库调查节点
            print("\n步骤1: 运行数据库调查节点...")
            investigation_result = await database_investigation_node(state, config)
            
            # 更新状态
            state.update(investigation_result)
            
            if state.get('database_investigation_results'):
                print(f"✓ 数据库调查完成，结果长度: {len(state['database_investigation_results'])} 字符")
                
                # 步骤2: 运行数据库计划节点
                print("\n步骤2: 运行数据库计划节点...")
                plan_command = database_planner_node(state, config)
                
                print(f"✓ 计划节点执行完成")
                print(f"  - 命令类型: {type(plan_command)}")
                print(f"  - 跳转目标: {plan_command.goto if hasattr(plan_command, 'goto') else 'N/A'}")
                
                # 检查生成的计划
                if hasattr(plan_command, 'update') and plan_command.update:
                    update_data = plan_command.update
                    
                    if 'current_plan' in update_data:
                        current_plan = update_data['current_plan']
                        print(f"\n✓ 成功生成计划")
                        print(f"  - 计划类型: {type(current_plan)}")
                        print(f"  - 计划标题: {getattr(current_plan, 'title', 'N/A')}")
                        print(f"  - 步骤数量: {len(getattr(current_plan, 'steps', []))}")
                        print(f"  - 语言设置: {getattr(current_plan, 'locale', 'N/A')}")
                        print(f"  - 有足够上下文: {getattr(current_plan, 'has_enough_context', 'N/A')}")
                        
                        # 显示详细的计划内容
                        print(f"\n计划详细内容:")
                        print("-" * 60)
                        
                        print(f"思考过程: {getattr(current_plan, 'thought', 'N/A')}")
                        
                        steps = getattr(current_plan, 'steps', [])
                        if steps:
                            print(f"\n计划步骤 ({len(steps)} 个):")
                            for j, step in enumerate(steps, 1):
                                print(f"\n  步骤 {j}:")
                                print(f"    标题: {getattr(step, 'title', 'N/A')}")
                                print(f"    类型: {getattr(step, 'step_type', 'N/A')}")
                                print(f"    需要搜索: {getattr(step, 'need_search', 'N/A')}")
                                description = getattr(step, 'description', 'N/A')
                                if len(description) > 200:
                                    description = description[:200] + "..."
                                print(f"    描述: {description}")
                        else:
                            print("\n  无步骤信息")
                        
                        print("-" * 60)
                    else:
                        print("\n✗ 未在更新数据中找到计划")
                        print(f"  更新数据键: {list(update_data.keys()) if update_data else 'None'}")
                
                    # 显示LLM原始响应（如果有）
                    if 'messages' in update_data and update_data['messages']:
                        last_message = update_data['messages'][-1]
                        if hasattr(last_message, 'content'):
                            print(f"\nLLM原始响应:")
                            print("-" * 40)
                            response_content = last_message.content
                            
                            # 分页显示完整响应
                            page_size = 10000
                            total_length = len(response_content)
                            current_pos = 0
                            
                            while current_pos < total_length:
                                end_pos = min(current_pos + page_size, total_length)
                                page_content = response_content[current_pos:end_pos]
                                
                                print(f"\n--- LLM响应页面 {current_pos//page_size + 1} (字符 {current_pos+1}-{end_pos}) ---")
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
                            print("-" * 40)
                else:
                    print("\n✗ 计划节点未返回更新数据")
            else:
                print("✗ 数据库调查失败，跳过计划生成")
            
        except Exception as e:
            logger.error(f"测试失败: {str(e)}", exc_info=True)
        
        # 暂停一下，避免API速率限制
        if i < len(test_queries) - 1:
            print(f"\n等待3秒后继续下一个测试...")
            await asyncio.sleep(3)
    
    print(f"\n{'='*80}")
    print("所有数据库计划测试完成！")
    print('='*80)

if __name__ == "__main__":
    asyncio.run(test_database_planner())