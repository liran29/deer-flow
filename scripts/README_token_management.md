# Token Management Toggle Tools

这个目录包含了用于管理和测试Token管理功能的工具脚本。

## 🎯 主要工具

### 1. `toggle_token_management.py` - Token管理开关

用于快速启用/禁用Token管理功能，方便进行对比测试。

**用法：**
```bash
# 查看当前状态
python scripts/toggle_token_management.py status

# 启用Token管理
python scripts/toggle_token_management.py on

# 禁用Token管理
python scripts/toggle_token_management.py off

# 无参数运行 - 显示帮助信息
python scripts/toggle_token_management.py
```

**功能：**
- ✅ 显示当前Token管理状态
- 🔧 一键启用/禁用Token管理
- ⚠️ 提供警告信息和重启提醒
- 📊 显示配置概览信息

### 2. `test_token_management_toggle.py` - 功能验证测试

验证Token管理开关是否正常工作的测试脚本。

**用法：**
```bash
# 测试当前Token管理行为
uv run python scripts/test_token_management_toggle.py
```

**功能：**
- 🧪 创建超大消息序列（52条消息）
- 📊 测试Token修剪行为
- ✅ 验证启用/禁用状态的效果
- 📈 显示修剪前后的消息数量对比

## 📋 对比测试流程

### 完整的对比测试步骤：

1. **启用Token管理测试：**
   ```bash
   # 确保Token管理启用
   python scripts/toggle_token_management.py on
   
   # 验证功能
   uv run python scripts/test_token_management_toggle.py
   
   # 启动服务器进行实际测试
   ./bootstrap-with-logs.sh -d --debug-log
   ```

2. **禁用Token管理测试：**
   ```bash
   # 禁用Token管理
   python scripts/toggle_token_management.py off
   
   # 验证功能
   uv run python scripts/test_token_management_toggle.py
   
   # 重启服务器进行对比测试
   ./bootstrap-with-logs.sh -d --debug-log
   ```

3. **恢复默认设置：**
   ```bash
   # 重新启用Token管理（推荐）
   python scripts/toggle_token_management.py on
   ```

## ⚠️ 重要提醒

- **重启要求**: 修改配置后必须重启服务器才能生效
- **安全警告**: 禁用Token管理可能导致超出LLM token限制的错误
- **测试建议**: 建议在测试环境中进行对比，避免影响生产使用
- **日志记录**: 使用 `--debug-log` 选项可以获得详细的Token管理日志

## 🔍 其他相关工具

- `diagnose_token_issue.py` - Token问题诊断工具
- `analyze_token_trimming.py` - Token修剪分析工具
- `logger_control.py` - 日志控制工具
- `view_logs.sh` - 日志查看工具

## 📊 预期测试结果

### Token管理启用时：
```
Current Status: ✅ ENABLED
Original Messages: 52
After Processing: 16 messages
✅ Token management is working - messages were trimmed
   Removed: 36 messages
```

### Token管理禁用时：
```
Current Status: ❌ DISABLED
Original Messages: 52
After Processing: 52 messages
✅ Token management is disabled - no trimming occurred
```

这种对比能够清楚地验证Token管理功能的有效性和影响。