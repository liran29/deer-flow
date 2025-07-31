# 数据库查询优化实施方案

## 背景

当前数据库研究员执行查询时，经常出现获取大量数据（如849行）的情况，导致性能问题、内存消耗过大和潜在的Token使用问题。需要通过智能查询规划来根本解决此问题。

## 核心设计思想

### 1. 数据分析本质认知
- **90%的数据分析是统计聚合**，而非查看原始数据
- 数据分析师关心的是模式、趋势、异常，而非每条记录的详情
- 原始数据查询仅在质量检查、异常调查等特殊情况需要

### 2. 职责分离原则
- **Planner**：负责将用户模糊需求分解为高效的分析步骤
- **Researcher**：专注执行具体查询，不做策略决策
- **Reporter**：综合各步骤分析结果生成完整报告

### 3. 数据库层面处理优先
- 使用SQL聚合函数在数据库层面完成统计
- 只传输分析结果，不传输原始数据
- 充分利用数据库的计算能力

## 技术实现方案

### 第一阶段：增强数据模型

#### 1.1 更新Step模型
```python
# 在 src/prompts/planner_model.py 中更新
class Step(BaseModel):
    title: str
    description: str
    
    # 新增字段
    query_strategy: Literal["aggregation", "sampling", "pagination", "window_analysis"] = "aggregation"
    batch_size: Optional[int] = None
    max_batches: Optional[int] = None
    sampling_rate: Optional[float] = None
    justification: str = ""  # 选择此策略的理由
    expected_result_size: Literal["single_value", "small_set", "medium_set"] = "small_set"
    
    # 保持向后兼容
    execution_res: str = ""
    need_search: bool = False
```

#### 1.2 更新验证逻辑
确保新字段的合理性验证：
- `batch_size` 在 10-10000 范围内
- `max_batches` 不超过 100
- `sampling_rate` 在 0.001-1.0 范围内

### 第二阶段：增强Planner智能

#### 2.1 更新database_planner.md提示词
```markdown
# 数据库分析计划制定专家指南

## 核心原则：智能查询策略

你是一个专业的数据分析师，需要将用户的模糊查询需求转换为高效的数据库分析步骤。

### 查询策略选择指南

1. **聚合优先原则**（推荐90%场景使用）
   - 趋势分析：`GROUP BY` + 时间字段
   - 分布分析：`GROUP BY` + 类别字段 + `COUNT`/`SUM`
   - 统计分析：使用 `COUNT`、`SUM`、`AVG`、`MAX`、`MIN`
   
2. **智能需求分解**
   当用户说"查看所有XX"时，分解为：
   - 概况统计（总数、总量、平均值）
   - 时间分布（按月/周/日统计）
   - 类别分布（按分类统计）  
   - 异常识别（用统计方法找出典型案例）

3. **采样策略**（仅在必要时使用）
   - 数据质量检查：`LIMIT 50`
   - 展示典型案例：`LIMIT 10`
   - 异常数据调查：使用统计方法筛选后 `LIMIT 20`

4. **分页策略**（极少使用）
   - 仅在确实需要处理大量详细数据时使用
   - 必须设置合理的 `batch_size`（1000以内）和 `max_batches`（10以内）
   - 必须在 `justification` 中说明为什么需要大量数据

### 步骤规划模板

对于"分析2024年订单情况"类需求：
```python
Plan(
    title="2024年订单全面分析",
    steps=[
        Step(
            title="订单基础统计",
            description="统计2024年订单总数、总金额、平均订单金额等基础指标",
            query_strategy="aggregation",
            justification="基础统计指标，一次聚合查询获取",
            expected_result_size="single_value"
        ),
        Step(
            title="月度趋势分析",
            description="按月统计2024年订单数量和金额的变化趋势",
            query_strategy="aggregation", 
            justification="时间序列分析，GROUP BY月份",
            expected_result_size="small_set"
        ),
        Step(
            title="订单类别分析",
            description="分析不同类别订单的数量分布和金额占比",
            query_strategy="aggregation",
            justification="分类统计分析，GROUP BY类别",
            expected_result_size="small_set"
        ),
        Step(
            title="异常订单案例",
            description="识别异常高额或低额的订单样例供参考",
            query_strategy="sampling",
            batch_size=10,
            justification="只需少量典型案例用于报告说明",
            expected_result_size="small_set"
        )
    ]
)
```

## 要求：
1. 每个步骤必须包含 `query_strategy` 和 `justification`
2. 优先使用 `aggregation` 策略
3. 避免使用 `pagination` 策略，除非有充分理由
4. `sampling` 时 `batch_size` 通常不超过 50
5. 确保分析的完整性和逻辑性
```

#### 2.2 创建查询策略验证机制
在planner中增加策略合理性检查，如果发现可能的低效查询，给出优化建议。

### 第三阶段：优化Researcher执行

#### 3.1 实现策略化执行逻辑
```python
# 在 src/graph/nodes_database.py 中增强 database_researcher_node
async def _execute_step_by_strategy(step: Step, agent, state: State):
    """根据步骤策略执行查询"""
    
    if step.query_strategy == "aggregation":
        # 正常执行，期望返回聚合结果
        return await _execute_aggregation_step(step, agent, state)
        
    elif step.query_strategy == "sampling":
        # 执行采样查询，在提示中明确限制数量
        return await _execute_sampling_step(step, agent, state)
        
    elif step.query_strategy == "pagination":
        # 分批处理并总结
        return await _execute_batch_analysis_step(step, agent, state)
        
    elif step.query_strategy == "window_analysis":
        # 窗口函数分析
        return await _execute_window_step(step, agent, state)
    
    else:
        # 默认按聚合处理
        return await _execute_aggregation_step(step, agent, state)

async def _execute_sampling_step(step: Step, agent, state: State):
    """执行采样查询步骤"""
    # 在agent输入中明确说明采样要求
    sampling_instruction = f"""
    注意：此步骤需要采样分析，请确保查询中包含适当的LIMIT子句。
    推荐限制：LIMIT {step.batch_size or 20}
    """
    
    # 修改agent输入，加入采样指导
    # ... 具体实现
    
async def _execute_batch_analysis_step(step: Step, agent, state: State):
    """执行分批分析步骤"""
    batch_size = step.batch_size or 1000
    max_batches = step.max_batches or 5
    
    # 实现分批查询和即时总结逻辑
    batch_summaries = []
    
    for batch_num in range(max_batches):
        # 构造分批查询指令
        batch_instruction = f"""
        执行第{batch_num + 1}批数据分析（共最多{max_batches}批）：
        - 使用 LIMIT {batch_size} OFFSET {batch_num * batch_size}
        - 对本批数据进行统计分析
        - 提供本批数据的关键统计指标
        """
        
        # 执行本批查询
        batch_result = await _execute_single_batch(batch_instruction, agent, state)
        
        # 立即分析和总结本批结果
        batch_summary = _summarize_batch_result(batch_result, batch_num + 1)
        batch_summaries.append(batch_summary)
        
        # 如果返回数据少于batch_size，说明已经到最后一批
        if _is_last_batch(batch_result, batch_size):
            break
    
    # 合并所有批次的总结
    final_summary = _merge_batch_summaries(batch_summaries)
    return final_summary
```

#### 3.2 增加查询监控和优化提醒
```python
def _analyze_query_efficiency(query: str, result_count: int) -> dict:
    """分析查询效率并给出优化建议"""
    analysis = {
        "is_efficient": True,
        "warnings": [],
        "suggestions": []
    }
    
    # 检查大数据量查询
    if result_count > 100:
        analysis["is_efficient"] = False
        analysis["warnings"].append(f"查询返回了{result_count}行数据，可能影响性能")
        
        if "GROUP BY" not in query.upper():
            analysis["suggestions"].append("考虑使用GROUP BY进行聚合分析")
        if "LIMIT" not in query.upper():
            analysis["suggestions"].append("考虑添加LIMIT限制返回行数")
    
    return analysis
```

### 第四阶段：测试验证

#### 4.1 创建优化效果测试
```python
# tests/manual/test_query_optimization.py
async def test_order_analysis_optimization():
    """测试订单分析查询优化效果"""
    
    # 模拟用户查询：查看2024年所有订单
    test_cases = [
        "分析2024年的销售订单情况",
        "查看今年所有商品订单",
        "统计沃尔玛2024年订单数据"
    ]
    
    for query in test_cases:
        result = await execute_database_research(query)
        
        # 验证查询效率
        assert all(step.query_strategy in ["aggregation", "sampling"] 
                  for step in result.plan.steps)
        
        # 验证数据量控制
        for step_result in result.step_results:
            if step_result.get("total_rows", 0) > 1000:
                assert step_result.get("strategy") == "pagination"
                assert "batch_summary" in step_result
```

#### 4.2 性能对比测试
对比优化前后的查询性能：
- 查询执行时间
- 返回数据量
- 内存使用情况
- Token消耗对比

## 实施时间表

### 第1周：基础架构更新
- [ ] 更新Step模型定义
- [ ] 更新相关导入和类型定义
- [ ] 基础向后兼容性测试

### 第2周：Planner智能增强
- [ ] 更新database_planner.md提示词
- [ ] 实现策略验证逻辑
- [ ] Planner功能测试

### 第3周：Researcher执行优化
- [ ] 实现策略化执行逻辑
- [ ] 实现分批分析功能
- [ ] 增加查询监控机制

### 第4周：测试和优化
- [ ] 完整功能测试
- [ ] 性能对比测试
- [ ] 文档更新和总结

## 预期效果

### 性能改进
- **查询速度**：聚合查询比全表查询快10-100倍
- **数据传输**：从数万行原始数据降低到数十行统计结果
- **内存使用**：大幅减少内存占用
- **Token消耗**：显著降低LLM处理的数据量

### 分析质量提升
- **结构化分析**：从混乱的数据查看转为有序的统计分析
- **洞察深度**：通过多维度分析发现数据规律
- **报告完整性**：系统性的分析框架

### 系统稳定性
- **可预测性**：避免意外的大数据量查询
- **容错性**：单步失败不影响整体分析
- **可维护性**：清晰的执行策略便于调试

## 风险和缓解

### 风险1：兼容性问题
- **风险**：新模型可能与现有代码不兼容
- **缓解**：保持向后兼容，逐步迁移

### 风险2：分析准确性
- **风险**：聚合分析可能丢失某些细节信息
- **缓解**：在必要时仍支持详细数据查询，但需要明确justification

### 风险3：实施复杂度
- **风险**：多策略执行增加代码复杂度
- **缓解**：清晰的接口设计和充分的测试覆盖

此方案通过智能查询规划从根本上解决大数据量查询问题，既提升了性能，又改善了分析质量，符合数据分析的专业实践。