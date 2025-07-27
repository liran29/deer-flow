# 数据需求分析提示词

## 目标
基于业务上下文，分析具体的数据需求，包括数据实体、指标和维度。

## 提示词模板

```
基于用户查询和业务上下文，分析具体的数据需求：

查询: {query}
业务上下文: {business_context}
可用数据源: {available_tables}

请分析：
1. 主要数据实体 (primary_entities) - 需要哪些核心数据对象？从可用数据源中选择
2. 次要数据实体 (secondary_entities) - 可能需要的补充数据？
3. 分析维度 (analysis_dimensions) - 需要按什么维度分析？
   - 时间维度 (temporal): 年、月、日、小时等
   - 分类维度 (categorical): 产品类别、地区、客户类型等  
   - 地理维度 (geographical): 国家、省份、城市等
4. 目标指标 (target_metrics) - 需要计算哪些指标？
   - 计数类 (count): 订单数量、用户数等
   - 金额类 (amount): 销售额、平均订单价值等
   - 比率类 (ratio): 增长率、转化率等
   - 统计类 (statistical): 平均值、最大值、最小值等
5. 数据关联 (data_relationships) - 不同数据源之间的关联关系
6. 时间范围 (time_range) - 分析的时间范围
7. 筛选条件 (filter_conditions) - 需要应用的筛选条件
8. 数据质量要求 (data_quality_requirements) - 对数据完整性、准确性的要求

**重要：请以JSON格式返回结果，所有key必须使用英文，确保引用的表名在可用数据源中存在。**

返回格式示例：
```json
{
  "primary_entities": [
    {
      "name": "订单",
      "table_name": "walmart_orders",
      "key_fields": ["order_id", "order_date", "total_amount"]
    }
  ],
  "secondary_entities": [
    {
      "name": "商品",
      "table_name": "walmart_online_item", 
      "key_fields": ["item_id", "category", "RetailPrice"]
    }
  ],
  "analysis_dimensions": [
    {
      "name": "时间",
      "type": "temporal",
      "granularity": "monthly",
      "required": true
    },
    {
      "name": "产品类别", 
      "type": "categorical",
      "field": "category",
      "required": false
    }
  ],
  "target_metrics": [
    {
      "name": "订单数量",
      "type": "count",
      "field": "order_id",
      "aggregation": "count"
    },
    {
      "name": "总销售额",
      "type": "amount", 
      "field": "total_amount",
      "aggregation": "sum"
    },
    {
      "name": "平均订单价值",
      "type": "amount",
      "field": "total_amount", 
      "aggregation": "avg"
    }
  ],
  "data_relationships": [
    {
      "type": "join",
      "left_table": "walmart_orders",
      "right_table": "walmart_online_item",
      "join_condition": "product_id"
    }
  ],
  "time_range": "最近12个月",
  "filter_conditions": [
    {
      "field": "order_status",
      "operator": "=", 
      "value": "completed"
    }
  ],
  "data_quality_requirements": [
    "订单日期不能为空",
    "订单金额必须大于0",
    "去除重复订单"
  ]
}
```
```