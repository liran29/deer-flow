#!/usr/bin/env python3
"""测试database researcher修复效果"""

import asyncio
import logging
from src.workflow import run_agent_workflow_async

logging.basicConfig(level=logging.INFO)

async def test_researcher_fix():
    """测试修复后的database researcher"""
    
    test_query = "分析沃尔玛2024年的销售趋势"
    
    print(f"🧪 测试查询: {test_query}")
    print("=" * 80)
    
    try:
        # 运行数据库研究工作流
        final_state = await run_agent_workflow_async(
            user_input=test_query,
            debug=True,
            max_plan_iterations=1,
            max_step_num=3,
            enable_background_investigation=True
        )
        
        print("\n✅ 工作流执行完成")
        
        # 检查是否有错误的查询
        if final_state:
            # 获取计划
            plan = final_state.get("current_plan")
            if plan and hasattr(plan, 'steps'):
                print(f"\n📋 执行的步骤:")
                for i, step in enumerate(plan.steps, 1):
                    print(f"{i}. {step.title}")
                    if step.execution_res:
                        # 检查执行结果中是否有month字段的错误
                        if "month" in step.execution_res.lower():
                            print(f"   ⚠️ 警告：步骤结果中包含'month'关键词")
                        if "0 rows" in step.execution_res:
                            print(f"   ❌ 错误：查询返回0行数据")
                        else:
                            print(f"   ✅ 步骤执行成功")
        
        # 显示最终报告的一部分
        if final_state and final_state.get("final_report"):
            report = final_state["final_report"]
            print(f"\n📊 最终报告预览 (前500字符):")
            print("-" * 80)
            print(report[:500] + "...")
            print("-" * 80)
            
            # 检查报告质量
            if "2024" in report and "销售" in report:
                print("✅ 报告包含2024年销售数据")
            else:
                print("❌ 报告可能缺少关键信息")
                
    except Exception as e:
        print(f"❌ 测试失败: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(test_researcher_fix())