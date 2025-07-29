"""测试完整的数据库研究团队工作流程"""

import asyncio
import logging
from src.workflow import run_agent_workflow_async

# 设置日志
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

async def test_database_research_team_workflow():
    """测试完整的数据库研究团队工作流程"""
    
    # 测试查询
    test_queries = [
        "分析沃尔玛2024年的销售趋势",
        "比较不同品类商品的价格分布", 
        "找出最受欢迎的产品类别",
        "请根据沃尔玛Walmart 2024年的主题和在售商品，结合当下市场流行趋势，做一份圣诞产品的推荐"
    ]
    
    for i, query in enumerate(test_queries):
        print(f"\n{'='*100}")
        print(f"测试查询 {i+1}: {query}")
        print('='*100)
        
        try:
            # 运行完整的数据库研究工作流
            final_state = await run_agent_workflow_async(
                user_input=query,
                debug=True,
                max_plan_iterations=1,
                max_step_num=3,
                enable_background_investigation=True   # 启用以执行database_investigation
            )
            
            print(f"✅ 工作流完成")
            
            # 显示关键结果
            if final_state and final_state.get("final_report"):
                print(f"\n📋 最终报告:")
                print("-" * 80)
                report = final_state["final_report"]
                # 分页显示报告
                if len(report) > 2000:
                    print(report[:2000])
                    print(f"\n... (报告已截断，总长度: {len(report)} 字符)")
                else:
                    print(report)
                print("-" * 80)
            else:
                print("❌ 未生成最终报告")
            
            # 显示执行的步骤
            current_plan = final_state.get("current_plan") if final_state else None
            if current_plan and hasattr(current_plan, 'steps'):
                print(f"\n📊 执行的分析步骤:")
                for j, step in enumerate(current_plan.steps, 1):
                    status = "✅ 已完成" if step.execution_res else "❌ 未完成"
                    print(f"  {j}. {step.title} - {status}")
                    if step.execution_res:
                        result_preview = step.execution_res[:200] + "..." if len(step.execution_res) > 200 else step.execution_res
                        print(f"     结果预览: {result_preview}")
            
            # 显示观察结果
            observations = final_state.get("observations", []) if final_state else []
            if observations:
                print(f"\n🔍 观察结果:")
                for obs in observations[-3:]:  # 显示最后3个观察
                    print(f"  - {obs}")
            
        except Exception as e:
            logger.error(f"测试查询 {i+1} 失败: {str(e)}", exc_info=True)
        
        # 测试间隔
        if i < len(test_queries) - 1:
            print(f"\n⏳ 等待5秒后继续下一个测试...")
            await asyncio.sleep(5)
    
    print(f"\n{'='*100}")
    print("所有数据库研究团队测试完成！")
    print('='*100)

if __name__ == "__main__":
    asyncio.run(test_database_research_team_workflow())