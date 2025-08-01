# 数据库研究架构文档

## 概述

数据库研究系统通过MindsDB集成，利用本地数据库资源提供了一个Token优化的Web搜索替代方案。该架构能够在不消耗外部API Token的情况下进行深度数据分析。

## 问题描述

- **Token限制**：Web搜索消耗大量Token，导致Token超限错误
- **本地数据未充分利用**：可用的数据库资源没有被有效使用
- **深度分析需求**：需要类似deep-research的综合数据分析能力

## 解决方案架构

### 核心组件

```
┌─────────────────────────────────────────────────────────────┐
│                    数据库研究流程                            │
├─────────────────────────────────────────────────────────────┤
│                                                             │
│  ┌─────────────────┐   ┌─────────────────┐   ┌──────────┐ │
│  │   调查节点      │──►│   计划节点      │──►│ 报告节点  │ │
│  │ Investigation   │   │    Planner      │   │ Reporter │ │
│  └─────────────────┘   └─────────────────┘   └──────────┘ │
│           │                     │                    │      │
│           ▼                     ▼                    ▼      │
│   ┌─────────────────┐  ┌──────────────┐   ┌─────────────┐ │
│   │ 数据库Schema    │  │  分析计划    │   │  最终报告   │ │
│   │ + LLM分析维度   │  │  (步骤列表)  │   │    输出     │ │
│   └─────────────────┘  └──────────────┘   └─────────────┘ │
│                                                             │
└─────────────────────────────────────────────────────────────┘
```

### 节点说明

#### 1. 数据库调查节点 (`database_investigation_node`)
**目的**：收集数据库Schema信息并分析查询维度

**处理过程**：
- 使用DatabaseSchemaManager获取数据库结构
- 使用LLM分析用户查询并建议数据分析维度
- 结合Schema信息与分析建议

**输出**：调查报告包含：
- 可用数据库结构
- LLM建议的分析维度
- 数据关系和可能性

#### 2. 数据库计划节点 (`database_planner_node`)
**目的**：基于调查结果生成结构化分析计划

**处理过程**：
- 接收调查结果作为输入
- 使用专门的数据库操作提示词模板
- 生成包含处理步骤的Plan对象（SQL查询、聚合等）

**输出**：结构化计划包含：
- 分析步骤（主要是`processing`类型，`need_search: false`）
- 每个步骤的明确目标
- 数据库操作的逻辑顺序

#### 3. 数据库报告节点 (`database_reporter_node`)
**目的**：生成综合分析报告（目前是概念性的）

**处理过程**：
- 接收调查结果和计划作为输入
- 基于计划模拟分析执行
- 生成综合报告结构

**输出**：分析报告包含：
- 执行摘要
- 方法概述
- 详细发现（概念性）
- 建议措施

## 配置系统

### 数据库Schema配置 (`config/database_schema.yaml`)

支持三种模式：

1. **静态模式（Static）**：手动配置的数据库Schema
2. **动态模式（Dynamic）**：从MindsDB实时获取Schema
3. **混合模式（Hybrid）**：静态和动态的结合

关键设置：
```yaml
mode: "dynamic"  # 或 "static" 或 "hybrid"
settings:
  max_tables_per_database: 3      # 每个数据库最多处理的表数量
  max_fields_per_table: 5         # 每个表最多显示的字段数量
  max_sample_records: 2           # 每个表最多显示的样本记录数量
  enable_enum_values: false       # 禁用以减少Token使用
```

### 数据库Schema管理器

管理数据库信息的核心组件：
- 处理配置加载
- 支持多种获取模式
- 为LLM消费格式化数据库信息
- 实现过滤和优化

## 提示词模板

### 1. `database_investigation.md`
- 在数据库上下文中分析用户查询
- 建议分析维度
- 为计划器构建输出结构

### 2. `database_planner.md`
- 聚焦数据库操作（70%以上的处理步骤）
- 强调SQL查询、连接、聚合
- 最小化外部搜索

### 3. `database_reporter.md`
- 生成综合报告
- 遵循商业分析结构
- 提供可行动的洞察

## 关键设计决策

### 1. 关注点分离
- 数据库代码与现有深度研究代码隔离
- 独立的节点文件（`nodes_database.py`）
- 独立的配置系统

### 2. Token优化
- 默认`enable_enum_values: false`
- 限制样本数据获取
- 聚焦的Schema信息

### 3. 处理优先方法
- 优先本地数据库操作
- 最小化外部搜索
- 充分利用SQL能力

### 4. LLM集成
- 使用基础模型以提高效率
- 计划的结构化输出
- 基于模板的提示

## 实现状态

### 已完成 ✅
- 数据库调查节点（含LLM集成）
- 数据库计划节点（结构化输出）
- 数据库报告节点（完整实现）
- 数据库研究团队节点（步骤协调）
- 数据库研究员节点（SQL执行）
- MindsDB工具集成（查询和表信息）
- 配置系统
- 提示词模板
- 完整图集成（含coordinator）
- 异步转同步工具适配（LangChain兼容）
- 查询中自动添加数据库前缀
- 样本数据限制（最多3行）

### 最近修复 🔧
- 修复`create_agent`参数以匹配LangChain API
- 修正代理响应处理（`result["messages"][-1].content`）
- 更新表信息查询使用`information_schema`
- 修复SQL查询包装问题
- 自动为表引用添加数据库前缀

### 待完成 🔄
- 自然语言转SQL（DeepSeek模型问题）
- 查询结果缓存优化性能
- 跨数据库连接操作
- 高级统计分析工具

## 使用示例

```python
# 使用用户查询初始化状态
state = State(
    messages=[{"role": "user", "content": "分析沃尔玛2024年的销售趋势"}],
    research_topic="分析沃尔玛2024年的销售趋势",
    locale='zh-CN'
)

# 流程执行
# 1. 调查 → 获取数据库Schema并分析查询
# 2. 计划 → 生成包含SQL操作的分析计划
# 3. 报告 → 基于计划创建概念性报告
```

## 查询优化策略

### 问题描述
数据库研究员执行了低效查询，获取大量数据集（如849行），导致：
- 性能问题和查询缓慢
- 内存使用过多
- 不必要的数据传输
- 潜在的Token消耗问题

### 解决方案：智能查询规划

#### 核心原则
1. **数据分析本质**：90%的数据分析是统计聚合，而非原始数据查看
2. **职责分离**：Planner制定策略决策，Researcher高效执行
3. **数据库层处理**：使用SQL聚合函数在源头处理数据

#### 增强的步骤模型
```python
class Step(BaseModel):
    title: str
    description: str
    query_strategy: Literal["aggregation", "sampling", "pagination", "window_analysis"] = "aggregation"
    batch_size: Optional[int] = None
    max_batches: Optional[int] = None
    sampling_rate: Optional[float] = None
    justification: str  # 选择此策略的理由
    expected_result_size: Literal["single_value", "small_set", "medium_set"] = "small_set"
```

#### 查询策略类型

1. **聚合查询**（90%的情况）：
   ```sql
   SELECT DATE(created_at), COUNT(*), SUM(amount) 
   FROM orders GROUP BY DATE(created_at)
   ```

2. **采样查询**（探索性分析）：
   ```sql
   SELECT * FROM large_table WHERE RAND() < 0.01 LIMIT 100
   ```

3. **分页查询**（需要详细数据时）：
   - 分批处理数据
   - 立即总结每批数据
   - 返回总结结果，而非原始数据

4. **窗口分析**（高级统计）：
   ```sql
   SELECT product_id, sales,
          ROW_NUMBER() OVER (ORDER BY sales DESC) as rank
   FROM product_sales WHERE rank <= 100
   ```

#### 示例："查看2024年所有订单"

**智能Planner生成：**
```python
Plan(steps=[
    Step(title="订单概况统计", 
         query_strategy="aggregation",
         justification="使用聚合函数获取基础指标"),
    Step(title="月度趋势分析",
         query_strategy="aggregation", 
         justification="时间序列分析，GROUP BY月份"),
    Step(title="类别分布分析",
         query_strategy="aggregation",
         justification="分类统计分析，GROUP BY类别"),
    Step(title="异常订单识别",
         query_strategy="sampling",
         batch_size=10,
         justification="只需少量样例用于说明")
])
```

**对应的高效查询：**
- 概况：`SELECT COUNT(*), SUM(amount), AVG(amount) FROM orders WHERE YEAR(date)=2024`
- 趋势：`SELECT MONTH(date), COUNT(*) FROM orders WHERE YEAR(date)=2024 GROUP BY MONTH(date)`
- 分布：`SELECT category, COUNT(*) FROM orders WHERE YEAR(date)=2024 GROUP BY category`
- 样例：`SELECT * FROM orders WHERE YEAR(date)=2024 AND amount > (SELECT AVG(amount)+3*STDDEV(amount) FROM orders WHERE YEAR(date)=2024) LIMIT 10`

### 实现状态
- ✅ 架构设计已完成
- 🔄 步骤模型增强待实现
- 🔄 Planner提示词更新待实现
- 🔄 Researcher执行逻辑更新待实现

## 未来增强

1. **高级统计函数**
   - 百分位数计算
   - 相关性分析
   - 时间序列分解

2. **查询性能监控**
   - 执行时间跟踪
   - 查询优化建议
   - 资源使用指标

3. **自适应批处理**
   - 动态批量大小调整
   - 内存感知处理
   - 渐进式结果流

## 测试

测试文件位于`tests/manual/`：
- `test_database_investigation_with_llm.py` - 测试调查节点
- `test_database_planner.py` - 测试计划工作流
- `test_database_research_team.py` - 测试完整的数据库研究工作流

### 运行测试
```bash
# 激活虚拟环境
. .venv/bin/activate

# 运行完整工作流测试
python tests/manual/test_database_research_team.py
```

## 注意事项

- 数据库研究员现在通过MindsDB执行真实的SQL查询
- 相比Web搜索，Token使用量显著减少
- 样本数据限制为3行以优化Token消耗
- 自动数据库前缀确保查询正确执行
- 完全集成LangGraph状态管理

## 背景说明

此方案的提出源于过去几天一直在解决Token超限的问题。用户明确表示：

> "我并不需要一个仅仅能够查询或者分析本地数据的工具，而是一个跟deep-research一样能够识别用户问题意图，做出本地数据查询、汇总、分类、分析等等计划，然后执行，最后给出report的deep-researcher。"

因此，本方案的核心是创建一个能够像deep-research一样进行深度分析，但使用本地数据库资源而非Web搜索的系统。