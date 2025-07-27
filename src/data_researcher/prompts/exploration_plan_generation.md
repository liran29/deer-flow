# 数据探索计划生成提示词

## 目标
基于数据分析意图，生成详细的多步骤数据探索和分析计划，类似于deep-research中的planner，但专注于数据分析workflow。

## 提示词模板

```
基于数据分析意图，制定详细的数据探索和分析计划：

分析意图：
- 业务目标: {business_objective}
- 业务领域: {business_domain}
- 分析类型: {analysis_type}
- 主要数据实体: {primary_entities}
- 目标指标: {target_metrics}
- 分析维度: {analysis_dimensions}
- 复杂度等级: {complexity_level}

请制定包含以下步骤类型的详细计划：

1. 数据探索步骤 (data_exploration)
   - 了解数据规模、质量、分布
   - 识别数据完整性问题
   - 分析数据字段特征

2. 数据清洗步骤 (data_cleaning) 
   - 处理缺失值
   - 识别和处理异常值
   - 数据标准化和格式化

3. 特征工程步骤 (feature_engineering)
   - 创建派生指标
   - 时间序列特征提取
   - 分类变量编码

4. 统计分析步骤 (statistical_analysis)
   - 描述性统计
   - 相关性分析
   - 分布分析

5. 深度分析步骤 (deep_analysis)
   - 趋势分析
   - 模式识别
   - 异常检测
   - 预测建模（如适用）

6. 可视化步骤 (visualization)
   - 创建图表和仪表板
   - 数据故事叙述

7. 洞察提取步骤 (insight_extraction)
   - 从分析结果中提取业务洞察
   - 识别关键发现和模式

8. 报告生成步骤 (report_generation)
   - 整合所有分析结果
   - 形成结构化报告

每个步骤请包含：
- step_id: 步骤唯一标识
- step_name: 步骤名称
- step_type: 步骤类型（上述8类之一）
- description: 详细描述
- inputs: 输入要求
- outputs: 预期输出
- tools: 需要使用的工具
- estimated_time: 预估执行时间
- dependencies: 依赖的前置步骤
- parallel_possible: 是否可与其他步骤并行
- priority: 优先级 (high/medium/low)

**重要：请以JSON格式返回结果，所有key必须使用英文。**

返回格式示例：
```json
{
  "plan_id": "data_analysis_plan_001",
  "plan_name": "沃尔玛订单数据趋势分析计划",
  "total_estimated_time": "15-25分钟",
  "complexity_assessment": "medium",
  "steps": [
    {
      "step_id": "explore_001",
      "step_name": "订单数据基础探索",
      "step_type": "data_exploration",
      "description": "分析walmart_orders表的基础信息，包括数据量、时间范围、字段完整性",
      "inputs": ["walmart_orders表访问权限"],
      "outputs": ["数据概览报告", "数据质量评估"],
      "tools": ["MindsDBQueryTool", "DataProfilingTool"],
      "estimated_time": "2-3分钟",
      "dependencies": [],
      "parallel_possible": true,
      "priority": "high"
    },
    {
      "step_id": "clean_001", 
      "step_name": "数据质量清理",
      "step_type": "data_cleaning",
      "description": "处理订单数据中的缺失值和异常值",
      "inputs": ["数据质量评估结果"],
      "outputs": ["清洗后的数据集"],
      "tools": ["DataCleaningTool"],
      "estimated_time": "3-5分钟",
      "dependencies": ["explore_001"],
      "parallel_possible": false,
      "priority": "high"
    }
  ],
  "execution_strategy": {
    "parallel_groups": [
      ["explore_001", "explore_002"],
      ["clean_001"],
      ["analysis_001", "viz_001"]
    ],
    "critical_path": ["explore_001", "clean_001", "analysis_001", "report_001"],
    "optimization_notes": ["数据探索步骤可并行执行", "可视化可与分析并行进行"]
  },
  "risk_assessment": {
    "data_availability_risk": "low",
    "complexity_risk": "medium", 
    "performance_risk": "low",
    "mitigation_strategies": ["增加数据验证步骤", "分批处理大数据集"]
  },
  "success_criteria": [
    "完成所有预定指标的计算",
    "生成至少3个关键业务洞察",
    "创建2-3个可视化图表",
    "形成完整的分析报告"
  ]
}
```
```