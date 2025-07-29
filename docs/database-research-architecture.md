# Database Research Architecture

## Overview

The Database Research system provides a token-optimized alternative to web searches by leveraging local database resources through MindsDB integration. This architecture enables deep data analysis without consuming tokens on external API calls.

## Problem Statement

- **Token Limitation**: Web searches consume significant tokens, leading to token limit errors
- **Local Data Underutilization**: Available database resources were not being used effectively
- **Need for Deep Analysis**: Requirements for comprehensive data analysis similar to deep-research capabilities

## Solution Architecture

### Core Components

```
┌─────────────────────────────────────────────────────────────┐
│                    Database Research Flow                    │
├─────────────────────────────────────────────────────────────┤
│                                                             │
│  ┌─────────────────┐   ┌─────────────────┐   ┌──────────┐ │
│  │  Investigation   │──►│     Planner     │──►│ Reporter │ │
│  │      Node        │   │      Node       │   │   Node   │ │
│  └─────────────────┘   └─────────────────┘   └──────────┘ │
│           │                     │                    │      │
│           ▼                     ▼                    ▼      │
│   ┌─────────────────┐  ┌──────────────┐   ┌─────────────┐ │
│   │ Database Schema │  │ Analysis Plan│   │Final Report │ │
│   │   + LLM Dims    │  │   (Steps)    │   │   Output    │ │
│   └─────────────────┘  └──────────────┘   └─────────────┘ │
│                                                             │
└─────────────────────────────────────────────────────────────┘
```

### Node Descriptions

#### 1. Database Investigation Node (`database_investigation_node`)
**Purpose**: Gather database schema information and analyze query dimensions

**Process**:
- Retrieves database schema using DatabaseSchemaManager
- Uses LLM to analyze user query and suggest data analysis dimensions
- Combines schema info with analytical recommendations

**Output**: Investigation report containing:
- Available database structures
- LLM-suggested analysis dimensions
- Data relationships and possibilities

#### 2. Database Planner Node (`database_planner_node`)
**Purpose**: Generate structured analysis plan based on investigation results

**Process**:
- Takes investigation results as input
- Uses specialized prompt template focused on database operations
- Generates Plan object with processing steps (SQL queries, aggregations, etc.)

**Output**: Structured plan with:
- Analysis steps (mostly `processing` type with `need_search: false`)
- Clear objectives for each step
- Logical sequence of database operations

#### 3. Database Reporter Node (`database_reporter_node`)
**Purpose**: Generate comprehensive analysis report (currently conceptual)

**Process**:
- Takes investigation results and plan as input
- Simulates analysis execution based on plan
- Generates comprehensive report structure

**Output**: Analysis report with:
- Executive summary
- Methodology overview
- Detailed findings (conceptual)
- Recommendations

## Configuration System

### Database Schema Configuration (`config/database_schema.yaml`)

Supports three modes:

1. **Static Mode**: Manually configured database schemas
2. **Dynamic Mode**: Real-time schema retrieval from MindsDB
3. **Hybrid Mode**: Combination of static and dynamic

Key settings:
```yaml
mode: "dynamic"  # or "static" or "hybrid"
settings:
  max_tables_per_database: 3
  max_fields_per_table: 5
  max_sample_records: 2
  enable_enum_values: false  # Disabled to reduce token usage
```

### Database Schema Manager

Central component for managing database information:
- Handles configuration loading
- Supports multiple retrieval modes
- Formats database information for LLM consumption
- Implements filtering and optimization

## Prompt Templates

### 1. `database_investigation.md`
- Analyzes user queries in database context
- Suggests analytical dimensions
- Structures output for planner consumption

### 2. `database_planner.md`
- Focuses on database operations (70%+ processing steps)
- Emphasizes SQL queries, joins, aggregations
- Minimizes external searches

### 3. `database_reporter.md`
- Generates comprehensive reports
- Follows business analysis structure
- Provides actionable insights

## Key Design Decisions

### 1. Separation of Concerns
- Database code isolated from existing deep research code
- Separate node files (`nodes_database.py`)
- Independent configuration system

### 2. Token Optimization
- `enable_enum_values: false` by default
- Limited sample data retrieval
- Focused schema information

### 3. Processing-First Approach
- Prioritize local database operations
- Minimize external searches
- Leverage SQL capabilities

### 4. LLM Integration
- Use basic model for efficiency
- Structured output for plans
- Template-based prompting

## Implementation Status

### Completed ✅
- Database investigation node with LLM integration
- Database planner node with structured output
- Database reporter node (full implementation)
- Database research team node for step coordination
- Database researcher node for SQL execution
- MindsDB tool integration (query & table info)
- Configuration system
- Prompt templates
- Full graph integration with coordinator
- Async to sync tool conversion for LangChain
- Database name auto-prefixing in queries
- Sample data limiting (3 rows max)

### Recent Fixes 🔧
- Fixed `create_agent` parameters to match LangChain API
- Corrected agent response handling (`result["messages"][-1].content`)
- Updated table info queries to use `information_schema`
- Fixed SQL query wrapping issue
- Added database prefix to table references automatically

### Pending 🔄
- Natural language to SQL conversion (DeepSeek model issues)
- Query result caching for performance
- Cross-database join operations
- Advanced statistical analysis tools

## Usage Example

```python
# Initialize state with user query
state = State(
    messages=[{"role": "user", "content": "分析沃尔玛2024年的销售趋势"}],
    research_topic="分析沃尔玛2024年的销售趋势",
    locale='zh-CN'
)

# Flow execution
# 1. Investigation → Retrieves database schema and analyzes query
# 2. Planner → Generates analysis plan with SQL operations
# 3. Reporter → Creates conceptual report based on plan
```

## Future Enhancements

1. **Step Executor Implementation**
   - Execute actual SQL queries
   - Handle query results
   - Pass real data to reporter

2. **Advanced Analysis Features**
   - Statistical calculations
   - Trend analysis
   - Predictive modeling

3. **Optimization**
   - Query caching
   - Parallel execution
   - Result streaming

## Testing

Test files available in `tests/manual/`:
- `test_database_investigation_with_llm.py` - Tests investigation node
- `test_database_planner.py` - Tests planner workflow
- `test_database_research_team.py` - Tests complete database research workflow

### Running Tests
```bash
# Activate virtual environment
. .venv/bin/activate

# Run complete workflow test
python tests/manual/test_database_research_team.py
```

## Notes

- Database researcher now executes real SQL queries via MindsDB
- Token usage significantly reduced compared to web searches
- Sample data limited to 3 rows to optimize token consumption
- Automatic database prefixing ensures queries work correctly
- Full integration with LangGraph state management