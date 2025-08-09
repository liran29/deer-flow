# Researcher执行流程深度分析

## 1. 系统架构概览

### 1.1 Graph结构（基于builder.py）
```
START 
  ↓
coordinator (决定是否需要research)
  ↓
background_investigator (如果启用，进行背景调查)
  ↓
planner (生成包含多个steps的计划)
  ↓
human_feedback (如果需要用户确认)
  ↓
research_team (协调节点)
  ↓
[循环执行steps]
  ├─→ researcher (执行RESEARCH类型的step)
  ├─→ coder (执行PROCESSING类型的step)
  └─→ 完成所有steps后 → reporter → END
```

### 1.2 关键组件
- **StateGraph**: LangGraph的状态图
- **State**: 共享状态，包含current_plan、messages、observations等
- **Plan**: 包含多个Step的执行计划
- **Step**: 单个任务单元，有title、description、step_type等属性

## 2. Researcher节点详细流程

### 2.1 触发机制
```python
# builder.py:43-65
def continue_to_running_research_team(state: State):
    # 查找第一个未完成的step
    for step in current_plan.steps:
        if not step.execution_res:
            if step.step_type == StepType.RESEARCH:
                return "researcher"  # 路由到researcher节点
            if step.step_type == StepType.PROCESSING:
                return "coder"
```

### 2.2 Researcher节点初始化（nodes.py）

#### 2.2.1 标准版本 (nodes.py:478-494)
```python
async def researcher_node(state: State, config: RunnableConfig):
    # 1. 获取配置
    configurable = Configuration.from_runnable_config(config)
    
    # 2. 准备工具
    tools = [
        get_web_search_tool(configurable.max_search_results),  # include_raw_content=True
        crawl_tool
    ]
    
    # 3. 执行
    return await _setup_and_execute_agent_step(
        state, config, "researcher", tools
    )
```

#### 2.2.2 增强版本 (nodes_enhanced.py:620-670)
```python
async def researcher_node_with_dependencies(state: State, config: RunnableConfig):
    if use_query_optimization:
        # 使用新的工具组合
        tools = [
            search_overview_tool,      # 轻量级搜索概览
            selective_crawl_tool,      # 选择性爬取
            batch_selective_crawl_tool # 批量爬取
        ]
        prompt_template = "researcher_enhanced"
    else:
        # 使用原始工具
        tools = [web_search_tool, crawl_tool]
        prompt_template = "researcher"
```

### 2.3 Agent创建和配置

#### 2.3.1 Agent创建 (agents.py:11-19)
```python
def create_agent(agent_name, agent_type, tools, prompt_template):
    return create_react_agent(
        name=agent_name,
        model=get_llm_by_type(AGENT_LLM_MAP[agent_type]),
        tools=tools,
        prompt=lambda state: apply_prompt_template(prompt_template, state)
    )
```

#### 2.3.2 ReAct Agent特性
- **工作模式**: Reasoning + Acting循环
- **执行流程**: 
  1. Thought（思考）: 分析当前任务
  2. Action（行动）: 选择并调用工具
  3. Observation（观察）: 查看工具返回结果
  4. 循环直到任务完成

### 2.4 Step执行详细流程

#### 2.4.1 准备Agent输入 (nodes.py:338-366)
```python
agent_input = {
    "messages": [
        HumanMessage(content=f"""
            # Research Topic
            {plan_title}
            
            {completed_steps_info}  # 已完成步骤的信息
            
            # Current Step
            ## Title
            {current_step.title}
            ## Description
            {current_step.description}
            ## Locale
            {locale}
        """),
        HumanMessage(  # 引用格式提醒
            content="IMPORTANT: DO NOT include inline citations..."
        )
    ]
}
```

#### 2.4.2 Agent执行 (nodes.py:392-402)
```python
# 调用agent
result = await agent.ainvoke(
    input=agent_input, 
    config={"recursion_limit": recursion_limit}
)

# 保存结果
current_step.execution_res = result["messages"][-1].content
```

## 3. 问题分析

### 3.1 Token超限的根本原因

#### 3.1.1 复杂Step导致多次搜索
**示例Step**: "新假日系列和影响者合作调查"
- 包含子任务1: 调查My Texas House Christmas Decor 2024系列
- 包含子任务2: 调查Amanda Vernaci的合作详情
- 包含子任务3: 分析节日装饰趋势

**Agent行为**:
```
Loop 1: 搜索 "My Texas House Christmas Decor 2024"
Loop 2: 搜索 "Amanda Vernaci Walmart collaboration"
Loop 3: 搜索 "2024 holiday decoration trends"
```

#### 3.1.2 每次搜索返回大量数据
- `web_search_tool` 设置 `include_raw_content=True`
- 每个搜索返回8个结果（虽然设置max_results=3）
- 每个结果包含完整HTML内容
- 累积: 3次搜索 × 8个结果 × 完整HTML = 大量token

#### 3.1.3 优化工具（OptimizedSearchTool）的局限
即使使用了OptimizedSearchTool：
- Agent仍可能多次调用它
- 每次调用内部执行3个优化查询
- 总计: 3次调用 × 3个优化查询 × 8个结果 = 72个结果

### 3.2 流程特点

1. **Step独立执行**: 每个step作为独立任务执行
2. **Agent自主性**: ReAct Agent自主决定工具调用次数
3. **缺乏约束**: 没有机制限制搜索次数或数据量
4. **工具设计**: 当前工具返回过多数据

## 4. 优化方案

### 4.1 方案A: 修改现有工具配置
- 设置 `include_raw_content=False`
- 限制 `max_results` 更严格
- 简单但可能影响搜索质量

### 4.2 方案B: 新工具组合（已实现）
**新工具**:
1. `search_overview`: 轻量级搜索概览（不含raw_content）
2. `selective_crawl_tool`: 选择性爬取特定URL
3. `batch_selective_crawl_tool`: 批量爬取2-3个URL

**优势**:
- 分离"概览"和"详细内容"获取
- Agent可以先分析后选择
- 显著减少token使用

### 4.3 方案C: 提示词优化
在`researcher_enhanced.md`中引导Agent:
- 对复杂任务，先整体规划
- 使用批量工具而非多次单独调用
- 明确搜索和爬取的界限

## 5. 执行循环示例

### 5.1 原始流程（问题流程）
```
Step: "新假日系列和影响者合作调查"
  ↓
Agent思考: 需要调查多个方面
  ↓
Loop 1: 调用web_search_tool("My Texas House") → 8个结果 with raw_content
Loop 2: 调用web_search_tool("Amanda Vernaci") → 8个结果 with raw_content  
Loop 3: 调用web_search_tool("trends") → 8个结果 with raw_content
  ↓
Token超限！
```

### 5.2 优化后流程（方案B）
```
Step: "新假日系列和影响者合作调查"
  ↓
Agent思考: 需要调查多个方面
  ↓
调用search_overview("My Texas House Amanda Vernaci trends") 
  → 轻量级概览（只有标题和摘要）
  ↓
分析概览，识别最相关的2-3个URL
  ↓
调用batch_selective_crawl_tool([url1, url2, url3])
  → 获取详细内容（限制长度）
  ↓
Token可控！
```

## 6. 关键洞察

1. **ReAct Agent的特性决定了行为**: Agent会根据任务复杂度自主调用工具多次
2. **Step设计影响执行**: 复杂的step描述会导致多次搜索
3. **工具设计是关键**: 需要提供"轻量概览"和"深度内容"分离的工具
4. **提示词引导有限**: 可以引导但不能完全控制Agent行为

## 7. 实施建议

### 7.1 短期方案
1. 使用新工具组合（search_overview + selective_crawl）
2. 优化researcher_enhanced.md提示词
3. 考虑限制recursion_limit

### 7.2 长期方案
1. 重新设计Step粒度，避免过于复杂的单个step
2. 实现更智能的查询优化（合并相关查询）
3. 考虑缓存机制，避免重复搜索

## 8. 配置要点

### 8.1 当前配置
```yaml
# conf.yaml
researcher_query_optimization: true  # 启用查询优化
max_search_results: 3                # 每次搜索最大结果数
```

### 8.2 工具配置
```python
# 原始工具
web_search_tool:
  - include_raw_content: true  # 问题所在
  - max_results: 3

# 新工具
search_overview:
  - include_raw_content: false
  - max_queries: 2
  - max_results_per_query: 3

selective_crawl:
  - max_content_length: 5000
  - max_urls: 3
```

## 9. 总结

Researcher的token超限问题源于：
1. **ReAct Agent的自主多次工具调用**
2. **复杂Step描述导致的多个子任务**
3. **工具返回过多数据（raw_content）**

解决方案的核心是：
1. **提供轻量级工具选项**
2. **引导Agent使用更高效的调用策略**
3. **在必要时限制Agent行为**

通过方案B（新工具组合）配合优化的提示词，可以在保持搜索质量的同时，显著减少token使用。