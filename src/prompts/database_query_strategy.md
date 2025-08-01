# Database Query Strategy Guidance

This document provides specific execution guidance for different database query strategies to optimize performance and token usage.

## Critical Database Schema Rules

**IMPORTANT**: Always follow these rules when querying databases:
- **Use exact table names** as shown in the provided database schema
- **Use exact field names** as confirmed in the schema
- **Verify field types** before applying date/time functions
- **Include database prefix** in queries (e.g., `ext_ref_db.amazon_reviews`, `htinfo_db.walmart_orders`)
- **Match strategy to data structure** based on actual schema information

## Query Strategy: AGGREGATION

**Purpose**: Statistical analysis using SQL aggregation functions (recommended for 90% of cases)

**Execution Guidelines**:
- Prioritize SQL aggregation functions: COUNT(), SUM(), AVG(), MAX(), MIN()
- Use GROUP BY for categorical analysis
- Focus on statistical insights, not raw data
- **Strategy**: {{ strategy }}
- **Justification**: {{ justification }}
- **Expected Size**: {{ expected_size }}

**Template Pattern**:
```sql
-- Replace with actual table/field names from schema
SELECT [category_field], 
       COUNT(*) as record_count,
       SUM([quantity_field]) as total_quantity,
       AVG([price_field]) as average_price
FROM [database].[table_name]
WHERE [filter_conditions]
GROUP BY [category_field]
ORDER BY [sort_field] DESC
```

## Query Strategy: SAMPLING

**Purpose**: Limited data sampling for exploration (5% of cases)

**Execution Guidelines**:
- Limit query results using LIMIT clause (batch_size: {{ batch_size }})
- Focus on representative sample data
- Use conditional filtering for typical cases
- **Strategy**: {{ strategy }}
- **Justification**: {{ justification }}

**Template Pattern**:
```sql
-- Replace with actual table/field names from schema
SELECT [relevant_fields]
FROM [database].[table_name]
WHERE [filter_conditions]
ORDER BY [sort_field]
LIMIT {{ batch_size }}
```

## Query Strategy: PAGINATION

**Purpose**: Batch processing with immediate analysis (4% of cases)

**Execution Guidelines**:
- Process data in batches of {{ batch_size }} records
- Analyze each batch immediately, don't accumulate
- Use OFFSET for pagination
- **Strategy**: {{ strategy }}
- **Justification**: {{ justification }}

**Template Pattern**:
```sql
-- Replace with actual table/field names from schema
SELECT [relevant_fields]
FROM [database].[table_name]
WHERE [filter_conditions]
ORDER BY [primary_key_field]
LIMIT {{ batch_size }} OFFSET [calculated_offset]
```

**Important**: Analyze each batch result immediately before requesting next batch

## Query Strategy: WINDOW_ANALYSIS

**Purpose**: Advanced analytics using window functions (1% of cases)

**Execution Guidelines**:
- Use window functions for ranking and cumulative analysis
- Suitable for TOP-N analysis and running totals
- **Strategy**: {{ strategy }}
- **Justification**: {{ justification }}

**Template Pattern**:
```sql
-- Replace with actual table/field names from schema
SELECT [fields],
       RANK() OVER (PARTITION BY [partition_field] ORDER BY [order_field] DESC) as rank,
       SUM([value_field]) OVER (PARTITION BY [partition_field]) as total
FROM [database].[table_name]
WHERE [filter_conditions]
```

## Database-Specific Considerations

### For Amazon Reviews Analysis (ext_ref_db)
- **Common tables**: amazon_reviews, amazon_products, amazon_categories
- **Key fields**: rating, review_text, review_date, asin, category_id
- **Sample aggregation**: `SELECT rating, COUNT(*) FROM ext_ref_db.amazon_reviews GROUP BY rating`

### For Walmart Sales Analysis (htinfo_db + ext_ref_db)
- **Order data**: htinfo_db.walmart_orders
- **Product data**: ext_ref_db.walmart_products
- **Key relationships**: Join on product identifiers

### General Guidelines
- **Always verify** table and field names from the actual schema
- **Use appropriate database prefix** for each query
- **Match analysis type** to available data structure
- **Focus on the user's specific question** rather than default patterns

## Error Prevention

**Critical Rules**:
- ❌ Never assume field names exist without schema confirmation
- ❌ Never use hardcoded table names without verifying database location
- ❌ Never apply date functions without confirming field types
- ❌ Never ignore database prefixes in multi-database environments

**Best Practices**:
- ✅ Always reference provided database schema information
- ✅ Use exact table and field names as shown in schema
- ✅ Include appropriate database prefixes (ext_ref_db.table_name)
- ✅ Match query complexity to analysis requirements
- ✅ Focus queries on answering the specific user question

## Context-Aware Query Construction

Remember to:
1. **Analyze the user's question** to determine which database/tables to use
2. **Review the provided schema** to get exact table and field names
3. **Choose appropriate strategy** based on analysis type and data volume
4. **Construct queries** using exact names and appropriate database prefixes
5. **Focus on insights** that directly answer the user's question