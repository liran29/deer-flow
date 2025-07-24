# MindsDB MCP Server 部署指南

本文档介绍如何快速部署MindsDB MCP Server并集成到deer-flow项目中。

## 目录

- [概述](#概述)
- [先决条件](#先决条件)
- [一键部署](#一键部署)
- [手动部署步骤](#手动部署步骤)
- [配置说明](#配置说明)
- [验证部署](#验证部署)
- [故障排除](#故障排除)

## 概述

MindsDB MCP (Model Context Protocol) Server提供了AI驱动的数据库查询能力，允许deer-flow项目通过自然语言查询本地数据库，从而减少对外部API的依赖，解决Token超限问题。

### 架构组件

- **MindsDB Server**: 提供SQL和自然语言查询接口
- **MySQL数据源**: htinfo_db和ext_ref_db
- **MCP集成层**: 连接deer-flow和MindsDB

## 先决条件

### 系统要求

- Docker Desktop (Windows/Mac/Linux)
- Python 3.9+
- 至少4GB可用内存
- 10GB可用磁盘空间

### 网络要求

- 端口47334 (MindsDB HTTP API)
- 端口47335 (MindsDB MySQL接口)
- 端口3306 (MySQL数据库)

## 一键部署

使用提供的部署脚本可以快速完成整个部署过程：

### Windows (PowerShell)

```powershell
# 运行部署脚本
.\scripts\deploy-mindsdb.ps1

# 如果需要自定义配置
.\scripts\deploy-mindsdb.ps1 -MySQLHost "192.168.1.100" -MySQLPort 3306
```

### Linux/Mac

```bash
# 添加执行权限
chmod +x scripts/deploy-mindsdb.sh

# 运行部署脚本
./scripts/deploy-mindsdb.sh

# 如果需要自定义配置
./scripts/deploy-mindsdb.sh --mysql-host 192.168.1.100 --mysql-port 3306
```

## 手动部署步骤

### 1. 启动MindsDB容器

```bash
# 拉取MindsDB镜像
docker pull mindsdb/mindsdb:latest

# 创建数据卷
docker volume create mindsdb_data

# 启动MindsDB容器
docker run -d \
  --name mindsdb \
  -p 47334:47334 \
  -p 47335:47335 \
  -v mindsdb_data:/root/mindsdb \
  mindsdb/mindsdb:latest
```

### 2. 配置MySQL数据源

等待MindsDB启动完成（约30秒），然后配置数据源：

```bash
# 通过MindsDB API创建数据源连接
curl -X POST http://localhost:47334/api/sql/query \
  -H "Content-Type: application/json" \
  -d '{
    "query": "CREATE DATABASE htinfo_db WITH ENGINE = '\''mysql'\'', PARAMETERS = {\"host\": \"host.docker.internal\", \"port\": 3306, \"database\": \"ht_info_db\", \"user\": \"mindsdb_user\", \"password\": \"your_password\"};"
  }'

curl -X POST http://localhost:47334/api/sql/query \
  -H "Content-Type: application/json" \
  -d '{
    "query": "CREATE DATABASE ext_ref_db WITH ENGINE = '\''mysql'\'', PARAMETERS = {\"host\": \"host.docker.internal\", \"port\": 3306, \"database\": \"ext_ref_db\", \"user\": \"mindsdb_user\", \"password\": \"your_password\"};"
  }'
```

### 3. 配置deer-flow集成

更新 `conf.yaml` 文件启用MindsDB集成：

```yaml
ENHANCED_FEATURES:
  enhanced_background_investigation: true
  step_dependency_optimization: true
  mindsdb_database_integration: true  # 启用MindsDB集成

# MindsDB配置
MINDSDB:
  host: localhost
  port: 47334
  timeout: 30
```

### 4. 创建MindsDB配置文件

创建 `config/mindsdb_mcp.yaml`：

```yaml
# MindsDB MCP Server Configuration
server:
  name: "mindsdb-mcp"
  version: "1.0.0"
  host: "localhost"
  port: 47334

databases:
  - name: "htinfo_db"
    type: "mysql"
    connection:
      host: "host.docker.internal"
      port: 3306
      database: "ht_info_db"
      user: "mindsdb_user"
      password: "${MYSQL_PASSWORD}"
    tables:
      - walmart_online_item
      - walmart_online_theme
      - walmart_orders

  - name: "ext_ref_db"
    type: "mysql"
    connection:
      host: "host.docker.internal"
      port: 3306
      database: "ext_ref_db"
      user: "mindsdb_user"
      password: "${MYSQL_PASSWORD}"
    tables:
      - amazon_categories
      - amazon_products
      - amazon_reviews
      - walmart_categories
      - walmart_product_images
      - walmart_products

models:
  - name: "text_analyzer"
    type: "deepseek"
    description: "Natural language query analyzer"
    
tools:
  - name: "query_database"
    description: "Execute SQL queries on connected databases"
    
  - name: "natural_language_query"
    description: "Query databases using natural language"
    
  - name: "analyze_data"
    description: "Analyze query results and generate insights"
```

## 配置说明

### 环境变量

创建 `.env` 文件设置敏感信息：

```bash
# MySQL配置
MYSQL_HOST=192.168.1.100
MYSQL_PORT=3306
MYSQL_USER=mindsdb_user
MYSQL_PASSWORD=your_secure_password

# MindsDB配置
MINDSDB_HOST=localhost
MINDSDB_PORT=47334

# AI模型配置（可选）
DEEPSEEK_API_KEY=your_api_key
```

### 数据库权限

确保MySQL用户具有必要的权限：

```sql
-- 为MindsDB用户授权
GRANT SELECT, SHOW VIEW ON ht_info_db.* TO 'mindsdb_user'@'%';
GRANT SELECT, SHOW VIEW ON ext_ref_db.* TO 'mindsdb_user'@'%';
FLUSH PRIVILEGES;
```

## 验证部署

### 1. 检查MindsDB状态

```bash
# 检查容器状态
docker ps | grep mindsdb

# 检查MindsDB日志
docker logs mindsdb --tail 50

# 测试API连接
curl http://localhost:47334/api/sql/query \
  -H "Content-Type: application/json" \
  -d '{"query": "SHOW DATABASES;"}'
```

### 2. 验证数据源连接

```bash
# 列出所有数据库
curl http://localhost:47334/api/sql/query \
  -H "Content-Type: application/json" \
  -d '{"query": "SHOW DATABASES;"}'

# 检查表结构
curl http://localhost:47334/api/sql/query \
  -H "Content-Type: application/json" \
  -d '{"query": "SHOW TABLES FROM htinfo_db;"}'
```

### 3. 测试集成功能

运行deer-flow测试查询：

```bash
# 测试数据库查询功能
uv run python main.py "查询沃尔玛最新的在线商品信息" --debug

# 查看集成日志
grep -i "mindsdb" logs/*.log
```

## 故障排除

### 常见问题

#### 1. MindsDB容器无法启动

```bash
# 检查端口占用
netstat -an | grep 47334

# 清理并重启
docker stop mindsdb
docker rm mindsdb
docker volume rm mindsdb_data
# 重新运行部署脚本
```

#### 2. 数据库连接失败

- **Windows Docker**: 使用 `host.docker.internal` 而不是 `localhost`
- **Linux**: 可能需要使用 `--network host` 或实际IP地址
- 检查防火墙设置是否允许连接

#### 3. 查询超时

调整超时设置：
```yaml
MINDSDB:
  timeout: 60  # 增加到60秒
```

### 日志位置

- MindsDB日志: `docker logs mindsdb`
- deer-flow日志: `logs/deer-flow.log`
- 集成测试日志: `logs/mindsdb-integration.log`

### 重置部署

如需完全重置：

```bash
# 停止并删除容器
docker stop mindsdb
docker rm mindsdb

# 删除数据卷
docker volume rm mindsdb_data

# 清理配置文件
rm -rf config/mindsdb_mcp.yaml

# 重新运行部署脚本
./scripts/deploy-mindsdb.sh
```

## 高级配置

### 使用Docker Compose

创建 `docker-compose.mindsdb.yml`:

```yaml
version: '3.8'

services:
  mindsdb:
    image: mindsdb/mindsdb:latest
    container_name: mindsdb
    ports:
      - "47334:47334"
      - "47335:47335"
    volumes:
      - mindsdb_data:/root/mindsdb
      - ./config/mindsdb:/root/.mindsdb
    environment:
      - MINDSDB_API_HOST=0.0.0.0
      - MINDSDB_API_PORT=47334
    restart: unless-stopped
    healthcheck:
      test: ["CMD", "curl", "-f", "http://localhost:47334/api/sql/query"]
      interval: 30s
      timeout: 10s
      retries: 3

volumes:
  mindsdb_data:
```

启动服务：
```bash
docker-compose -f docker-compose.mindsdb.yml up -d
```

### 性能优化

1. **增加内存分配**：
   ```bash
   docker run -d --name mindsdb -m 4g ...
   ```

2. **启用查询缓存**：
   在MindsDB配置中启用缓存以提高重复查询性能

3. **使用连接池**：
   配置适当的连接池大小以处理并发请求

## 安全建议

1. **使用强密码**: 确保所有数据库密码足够复杂
2. **限制网络访问**: 仅允许必要的IP访问MindsDB端口
3. **定期更新**: 保持MindsDB镜像更新到最新版本
4. **监控访问日志**: 定期检查异常访问模式

## 相关资源

- [MindsDB官方文档](https://docs.mindsdb.com/)
- [Model Context Protocol规范](https://modelcontextprotocol.io/)
- [deer-flow项目文档](../README.md)