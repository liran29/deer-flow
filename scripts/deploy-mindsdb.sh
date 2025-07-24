#!/bin/bash
# MindsDB MCP Server 一键部署脚本 (Linux/Mac)
# 用于快速部署MindsDB并配置数据源连接

# 默认配置
MYSQL_HOST="host.docker.internal"
MYSQL_PORT=3306
MYSQL_USER="mindsdb_user"
MYSQL_PASSWORD=""
MINDSDB_VERSION="latest"
SKIP_HEALTH_CHECK=false
FORCE=false

# 颜色定义
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
CYAN='\033[0;36m'
WHITE='\033[1;37m'
NC='\033[0m' # No Color

# 解析命令行参数
while [[ $# -gt 0 ]]; do
    case $1 in
        --mysql-host)
            MYSQL_HOST="$2"
            shift 2
            ;;
        --mysql-port)
            MYSQL_PORT="$2"
            shift 2
            ;;
        --mysql-user)
            MYSQL_USER="$2"
            shift 2
            ;;
        --mysql-password)
            MYSQL_PASSWORD="$2"
            shift 2
            ;;
        --mindsdb-version)
            MINDSDB_VERSION="$2"
            shift 2
            ;;
        --skip-health-check)
            SKIP_HEALTH_CHECK=true
            shift
            ;;
        --force)
            FORCE=true
            shift
            ;;
        -h|--help)
            show_help
            exit 0
            ;;
        *)
            echo "未知参数: $1"
            show_help
            exit 1
            ;;
    esac
done

# 显示帮助信息
show_help() {
    cat << EOF
MindsDB MCP Server 部署脚本

使用方法:
    ./deploy-mindsdb.sh [选项]

选项:
    --mysql-host HOST        MySQL主机地址 (默认: host.docker.internal)
    --mysql-port PORT        MySQL端口 (默认: 3306)
    --mysql-user USER        MySQL用户名 (默认: mindsdb_user)
    --mysql-password PASS    MySQL密码
    --mindsdb-version VER    MindsDB版本 (默认: latest)
    --skip-health-check      跳过健康检查
    --force                  强制执行，忽略端口占用
    -h, --help              显示此帮助信息

示例:
    ./deploy-mindsdb.sh
    ./deploy-mindsdb.sh --mysql-host 192.168.1.100 --mysql-port 3306
EOF
}

# 打印带颜色的输出
print_color() {
    local color=$1
    local message=$2
    echo -e "${color}${message}${NC}"
}

# 显示横幅
show_banner() {
    print_color "$CYAN" "
╔══════════════════════════════════════════════╗
║     MindsDB MCP Server 自动部署工具          ║
║     Version: 1.0.0                           ║
║     Project: deer-flow                       ║
╚══════════════════════════════════════════════╝
"
}

# 检查命令是否存在
command_exists() {
    command -v "$1" >/dev/null 2>&1
}

# 检查先决条件
check_prerequisites() {
    print_color "$YELLOW" "\n[1/7] 检查先决条件..."
    
    # 检查Docker
    if command_exists docker; then
        docker_version=$(docker --version)
        print_color "$GREEN" "  ✓ Docker已安装: $docker_version"
    else
        print_color "$RED" "  ✗ Docker未安装"
        print_color "$WHITE" "    请访问: https://docs.docker.com/get-docker/"
        exit 1
    fi
    
    # 检查Docker是否运行
    if docker ps >/dev/null 2>&1; then
        print_color "$GREEN" "  ✓ Docker正在运行"
    else
        print_color "$RED" "  ✗ Docker未运行，请启动Docker服务"
        exit 1
    fi
    
    # 检查端口
    for port in 47334 47335; do
        if lsof -Pi :$port -sTCP:LISTEN -t >/dev/null 2>&1; then
            print_color "$YELLOW" "  ! 端口 $port 已被占用"
            if [ "$FORCE" = false ]; then
                print_color "$WHITE" "    使用 --force 参数强制继续"
                exit 1
            fi
        else
            print_color "$GREEN" "  ✓ 端口 $port 可用"
        fi
    done
    
    # 检查curl
    if command_exists curl; then
        print_color "$GREEN" "  ✓ curl已安装"
    else
        print_color "$RED" "  ✗ curl未安装"
        print_color "$WHITE" "    请安装curl: sudo apt-get install curl 或 brew install curl"
        exit 1
    fi
}

# 创建必要的目录
initialize_directories() {
    print_color "$YELLOW" "\n[2/7] 初始化目录结构..."
    
    directories=("config" "scripts" "logs")
    
    for dir in "${directories[@]}"; do
        if [ ! -d "$dir" ]; then
            mkdir -p "$dir"
            print_color "$GREEN" "  ✓ 创建目录: $dir"
        else
            print_color "$GREEN" "  ✓ 目录已存在: $dir"
        fi
    done
}

# 停止旧容器
stop_old_container() {
    print_color "$YELLOW" "\n[3/7] 检查现有MindsDB容器..."
    
    if docker ps -a --format "{{.Names}}" | grep -q "^mindsdb$"; then
        print_color "$YELLOW" "  ! 发现现有容器，正在停止和删除..."
        docker stop mindsdb >/dev/null 2>&1
        docker rm mindsdb >/dev/null 2>&1
        print_color "$GREEN" "  ✓ 已清理旧容器"
    else
        print_color "$GREEN" "  ✓ 没有发现旧容器"
    fi
}

# 启动MindsDB容器
start_mindsdb_container() {
    print_color "$YELLOW" "\n[4/7] 启动MindsDB容器..."
    
    # 创建数据卷
    docker volume create mindsdb_data >/dev/null 2>&1
    print_color "$GREEN" "  ✓ 创建数据卷: mindsdb_data"
    
    # 检测操作系统类型
    if [[ "$OSTYPE" == "linux-gnu"* ]]; then
        # Linux系统，可能需要使用实际IP
        if [ "$MYSQL_HOST" == "host.docker.internal" ]; then
            MYSQL_HOST=$(ip route | grep default | awk '{print $3}')
            print_color "$YELLOW" "  ! Linux系统检测，使用主机IP: $MYSQL_HOST"
        fi
    fi
    
    # 拉取镜像
    print_color "$WHITE" "  → 拉取MindsDB镜像..."
    docker pull mindsdb/mindsdb:$MINDSDB_VERSION >/dev/null 2>&1
    
    # 启动容器
    print_color "$WHITE" "  → 启动容器..."
    container_id=$(docker run -d \
        --name mindsdb \
        -p 47334:47334 \
        -p 47335:47335 \
        -v mindsdb_data:/root/mindsdb \
        --restart unless-stopped \
        mindsdb/mindsdb:$MINDSDB_VERSION 2>&1)
    
    if [ $? -eq 0 ]; then
        print_color "$GREEN" "  ✓ 容器已启动: ${container_id:0:12}"
    else
        print_color "$RED" "  ✗ 容器启动失败"
        exit 1
    fi
}

# 等待MindsDB启动
wait_for_mindsdb() {
    if [ "$SKIP_HEALTH_CHECK" = true ]; then
        print_color "$YELLOW" "\n[5/7] 跳过健康检查..."
        return
    fi
    
    print_color "$YELLOW" "\n[5/7] 等待MindsDB启动..."
    
    max_attempts=30
    attempt=0
    
    while [ $attempt -lt $max_attempts ]; do
        if curl -s -X POST http://localhost:47334/api/sql/query \
            -H "Content-Type: application/json" \
            -d '{"query": "SELECT 1;"}' >/dev/null 2>&1; then
            print_color "$GREEN" "  ✓ MindsDB已成功启动"
            return
        fi
        
        attempt=$((attempt + 1))
        echo -n "."
        sleep 2
    done
    
    print_color "$RED" "\n  ✗ MindsDB启动超时"
    print_color "$WHITE" "    请检查容器日志: docker logs mindsdb"
    exit 1
}

# 配置数据源
configure_data_sources() {
    print_color "$YELLOW" "\n[6/7] 配置MySQL数据源..."
    
    # 获取MySQL密码
    if [ -z "$MYSQL_PASSWORD" ]; then
        echo -n "请输入MySQL密码: "
        read -s MYSQL_PASSWORD
        echo
    fi
    
    # 配置数据库
    databases=(
        "htinfo_db:ht_info_db"
        "ext_ref_db:ext_ref_db"
    )
    
    for db_pair in "${databases[@]}"; do
        IFS=':' read -r db_name db_actual <<< "$db_pair"
        
        query="CREATE DATABASE IF NOT EXISTS $db_name WITH ENGINE = 'mysql', PARAMETERS = {\"host\": \"$MYSQL_HOST\", \"port\": $MYSQL_PORT, \"database\": \"$db_actual\", \"user\": \"$MYSQL_USER\", \"password\": \"$MYSQL_PASSWORD\"};"
        
        print_color "$WHITE" "  → 配置数据源: $db_name"
        
        response=$(curl -s -X POST http://localhost:47334/api/sql/query \
            -H "Content-Type: application/json" \
            -d "{\"query\": \"$query\"}" 2>&1)
        
        if [ $? -eq 0 ]; then
            print_color "$GREEN" "  ✓ 数据源配置成功: $db_name"
        else
            print_color "$YELLOW" "  ! 数据源配置失败: $db_name"
            print_color "$WHITE" "    错误: $response"
        fi
    done
}

# 创建配置文件
create_config_files() {
    print_color "$YELLOW" "\n[7/7] 生成配置文件..."
    
    # 创建MindsDB MCP配置文件
    cat > config/mindsdb_mcp.yaml << EOF
# MindsDB MCP Server Configuration
# Generated by deploy-mindsdb.sh
server:
  name: "mindsdb-mcp"
  version: "1.0.0"
  host: "localhost"
  port: 47334

databases:
  - name: "htinfo_db"
    type: "mysql"
    connection:
      host: "$MYSQL_HOST"
      port: $MYSQL_PORT
      database: "ht_info_db"
      user: "$MYSQL_USER"
    tables:
      - walmart_online_item
      - walmart_online_theme
      - walmart_orders

  - name: "ext_ref_db"
    type: "mysql"
    connection:
      host: "$MYSQL_HOST"
      port: $MYSQL_PORT
      database: "ext_ref_db"
      user: "$MYSQL_USER"
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
EOF
    
    print_color "$GREEN" "  ✓ 创建配置文件: config/mindsdb_mcp.yaml"
    
    # 创建环境变量文件模板
    if [ ! -f ".env" ]; then
        cat > .env.example << EOF
# MindsDB MCP Server Environment Variables
# Generated by deploy-mindsdb.sh

# MySQL Configuration
MYSQL_HOST=$MYSQL_HOST
MYSQL_PORT=$MYSQL_PORT
MYSQL_USER=$MYSQL_USER
MYSQL_PASSWORD=your_secure_password_here

# MindsDB Configuration
MINDSDB_HOST=localhost
MINDSDB_PORT=47334

# AI Model Configuration (Optional)
DEEPSEEK_API_KEY=your_api_key_here
EOF
        
        print_color "$GREEN" "  ✓ 创建环境变量模板: .env.example"
        print_color "$YELLOW" "    请复制并编辑.env.example为.env，填入实际密码"
    fi
}

# 显示部署摘要
show_summary() {
    print_color "$CYAN" "\n═══════════════════════════════════════════════"
    print_color "$GREEN" "         部署完成！"
    print_color "$CYAN" "═══════════════════════════════════════════════"
    
    print_color "$YELLOW" "\n访问地址:"
    print_color "$WHITE" "  MindsDB Web UI: http://localhost:47334"
    print_color "$WHITE" "  API Endpoint:   http://localhost:47334/api/sql/query"
    
    print_color "$YELLOW" "\n验证部署:"
    print_color "$WHITE" "  docker logs mindsdb --tail 50"
    print_color "$WHITE" "  curl http://localhost:47334/api/sql/query -H \"Content-Type: application/json\" -d '{\"query\": \"SHOW DATABASES;\"}'"
    
    print_color "$YELLOW" "\n测试集成:"
    print_color "$WHITE" "  uv run python main.py \"查询沃尔玛最新的在线商品信息\" --debug"
    
    print_color "$YELLOW" "\n管理命令:"
    print_color "$WHITE" "  停止服务: docker stop mindsdb"
    print_color "$WHITE" "  启动服务: docker start mindsdb"
    print_color "$WHITE" "  查看日志: docker logs mindsdb -f"
    print_color "$WHITE" "  删除服务: docker rm mindsdb"
    
    print_color "$YELLOW" "\n注意事项:"
    print_color "$WHITE" "  1. 请确保MySQL服务可访问"
    print_color "$WHITE" "  2. 更新conf.yaml启用MindsDB集成"
    print_color "$WHITE" "  3. 配置.env文件中的密码信息"
}

# 主函数
main() {
    show_banner
    
    # 设置错误处理
    set -e
    trap 'print_color "$RED" "\n✗ 部署失败: 第 $LINENO 行出错"' ERR
    
    check_prerequisites
    initialize_directories
    stop_old_container
    start_mindsdb_container
    wait_for_mindsdb
    configure_data_sources
    create_config_files
    show_summary
}

# 执行主函数
main "$@"