# Database Nodes Code Refactoring

## Overview

This document describes the refactoring of database nodes to improve code structure, maintainability, and follow best practices.

## Key Improvements

### 1. Separated Strategy Guidance into Template Files

**Before**: Hard-coded Chinese prompts mixed in Python code
```python
base_guidance += """**重要查询规则**:
- 使用数据库中实际存在的表名：walmart_orders
- 只使用实际存在的字段名，walmart_orders表的主要字段包括：
  * id, category, subcategory, ItemDescription
"""
```

**After**: External template file with English prompts
```markdown
# Database Query Strategy Guidance

## Critical Database Schema Rules

**IMPORTANT**: Always follow these rules when querying databases:
- Use exact table names as shown in schema: `walmart_orders`
- Use only existing field names:
  * id, category, subcategory, ItemDescription
```

### 2. English Internal Messages

**Before**: Chinese logging and internal messages
```python
logger.info("数据库研究员开始执行查询分析")
logger.warning("缺少分析计划，无法执行步骤")
```

**After**: English logging and internal messages
```python
logger.info("Database researcher starting query analysis")
logger.warning("Missing analysis plan, cannot execute step")
```

### 3. Template-Based Strategy Guidance

**Before**: Hard-coded if/else logic in Python
```python
if strategy == QueryStrategy.AGGREGATION:
    return base_guidance + """**执行指导**:
    - 优先使用SQL聚合函数：COUNT(), SUM(), AVG(), MAX(), MIN()
    """
```

**After**: Template file loading with Jinja2
```python
def _get_strategy_guidance(step) -> str:
    strategy_file = os.path.join(
        os.path.dirname(os.path.dirname(__file__)), 
        "prompts", 
        "database_query_strategy.md"
    )
    
    with open(strategy_file, 'r', encoding='utf-8') as f:
        strategy_template = f.read()
        
    template = Template(strategy_template)
    return template.render(**context)
```

## Files Created/Modified

### New Files

1. **`src/prompts/database_query_strategy.md`**
   - Contains all strategy guidance templates
   - English prompts with proper formatting
   - Context variables for dynamic content

2. **`src/graph/nodes_database_refactored.py`**
   - Refactored database nodes with improved structure
   - English internal messages
   - Template-based strategy guidance
   - Better error handling and logging

### Benefits

1. **Maintainability**: Strategy guidance can be updated without changing Python code
2. **Internationalization**: Clear separation between internal (English) and user-facing messages
3. **Consistency**: All database query rules in one centralized template
4. **Flexibility**: Template variables allow dynamic content generation
5. **Code Quality**: Cleaner Python code without embedded multi-line strings

## Migration Notes

- Original `nodes_database.`) remains unchanged for backward compatibility
- New refactored version can be gradually adopted
- Template file provides single source of truth for query guidance
- English logging improves debugging for international teams

## Template Structure

The `database_query_strategy.md` template includes:

- **Critical Database Schema Rules**: Table and field naming guidelines
- **Strategy-Specific Guidance**: Different approaches for each query strategy
- **Error Prevention**: Common mistakes and correct patterns
- **Context Variables**: Dynamic content like batch sizes and justifications

## Future Enhancements

1. Add more template variables for dynamic content
2. Create separate templates for different database types
3. Implement template validation and testing
4. Add support for multiple languages in templates

---

*Created: 2025-07-31*
*Author: Database Research Team*