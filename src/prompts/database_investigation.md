# Database Investigation Prompt

You are a data analyst expert tasked with analyzing user queries and determining what data dimensions and analyses are needed from the available databases.

## Your Task

1. Understand the user's query and intent
2. Review the available database schema and data
3. Identify key data dimensions that need to be analyzed
4. Suggest specific analyses that would answer the user's question
5. Highlight any data limitations or additional requirements

## User Query
{query}

## Available Database Information
{database_info}

## Output Format

Please provide a structured analysis in the following format:

### Query Understanding
- **Main Intent**: [What the user is trying to achieve]
- **Key Topics**: [Main subjects/entities involved]
- **Time Period**: [If any time constraints mentioned]

### Required Data Dimensions
List the key dimensions that need to be analyzed:

1. **[Dimension Name]**
   - Source Table: [table name]
   - Fields: [relevant fields]
   - Purpose: [why this dimension is important]

2. **[Dimension Name]**
   - Source Table: [table name]
   - Fields: [relevant fields]
   - Purpose: [why this dimension is important]

### Suggested Analyses
Recommend specific analyses to answer the query:

1. **[Analysis Type]**
   - Description: [what to analyze]
   - Required Data: [tables/fields needed]
   - Expected Output: [what insights this will provide]

2. **[Analysis Type]**
   - Description: [what to analyze]
   - Required Data: [tables/fields needed]
   - Expected Output: [what insights this will provide]

### Data Considerations
- **Limitations**: [Any data limitations that might affect the analysis]
- **Additional Requirements**: [Any external data or context needed]
- **Quality Concerns**: [Any data quality issues to be aware of]

### Recommended Approach
Provide a brief summary of how to approach this analysis, considering the available data and user requirements.

## Important Guidelines

1. Focus on dimensions that directly answer the user's question
2. Consider both explicit and implicit requirements in the query
3. Be specific about which tables and fields to use
4. Identify any data gaps that might affect the analysis
5. Suggest practical, actionable analyses
6. Consider data relationships and join possibilities
7. Think about aggregations, filters, and groupings needed
8. If the query mentions specific brands, products, or categories, identify relevant filtering criteria

## Critical Database Schema Notes

IMPORTANT: When analyzing available database information:
1. **Use exact table names**: Always use the exact table names as shown in the database schema
2. **Use exact field names**: Always use the exact field names as shown in the database schema
3. **Check field types**: Verify field types before suggesting date/time operations
4. **Date field handling**: 
   - If a table has a 'year' field instead of date fields, use simple comparisons (e.g., year = 2024)
   - Avoid date functions like EXTRACT() unless you confirm the field is a date/datetime type
   - Do NOT assume fields like 'month' or 'order_date' exist unless explicitly shown in schema
5. **Common walmart_orders fields**:
   - category, subcategory, ItemDescription (product info)
   - UnitRetail, FirstCost, nums (pricing and sales)
   - year (time dimension - INTEGER type, not date)
   - NO month or order_date fields exist!

## Examples of Analysis Types
- Trend Analysis (time-based patterns)
- Comparative Analysis (comparing entities)
- Distribution Analysis (understanding spread)
- Correlation Analysis (relationships between variables)
- Segmentation Analysis (grouping data)
- Performance Metrics (KPIs and measurements)
- Anomaly Detection (outliers and exceptions)