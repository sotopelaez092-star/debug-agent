# Debug Agent

AI-powered Python debugging tool. Automatically finds and fixes bugs using LLM agents and pattern matching.

**85.6% success rate** on complex test cases | **~$0.01 per fix** (DeepSeek) | **~40s average**

---

## Quick Start

```bash
# Clone & install
git clone https://github.com/sotopelaez092-star/debug-agent.git
cd debug-agent
pip install -r requirements.txt

# Set your API key
echo "DEEPSEEK_API_KEY=your_key_here" > .env
```

## CLI Usage

```bash
# Run a file, auto-detect and fix errors
python cli.py run ./my_project main.py

# Provide error message manually
python cli.py fix ./my_project main.py --error "NameError: name 'foo' is not defined"

# Interactive demo with built-in test cases
python cli.py demo
```

### Example: Fix a NameError

```bash
$ python cli.py run tests/test_cases_v1/name_error_v1_01_edit_dist_1 main.py

运行 main.py ...
  捕获到错误:
  NameError: name 'calculate_summ' is not defined

============================================================
  Debug Agent - AI 自动调试
============================================================

[1/3] 分析错误中...
   ✓ 检测到: NameError
   ✓ 单文件错误（快速修复）
   ✓ 验证成功！

============================================================
  ✅ 修复成功!
  尝试次数: 1
  说明: 修复变量名拼写: calculate_summ → calculate_sum
============================================================
```

### Python API

```python
import asyncio
from src.agent.debug_agent import DebugAgent

async def main():
    agent = DebugAgent(project_path="./my_project")
    result = await agent.debug(
        buggy_code=open("main.py").read(),
        error_traceback="NameError: name 'calculate_summ' is not defined",
        error_file="main.py",
    )
    if result.success:
        print(result.fixed_code)

asyncio.run(main())
```

---

## Architecture

```
输入错误 → ErrorIdentifier 解析 → ScopeAnalyzer 判断范围
                                    │
                    ┌───────────────┴───────────────┐
                    │                               │
                 单文件                            跨文件
                    │                               │
            PatternFixer                     FastPath 快速路径
          （不用 LLM，~15ms）                       │
                    │                        Investigator
                    ↓                      （ReAct 深度调查）
               CodeFixer                        │
             （调 LLM 修复）                     ↓
                    │                       CodeFixer
                    └───────────┬───────────────┘
                                │
                         LocalExecutor
                           本地验证
                                │
                        ┌───────┴───────┐
                        │               │
                      成功           重试
                                 (RetryStrategy)
```

### Key Design

- **双路径分流:** 简单错误走 PatternFixer（~15ms，无 LLM 调用），复杂错误才走 LLM 路径
- **策略模式:** 6 种错误类型各有专门策略（NameError / ImportError / AttributeError / TypeError / KeyError / CircularImport）
- **预建索引:** ContextTools 启动时扫描项目，建立符号表，为后续查找提供毫秒级响应

### Supported Error Types

| Error Type | Strategy |
|---|---|
| `NameError` | Levenshtein distance matching against symbol table |
| `ImportError` | Module path fuzzy matching (threshold 0.75) |
| `AttributeError` | Class method list search across inheritance chain |
| `TypeError` | Function signature analysis |
| `KeyError` | Dictionary structure tracking + nested key search |
| `CircularImport` | Import graph cycle detection + TYPE_CHECKING fix |

---

## Benchmarks

### V2 (30 complex multi-file cases)

| Tool | Success Rate | Stability | Avg Time | Cost/Fix |
|---|---|---|---|---|
| **Debug Agent (DeepSeek)** | **85.6%** | ±1.9% | 39.9s | ~$0.01 |
| Aider (DeepSeek) | 73.3% | ±8.8% | 75.6s | ~$0.02 |
| Claude Code | - | - | - | ~$0.25 |

### V1 (30 basic single-file cases)

| Tool | Success Rate |
|---|---|
| **Debug Agent** | **100%** |
| Claude Code | 100% |
| Aider | 73.3% |

---

## Project Structure

```
debug-agent/
├── cli.py                  # CLI entry point
├── requirements.txt
├── .env.example
│
├── src/                    # Source code
│   ├── agent/              #   Core agent modules
│   │   ├── debug_agent.py  #     Main orchestrator / dispatch
│   │   ├── scope_analyzer.py #   Single-file vs cross-file scope detection
│   │   ├── fast_path.py    #     Fast path for high-confidence fixes
│   │   ├── investigator.py #     ReAct investigation loop
│   │   └── retry_strategy.py #   Retry logic on validation failure
│   ├── core/               #   Error ID, code fixer, executor, pattern fixer
│   ├── models/             #   Data models (Pydantic)
│   ├── strategies/         #   6 error-type strategies
│   ├── tools/              #   Code analysis tools (symbol search, grep, etc.)
│   └── utils/              #   LLM client, config, logging
│
├── tests/                  # Test cases
│   ├── test_cases_v1/      #   Simple single-file cases
│   ├── test_cases_v2/      #   Complex multi-file cases
│   └── test_cases_30/      #   V2 benchmark set
│
├── benchmarks/             # Evaluation
│   ├── scripts/            #   Benchmark runner scripts
│   ├── results/            #   Raw results (JSON/CSV)
│   ├── reports/            #   Analysis reports
│   └── test_queries/       #   Test query sets
│
└── data/                   # Test data (JSON reports)
```

---

## Configuration

Copy `.env.example` to `.env` and set your API key:

```bash
cp .env.example .env
```

Key settings:

| Variable | Default | Description |
|---|---|---|
| `DEEPSEEK_API_KEY` | (required) | DeepSeek API key |
| `LLM_PROVIDER` | `deepseek` | LLM provider (deepseek/openai/anthropic) |
| `LLM_MODEL` | `deepseek-chat` | Model name |
| `LLM_TEMPERATURE` | `0.7` | Sampling temperature |
| `MAX_RETRY_ATTEMPTS` | `3` | Max fix attempts |

---

## License

MIT
