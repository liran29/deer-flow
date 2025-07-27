# 数据实体映射配置

## 实体映射定义

本文件定义了业务概念到数据库表的映射关系，用于意图分析和查询生成。

## 核心业务实体

### 订单 (Orders)
**业务概念**: 客户购买商品的交易记录
```json
{
  "entity_name": "订单",
  "entity_name_en": "orders", 
  "table_mapping": {
    "primary_table": "walmart_orders",
    "database": "htinfo_db"
  },
  "key_attributes": [
    {
      "name": "订单ID",
      "field": "order_id",
      "type": "identifier"
    },
    {
      "name": "订单日期", 
      "field": "order_date",
      "type": "temporal"
    },
    {
      "name": "订单金额",
      "field": "total_amount", 
      "type": "numerical"
    },
    {
      "name": "客户ID",
      "field": "customer_id",
      "type": "identifier"
    },
    {
      "name": "订单状态",
      "field": "order_status",
      "type": "categorical"
    }
  ],
  "relationships": [
    {
      "target_entity": "商品",
      "relationship_type": "many_to_many",
      "description": "一个订单可包含多个商品"
    },
    {
      "target_entity": "客户", 
      "relationship_type": "many_to_one",
      "description": "多个订单属于一个客户"
    }
  ],
  "common_analysis_dimensions": [
    "时间维度（按日/月/年）",
    "状态维度（按订单状态）",
    "金额区间维度"
  ],
  "common_metrics": [
    {
      "name": "订单数量",
      "calculation": "COUNT(order_id)"
    },
    {
      "name": "总销售额", 
      "calculation": "SUM(total_amount)"
    },
    {
      "name": "平均订单价值",
      "calculation": "AVG(total_amount)"
    },
    {
      "name": "订单增长率",
      "calculation": "period_over_period_growth"
    }
  ]
}
```

### 商品 (Products/Items)
**业务概念**: 可销售的产品或服务
```json
{
  "entity_name": "商品",
  "entity_name_en": "products",
  "table_mapping": {
    "primary_table": "walmart_online_item",
    "database": "htinfo_db"
  },
  "key_attributes": [
    {
      "name": "商品ID",
      "field": "item_id", 
      "type": "identifier"
    },
    {
      "name": "商品类别",
      "field": "category",
      "type": "categorical"
    },
    {
      "name": "零售价格",
      "field": "RetailPrice",
      "type": "numerical"
    },
    {
      "name": "品牌",
      "field": "brand",
      "type": "categorical"
    },
    {
      "name": "商品名称",
      "field": "item_name",
      "type": "text"
    },
    {
      "name": "库存数量",
      "field": "stock_quantity",
      "type": "numerical"
    }
  ],
  "relationships": [
    {
      "target_entity": "订单",
      "relationship_type": "many_to_many", 
      "description": "多个商品可出现在多个订单中"
    },
    {
      "target_entity": "供应商",
      "relationship_type": "many_to_one",
      "description": "多个商品属于一个供应商"
    }
  ],
  "common_analysis_dimensions": [
    "类别维度（按商品类别）",
    "品牌维度（按品牌）", 
    "价格区间维度"
  ],
  "common_metrics": [
    {
      "name": "商品数量",
      "calculation": "COUNT(item_id)"
    },
    {
      "name": "平均价格",
      "calculation": "AVG(RetailPrice)"
    },
    {
      "name": "价格中位数",
      "calculation": "MEDIAN(RetailPrice)"
    },
    {
      "name": "库存总值",
      "calculation": "SUM(stock_quantity * RetailPrice)"
    }
  ]
}
```

### 客户 (Customers)
**业务概念**: 购买商品的个人或企业
```json
{
  "entity_name": "客户",
  "entity_name_en": "customers",
  "table_mapping": {
    "primary_table": "customers",
    "database": "htinfo_db"
  },
  "key_attributes": [
    {
      "name": "客户ID",
      "field": "customer_id",
      "type": "identifier"
    },
    {
      "name": "注册日期",
      "field": "registration_date", 
      "type": "temporal"
    },
    {
      "name": "客户位置",
      "field": "location",
      "type": "geographical"
    }
  ],
  "relationships": [
    {
      "target_entity": "订单",
      "relationship_type": "one_to_many",
      "description": "一个客户可有多个订单"
    }
  ],
  "common_analysis_dimensions": [
    "注册时间维度",
    "地理位置维度",
    "客户类型维度"
  ],
  "common_metrics": [
    {
      "name": "客户数量",
      "calculation": "COUNT(DISTINCT customer_id)"
    },
    {
      "name": "新客户数",
      "calculation": "COUNT(new_customers_in_period)"
    },
    {
      "name": "客户生命周期价值",
      "calculation": "customer_lifetime_value"
    }
  ]
}
```

## 跨实体分析模式

### 订单-商品分析
**常用场景**: 商品销售表现分析
```json
{
  "analysis_pattern": "order_product_analysis",
  "entities": ["订单", "商品"],
  "join_conditions": [
    "通过订单明细表关联"
  ],
  "common_queries": [
    "热销商品排行",
    "商品类别销售分析", 
    "商品价格与销量关系"
  ]
}
```

### 时间序列分析
**常用场景**: 趋势分析和预测
```json
{
  "analysis_pattern": "time_series_analysis",
  "temporal_field": "order_date",
  "granularities": ["daily", "weekly", "monthly", "quarterly", "yearly"],
  "common_metrics": [
    "订单量趋势",
    "销售额趋势", 
    "同比增长率",
    "环比增长率"
  ]
}
```

## 查询模板映射

### 趋势分析查询
**关键词**: 趋势, 增长, 变化, 发展
**对应实体**: 订单（主要）
**时间维度**: 必需
**典型指标**: 数量、金额、增长率

### 分类统计查询  
**关键词**: 统计, 分布, 分类, 类别
**对应实体**: 商品（主要）
**分类维度**: 必需
**典型指标**: 计数、占比、平均值

### 对比分析查询
**关键词**: 对比, 比较, 差异
**对应实体**: 多个实体或多个时间段
**对比维度**: 必需
**典型指标**: 差值、比率、排名