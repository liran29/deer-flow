# 技术需求分析提示词

## 目标
评估查询的技术实现要求，包括复杂度、资源需求和性能要求。

## 提示词模板

```
基于查询和数据需求，评估技术实现要求：

查询: {query}
数据需求: {data_requirements}

请评估：
1. 复杂度等级 (complexity_level) - 可选值：low, medium, high
2. 预估执行时间 (estimated_execution_time) - 考虑数据量和计算复杂度
3. 资源需求 (resource_requirements) - 内存、计算资源要求
4. 性能要求 (performance_requirements) - 响应时间、吞吐量等
5. 并行化可能 (parallelization_opportunities) - 哪些步骤可以并行执行？
6. 缓存策略 (caching_strategy) - 哪些结果可以缓存？
7. 数据量估算 (data_volume_estimation) - 预估需要处理的数据量
8. 瓶颈识别 (potential_bottlenecks) - 可能的性能瓶颈

**重要：请以JSON格式返回结果，所有key必须使用英文。**

返回格式示例：
```json
{
  "complexity_level": "medium",
  "estimated_execution_time": "2-5分钟",
  "resource_requirements": {
    "memory": "moderate",
    "compute": "moderate",
    "storage": "low"
  },
  "performance_requirements": {
    "max_response_time": "300s",
    "concurrent_users": 5,
    "data_freshness": "near_real_time"
  },
  "parallelization_opportunities": [
    "data_extraction",
    "basic_statistics", 
    "visualization_generation"
  ],
  "caching_strategy": [
    "table_metadata",
    "common_aggregations",
    "dimension_mappings"
  ],
  "data_volume_estimation": {
    "rows_processed": "10K-100K",
    "data_size": "10-100MB",
    "result_size": "1-10MB"
  },
  "potential_bottlenecks": [
    "large_table_joins",
    "complex_aggregations",
    "visualization_rendering"
  ],
  "optimization_recommendations": [
    "使用索引优化查询",
    "分批处理大数据集",
    "预计算常用指标"
  ]
}
```
```