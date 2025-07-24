# MindsDB MCP Server 部署脚本

本目录包含用于快速部署MindsDB MCP Server的自动化脚本。

## 脚本说明

### deploy-mindsdb.ps1 (Windows PowerShell)
Windows系统的一键部署脚本，提供完整的部署流程。

**使用方法：**
```powershell
# 基本使用
.\deploy-mindsdb.ps1

# 自定义MySQL连接
.\deploy-mindsdb.ps1 -MySQLHost "192.168.1.100" -MySQLPort 3306 -MySQLUser "mindsdb_user"

# 跳过健康检查
.\deploy-mindsdb.ps1 -SkipHealthCheck

# 强制部署（忽略端口占用）
.\deploy-mindsdb.ps1 -Force
```

### deploy-mindsdb.sh (Linux/Mac)
Linux和Mac系统的一键部署脚本。

**使用方法：**
```bash
# 添加执行权限
chmod +x deploy-mindsdb.sh

# 基本使用
./deploy-mindsdb.sh

# 自定义MySQL连接
./deploy-mindsdb.sh --mysql-host 192.168.1.100 --mysql-port 3306

# 查看帮助
./deploy-mindsdb.sh --help
```

### verify-mindsdb.sh
部署验证脚本，用于检查MindsDB是否正确部署和配置。

**使用方法：**
```bash
chmod +x verify-mindsdb.sh
./verify-mindsdb.sh
```

## 部署流程

1. **检查先决条件**
   - Docker是否安装和运行
   - 端口是否可用（47334, 47335）
   - 必要的工具是否安装

2. **初始化目录**
   - 创建config、scripts、logs目录

3. **容器管理**
   - 停止和删除旧容器（如果存在）
   - 拉取最新MindsDB镜像
   - 启动新容器

4. **健康检查**
   - 等待MindsDB完全启动
   - 验证API可访问性

5. **配置数据源**
   - 连接htinfo_db数据库
   - 连接ext_ref_db数据库

6. **生成配置文件**
   - 创建mindsdb_mcp.yaml
   - 创建.env.example模板

## 配置文件

### config/mindsdb_mcp.yaml
MindsDB MCP配置文件，包含：
- 服务器配置
- 数据库连接信息
- 模型配置
- 工具定义

### .env
环境变量文件（需要从.env.example复制并修改）：
```bash
MYSQL_HOST=192.168.1.100
MYSQL_PORT=3306
MYSQL_USER=mindsdb_user
MYSQL_PASSWORD=your_password
MINDSDB_HOST=localhost
MINDSDB_PORT=47334
```

## Docker Compose部署

对于生产环境，推荐使用Docker Compose：

```bash
# 启动服务
docker-compose -f ../docker-compose.mindsdb.yml up -d

# 查看日志
docker-compose -f ../docker-compose.mindsdb.yml logs -f

# 停止服务
docker-compose -f ../docker-compose.mindsdb.yml down
```

## 故障排除

### 端口被占用
```bash
# 查找占用端口的进程
lsof -i :47334
netstat -an | grep 47334

# 使用强制模式
./deploy-mindsdb.sh --force
```

### 容器启动失败
```bash
# 查看容器日志
docker logs mindsdb

# 检查Docker资源
docker system df
docker system prune
```

### 数据库连接失败
- Windows: 确保使用 `host.docker.internal`
- Linux: 可能需要使用实际IP地址
- 检查MySQL用户权限

## 管理命令

```bash
# 停止MindsDB
docker stop mindsdb

# 启动MindsDB
docker start mindsdb

# 重启MindsDB
docker restart mindsdb

# 查看实时日志
docker logs -f mindsdb

# 进入容器
docker exec -it mindsdb bash

# 完全清理
docker stop mindsdb
docker rm mindsdb
docker volume rm mindsdb_data
```

## 性能优化

1. **增加内存限制**
   ```bash
   docker update --memory 4g mindsdb
   ```

2. **配置CPU限制**
   ```bash
   docker update --cpus 2 mindsdb
   ```

3. **使用本地缓存**
   MindsDB会自动缓存查询结果，提高重复查询性能

## 安全建议

1. 不要在脚本中硬编码密码
2. 使用强密码
3. 限制网络访问
4. 定期更新MindsDB镜像
5. 监控访问日志

## 支持

如遇到问题，请：
1. 运行验证脚本：`./verify-mindsdb.sh`
2. 查看容器日志：`docker logs mindsdb`
3. 检查配置文件
4. 参考主文档：[MindsDB MCP部署指南](../docs/mindsdb-mcp-deployment.md)