# 业务上下文分析提示词

## 目标
深度理解用户查询的业务背景和目标，识别分析类型和业务价值。

## 提示词模板

```
基于用户查询和基础分析结果，深度理解业务上下文：

原始查询: {query}
基础分析: {basic_analysis}

请分析：
1. 业务目标 (business_objective) - 用户想要解决什么业务问题？
2. 业务领域 (business_domain) - 属于哪个业务领域？可选值：retail, ecommerce, finance, marketing, operations, general
3. 分析类型 (analysis_type) - 可选值：descriptive（描述性）, diagnostic（诊断性）, predictive（预测性）, prescriptive（处方性）
4. 业务价值 (business_value) - 这个分析对业务的价值是什么？
5. 利益相关者 (stakeholders) - 谁会使用这个分析结果？
6. 紧急程度 (urgency_level) - 可选值：low, medium, high
7. 决策影响 (decision_impact) - 分析结果会影响哪些业务决策？

**重要：请以JSON格式返回结果，所有key必须使用英文。**

返回格式示例：
```json
{
  "business_objective": "了解沃尔玛订单数据的发展趋势，识别业务增长模式",
  "business_domain": "retail", 
  "analysis_type": "descriptive",
  "business_value": "帮助管理层了解业务发展状况，制定未来策略",
  "stakeholders": ["业务分析师", "管理层", "运营团队"],
  "urgency_level": "medium",
  "decision_impact": ["库存管理", "营销策略", "业务扩张"],
  "confidence_score": 0.85
}
```
```