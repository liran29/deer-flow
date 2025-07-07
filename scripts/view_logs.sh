#!/bin/bash
# 查看 deer-flow 日志

echo "================================"
echo "🔍 查看 Token Management 日志"
echo "================================"
echo ""
echo "请在另一个终端运行服务："
echo "1. API Server: uv run python server.py"
echo "2. Web: cd web && npm run dev"
echo ""
echo "然后在 Web 界面测试，这里会显示日志..."
echo ""
echo "按 Ctrl+C 退出"
echo "================================"
echo ""

# 如果有日志文件，tail 它
if [ -f "deer-flow.log" ]; then
    tail -f deer-flow.log | grep -E "(Token Management|token counter|Reduction|INFO|ERROR)"
else
    echo "提示：服务日志会直接输出到运行服务的终端窗口"
    echo "请查看运行 'uv run python server.py' 的终端窗口"
fi