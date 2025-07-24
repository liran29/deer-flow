# MindsDB MCP Server 一键部署脚本 (Windows PowerShell)
# 用于快速部署MindsDB并配置数据源连接

param(
    [string]$MySQLHost = "host.docker.internal",
    [int]$MySQLPort = 3306,
    [string]$MySQLUser = "mindsdb_user",
    [string]$MySQLPassword = "",
    [string]$MindsDBVersion = "latest",
    [switch]$SkipHealthCheck = $false,
    [switch]$Force = $false
)

# 设置错误处理
$ErrorActionPreference = "Stop"

# 颜色输出函数
function Write-ColorOutput {
    param(
        [string]$Message,
        [string]$Color = "White"
    )
    Write-Host $Message -ForegroundColor $Color
}

# 打印横幅
function Show-Banner {
    Write-ColorOutput @"

╔══════════════════════════════════════════════╗
║     MindsDB MCP Server 自动部署工具           ║
║     Version: 1.0.0                           ║
║     Project: deer-flow                       ║
╚══════════════════════════════════════════════╝

"@ -Color Cyan
}

# 检查先决条件
function Test-Prerequisites {
    Write-ColorOutput "`n[1/7] 检查先决条件..." -Color Yellow
    
    # 检查Docker
    try {
        $dockerVersion = docker --version
        Write-ColorOutput "  ✓ Docker已安装: $dockerVersion" -Color Green
    }
    catch {
        Write-ColorOutput "  ✗ Docker未安装或未运行" -Color Red
        Write-ColorOutput "    请安装Docker Desktop: https://www.docker.com/products/docker-desktop" -Color White
        exit 1
    }
    
    # 检查Docker是否运行
    try {
        docker ps > $null 2>&1
        Write-ColorOutput "  ✓ Docker正在运行" -Color Green
    }
    catch {
        Write-ColorOutput "  ✗ Docker未运行，请启动Docker Desktop" -Color Red
        exit 1
    }
    
    # 检查端口
    $ports = @(47334, 47335)
    foreach ($port in $ports) {
        $tcpConnection = Get-NetTCPConnection -LocalPort $port -ErrorAction SilentlyContinue
        if ($tcpConnection) {
            Write-ColorOutput "  ! 端口 $port 已被占用" -Color Yellow
            if (-not $Force) {
                Write-ColorOutput "    使用 -Force 参数强制继续" -Color White
                exit 1
            }
        }
        else {
            Write-ColorOutput "  ✓ 端口 $port 可用" -Color Green
        }
    }
}

# 创建配置目录
function Initialize-Directories {
    Write-ColorOutput "`n[2/7] 初始化目录结构..." -Color Yellow
    
    $directories = @(
        "config",
        "scripts",
        "logs"
    )
    
    foreach ($dir in $directories) {
        if (-not (Test-Path $dir)) {
            New-Item -ItemType Directory -Path $dir -Force | Out-Null
            Write-ColorOutput "  ✓ 创建目录: $dir" -Color Green
        }
        else {
            Write-ColorOutput "  ✓ 目录已存在: $dir" -Color Green
        }
    }
}

# 检查并停止旧容器
function Stop-OldContainer {
    Write-ColorOutput "`n[3/7] 检查现有MindsDB容器..." -Color Yellow
    
    $existingContainer = docker ps -a --filter "name=mindsdb" --format "{{.Names}}" 2>$null
    
    if ($existingContainer) {
        Write-ColorOutput "  ! 发现现有容器，正在停止和删除..." -Color Yellow
        docker stop mindsdb 2>$null | Out-Null
        docker rm mindsdb 2>$null | Out-Null
        Write-ColorOutput "  ✓ 已清理旧容器" -Color Green
    }
    else {
        Write-ColorOutput "  ✓ 没有发现旧容器" -Color Green
    }
}

# 启动MindsDB容器
function Start-MindsDBContainer {
    Write-ColorOutput "`n[4/7] 启动MindsDB容器..." -Color Yellow
    
    # 创建数据卷
    docker volume create mindsdb_data 2>$null | Out-Null
    Write-ColorOutput "  ✓ 创建数据卷: mindsdb_data" -Color Green
    
    # 启动容器
    $runCommand = @"
docker run -d `
    --name mindsdb `
    -p 47334:47334 `
    -p 47335:47335 `
    -v mindsdb_data:/root/mindsdb `
    --restart unless-stopped `
    mindsdb/mindsdb:$MindsDBVersion
"@
    
    Write-ColorOutput "  → 拉取MindsDB镜像..." -Color White
    docker pull mindsdb/mindsdb:$MindsDBVersion | Out-Null
    
    Write-ColorOutput "  → 启动容器..." -Color White
    $containerId = Invoke-Expression $runCommand
    
    if ($containerId) {
        Write-ColorOutput "  ✓ 容器已启动: $($containerId.Substring(0, 12))" -Color Green
    }
    else {
        Write-ColorOutput "  ✗ 容器启动失败" -Color Red
        exit 1
    }
}

# 等待MindsDB启动
function Wait-ForMindsDB {
    if ($SkipHealthCheck) {
        Write-ColorOutput "`n[5/7] 跳过健康检查..." -Color Yellow
        return
    }
    
    Write-ColorOutput "`n[5/7] 等待MindsDB启动..." -Color Yellow
    
    $maxAttempts = 30
    $attempt = 0
    
    while ($attempt -lt $maxAttempts) {
        try {
            $response = Invoke-WebRequest -Uri "http://localhost:47334/api/sql/query" `
                -Method POST `
                -ContentType "application/json" `
                -Body '{"query": "SELECT 1;"}' `
                -UseBasicParsing `
                -ErrorAction SilentlyContinue
            
            if ($response.StatusCode -eq 200) {
                Write-ColorOutput "  ✓ MindsDB已成功启动" -Color Green
                return
            }
        }
        catch {
            # 继续等待
        }
        
        $attempt++
        Write-Host "." -NoNewline
        Start-Sleep -Seconds 2
    }
    
    Write-ColorOutput "`n  ✗ MindsDB启动超时" -Color Red
    Write-ColorOutput "    请检查容器日志: docker logs mindsdb" -Color White
    exit 1
}

# 配置数据源
function Configure-DataSources {
    Write-ColorOutput "`n[6/7] 配置MySQL数据源..." -Color Yellow
    
    # 获取MySQL密码
    if (-not $MySQLPassword) {
        $securePassword = Read-Host "请输入MySQL密码" -AsSecureString
        $MySQLPassword = [Runtime.InteropServices.Marshal]::PtrToStringAuto(
            [Runtime.InteropServices.Marshal]::SecureStringToBSTR($securePassword)
        )
    }
    
    # 创建数据源的SQL命令
    $databases = @(
        @{
            Name = "htinfo_db"
            Database = "ht_info_db"
        },
        @{
            Name = "ext_ref_db"
            Database = "ext_ref_db"
        }
    )
    
    foreach ($db in $databases) {
        $query = @"
CREATE DATABASE IF NOT EXISTS $($db.Name) 
WITH ENGINE = 'mysql', 
PARAMETERS = {
    "host": "$MySQLHost",
    "port": $MySQLPort,
    "database": "$($db.Database)",
    "user": "$MySQLUser",
    "password": "$MySQLPassword"
};
"@
        
        $body = @{
            query = $query
        } | ConvertTo-Json
        
        try {
            Write-ColorOutput "  → 配置数据源: $($db.Name)" -Color White
            
            $response = Invoke-RestMethod -Uri "http://localhost:47334/api/sql/query" `
                -Method POST `
                -ContentType "application/json" `
                -Body $body `
                -ErrorAction Stop
            
            Write-ColorOutput "  ✓ 数据源配置成功: $($db.Name)" -Color Green
        }
        catch {
            Write-ColorOutput "  ! 数据源配置失败: $($db.Name)" -Color Yellow
            Write-ColorOutput "    错误: $_" -Color White
            # 继续配置其他数据源
        }
    }
}

# 创建配置文件
function Create-ConfigFiles {
    Write-ColorOutput "`n[7/7] 生成配置文件..." -Color Yellow
    
    # 创建MindsDB MCP配置文件
    $mcpConfig = @"
# MindsDB MCP Server Configuration
# Generated by deploy-mindsdb.ps1
server:
  name: "mindsdb-mcp"
  version: "1.0.0"
  host: "localhost"
  port: 47334

databases:
  - name: "htinfo_db"
    type: "mysql"
    connection:
      host: "$MySQLHost"
      port: $MySQLPort
      database: "ht_info_db"
      user: "$MySQLUser"
    tables:
      - walmart_online_item
      - walmart_online_theme
      - walmart_orders

  - name: "ext_ref_db"
    type: "mysql"
    connection:
      host: "$MySQLHost"
      port: $MySQLPort
      database: "ext_ref_db"
      user: "$MySQLUser"
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
"@
    
    $mcpConfig | Out-File -FilePath "config/mindsdb_mcp.yaml" -Encoding UTF8
    Write-ColorOutput "  ✓ 创建配置文件: config/mindsdb_mcp.yaml" -Color Green
    
    # 创建环境变量文件模板
    if (-not (Test-Path ".env")) {
        $envTemplate = @"
# MindsDB MCP Server Environment Variables
# Generated by deploy-mindsdb.ps1

# MySQL Configuration
MYSQL_HOST=$MySQLHost
MYSQL_PORT=$MySQLPort
MYSQL_USER=$MySQLUser
MYSQL_PASSWORD=your_secure_password_here

# MindsDB Configuration
MINDSDB_HOST=localhost
MINDSDB_PORT=47334

# AI Model Configuration (Optional)
DEEPSEEK_API_KEY=your_api_key_here
"@
        
        $envTemplate | Out-File -FilePath ".env.example" -Encoding UTF8
        Write-ColorOutput "  ✓ 创建环境变量模板: .env.example" -Color Green
        Write-ColorOutput "    请复制并编辑.env.example为.env，填入实际密码" -Color Yellow
    }
}

# 显示部署摘要
function Show-Summary {
    Write-ColorOutput "`n" -Color White
    Write-ColorOutput "═══════════════════════════════════════════════" -Color Cyan
    Write-ColorOutput "         部署完成！" -Color Green
    Write-ColorOutput "═══════════════════════════════════════════════" -Color Cyan
    
    Write-ColorOutput "`n访问地址:" -Color Yellow
    Write-ColorOutput "  MindsDB Web UI: http://localhost:47334" -Color White
    Write-ColorOutput "  API Endpoint:   http://localhost:47334/api/sql/query" -Color White
    
    Write-ColorOutput "`n验证部署:" -Color Yellow
    Write-ColorOutput "  docker logs mindsdb --tail 50" -Color White
    Write-ColorOutput "  curl http://localhost:47334/api/sql/query -H `"Content-Type: application/json`" -d '{`"query`": `"SHOW DATABASES;`"}'" -Color White
    
    Write-ColorOutput "`n测试集成:" -Color Yellow
    Write-ColorOutput "  uv run python main.py `"查询沃尔玛最新的在线商品信息`" --debug" -Color White
    
    Write-ColorOutput "`n管理命令:" -Color Yellow
    Write-ColorOutput "  停止服务: docker stop mindsdb" -Color White
    Write-ColorOutput "  启动服务: docker start mindsdb" -Color White
    Write-ColorOutput "  查看日志: docker logs mindsdb -f" -Color White
    Write-ColorOutput "  删除服务: docker rm mindsdb" -Color White
    
    Write-ColorOutput "`n注意事项:" -Color Yellow
    Write-ColorOutput "  1. 请确保MySQL服务可访问" -Color White
    Write-ColorOutput "  2. 更新conf.yaml启用MindsDB集成" -Color White
    Write-ColorOutput "  3. 配置.env文件中的密码信息" -Color White
}

# 主函数
function Main {
    Show-Banner
    
    try {
        Test-Prerequisites
        Initialize-Directories
        Stop-OldContainer
        Start-MindsDBContainer
        Wait-ForMindsDB
        Configure-DataSources
        Create-ConfigFiles
        Show-Summary
    }
    catch {
        Write-ColorOutput "`n✗ 部署失败: $_" -Color Red
        Write-ColorOutput "  查看详细错误: `$Error[0] | Format-List -Force" -Color White
        exit 1
    }
}

# 执行主函数
Main