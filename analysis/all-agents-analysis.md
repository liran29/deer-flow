# Deer-Flow 所有Agent完整分析

## 主要研究工作流Agent

### 1. **coordinator** (协调员)
- **位置**: `src/graph/nodes.py:coordinator_node()`
- **LLM类型**: basic
- **工具**: handoff_to_planner工具
- **作用**: 
  - 解析用户输入
  - 提取research_topic和locale
  - 决定是否进入研究流程
- **Token影响**: 轻微 (~200 tokens)

### 2. **planner** (规划员)  
- **位置**: `src/graph/nodes.py:planner_node()`
- **LLM类型**: basic
- **工具**: 无工具，纯LLM推理
- **作用**:
  - 生成详细研究计划
  - 创建结构化的Plan对象
  - 包含背景调查结果
- **Token影响**: 重大 (~4000 tokens)
  - 包含完整background_investigation_results
  - 详细的planner prompt模板

### 3. **researcher** (研究员)
- **位置**: `src/graph/nodes.py:researcher_node()`  
- **LLM类型**: basic
- **工具**: 
  - Web search tool
  - Crawl tool  
  - Local retriever tool (如果有resources)
  - MCP tools (动态加载)
- **作用**:
  - 执行研究步骤
  - 收集信息和证据
  - 生成研究发现
- **Token影响**: 累积性爆炸
  - Step 1: ~2000 tokens
  - Step 2: ~5000 tokens (包含Step 1)
  - Step 3: ~8000 tokens (包含Step 1&2)

### 4. **coder** (编码员)
- **位置**: `src/graph/nodes.py:coder_node()`
- **LLM类型**: basic  
- **工具**:
  - Python REPL tool
  - MCP tools (动态加载)
- **作用**:
  - 执行数据处理步骤
  - 代码分析和计算
  - 生成量化结果
- **Token影响**: 与researcher相同的累积模式

### 5. **reporter** (报告员)
- **位置**: `src/graph/nodes.py:reporter_node()`
- **LLM类型**: basic
- **工具**: 无工具，纯LLM推理
- **作用**:
  - 综合所有研究发现
  - 生成最终报告
  - 应用报告样式格式化
- **Token影响**: 最大 (~15000+ tokens)
  - 包含所有observations
  - 详细的reporter prompt模板

## 专业化Agent (非研究工作流)

### 6. **podcast_script_writer** (播客脚本写手)
- **位置**: `src/podcast/graph/script_writer_node.py`
- **LLM类型**: basic
- **工具**: 无
- **作用**: 将研究报告转换为播客脚本
- **使用模式**: 直接LLM调用，非agent框架

### 7. **ppt_composer** (PPT组成员)
- **位置**: `src/ppt/graph/ppt_composer_node.py`  
- **LLM类型**: basic
- **工具**: 无
- **作用**: 将研究报告转换为PPT内容
- **使用模式**: 直接LLM调用，非agent框架

### 8. **prompt_enhancer** (提示增强器)
- **位置**: `src/prompt_enhancer/graph/enhancer_node.py`
- **LLM类型**: basic
- **工具**: 无
- **作用**: 增强和优化用户提示词
- **使用模式**: 直接LLM调用，非agent框架

### 9. **prose_writer** (散文写手)
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

## Agent调用模式分析

### 1. **ReAct Agent框架** (主要研究流程)
```python
# 使用create_agent创建的真正agent
agent = create_agent(agent_type, agent_type, tools, agent_type)
result = await agent.ainvoke(input=agent_input, config={"recursion_limit": recursion_limit})
```

**使用此模式的Agent**:
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

**使用此模式的Agent**:
- podcast_script_writer
- ppt_composer
- prompt_enhancer
- prose_writer (所有变体)

**特点**:
- 单次调用，无工具
- 简单的输入输出
- 不参与累积上下文
- Token消耗相对固定

## Token累积的关键Agent

### **累积性Agent** (问题来源)
1. **researcher**: 每个step累积前面所有step的结果
2. **coder**: 与researcher相同的累积模式  
3. **reporter**: 接收所有累积的observations

### **非累积性Agent** (相对安全)
1. **coordinator**: 只处理初始输入
2. **planner**: 虽然包含background results，但只执行一次
3. **专业化agent**: 独立调用，不参与主工作流

## 解决Token问题的Agent优先级

### **高优先级** (必须解决)
1. **researcher/coder**: 修改completed_steps_info构建逻辑
2. **reporter**: 修改observations处理逻辑

### **中等优先级** (可以优化)  
1. **planner**: 压缩background_investigation_results

### **低优先级** (影响较小)
1. **coordinator**: 已经比较轻量
2. **专业化agent**: 不参与主要累积问题

## 关键发现

1. **真正的Agent只有5个**: coordinator, planner, researcher, coder, reporter
2. **Token爆炸的源头**: researcher和coder的completed_steps_info累积机制
3. **最终的Token爆炸点**: reporter接收所有observations
4. **专业化功能**: 使用直接LLM调用，不是问题源头

因此，解决token超限问题的关键是：
- **修改researcher/coder的上下文构建逻辑**
- **优化reporter的observations处理**
- **保持专业化agent的简单调用模式**