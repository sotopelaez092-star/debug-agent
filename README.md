# 🐛 Debug Agent

> 基于 LLM 的 Python 自动调试工具，达到 85.6% 成功率

[![Python](https://img.shields.io/badge/Python-3.11+-blue.svg)](https://www.python.org/)
[![License](https://img.shields.io/badge/License-MIT-green.svg)](LICENSE)

---

## 📋 项目简介

Debug Agent 是一个能够自动修复 Python 代码错误的命令行工具。用户只需运行命令，工具就会自动：

1. 捕获错误信息
2. 分析错误原因
3. 定位问题代码
4. 生成修复方案
5. 验证修复结果

**最终成绩**：在 30 个测试用例的 Benchmark 中达到 **85.6% 成功率**（DeepSeek 模型），稳定性 ±1.9%，平均耗时 39.9 秒。

---

## ✨ 核心特性

### 1. 双路径架构
- **快速路径**：简单错误（拼写、导入）无需 LLM，直接修复
- **完整调查**：复杂错误使用 ReAct 循环深入分析
- **置信度判断**：自动选择最合适的修复策略（阈值 0.7）

### 2. 预建索引系统（ContextTools）
- 自动扫描项目所有文件
- 构建符号表和依赖图
- 智能提取跨文件上下文
- 增量更新机制（缓存优化）

### 3. 策略模式（6种错误类型）
- **NameError**: Levenshtein 匹配符号表
- **ImportError**: 模块路径模糊匹配（置信度 0.75）
- **AttributeError**: 搜索类方法列表
- **KeyError**: 字典结构追踪 + 嵌套搜索
- **TypeError**: 函数签名分析
- **CircularImport**: 导入图环检测 + TYPE_CHECKING 方案

### 4. 多层重试机制
- **SmartRetryStrategy**: 建议下一个尝试的方法
- **LoopDetector**: 检测重复修复（2-3-8 阈值）
- **错误类型切换**: 新错误自动重置状态

---

## 🚀 快速开始

### 环境要求
```bash
Python 3.11+
```

### 安装
```bash
# 1. 克隆项目
git clone https://github.com/你的用户名/debug-agent.git
cd debug-agent

# 2. 创建虚拟环境
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate

# 3. 安装依赖
pip install -r requirements.txt

# 4. 配置环境变量
echo "DEEPSEEK_API_KEY=your_api_key_here" > .env
```

### 使用示例
```python
from src.agent.debug_agent_new import DebugAgentNew
from src.core.error_identifier import ErrorIdentifier
from src.core.local_executor import LocalExecutor

# 创建 agent
agent = DebugAgentNew(project_path="./your_project")

# 调试代码
result = await agent.debug(
    buggy_code=buggy_code,
    error_traceback=error_traceback,
    main_file="main.py"
)

print(f"修复成功: {result.success}")
print(f"修复后的代码:\n{result.fixed_code}")
```

---

## 📊 性能指标

### V1 Benchmark（30 个基础用例）
| 工具 | 成功率 | 稳定性 | 平均耗时 |
|-----|--------|-------|---------|
| **Debug Agent (DeepSeek)** | **100%** | ±0% | 35.2s |
| Aider (DeepSeek) | 73.3% | ±8.8% | 75.6s |
| Claude Code | 100% | - | 46.2s |

### V2 Benchmark（30 个复杂用例）
| 工具 | 成功率 | 稳定性 | 平均耗时 |
|-----|--------|-------|---------|
| **Debug Agent (DeepSeek)** | **85.6%** | ±1.9% | 39.9s |
| Aider (DeepSeek) | 73.3% | ±8.8% | 75.6s |

### 成本对比
| 工具 | 单次调试成本 |
|-----|------------|
| Debug Agent (DeepSeek) | ~$0.01 |
| Aider (DeepSeek) | ~$0.02 |
| Claude Code (Claude) | ~$0.25 |

**Debug Agent 成本约为 Claude Code 的 1/25**

---

## 🏗️ 项目结构
```
debug-agent/
├── src/
│   ├── agent/
│   │   ├── debug_agent_new.py    # 主调度器（双路径架构）
│   │   ├── investigator.py       # ReAct 调查员
│   │   └── retry_strategy.py     # 重试策略
│   ├── core/
│   │   ├── error_identifier.py   # 错误识别
│   │   ├── code_fixer.py         # LLM 修复
│   │   ├── pattern_fixer.py      # 快速修复（无需 LLM）
│   │   ├── local_executor.py     # 本地执行
│   │   └── loop_detector.py      # 循环检测
│   ├── strategies/               # 错误处理策略
│   │   ├── base.py               # 策略基类
│   │   ├── registry.py           # 策略注册表
│   │   ├── name_error.py         # NameError 策略
│   │   ├── import_error.py       # ImportError 策略
│   │   ├── attribute_error.py    # AttributeError 策略
│   │   ├── type_error.py         # TypeError 策略
│   │   ├── key_error.py          # KeyError 策略
│   │   └── circular_import.py    # 循环导入策略
│   ├── tools_new/                # 工具系统
│   │   ├── base.py               # 工具基类
│   │   ├── registry.py           # 工具注册表
│   │   ├── context_tools.py      # 预建索引（核心）
│   │   ├── search_symbol_tool.py # 符号搜索
│   │   ├── read_file_tool.py     # 文件读取
│   │   └── grep_tool.py          # 文本搜索
│   ├── models/                   # 数据模型
│   │   ├── error_context.py      # 错误上下文
│   │   ├── investigation_report.py # 调查报告
│   │   └── results.py            # 结果模型
│   └── utils/                    # 工具类
│       ├── llm_client.py         # LLM 客户端
│       └── config.py             # 配置管理
├── tests/
│   └── test_cases_30/            # 30 个测试用例（V2 Benchmark）
├── data/                         # 数据文件
└── docs/                         # 文档
```

---

## 🎯 核心设计

### 1. 双路径架构（借鉴 Gemini CLI）
```
输入错误 → 错误识别 → 范围判断 → ┬─ 单文件 → 快速修复
                              └─ 跨文件 → ┬─ 快速路径（置信度≥0.7）
                                         └─ 完整调查（ReAct 循环）
```

### 2. 工具注册表模式
- 统一的工具基类（`BaseTool`）
- OpenAI function calling 格式
- 6 个核心工具：SearchSymbol, ReadFile, Grep, GetCallers, SetPhase, CompleteInvestigation

### 3. ContextTools 预建索引
```python
{
    "symbol_table": {...},          # 符号定义位置
    "import_graph": {...},          # 导入关系图
    "class_table": {...},           # 类信息（方法列表）
    "function_signatures": {...},   # 函数签名
    "dict_keys": {...},             # 所有字典键
    "call_graph": {...},            # 调用关系图
}
```

### 4. 置信度计算
```python
score = edit_sim * 0.5        # 编辑距离（权重 0.5）
      + uniqueness * 0.2      # 唯一性（权重 0.2）
      + reachable * 0.2       # 可达性（权重 0.2）
      + type_score * 0.1      # 类型匹配（权重 0.1）
```

### 5. PatternFixer（快速修复）
- ~50 个常见方法拼写错误
- ~30 个标准库拼写错误
- ~40% 命中率（无需 LLM）

---

## 🔑 关键数字

| 指标 | 数值 | 说明 |
|-----|------|-----|
| 置信度阈值 | 0.7 | 快速路径 vs 完整调查的分界 |
| ImportError 阈值 | 0.75 | 比其他错误更严格 |
| 相同修复阈值 | 2 | 出现 2 次切换策略 |
| 相同错误阈值 | 3 | 出现 3 次升级调查 |
| 最大尝试次数 | 8 | 超过则放弃 |
| PatternFixer 命中率 | ~40% | 简单拼写错误 |

---

## 🤝 贡献

欢迎提Issue和PR！

---

## 📝 License

MIT License

---

## 👨‍💻 作者

Tom - [GitHub](https://github.com/你的用户名)

---

## 🙏 致谢

- DeepSeek 提供的高性价比 LLM API
- Gemini CLI 的架构设计启发

---

**Star ⭐ 如果这个项目对你有帮助！**
