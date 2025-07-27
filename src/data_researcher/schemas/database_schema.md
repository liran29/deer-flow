# 数据库结构定义

## 数据库概览

本系统主要使用两个数据库：
- **htinfo_db**: 主要业务数据库，包含沃尔玛相关数据
- **ext_ref_db**: 外部参考数据库，包含汇率、税率等参考数据

## htinfo_db 数据库

### walmart_orders 表
**描述**: 沃尔玛订单数据表

| 字段名 | 数据类型 | 描述 | 示例值 |
|--------|----------|------|--------|
| order_id | VARCHAR(50) | 订单ID（主键） | "WM202401001" |
| order_date | DATE | 订单日期 | "2024-01-15" |
| total_amount | DECIMAL(10,2) | 订单总金额 | 156.78 |
| customer_id | VARCHAR(50) | 客户ID | "CUST001" |
| order_status | VARCHAR(20) | 订单状态 | "completed" |
| payment_method | VARCHAR(30) | 支付方式 | "credit_card" |
| shipping_address | VARCHAR(200) | 配送地址 | "123 Main St, City" |

**业务规则**:
- order_id 为主键，唯一标识订单
- total_amount 必须大于0
- order_status 可选值：pending, processing, completed, cancelled
- order_date 不能为空且不能是未来日期

### walmart_online_item 表
**描述**: 沃尔玛在线商品数据表

| 字段名 | 数据类型 | 描述 | 示例值 |
|--------|----------|------|--------|
| item_id | VARCHAR(50) | 商品ID（主键） | "ITEM001" |
| category | VARCHAR(100) | 商品类别 | "Electronics" |
| RetailPrice | DECIMAL(8,2) | 零售价格 | 29.99 |
| brand | VARCHAR(100) | 品牌名称 | "Samsung" |
| item_name | VARCHAR(200) | 商品名称 | "Samsung Galaxy Phone" |
| description | TEXT | 商品描述 | "Latest smartphone..." |
| stock_quantity | INT | 库存数量 | 150 |
| supplier_id | VARCHAR(50) | 供应商ID | "SUP001" |

**业务规则**:
- item_id 为主键，唯一标识商品
- RetailPrice 必须大于0
- category 不能为空
- stock_quantity 不能为负数

## ext_ref_db 数据库

### reference_data 表
**描述**: 外部参考数据表

| 字段名 | 数据类型 | 描述 | 示例值 |
|--------|----------|------|--------|
| ref_id | VARCHAR(50) | 参考数据ID（主键） | "REF001" |
| ref_type | VARCHAR(50) | 参考数据类型 | "exchange_rate" |
| ref_key | VARCHAR(100) | 参考键 | "USD_to_CNY" |
| ref_value | VARCHAR(500) | 参考值 | "7.25" |
| effective_date | DATE | 生效日期 | "2024-01-01" |
| source | VARCHAR(100) | 数据来源 | "central_bank" |

**业务规则**:
- ref_id 为主键
- ref_type 可选值：exchange_rate, tax_rate, holiday_calendar
- effective_date 用于时间有效性判断

## 数据关系

### 主要关联关系
1. **订单-商品关系**: 通过 order_items 中间表关联（如果存在）
2. **订单-客户关系**: walmart_orders.customer_id 关联客户信息
3. **商品-供应商关系**: walmart_online_item.supplier_id 关联供应商信息

### 常用查询模式
1. **时间序列分析**: 按 order_date 分组统计订单趋势
2. **商品分析**: 按 category 分组分析商品表现
3. **金额分析**: 对 total_amount 和 RetailPrice 进行聚合计算

## 数据质量说明

### 数据完整性
- walmart_orders: 约99%记录完整
- walmart_online_item: 约95%记录完整，部分商品描述可能为空

### 数据时效性
- 订单数据：实时更新
- 商品数据：每日更新
- 参考数据：根据需要更新

### 已知数据问题
1. 部分历史订单的customer_id可能为空
2. 商品价格可能存在异常值（过高或过低）
3. 商品类别命名可能不统一