# Token 优化方案讨论记录 - 2025-07-15

## 问题背景

在实际测试过程中，deer-flow 系统出现 token 超限问题：
- **具体错误**: 68,337 tokens 超过 DeepSeek 的 65,536 限制
- **发生位置**: 在 planner 阶段就出现超限，原因是 background_investigation 结果过大
- **影响**: 无法完成"Content Exists Risk"错误处理机制的测试

## 深度分析过程

### 1. 根因分析
- **Investigation Node**: `background_investigation_node` 是独立节点，不受现有 `pre_model_hook` token 管理保护
- **数据源**: Tavily 搜索返回详细的 `raw_content`、图片、图片描述
- **累积机制**: 所有搜索结果拼接成一个巨大字符串直接传递给 planner
- **配置问题**: `include_raw_content=True`, `include_images=True`, `include_image_descriptions=True`

### 2. 方案演进历程

#### 2.1 初始方案（被否决）
**立即可实施方案**:
- 减少 `max_search_results` 到 2-3
- 内容截断：每个结果限制到 500 tokens
- 移除 `raw_content` 和图片信息

**否决原因**: 用户明确拒绝减少搜索结果数量，认为可能需要更多而不是更少

#### 2.2 复杂方案（被质疑）
**分层传递 + 动态加载方案**:
1. Background investigation 生成智能摘要 + 保存详细内容
2. Planner 基于摘要做初步规划，标注需要详细信息的方面
3. 系统动态加载特定方面的详细内容
4. 支持多轮 planner 优化

**问题分析**:
- **工程复杂度高**: 需要大量代码修改和新组件
- **多轮复杂性**: 状态管理复杂，调试困难
- **实际 token 使用可能更高**: 多轮累积效应
- **过度工程化**: 在解决简单问题时引入复杂架构

#### 2.3 批判性反思
**Claude 自我批评**:
- 犯了典型的过度工程化错误
- 在试图解决复杂问题时忽略了简单方案
- 应该先从最直接的方法开始：减少 token 数量

#### 2.4 用户质疑的关键点
1. **Image 内容价值**: 对于 UI/UX、医疗影像、数据可视化等研究，图片信息有重要价值
2. **截断的负面影响**: 简单截断会破坏信息完整性，关键信息可能在后半部分

## 最终选定方案：智能信息压缩

### 核心思路
**更多搜索结果 + 智能压缩 = 更好的信息密度**

### 技术方案

#### 实施目标
```
原始：5个结果 × 4000 tokens = 20000 tokens
优化：8个结果 × 800 tokens = 6400 tokens  
收益：更多信息源 + 更少 token 使用
```

#### 代码实现框架
```python
def background_investigation_enhanced(state):
    """改进版background investigation - 使用LLM智能摘要"""
    
    # 1. 获取更多搜索结果
    searched_content = LoggedTavilySearch(
        max_results=8,  # 增加而不是减少
        include_raw_content=True,
        include_images=True,
    ).invoke(query)
    
    # 2. 对每个搜索结果使用LLM进行智能摘要
    compressed_results = []
    for item in searched_content:
        summary = llm_summarize_search_result(item, query)
        
        compressed_results.append({
            'title': item['title'],
            'url': item.get('url', ''),
            'summary': summary,
            'has_images': bool(item.get('images', []))
        })
    
    return format_for_planner(compressed_results)

def llm_summarize_search_result(content_item, query):
    """使用LLM对单个搜索结果进行智能摘要"""
    
    summary_prompt = f"""
    请对以下搜索结果进行摘要，保留与查询"{query}"最相关的关键信息：
    
    标题：{content_item['title']}
    内容：{content_item['content']}
    
    要求：
    1. 提取3-5个关键要点
    2. 保持信息准确性
    3. 控制在200字以内
    4. 突出与查询最相关的信息
    """
    
    summary = get_llm_by_type("basic").invoke([
        {"role": "user", "content": summary_prompt}
    ]).content
    
    return summary
```

### 方案优势

1. **满足用户需求**: 可以处理更多搜索结果，不减少信息源
2. **控制 token**: 通过LLM智能摘要而不是简单删减
3. **保持质量**: LLM理解内容并提取关键信息，而不是随意截断  
4. **实施简单**: 主要在当前节点内修改，避免复杂的多轮机制
5. **保留图片信息**: 通过 `has_images` 标记保留图片信息价值
6. **真正智能**: 利用LLM的理解能力进行内容压缩，而不是基于规则的文本处理

## 关键决策原则

### 1. 从简单开始
- 先尝试最直接的解决方案
- 验证效果后再考虑复杂化

### 2. 批判性思维
- 质疑复杂方案的必要性
- 优秀的 Coding Agent 应该避免过度工程化

### 3. 平衡约束条件
- 用户需求：更多搜索结果
- 技术限制：token 上限
- 质量要求：信息完整性

### 4. 智能压缩 vs 简单删减
- **LLM智能摘要 > 基于规则的文本提取**
- **理解内容含义 > 简单字符截断**
- **保持信息完整性 > 破坏信息结构**
- **针对查询相关性 > 随机删除**

## 后续实施计划

### 阶段1: 基础实现
- 实现 `llm_summarize_search_result` 函数
- 修改 `background_investigation_node` 使用LLM摘要
- 测试 token 使用量和信息质量

### 阶段2: 优化改进
- 根据实际效果调整摘要prompt
- 优化LLM摘要的质量和相关性
- 考虑查询意图分析来改进摘要重点

### 阶段3: 验证效果
- 测试原始的"Content Exists Risk"处理机制
- 验证 planner 规划质量是否受影响
- 监控系统整体性能

## 经验总结

1. **技术方案需要在理论正确性和实施复杂度之间平衡**
2. **用户的约束条件往往揭示了真实需求的复杂性**
3. **批判性思维对于避免过度工程化至关重要**
4. **简单方案的局限性需要通过实际场景来验证**
5. **信息密度优化是处理 token 限制的有效策略**
6. **LLM智能摘要比基于规则的文本处理更适合内容压缩**
7. **准确理解用户意图比急于实施更重要**

---

**讨论参与者**: 用户、Claude (Coding Agent)  
**时间**: 2025-07-15  
**状态**: 方案确定，待实施