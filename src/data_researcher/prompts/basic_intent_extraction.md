# 基础意图提取提示词

## 目标
从用户查询中提取基础意图信息，为后续深度分析提供基础。

## 提示词模板

```
分析以下用户查询，提取基础信息：

查询: {query}

请提取：
1. 主要关键词 (main_keywords)
2. 动作词 (action_words) - 如：分析、统计、查询、对比等
3. 数据对象 (data_objects) - 如：订单、商品、用户等
4. 时间相关词汇 (time_related)
5. 数量/金额相关词汇 (metrics_related)
6. 业务相关词汇 (business_related)
7. 公司/品牌名称 (entities)

**重要：请以JSON格式返回结果，所有key必须使用英文。**

返回格式示例：
```json
{
  "main_keywords": ["分析", "订单", "趋势"],
  "action_words": ["分析"],
  "data_objects": ["订单"],
  "time_related": ["趋势"],
  "metrics_related": ["数据"],
  "business_related": ["沃尔玛"],
  "entities": ["沃尔玛"],
  "extraction_confidence": 0.8
}
```

注意：key字段使用英文，value内容保持原始语言（中文词汇保持中文）。
```