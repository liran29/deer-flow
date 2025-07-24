#!/bin/bash
# MindsDB部署验证脚本

# 颜色定义
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m'

echo -e "${YELLOW}MindsDB部署验证${NC}\n"

# 1. 检查容器状态
echo -e "${YELLOW}[1/5] 检查容器状态...${NC}"
if docker ps | grep -q mindsdb; then
    echo -e "${GREEN}✓ MindsDB容器正在运行${NC}"
    docker ps --filter "name=mindsdb" --format "table {{.Names}}\t{{.Status}}\t{{.Ports}}"
else
    echo -e "${RED}✗ MindsDB容器未运行${NC}"
    exit 1
fi

# 2. 检查API连接
echo -e "\n${YELLOW}[2/5] 检查API连接...${NC}"
if curl -s -X POST http://localhost:47334/api/sql/query \
    -H "Content-Type: application/json" \
    -d '{"query": "SELECT 1;"}' > /dev/null 2>&1; then
    echo -e "${GREEN}✓ API连接正常${NC}"
else
    echo -e "${RED}✗ API无法连接${NC}"
    exit 1
fi

# 3. 列出数据库
echo -e "\n${YELLOW}[3/5] 列出配置的数据库...${NC}"
response=$(curl -s -X POST http://localhost:47334/api/sql/query \
    -H "Content-Type: application/json" \
    -d '{"query": "SHOW DATABASES;"}')

if [ $? -eq 0 ]; then
    echo -e "${GREEN}✓ 数据库列表:${NC}"
    echo "$response" | python3 -m json.tool 2>/dev/null || echo "$response"
else
    echo -e "${RED}✗ 无法获取数据库列表${NC}"
fi

# 4. 检查数据源连接
echo -e "\n${YELLOW}[4/5] 检查数据源连接...${NC}"
for db in htinfo_db ext_ref_db; do
    echo -n "  检查 $db... "
    response=$(curl -s -X POST http://localhost:47334/api/sql/query \
        -H "Content-Type: application/json" \
        -d "{\"query\": \"SHOW TABLES FROM $db;\"}" 2>&1)
    
    if echo "$response" | grep -q "error"; then
        echo -e "${RED}✗ 连接失败${NC}"
    else
        echo -e "${GREEN}✓ 连接成功${NC}"
    fi
done

# 5. 检查配置文件
echo -e "\n${YELLOW}[5/5] 检查配置文件...${NC}"
files=("config/mindsdb_mcp.yaml" "conf.yaml")
for file in "${files[@]}"; do
    if [ -f "$file" ]; then
        echo -e "${GREEN}✓ $file 存在${NC}"
        if [ "$file" == "conf.yaml" ] && grep -q "mindsdb_database_integration: true" "$file"; then
            echo -e "${GREEN}  ✓ MindsDB集成已启用${NC}"
        elif [ "$file" == "conf.yaml" ]; then
            echo -e "${YELLOW}  ! MindsDB集成未启用，请更新配置${NC}"
        fi
    else
        echo -e "${RED}✗ $file 不存在${NC}"
    fi
done

echo -e "\n${GREEN}验证完成！${NC}"