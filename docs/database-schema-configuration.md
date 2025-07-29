# 数据库Schema配置使用指南

## 概述

数据库Schema配置系统提供了灵活的方式来管理数据库元数据信息，支持静态配置、动态获取和混合模式。

## 配置文件位置

主配置文件：`config/database_schema.yaml`

## 配置模式

### 1. Static（静态模式）
- 完全从配置文件读取数据库信息
- 不需要实际连接数据库
- 适合生产环境或数据库结构稳定的情况

```yaml
mode: "static"
```

### 2. Dynamic（动态模式）
- 实时从MindsDB查询数据库信息
- 自动获取最新的表结构和数据
- 适合开发环境或数据库结构经常变化的情况

```yaml
mode: "dynamic"
```

### 3. Hybrid（混合模式）【推荐】
- 优先使用静态配置
- 当静态配置不足时，自动回退到动态获取
- 兼具性能和灵活性

```yaml
mode: "hybrid"
```

## 主要配置项

### 全局设置

```yaml
settings:
  max_tables_per_database: 3     # 每个数据库最多处理的表数量
  max_fields_per_table: 5        # 每个表最多显示的字段数量
  max_sample_records: 2          # 每个表最多显示的样本记录数量
  enable_statistics: true        # 是否包含统计信息
  enable_enum_values: true       # 是否包含枚举值
  enable_sample_data: true       # 是否包含样本数据
```

### 数据库配置示例

```yaml
databases:
  htinfo_db:
    name: "HT信息数据库"
    description: "包含产品、订单、用户等核心业务数据"
    enabled: true
    tables:
      products:
        name: "商品表"
        description: "商品基础信息和属性"
        priority: 1  # 优先级，数字越小优先级越高
        fields:
          - name: "id"
            type: "INT"
            description: "商品唯一标识"
            is_primary_key: true
          - name: "name"
            type: "VARCHAR(255)"
            description: "商品名称"
            sample_values: ["iPhone 15", "MacBook Pro"]
        statistics:
          total_records: 1501
          date_range:
            column: "created_at"
            min: "2023-01-01"
            max: "2024-12-31"
        sample_data:
          - [1, "iPhone 15 Pro", 1, 1299.99, 50, "2024-09-15"]
```

## 动态配置选项

```yaml
dynamic_config:
  fallback_to_dynamic: true      # 混合模式下是否允许回退到动态获取
  database_filter:
    include: ["htinfo_db", "ext_ref_db"]    # 包含的数据库
    exclude: ["information_schema", "mysql"] # 排除的数据库
  table_filter:
    exclude_patterns: ["tmp_*", "temp_*"]    # 排除的表名模式
    include_patterns: ["*"]                  # 包含的表名模式
```

## 使用场景

### 场景1：纯静态配置（离线环境）
1. 设置 `mode: "static"`
2. 在配置文件中定义所有数据库和表信息
3. 无需连接实际数据库

### 场景2：纯动态获取（开发环境）
1. 设置 `mode: "dynamic"`
2. 只需配置数据库过滤规则
3. 实时获取最新数据库信息

### 场景3：混合使用（推荐）
1. 设置 `mode: "hybrid"`
2. 配置常用的表结构信息
3. 新增的表会自动从数据库获取

## 配置优先级

1. 静态配置的表信息优先级最高
2. 表的 `priority` 字段决定显示顺序
3. 动态获取的表按字母顺序排列

## 最佳实践

1. **生产环境**：使用静态模式，确保稳定性和性能
2. **开发环境**：使用动态或混合模式，方便调试
3. **Token优化**：适当减少字段数量和样本数据
4. **定期更新**：使用动态模式生成配置，然后转为静态配置

## 故障排除

### 问题：配置文件未找到
- 解决：检查文件路径是否正确，系统会自动使用默认配置

### 问题：动态模式下无法连接数据库
- 解决：检查MindsDB服务是否运行，数据库连接是否正常

### 问题：混合模式下数据重复
- 解决：检查静态配置和动态获取的数据库是否重复