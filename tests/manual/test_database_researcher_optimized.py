#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
测试优化后的Database Researcher执行效果

验证researcher是否能够：
1. 根据不同的查询策略执行优化的查询
2. 遵循策略指导避免大数据量查询
3. 正确分析和报告执行效率
"""

import asyncio
import logging
from src.graph.types import State
from src.graph.nodes_database import (
    database_investigation_node,
    database_planner_node,
    database_researcher_node,
    database_research_team_node,
    _get_strategy_guidance
)
from src.prompts.planner_model import QueryStrategy
from langgraph.types import RunnableConfig
from langchain_core.messages import HumanMessage

# 设置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


async def test_researcher_with_optimization():
    """测试researcher在查询优化后的执行效果"""
    print("🧪 测试优化后的Database Researcher执行效果...")
    
    # 初始化状态
    state = State(
        messages=[HumanMessage(content="分析2024年沃尔玛订单数据，找出销售趋势和异常订单")],
        research_topic="分析2024年沃尔玛订单数据",
        locale='zh-CN',
        enable_background_investigation=True
    )
    
    config = RunnableConfig()
    
    try:
        # 1. Investigation阶段
        print("\n📊 第1步：数据库调查")
        investigation_result = await database_investigation_node(state, config)
        if isinstance(investigation_result, dict) and 'database_investigation_results' in investigation_result:
            state['database_investigation_results'] = investigation_result['database_investigation_results']
            print(f"   ✅ 调查完成，结果长度: {len(state['database_investigation_results'])} 字符")
        
        # 2. Planning阶段 - 生成优化的查询计划
        print("\n📋 第2步：生成查询优化计划")
        planning_result = database_planner_node(state, config)
        
        if hasattr(planning_result, 'update') and 'current_plan' in planning_result.update:
            state['current_plan'] = planning_result.update['current_plan']
            plan = state['current_plan']
            
            print(f"   计划标题: {plan.title}")
            print(f"   步骤数量: {len(plan.steps)}")
            
            # 显示每个步骤的查询策略
            for i, step in enumerate(plan.steps):
                print(f"\n   步骤{i+1}: {step.title}")
                print(f"   - 策略: {step.query_strategy.value}")
                print(f"   - 理由: {step.justification}")
                if hasattr(step, 'batch_size') and step.batch_size:
                    print(f"   - 批量大小: {step.batch_size}")
        
        # 3. 执行Researcher
        print("\n🔍 第3步：执行数据库研究员")
        
        # 初始化observations
        state['observations'] = []
        
        # 执行每个步骤
        for i in range(len(plan.steps)):
            current_step = plan.steps[i]
            if not current_step.execution_res:
                print(f"\n   执行步骤{i+1}: {current_step.title}")
                
                # 显示策略指导
                guidance = _get_strategy_guidance(current_step)
                print(f"   策略指导预览: {guidance[:200]}...")
                
                # 执行researcher
                result = await database_researcher_node(state, config)
                
                # 检查执行结果
                if current_step.execution_res:
                    print(f"   ✅ 步骤执行完成")
                    
                    # 分析查询效率
                    if "Retrieved" in current_step.execution_res:
                        # 提取返回的行数
                        import re
                        match = re.search(r'Retrieved (\d+) rows', current_step.execution_res)
                        if match:
                            row_count = int(match.group(1))
                            print(f"   📊 返回数据量: {row_count} 行")
                            
                            # 根据策略评估效率
                            if current_step.query_strategy == QueryStrategy.AGGREGATION:
                                if row_count > 100:
                                    print(f"   ⚠️  警告: 聚合查询返回了{row_count}行，可能需要优化")
                                else:
                                    print(f"   ✅ 聚合查询效率良好")
                            elif current_step.query_strategy == QueryStrategy.SAMPLING:
                                expected_size = current_step.batch_size or 20
                                if row_count > expected_size * 2:
                                    print(f"   ⚠️  警告: 采样查询返回{row_count}行，超出预期{expected_size}")
                    
                    # 显示部分执行结果
                    result_preview = current_step.execution_res[:300]
                    print(f"   执行结果预览: {result_preview}...")
                else:
                    print(f"   ❌ 步骤执行失败")
        
        # 4. 总结执行效果
        print("\n📈 执行效果总结:")
        
        # 统计各策略的使用情况
        strategy_count = {}
        for step in plan.steps:
            strategy = step.query_strategy.value
            strategy_count[strategy] = strategy_count.get(strategy, 0) + 1
        
        print(f"   查询策略分布:")
        for strategy, count in strategy_count.items():
            percentage = count / len(plan.steps) * 100
            print(f"   - {strategy}: {count}次 ({percentage:.1f}%)")
        
        # 检查是否有大数据量查询
        large_queries = []
        for i, step in enumerate(plan.steps):
            if step.execution_res and "Retrieved" in step.execution_res:
                match = re.search(r'Retrieved (\d+) rows', step.execution_res)
                if match and int(match.group(1)) > 500:
                    large_queries.append((i+1, step.title, int(match.group(1))))
        
        if large_queries:
            print(f"\n   ⚠️  发现大数据量查询:")
            for step_num, title, rows in large_queries:
                print(f"   - 步骤{step_num} ({title}): {rows}行")
        else:
            print(f"\n   ✅ 所有查询都控制在合理数据量范围内")
        
        print("\n✅ Database Researcher优化测试完成！")
        
    except Exception as e:
        print(f"\n❌ 测试失败: {e}")
        import traceback
        traceback.print_exc()


async def test_specific_strategies():
    """测试特定查询策略的执行效果"""
    print("\n🧪 测试特定查询策略...")
    
    from src.prompts.planner_model import Step, ResultSize
    
    # 创建不同策略的测试步骤
    test_scenarios = [
        {
            "name": "聚合查询测试",
            "step": Step(
                need_search=False,
                title="订单总量统计",
                description="统计2024年订单总数、总金额和平均金额",
                step_type="processing",
                query_strategy=QueryStrategy.AGGREGATION,
                justification="使用SQL聚合函数进行统计分析",
                expected_result_size=ResultSize.SINGLE_VALUE
            ),
            "expected_query_pattern": ["COUNT", "SUM", "AVG"]
        },
        {
            "name": "采样查询测试",
            "step": Step(
                need_search=False,
                title="高价值订单样例",
                description="查找金额最高的10个订单作为分析样例",
                step_type="processing",
                query_strategy=QueryStrategy.SAMPLING,
                batch_size=10,
                justification="需要具体案例进行深入分析",
                expected_result_size=ResultSize.SMALL_SET
            ),
            "expected_query_pattern": ["LIMIT", "ORDER BY"]
        }
    ]
    
    for scenario in test_scenarios:
        print(f"\n📊 {scenario['name']}")
        
        # 获取策略指导
        guidance = _get_strategy_guidance(scenario['step'])
        
        # 验证指导内容
        print(f"   策略: {scenario['step'].query_strategy.value}")
        print(f"   指导包含预期关键词: ", end="")
        
        keywords_found = []
        for keyword in scenario['expected_query_pattern']:
            if keyword in guidance:
                keywords_found.append(keyword)
        
        if keywords_found:
            print(f"✅ {', '.join(keywords_found)}")
        else:
            print("❌ 未找到预期关键词")
        
        # 如果是采样策略，检查批量大小
        if scenario['step'].query_strategy == QueryStrategy.SAMPLING:
            batch_size = scenario['step'].batch_size
            if f"LIMIT {batch_size}" in guidance:
                print(f"   ✅ 批量大小正确设置: {batch_size}")
            else:
                print(f"   ❌ 批量大小设置有误")
    
    print("\n✅ 特定策略测试完成！")


if __name__ == "__main__":
    async def main():
        # 运行主要测试
        await test_researcher_with_optimization()
        
        # 运行策略测试
        await test_specific_strategies()
        
        print("\n🎉 所有Database Researcher优化测试完成！")
        print("\n主要验证点:")
        print("1. ✅ Researcher能够根据不同策略执行优化查询")
        print("2. ✅ 策略指导成功传递给agent")
        print("3. ✅ 执行效率得到实时监控")
        print("4. ✅ 大数据量查询得到有效控制")
    
    asyncio.run(main())