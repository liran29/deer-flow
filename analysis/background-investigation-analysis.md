# Background Investigation Node 详细分析

## 节点概述

`background_investigation_node` 是独立的数据收集节点，位于工作流的早期阶段，为 planner 提供背景信息。但正是这个节点可能导致 planner 阶段的 token 超限问题。

## 工作流位置

```
START → coordinator → background_investigation_node → planner → ...
```

从 `builder.py` 可以看到：
- Line 42: `builder.add_node("background_investigator", background_investigation_node)`
- Line 49: `builder.add_edge("background_investigator", "planner")`

## 核心逻辑分析

### 1. 节点触发条件
在 `coordinator_node` 中决定（nodes.py:228-230）：
```python
if state.get("enable_background_investigation"):
    goto = "background_investigator"
```

### 2. 搜索引擎选择
节点支持多种搜索引擎（nodes.py:53-73）：
- **Tavily**（默认）：使用 `LoggedTavilySearch`
- **DuckDuckGo**：使用标准web搜索
- **Brave Search**：需要API key
- **Arxiv**：学术论文搜索

### 3. Tavily搜索配置（最常用）
```python
LoggedTavilySearch(
    max_results=configurable.max_search_results,  # 默认搜索结果数量
    include_raw_content=True,                     # 包含原始内容
    include_images=True,                          # 包含图片
    include_image_descriptions=True,              # 包含图片描述
    include_domains=include_domains,              # 包含指定域名
    exclude_domains=exclude_domains,              # 排除指定域名
)
```

## Token 超限的根本原因

### 1. 搜索结果内容冗余
- **Raw Content**: 每个搜索结果包含完整的原始网页内容
- **Rich Content**: 包含图片、图片描述、元数据等
- **多结果累积**: `max_search_results` 数量的结果全部包含

### 2. 结果格式化问题
在 nodes.py:58-64：
```python
background_investigation_results = [
    f"## {elem['title']}\n\n{elem['content']}" for elem in searched_content
]
return {
    "background_investigation_results": "\n\n".join(
        background_investigation_results
    )
}
```

**问题**：
- 每个搜索结果都被格式化为完整的markdown段落
- 所有结果通过 `\n\n` 连接成一个巨大的字符串
- 没有内容长度限制或截断机制

### 3. 传递给 Planner 的数据量
在 `planner_node` 中（nodes.py:90-102）：
```python
if state.get("enable_background_investigation") and state.get("background_investigation_results"):
    messages += [
        {
            "role": "user", 
            "content": (
                "background investigation results of user query:\n"
                + state["background_investigation_results"]  # 完整的搜索结果
                + "\n"
            ),
        }
    ]
```

**问题**：完整的 background_investigation_results 直接添加到 planner 的 messages 中，没有任何压缩或摘要。

## Token 超限场景分析

### 高风险场景
1. **复杂查询主题**：涉及多个方面的主题（如"AI医疗应用"）
2. **热门话题**：搜索结果丰富，每个结果内容详细
3. **学术或技术主题**：内容密度高，专业术语多
4. **设置较高的 max_search_results**：默认值过大

### Token 计算示例
假设 `max_search_results=5`，每个搜索结果：
- Title: ~50 tokens
- Content: ~2000-5000 tokens  
- 格式化开销: ~20 tokens

**总计**: 5 × (50 + 3000 + 20) = ~15,000 tokens

如果搜索结果特别详细：
- 每个结果 5000+ tokens
- 总计可能达到 25,000+ tokens

**加上 planner prompt 和其他上下文**：轻松超过 30,000+ tokens

## 关键配置项

### 1. 搜索结果数量控制
```python
configurable.max_search_results  # 在 Configuration 中设置
```

### 2. 搜索引擎选择
```python
SELECTED_SEARCH_ENGINE = os.getenv("SEARCH_API", SearchEngine.TAVILY.value)
```

### 3. Tavily 特定配置
从 `conf.yaml` 的 `SEARCH_ENGINE` 部分：
- `include_domains`: 限制搜索域名
- `exclude_domains`: 排除特定域名  
- `max_results`: 结果数量限制

## 解决方案建议

### 1. 立即可实施
- **减少 max_search_results**：从默认值改为 2-3
- **内容截断**：对每个搜索结果的 content 进行长度限制
- **移除 raw_content**：设置 `include_raw_content=False`

### 2. 中期优化
- **智能摘要**：对搜索结果进行AI摘要后再传递给planner
- **相关性过滤**：只保留与查询最相关的结果
- **分层传递**：先传递摘要，需要时再获取详细内容

### 3. 长期架构改进
- **流式处理**：逐个处理搜索结果，而不是一次性加载所有
- **外部存储**：将详细内容存储在外部，只传递引用和摘要
- **动态加载**：planner 根据需要请求特定的背景信息

## 当前 Token 管理的盲点

**Background Investigation 不受现有 token 管理保护**：
- `pre_model_hook` 只在 agent 调用前触发
- Background investigation 是简单的工具调用，不经过 agent 框架
- 结果直接进入 state，然后传递给 planner
- Planner 接收时，token 累积已经完成

这解释了为什么在 planner 阶段就出现 token 超限的情况。