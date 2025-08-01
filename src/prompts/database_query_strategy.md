# Database Query Strategy Guidance

This document provides specific execution guidance for different database query strategies to optimize performance and token usage.

## Critical Database Schema Rules

**IMPORTANT**: Always follow these rules when querying databases:
- Use exact table names as shown in schema: `walmart_orders`
- Use only existing field names:
  * id, category, subcategory, ItemDescription
  * UnitRetail (retail price), FirstCost (cost), nums (sales quantity)
  * year (year field - INTEGER type)
  * **NOTE**: NO `order_date` or `month` fields exist!
- For year filtering: use `WHERE year = 2024`
- Sales calculation: use `UnitRetail * nums`
- Avoid non-existent fields like month, order_date

## Query Strategy: AGGREGATION

**Purpose**: Statistical analysis using SQL aggregation functions (recommended for 90% of cases)

**Execution Guidelines**:
- Prioritize SQL aggregation functions: COUNT(), SUM(), AVG(), MAX(), MIN()
- Use GROUP BY for categorical analysis
- Focus on statistical insights, not raw data
- Query example:
  ```sql
  SELECT category, 
         COUNT(*) as product_count,
         SUM(nums) as total_quantity,
         SUM(UnitRetail * nums) as total_sales
  FROM walmart_orders 
  WHERE year = 2024 
  GROUP BY category
  ORDER BY total_sales DESC
  ```

## Query Strategy: SAMPLING

**Purpose**: Limited data sampling for exploration (5% of cases)

**Execution Guidelines**:
- Limit query results using LIMIT clause
- Focus on representative sample data
- Use conditional filtering for typical cases
- Query example:
  ```sql
  SELECT ItemDescription, category, nums, UnitRetail
  FROM walmart_orders 
  WHERE year = 2024 AND nums > 0
  ORDER BY nums DESC 
  LIMIT {batch_size}
  ```

## Query Strategy: PAGINATION

**Purpose**: Batch processing with immediate analysis (4% of cases)

**Execution Guidelines**:
- Process data in batches of {batch_size} records
- Analyze each batch immediately, don't accumulate
- Use OFFSET for pagination
- Query example:
  ```sql
  SELECT * FROM walmart_orders 
  WHERE year = 2024
  ORDER BY id 
  LIMIT {batch_size} OFFSET {offset}
  ```
- **Important**: Analyze each batch result immediately before requesting next batch

## Query Strategy: WINDOW_ANALYSIS

**Purpose**: Advanced analytics using window functions (1% of cases)

**Execution Guidelines**:
- Use window functions for ranking and cumulative analysis
- Suitable for TOP-N analysis and running totals
- Query example:
  ```sql
  SELECT category, ItemDescription, nums,
         RANK() OVER (PARTITION BY category ORDER BY nums DESC) as sales_rank,
         SUM(nums) OVER (PARTITION BY category) as category_total
  FROM walmart_orders 
  WHERE year = 2024
  ```

## Error Prevention

**Common Mistakes to Avoid**:
- ❌ `SELECT category, month, ...` (month field doesn't exist)
- ❌ `EXTRACT(YEAR FROM order_date)` (order_date field doesn't exist)
- ❌ `FROM orders` (table name should be walmart_orders)
- ❌ `WHERE order_date LIKE '2024%'` (use year = 2024 instead)

**Correct Patterns**:
- ✅ `SELECT category, year, COUNT(*) FROM walmart_orders`
- ✅ `WHERE year = 2024`
- ✅ `SUM(UnitRetail * nums) as total_sales`
- ✅ `GROUP BY category, year`