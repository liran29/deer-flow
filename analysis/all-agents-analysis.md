# Deer-Flow 完整工作流和Token分析

## 主要研究工作流节点

### 1. **coordinator** (协调员)
- **位置**: `src/graph/nodes.py:coordinator_node()`
- **LLM类型**: basic
- **工具**: handoff_to_planner工具
- **作用**: 
  - 解析用户输入
  - 提取research_topic和locale
  - 决定是否进入研究流程
- **Token影响**: 轻微 (~200 tokens)
- **调用次数**: 1次

### 2. **background_investigator** (背景调查员)
- **位置**: `src/graph/nodes.py:background_investigation_node()`
- **LLM类型**: 无LLM调用（使用搜索API）
- **工具**: Tavily搜索或Web搜索
- **作用**:
  - 获取研究主题的背景信息
  - 为planner提供初始上下文
- **Token影响**: 输出到state (~3000-8000 tokens)
- **调用次数**: 1次

### 3. **planner** (规划员)  
- **位置**: `src/graph/nodes.py:planner_node()`
- **LLM类型**: basic
- **工具**: 无工具，纯LLM推理
- **作用**:
  - **第一次调用**: 基于背景调查生成研究计划
  - **第二次调用**: 评估研究完成度，决定是否生成报告
- **输入数据**:
  - 第一次: research_topic + background_investigation_results
  - 第二次: 同上 + 所有completed steps (通过state传递)
- **Token影响**: 重大 (~4000-6000 tokens)
- **调用次数**: 通常2次

### 4. **human_feedback** (人工反馈)
- **位置**: `src/graph/nodes.py:human_feedback_node()`
- **LLM类型**: 无LLM调用
- **作用**: 等待用户确认研究计划
- **Token影响**: 无
- **调用次数**: 1次

### 5. **research_team** (研究团队协调)
- **位置**: `src/graph/nodes.py:research_team_node()`
- **LLM类型**: 无LLM调用（路由节点）
- **作用**: 通过条件判断路由到具体执行节点
- **Token影响**: 无
- **调用次数**: 每个步骤1次

### 6. **researcher** (研究员)
- **位置**: `src/graph/nodes.py:researcher_node()`  
- **LLM类型**: basic (ReAct框架)
- **工具**: 
  - Web search tool
  - Crawl tool  
  - Local retriever tool (如果有resources)
  - MCP tools (动态加载)
- **作用**:
  - 执行RESEARCH类型的步骤
  - 收集信息和证据
  - 生成研究发现
- **Token累积机制**: 
  - Step 1: 基础prompt + 当前任务 (~2000 tokens)
  - Step 2: 基础prompt + Step1结果 + 当前任务 (~5000 tokens)
  - Step 3: 基础prompt + Step1&2结果 + 当前任务 (~8000 tokens)
  - Step N: 指数级增长
- **调用次数**: 每个RESEARCH步骤1次

### 7. **coder** (编码员)
- **位置**: `src/graph/nodes.py:coder_node()`
- **LLM类型**: basic (ReAct框架)
- **工具**:
  - Python REPL tool
  - MCP tools (动态加载)
- **作用**:
  - 执行PROCESSING类型的步骤
  - 代码分析和计算
  - 生成量化结果
- **Token影响**: 与researcher相同的累积模式
- **调用次数**: 每个PROCESSING步骤1次

### 8. **reporter** (报告员)
- **位置**: `src/graph/nodes.py:reporter_node()`
- **LLM类型**: basic
- **工具**: 无工具，纯LLM推理
- **作用**:
  - 综合所有研究发现
  - 生成最终报告
  - 应用报告样式格式化
- **输入数据**: current_plan + 所有observations
- **Token影响**: 最大 (~15000+ tokens)
- **调用次数**: 1次

## 专业化Agent (非研究工作流)

### 9. **podcast_script_writer** (播客脚本写手)
- **位置**: `src/podcast/graph/script_writer_node.py`
- **LLM类型**: basic
- **工具**: 无
- **作用**: 将研究报告转换为播客脚本
- **使用模式**: 直接LLM调用，非agent框架

### 10. **ppt_composer** (PPT组成员)
- **位置**: `src/ppt/graph/ppt_composer_node.py`  
- **LLM类型**: basic
- **工具**: 无
- **作用**: 将研究报告转换为PPT内容
- **使用模式**: 直接LLM调用，非agent框架

### 11. **prompt_enhancer** (提示增强器)
- **位置**: `src/prompt_enhancer/graph/enhancer_node.py`
- **LLM类型**: basic
- **工具**: 无
- **作用**: 增强和优化用户提示词
- **使用模式**: 直接LLM调用，非agent框架

### 12. **prose_writer** (散文写手)
- **位置**: `src/prose/graph/prose_*_node.py` (多个变体)
- **LLM类型**: basic
- **工具**: 无
- **作用**: 文本处理和优化
- **变体**:
  - prose_continue: 继续写作
  - prose_fix: 修复文本
  - prose_improve: 改进文本  
  - prose_longer: 延长文本
  - prose_shorter: 缩短文本
  - prose_zap: 文本处理

## 完整数据流分析

### 工作流调用顺序
```
用户输入
    ↓
coordinator (提取research_topic, locale)
    ↓
background_investigator (生成background_investigation_results)
    ↓
planner [第一次] (基于背景调查 + research_topic)
    ↓ [has_enough_context=false]
human_feedback (计划确认)
    ↓
research_team (路由分发) → researcher/coder (循环执行所有步骤)
    ↓ [所有步骤完成]
planner [第二次] (基于背景调查 + 所有研究结果)
    ↓ [has_enough_context=true]
reporter (基于current_plan + observations)
    ↓
END
```

### State数据重复分析

**重复存储的内容**:
- `observations[]` = [研究结果1, 研究结果2, 研究结果3]
- `current_plan.steps[i].execution_res` = 同样的研究结果

**LLM调用中的数据使用**:
- **Researcher**: 只使用 `step.execution_res` (completed_steps_info)
- **Planner**: 通过模板注入state，但不直接使用重复字段
- **Reporter**: 只使用 `observations`

**结论**: 虽然state中有重复存储，但没有在同一次LLM调用中重复传递

### Token累积机制详解

**Researcher步骤累积**:
```
Step 1执行: 只有当前任务
Step 2执行: Step1结果 + 当前任务
Step 3执行: Step1结果 + Step2结果 + 当前任务  
Step N执行: 所有前面步骤结果 + 当前任务
```

**关键发现**: 每增加一个step，输入token都会累积增长，这是token指数级增长的根本原因

## Agent调用模式分析

### 1. **ReAct Agent框架** (主要研究流程)
```python
# 使用create_agent创建的真正agent
agent = create_agent(agent_type, agent_type, tools, agent_type)
result = await agent.ainvoke(input=agent_input, config={"recursion_limit": recursion_limit})
```

**使用此模式的节点**:
- coordinator
- planner  
- researcher
- coder
- reporter

**特点**:
- 支持工具调用
- 支持多轮推理
- 包含pre_model_hook token管理
- 累积式上下文传递

### 2. **直接LLM调用** (专业化功能)
```python
# 直接使用LLM，不通过agent框架
model = get_llm_by_type(AGENT_LLM_MAP["agent_name"])
result = model.invoke([SystemMessage(...), HumanMessage(...)])
```

**使用此模式的节点**:
- podcast_script_writer
- ppt_composer
- prompt_enhancer
- prose_writer (所有变体)

**特点**:
- 单次调用，无工具
- 简单的输入输出
- 不参与累积上下文
- Token消耗相对固定

## Token累积问题根源分析

### **累积性节点** (Token爆炸源头)
1. **researcher**: 每个step累积前面所有step的结果
   - 核心问题: `completed_steps_info` 构建逻辑
   - 影响: 指数级token增长

2. **coder**: 与researcher相同的累积模式  
   - 同样的累积机制
   - 同样的token风险

3. **reporter**: 接收所有累积的observations
   - 最终的token爆炸点
   - 包含所有研究步骤的完整结果

### **非累积性节点** (相对安全)
1. **coordinator**: 只处理初始输入
2. **background_investigator**: 单次搜索调用
3. **planner**: 虽然包含背景结果，但调用次数固定
4. **专业化节点**: 独立调用，不参与主工作流

### **Planner的特殊情况**
- **第一次调用**: 基于背景调查，token量可控
- **第二次调用**: 包含所有研究结果，但通过state传递，不重复计算
- **investigation结果**: 两次调用都包含，持久存储在state中

## 解决Token问题的优化策略

### **高优先级** (必须解决)
1. **researcher/coder累积优化**:
   - 限制completed_steps_info的长度
   - 使用摘要而非完整结果
   - 实施滑动窗口机制

2. **reporter输入优化**:
   - 压缩observations内容
   - 智能筛选相关信息

### **中等优先级** (已部分解决)
1. **background_investigation压缩**: 已实施LLM摘要方案
2. **搜索结果过滤**: 已实施内容验证机制

### **低优先级** (影响较小)
1. **coordinator**: 已经比较轻量
2. **专业化节点**: 不参与主要累积问题

## 关键发现和结论

### **数据流特点**
1. **主要工作流节点**: 8个 (coordinator → background_investigator → planner → human_feedback → research_team → researcher/coder → planner → reporter)
2. **专业化功能节点**: 4个 (独立的文档处理功能)
3. **Token累积机制**: researcher/coder的completed_steps_info是根本原因
4. **数据重复**: state中有重复存储，但LLM调用中无重复传递

### **优化成果**
1. ✅ **Background investigation智能压缩**: 已实施LLM摘要
2. ✅ **搜索结果过滤**: 已实施内容验证
3. ✅ **Template渲染修复**: 已解决空变量问题
4. 🔄 **Researcher累积优化**: 待进一步实施

### **下一步重点**
- **核心问题**: researcher/coder的completed_steps_info累积机制需要根本性优化
- **解决方案**: 实施智能摘要或滑动窗口，避免无限累积
- **目标**: 将token增长从指数级降低到线性或常量级