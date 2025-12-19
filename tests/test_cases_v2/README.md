# Debug Agent V2 Benchmark 测试用例

## 📊 概述

共 **30 个复杂跨文件测试用例**，分为 6 种错误类型，每种 5 个测试。

## 🎯 测试分类

| 错误类型 | 测试数量 | 难度 |
|---------|---------|------|
| NameError | 5 | Medium |
| ImportError | 5 | Medium |
| AttributeError | 5 | Medium-Hard |
| TypeError | 5 | Medium-Hard |
| KeyError | 5 | Hard |
| CircularImport | 5 | Hard |

## 📁 测试结构

每个测试用例包含：
- `main.py` - 入口文件
- `metadata.json` - 测试元数据
- 多个子目录/文件 - 模拟真实项目结构

## 📝 元数据格式

```json
{
  "error_type": "CircularImport",
  "case_id": "circular_import_v2_01_deep_chain",
  "description": "测试描述",
  "error_file": "main.py",
  "error_message": "错误信息",
  "expected_fix": "预期修复方案",
  "difficulty": "hard",
  "files_involved": ["相关文件列表"],
  "requires_exploration": true,
  "expected_lines_to_change": 4,
  "complexity_factors": ["复杂度因素"],
  "optimal_fix": "最优修复策略"
}
```

## 🎯 性能目标

- **成功率**: 85%+
- **平均耗时**: <40s
- **稳定性**: ±2%

## 🔍 测试用例示例

### CircularImport - case_01_deep_chain
- **场景**: 4个服务的循环导入链
- **复杂度**: UserService → OrderService → ProductService → NotificationService → UserService
- **预期修复**: 延迟导入（lazy imports）或 TYPE_CHECKING

### NameError - case_01_refactored_function  
- **场景**: 函数重构后名称变更
- **复杂度**: 跨文件调用未更新
- **预期修复**: 更新所有调用点的函数名

## 📈 与 V1 的区别

| 特性 | V1 | V2 |
|-----|----|----|
| 测试数量 | 30 | 30 |
| 文件复杂度 | 单文件为主 | 多文件跨文件 |
| 错误类型 | 基础错误 | 复杂场景错误 |
| 需要探索 | 较少 | 大部分需要 |
| 成功率目标 | 100% | 85%+ |

