#!/usr/bin/env python
"""
测试本地数据驱动的深度研究员系统核心组件
"""
import asyncio
import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__)))

from src.data_researcher import DataIntentAnalyzer, DataExplorationPlanner
import logging

# 设置日志
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

async def test_intent_analyzer():
    """测试意图识别器"""
    print("=" * 80)
    print("测试 DataIntentAnalyzer")
    print("=" * 80)
    
    analyzer = DataIntentAnalyzer()
    
    # 测试查询
    test_queries = [
        "分析沃尔玛的订单数据趋势",
        "统计沃尔玛商品的类别分布",
        "显示所有商品的平均价格"
    ]
    
    for i, query in enumerate(test_queries, 1):
        print(f"\n第{i}个测试查询: {query}")
        try:
            intent = await analyzer.analyze_query(query)
            print(f"✓ 业务目标: {intent.business_objective}")
            print(f"✓ 业务领域: {intent.business_domain}")
            print(f"✓ 分析类型: {intent.analysis_type}")
            print(f"✓ 主要实体数量: {len(intent.primary_entities)}")
            print(f"✓ 目标指标数量: {len(intent.target_metrics)}")
            print(f"✓ 置信度: {intent.confidence_score:.2f}")
            print(f"✓ 复杂度: {intent.complexity_level}")
        except Exception as e:
            print(f"✗ 测试失败: {e}")
            import traceback
            traceback.print_exc()

async def test_exploration_planner():
    """测试探索规划器"""
    print("\n" + "=" * 80)
    print("测试 DataExplorationPlanner")
    print("=" * 80)
    
    # 首先获取一个意图
    analyzer = DataIntentAnalyzer()
    query = "分析沃尔玛的订单数据趋势"
    
    print(f"\n基于查询生成计划: {query}")
    
    try:
        # 1. 意图分析
        print("\n第1步: 分析用户意图...")
        intent = await analyzer.analyze_query(query)
        print(f"✓ 意图分析完成，置信度: {intent.confidence_score:.2f}")
        
        # 2. 规划生成
        print("\n第2步: 生成探索计划...")
        planner = DataExplorationPlanner()
        plan = await planner.create_analysis_plan(intent)
        
        print(f"✓ 计划生成完成")
        print(f"  计划ID: {plan.plan_id}")
        print(f"  计划名称: {plan.plan_name}")
        print(f"  预估时间: {plan.total_estimated_time}")
        print(f"  复杂度: {plan.complexity_assessment}")
        print(f"  步骤数量: {len(plan.steps)}")
        print(f"  计划置信度: {plan.plan_confidence:.2f}")
        
        # 3. 显示步骤详情
        print(f"\n第3步: 分析计划步骤...")
        for i, step in enumerate(plan.steps[:3], 1):  # 只显示前3个步骤
            print(f"  步骤 {i}: {step.step_name}")
            print(f"    类型: {step.step_type}")
            print(f"    描述: {step.description}")
            print(f"    工具: {', '.join(step.tools)}")
            print(f"    预估时间: {step.estimated_time}")
            print(f"    优先级: {step.priority}")
            print(f"    可并行: {step.parallel_possible}")
        
        if len(plan.steps) > 3:
            print(f"  ... 还有 {len(plan.steps) - 3} 个步骤")
        
        # 4. 显示执行策略
        print(f"\n第4步: 执行策略分析...")
        print(f"  并行组数: {len(plan.execution_strategy.parallel_groups)}")
        print(f"  关键路径长度: {len(plan.execution_strategy.critical_path)}")
        print(f"  优化建议: {plan.execution_strategy.optimization_notes}")
        
        # 5. 显示风险评估
        print(f"\n第5步: 风险评估...")
        print(f"  数据可用性风险: {plan.risk_assessment.data_availability_risk}")
        print(f"  复杂度风险: {plan.risk_assessment.complexity_risk}")
        print(f"  性能风险: {plan.risk_assessment.performance_risk}")
        
        return plan
        
    except Exception as e:
        print(f"✗ 测试失败: {e}")
        import traceback
        traceback.print_exc()
        return None

async def test_integration():
    """测试集成场景"""
    print("\n" + "=" * 80)
    print("测试完整集成场景")
    print("=" * 80)
    
    test_scenarios = [
        {
            "name": "简单查询场景",
            "query": "查询订单总数",
            "expected_complexity": "low"
        },
        {
            "name": "中等复杂度场景", 
            "query": "分析沃尔玛最近12个月的订单趋势和商品类别分布",
            "expected_complexity": "medium"
        },
        {
            "name": "复杂分析场景",
            "query": "深度分析沃尔玛订单数据，包括趋势预测、异常检测、客户行为分析和商品推荐",
            "expected_complexity": "high"
        }
    ]
    
    analyzer = DataIntentAnalyzer()
    planner = DataExplorationPlanner()
    
    results = []
    
    for scenario in test_scenarios:
        print(f"\n测试场景: {scenario['name']}")
        print(f"查询: {scenario['query']}")
        
        try:
            # 意图分析
            intent = await analyzer.analyze_query(scenario['query'])
            
            # 计划生成
            plan = await planner.create_analysis_plan(intent)
            
            result = {
                "scenario": scenario['name'],
                "intent_confidence": intent.confidence_score,
                "complexity": intent.complexity_level,
                "steps_count": len(plan.steps),
                "estimated_time": plan.total_estimated_time,
                "plan_confidence": plan.plan_confidence
            }
            
            results.append(result)
            
            print(f"✓ 意图置信度: {intent.confidence_score:.2f}")
            print(f"✓ 识别复杂度: {intent.complexity_level}")
            print(f"✓ 生成步骤数: {len(plan.steps)}")
            print(f"✓ 预估时间: {plan.total_estimated_time}")
            
            # 验证复杂度是否符合预期
            if intent.complexity_level == scenario.get('expected_complexity'):
                print(f"✓ 复杂度识别正确")
            else:
                print(f"⚠️  复杂度识别可能有偏差，预期: {scenario.get('expected_complexity')}, 实际: {intent.complexity_level}")
                
        except Exception as e:
            print(f"✗ 场景测试失败: {e}")
            results.append({
                "scenario": scenario['name'],
                "error": str(e)
            })
    
    # 总结
    print(f"\n" + "=" * 80)
    print("测试总结")
    print("=" * 80)
    
    successful_tests = [r for r in results if "error" not in r]
    print(f"成功测试: {len(successful_tests)}/{len(results)}")
    
    if successful_tests:
        avg_intent_confidence = sum(r["intent_confidence"] for r in successful_tests) / len(successful_tests)
        avg_plan_confidence = sum(r["plan_confidence"] for r in successful_tests) / len(successful_tests)
        
        print(f"平均意图置信度: {avg_intent_confidence:.2f}")
        print(f"平均计划置信度: {avg_plan_confidence:.2f}")
        
        for result in successful_tests:
            print(f"  {result['scenario']}: {result['complexity']} ({result['steps_count']} 步骤)")

async def main():
    """主测试函数"""
    print("🚀 开始测试本地数据驱动的深度研究员系统")
    print("⚠️  确保已配置LLM和相关依赖")
    
    try:
        # 测试1: 意图识别器
        await test_intent_analyzer()
        
        # 测试2: 探索规划器  
        await test_exploration_planner()
        
        # 测试3: 集成测试
        await test_integration()
        
        print(f"\n🎉 所有测试完成")
        
    except Exception as e:
        print(f"\n❌ 测试过程出现错误: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(main())