# 背景调查查询优化方案

## 背景

在测试背景调查功能时发现，中文查询"沟尔玛在线商城最近推出了哪些新的热门圣诞节装饰品商品类别？"返回的搜索结果质量极差，问题率高达686.7%，质量评级为D级。

## 问题发现过程

### 初始问题现象
- 搜索结果15个，但只有1个与查询相关
- 大量结果来自scribd.com（PDF文档分享网站）
- 内容多为无关文档：外贸心得、人脉管理、增长黑客等

### 错误的初始判断
最初认为是域名过滤配置问题：
- 怀疑`include_domains`配置不生效
- 认为需要添加walmart.com等域名

### 发现真正原因
通过对比测试发现：
- **中文查询**："沃尔玛在线商城..." → 结果来自scribd.com等文档网站
- **英文查询**："Walmart Christmas decorations 2024" → 结果来自walmart.com, youtube.com等相关网站

**核心问题：中文查询与英文网站内容的语言匹配问题**

## 根本原因分析

### 1. 语言障碍
- 配置的域名（walmart.com等）内容主要是英文
- 中文查询无法有效匹配英文网站内容
- Tavily只能在scribd.com等网站找到中文PDF文档

### 2. 查询策略问题
**完整问句 vs 关键词搜索的逻辑冲突：**
- ❌ **原查询**："沃尔玛在线商城最近推出了哪些新的热门圣诞节装饰品商品类别？"
- ✅ **优化查询**："Walmart Christmas decorations 2024 new categories"

**搜索引擎更适合：**
- 核心关键词组合
- 具体实体名词  
- 简洁明确的概念

**不适合：**
- 自然语言完整问句
- 包含修饰词的长句
- 概念过于抽象的查询

## 解决方案设计

### 核心策略
1. **中文→英文翻译**：自动将中文查询翻译为地道英文
2. **问句→关键词优化**：从自然语言问句提取搜索关键词
3. **多查询策略**：生成多个角度的关键词组合

### 关键词提取逻辑

**原问句：** "沃尔玛在线商城最近推出了哪些新的热门圣诞节装饰品商品类别？"

**提取过程：**
```
实体提取:
- 沃尔玛 → Walmart
- 在线商城 → online store (可省略，Walmart已含此意)

概念提取:
- 圣诞节装饰品 → Christmas decorations  
- 商品类别 → categories
- 最近/新的 → new/2024/2025
- 热门 → popular/trending

去除冗余:
- "最近推出了哪些" → 简化为年份标识
- "新的热门" → 简化为 new/popular
```

**优化后关键词：**
```
Query1: "Walmart Christmas decorations 2024 2025 new categories"
Query2: "Christmas decor trends 2024 2025 Walmart online"
Query3: "popular Christmas decorations 2024 2025 Walmart" 
Query4: "Walmart holiday decor categories latest 2024 2025"
```

### 时效性处理

**当前时间：2025年8月7日**

**时间策略：最近两年并列**
- 包含2024年（最近的圣诞节）
- 包含2025年（即将到来的圣诞节）
- 动态年份计算，避免硬编码

```python
def get_recent_years(current_year=2025):
    """获取最近两年"""
    return [current_year, current_year - 1]  # [2025, 2024]
```

### 搜索调用策略

**选择：简单多次搜索**
```python
def multi_query_search(optimized_queries, max_results_per_query=3):
    """多次搜索策略"""
    all_results = []
    for query in optimized_queries:
        results = tavily_search(query, max_results=max_results_per_query)
        all_results.extend(results)
    return remove_duplicate_urls(all_results)
```

**考虑过的其他策略（暂未采用）：**
- 单次优化查询（信息覆盖不够全面）
- 分层搜索（逻辑复杂，通用性差）
- 自适应搜索（实现复杂度高）

## 实施计划

### 第一阶段：查询优化
1. 实现中文→英文翻译函数
2. 实现问句→关键词提取函数  
3. 实现时效性年份处理
4. 集成到background_investigation_node_enhanced

### 第二阶段：搜索策略
1. 实现多查询搜索函数
2. 实现基于URL的结果去重
3. 测试验证搜索质量改善效果

### 第三阶段：质量评估
1. 建立搜索结果质量评估标准
2. 对比优化前后的效果
3. 根据结果调整参数

## 关键设计原则

1. **语言匹配优先**：英文网站用英文查询
2. **关键词思维**：从问答思维转向搜索思维
3. **时效性保证**：动态处理时间相关查询
4. **简单有效**：避免过度工程化
5. **通用性考虑**：方案应适用于各种查询类型

## 预期效果

**优化前：**
- 问题率：686.7%
- 质量评级：D级
- 相关结果：1/15个

**优化后预期：**
- 问题率：<50%
- 质量评级：B级以上  
- 相关结果：>80%

## 后续优化方向

1. **LLM辅助查询优化**：使用LLM进行更智能的查询词生成
2. **领域特定优化**：针对不同领域（商品、新闻、技术）的专门优化
3. **结果质量过滤**：基于LLM的搜索结果质量评估和过滤
4. **多语言支持**：支持更多语言的查询优化

## 相关文件

- 配置文件：`conf.yaml` - 域名过滤和功能开关配置
- 核心节点：`src/graph/nodes_enhanced.py` - 背景调查节点实现
- 测试文件：`tests/manual/test_background_investigation_quality.py` - 质量测试
- 功能配置：`src/utils/enhanced_features.py` - 功能开关管理

---

**创建时间：** 2025-08-07  
**讨论参与者：** Claude Code & User  
**问题类型：** 搜索质量优化  
**解决状态：** 方案确定，待实施