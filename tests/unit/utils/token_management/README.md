# Token Management Tests

This directory contains comprehensive tests for the deer-flow token management system.

## Overview

The token management system ensures that deer-flow works correctly with LLMs that have smaller token limits (like DeepSeek's 32K tokens) by automatically trimming messages and managing large inputs.

## Files

- **`test_token_management.py`** - Comprehensive pytest test suite
- **`demo_token_management.py`** - Interactive demo showing token management in action
- **`run_tests.py`** - Test runner script
- **`README.md`** - This documentation

## Running Tests

### Quick Start (推荐)
```bash
# 从项目根目录运行演示
uv run python tests/unit/utils/token_management/demo_token_management.py

# 从项目根目录运行所有测试
uv run python tests/unit/utils/token_management/test_token_management.py
```

### 使用测试运行器
```bash
# 进入测试目录
cd tests/unit/utils/token_management

# 运行演示
uv run python run_tests.py --demo

# 运行测试套件
uv run python run_tests.py --tests

# 运行所有
uv run python run_tests.py
```

### 单独运行组件
```bash
# 直接运行演示脚本
uv run python demo_token_management.py

# 使用pytest运行测试
uv run python -m pytest test_token_management.py -v
```

## What the Tests Cover

### 1. Token Counting (`TestTokenCounting`)
- Verifies that different models have different token counting ratios
- Ensures token counters work correctly for various models

### 2. Message Trimming (`TestMessageTrimming`)
- Tests that DeepSeek trimming reduces message count appropriately
- Verifies Gemini can handle more messages than DeepSeek
- Ensures message types are preserved during trimming

### 3. Observation Management (`TestObservationManagement`)
- Tests reduction of large observation sets
- Handles empty observation lists correctly

### 4. Real-World Scenarios (`TestRealWorldScenarios`)
- Creates content that actually exceeds DeepSeek's 32K token limit
- Verifies that token management brings inputs within limits
- Tests background investigation result trimming

### 5. Pre-Model Hook (`TestPreModelHook`)
- Tests hook creation and functionality
- Verifies hooks trim messages when needed

### 6. Logging (`TestLogging`)
- Ensures token management operations produce appropriate logs
- Helps with debugging and monitoring

## Demo Output

The demo script shows:
- Token counts for large inputs with different models
- How trimming works with DeepSeek vs Gemini
- Observation management in action
- Real-world scenario simulation
- Logging output from token management

## Expected Results

### Demo Output (演示结果)
```
🦌 Deer-Flow Token Management Demo
==================================================
=== Token Management Demo ===

Large content length: 82,000 characters
DeepSeek tokens: 20,505 (limit: 32,768)
Gemini tokens: 23,433 (limit: 1,000,000)
DeepSeek exceeds limit by: 0 tokens

=== Observation Management Demo ===
Original observations: 15
Average length: 4489 characters
Managed observations: 4
Average length: 3386 characters
Content reduction: 79.9%

=== Real-World Scenario Demo ===
Background investigation would be trimmed:
Original: 69,100 characters
Trimmed: 8,050 characters
Reduction: 88.4%

✓ Token management prevents workflow failures!
✓ Your deer-flow system can now handle models like DeepSeek!
```

### Test Results (测试结果)
```
============================= test session starts ==============================
collecting ... collected 12 items

TestTokenCounting::test_different_models_have_different_ratios PASSED [  8%]
TestMessageTrimming::test_deepseek_trimming_reduces_messages PASSED [ 16%]
TestMessageTrimming::test_gemini_handles_more_than_deepseek PASSED [ 25%]
TestMessageTrimming::test_trimming_preserves_message_types PASSED [ 33%]
TestObservationManagement::test_observation_management_reduces_count PASSED [ 41%]
TestObservationManagement::test_empty_observations_handled PASSED [ 50%]
TestRealWorldScenarios::test_massive_input_exceeds_deepseek_limit PASSED [ 58%]
TestRealWorldScenarios::test_token_management_brings_within_limits PASSED [ 66%]
TestRealWorldScenarios::test_background_investigation_trimming PASSED [ 75%]
TestPreModelHook::test_pre_model_hook_creation PASSED [ 83%]
TestPreModelHook::test_pre_model_hook_trims_messages PASSED [ 91%]
TestLogging::test_trimming_produces_logs PASSED [100%]

============================== 12 passed in 3.98s ==============================
```

### Key Success Indicators (成功指标)
- ✅ **12/12 tests passing** - 所有测试通过
- ✅ **Observation management**: 15 → 4 observations (79.9% reduction)
- ✅ **Background investigation trimming**: 88.4% content reduction
- ✅ **Token limits respected**: Large inputs handled correctly for DeepSeek
- ✅ **Logging working**: Token management logs produced
- ✅ **Cross-model compatibility**: DeepSeek and Gemini both supported

## Troubleshooting

If tests fail:

### 常见问题 (Common Issues)
1. **ModuleNotFoundError**: 确保从项目根目录运行，使用 `uv run`
   ```bash
   cd /path/to/deer-flow
   uv run python tests/unit/utils/token_management/demo_token_management.py
   ```

2. **Dependencies missing**: 安装测试依赖
   ```bash
   uv add --group test pytest pytest-cov pytest-asyncio
   ```

3. **Import errors**: 检查必要文件存在
   - `src/utils/token_manager.py`
   - `src/utils/token_counter.py` 
   - `conf.yaml` (包含 TOKEN_MANAGEMENT 配置)

4. **Tests not found**: 使用完整路径运行
   ```bash
   uv run python tests/unit/utils/token_management/test_token_management.py
   ```

### 检查清单 (Checklist)
- [ ] 在项目根目录 (`deer-flow/`)
- [ ] 使用 `uv run` 命令
- [ ] TOKEN_MANAGEMENT 配置在 `conf.yaml` 中
- [ ] TokenManager 和 TokenCounter 类可导入

## Integration

These tests verify that the token management system works correctly with the actual deer-flow workflow, ensuring that:
- Large background investigation results are trimmed
- Conversation history doesn't exceed model limits
- Different models get appropriate token allocations
- The system provides detailed logging for monitoring