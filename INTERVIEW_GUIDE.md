# AI Debug Assistant - 面试准备指南

> 本文档帮助你准备项目面试，包含技术亮点、架构设计、难点突破等内容

---

## 一、项目一句话介绍

**AI Debug Assistant** 是一个基于 LLM 的自动化 Python 代码调试系统，能够自动识别错误、提取跨文件上下文、检索知识库、生成修复代码，并在 Docker 沙箱中验证——实现从错误到修复的全自动闭环。

---

## 二、为什么做这个项目？（项目动机）

### 痛点分析
1. **ChatGPT/Claude 的局限性**：只能看到用户粘贴的代码片段，无法理解多文件项目的上下文
2. **手动调试效率低**：开发者需要反复 Google、Stack Overflow、尝试修复
3. **调试知识分散**：解决方案散落在各个网站，没有统一的知识库

### 解决方案
构建一个端到端的自动调试系统：
```
错误识别 → 上下文提取 → 知识检索 → 代码修复 → 沙箱验证 → 自动重试
```

---

## 三、系统架构图

```
┌─────────────────────────────────────────────────────────────────┐
│                        DebugAgent (主编排器)                      │
├─────────────────────────────────────────────────────────────────┤
│                                                                   │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐           │
│  │ LoopDetector │  │ TokenManager │  │ ConfigLoader │           │
│  │  循环检测     │  │  上下文压缩   │  │  配置加载    │           │
│  └──────────────┘  └──────────────┘  └──────────────┘           │
│                                                                   │
│  ┌─────────────────────────────────────────────────────────┐    │
│  │                    Core Pipeline                         │    │
│  │  ┌─────────┐  ┌─────────┐  ┌─────────┐  ┌─────────┐    │    │
│  │  │ Error   │→ │ Context │→ │  RAG    │→ │  Code   │    │    │
│  │  │Identifier│  │ Manager │  │Searcher │  │  Fixer  │    │    │
│  │  └─────────┘  └─────────┘  └─────────┘  └─────────┘    │    │
│  │       ↓                                      ↓          │    │
│  │  ┌─────────┐                          ┌─────────┐      │    │
│  │  │ Error   │                          │ Docker  │      │    │
│  │  │ Router  │                          │Executor │      │    │
│  │  └─────────┘                          └─────────┘      │    │
│  └─────────────────────────────────────────────────────────┘    │
│                                                                   │
└─────────────────────────────────────────────────────────────────┘

┌─────────────────┐  ┌─────────────────┐  ┌─────────────────┐
│   handlers/     │  │   collectors/   │  │      rag/       │
│  NameError      │  │  EnvDetector    │  │  ChromaDB       │
│  ImportError    │  │  (Python环境)    │  │  BM25           │
│  TypeError      │  │                 │  │  Query Rewrite  │
└─────────────────┘  └─────────────────┘  └─────────────────┘
```

---

## 四、核心技术亮点（面试重点）

### 1. ContextManager - 跨文件上下文提取（核心创新）

**问题**：ChatGPT/Claude 只能看到用户粘贴的代码，无法理解项目中其他文件的定义

**解决方案**：
```python
class ContextManager:
    def __init__(self, project_path):
        self._file_cache = {}      # 懒加载文件缓存
        self._symbol_cache = {}    # 符号表缓存
        self._all_files = None     # 延迟发现

    def get_context_for_error(self, error_type, error_message, error_file):
        # 根据错误类型智能提取上下文
        if error_type == "NameError":
            return self._handle_name_error(symbol_name)
        elif error_type == "ImportError":
            return self._handle_import_error(module_name)
        # ...
```

**技术细节**：
- 使用 Python AST 解析代码，提取函数/类定义
- 构建项目级符号表（symbol table）
- 分析 import 依赖关系，构建依赖图
- **懒加载设计**：不在初始化时扫描所有文件，而是按需加载

**面试话术**：
> "这是项目的核心创新点。传统的 AI 编程助手只能看到用户粘贴的代码片段，但真实项目往往是多文件的。比如 main.py 引用了 utils.py 中的函数，AI 看不到 utils.py 就无法正确修复。我的 ContextManager 通过 AST 解析构建项目级符号表，能够自动追踪 import 链，提取相关文件的上下文。"

---

### 2. LoopDetector - 智能循环检测

**问题**：LLM 可能反复生成相似的错误修复，陷入无限重试

**解决方案**：
```python
class LoopDetector:
    def check(self, attempt):
        # 检测代码相似度（使用 hash）
        code_hash = self._hash_code(attempt['fixed_code'])
        if code_hash in self._code_history:
            return {"is_loop": True, "loop_type": "similar_code"}

        # 检测相同错误重复出现
        error_hash = self._hash_error(attempt['error'])
        if self._error_counts[error_hash] >= self.max_same_error:
            return {"is_loop": True, "loop_type": "same_error"}
```

**面试话术**：
> "这个设计灵感来自 Google 的 Gemini CLI。LLM 有时会'固执'地重复相同的修复思路，导致无限重试。我设计了双重检测机制：一是代码指纹检测，避免生成重复代码；二是错误计数，同一错误出现3次就终止并建议换个思路。"

---

### 3. TokenManager - 上下文压缩

**问题**：LLM 有 token 限制，过多的上下文会导致截断或成本过高

**解决方案**：
```python
class TokenManager:
    PRIORITY_ORDER = [
        'error_file_content',   # 最高优先级
        'error_message',
        'related_symbols',
        'import_suggestions',
        'rag_solutions',
        'related_files',        # 最低优先级
    ]

    def compress_context(self, context):
        # 按优先级保留内容，超出 token 限制则截断低优先级内容
```

**面试话术**：
> "LLM 的上下文窗口是有限的，我设计了基于优先级的压缩策略。错误所在文件的代码优先级最高，RAG 检索结果次之，相关文件最低。当总 token 超限时，从低优先级开始截断，确保最重要的信息不丢失。"

---

### 4. RAG 知识检索系统

**技术栈**：
- Embedding: `BAAI/bge-small-en-v1.5` (384维)
- Vector DB: ChromaDB
- 混合检索: Vector + BM25

**Query 改写策略**：
```python
class QueryRewriter:
    def rewrite(self, error_message):
        # 移除 traceback 干扰信息
        # 提取核心错误类型和描述
        # 限制 query 长度
```

**性能指标**：
| 指标 | 优化前 | 优化后 |
|------|--------|--------|
| MRR | 0.733 | **1.0** |
| Recall@10 | 65% | **78.86%** |

**面试话术**：
> "RAG 系统索引了 5000+ Stack Overflow 高质量问答。关键优化是 Query 改写——原始的 traceback 太长太杂，我提取核心错误信息重写 query，MRR 从 0.733 提升到 1.0，即首个检索结果就是最相关的。"

---

### 5. Docker 安全沙箱

**为什么需要**：自动生成的代码可能有 bug 甚至恶意代码，必须隔离执行

**配置**：
```python
DockerExecutor(
    image="python:3.11-alpine",
    timeout=30,           # 防止死循环
    memory_limit="256m",  # 防止内存炸弹
    network_disabled=True # 防止网络攻击
)
```

**多文件执行支持**：
```python
def execute_with_context(self, main_code, related_files, main_filename):
    # 将相关文件挂载到容器中
    # 执行主文件并捕获输出
```

---

### 6. ErrorRouter - 错误类型路由

**设计模式**：策略模式（Strategy Pattern）

```python
class ErrorRouter:
    def __init__(self):
        self.handlers = {
            'NameError': NameErrorHandler(),
            'ImportError': ImportErrorHandler(),
            'TypeError': TypeErrorHandler(),
        }

    def route(self, error_info):
        handler = self.handlers.get(error_info['error_type'])
        return handler.handle(error_info)
```

**每种 Handler 的专业能力**：
- **NameErrorHandler**: 在符号表中搜索未定义变量，检查拼写错误
- **ImportErrorHandler**: 检查模块路径、fuzzy match 模块名
- **TypeErrorHandler**: 分析参数类型、推断期望类型

---

## 五、项目数据指标

### Route vs ReAct 模式对比测试（18个用例）

| 指标 | Route 模式 | ReAct 模式 | 胜者 |
|------|-----------|-----------|------|
| **正确率** | 94.4% (17/18) | 94.4% (17/18) | 平手 |
| **可运行率** | 100% (18/18) | 94.4% (17/18) | Route |
| **平均耗时** | 15.2s | 27.1s | Route |
| **平均迭代** | N/A | 3.4次 | - |

### 按错误类型统计

| 错误类型 | Route 正确率 | ReAct 正确率 |
|----------|-------------|-------------|
| NameError | 80% (4/5) | 80% (4/5) |
| TypeError | 100% (3/3) | 100% (3/3) |
| AttributeError | 100% (4/4) | 100% (4/4) |
| IndexError | 100% (3/3) | 100% (3/3) |
| KeyError | 100% (2/2) | 100% (2/2) |
| RecursionError | 100% (1/1) | 100% (1/1) |

### RAG 系统性能
```
MRR: 1.0 (完美首位命中)
Recall@5: 63.54%
Recall@10: 78.86%
知识库: 5000+ Stack Overflow Q&A
```

### Docker 沙箱测试
```
基础执行: Pass
超时机制: 30秒精确终止
网络隔离: 验证通过
内存限制: 256MB生效
```

---

## 六、技术难点与解决方案

### 难点1：跨文件符号解析
**问题**：Python 的 import 机制复杂（相对导入、包导入、别名等）

**解决**：
1. 使用 AST 提取所有 import 语句
2. 构建 import 图，支持循环引用检测
3. 懒加载设计，避免扫描无关文件

### 难点2：LLM 输出不稳定
**问题**：LLM 返回的格式不一定符合预期（JSON 解析失败等）

**解决**：
1. 在 prompt 中明确要求 JSON 格式
2. 多重解析尝试（正则 fallback）
3. 验证修复代码的语法正确性

### 难点3：性能优化
**问题**：大项目扫描所有文件很慢

**解决**：
1. **懒加载**：只在需要时加载文件
2. **缓存**：符号表和文件内容缓存
3. **配置忽略**：支持 `.debugagent.yaml` 配置忽略目录

---

## 七、与竞品对比

| 特性 | ChatGPT/Claude | GitHub Copilot | AI Debug Assistant |
|------|----------------|----------------|-------------------|
| 跨文件上下文 | ❌ | 部分支持 | ✅ 完整支持 |
| 知识库检索 | ❌ | ❌ | ✅ RAG |
| 代码验证 | ❌ | ❌ | ✅ Docker 沙箱 |
| 自动重试 | ❌ | ❌ | ✅ 带循环检测 |
| 本地部署 | ❌ | ❌ | ✅ |

---

## 八、未来规划

1. **Web 界面**：React + Tailwind CSS
2. **更多语言支持**：JavaScript、Go、Rust
3. **IDE 插件**：VSCode Extension
4. **增量扫描**：文件变更时增量更新符号表
5. **Agent 协作**：多 Agent 并行调试

---

## 九、面试常见问题

### 项目介绍类

**Q1: 一句话介绍你的项目？**
> "这是一个基于 LLM 的自动化 Python 调试系统，支持跨文件上下文提取、RAG 知识检索、Docker 沙箱验证，实现从错误识别到代码修复的端到端自动化。测试正确率 94.4%。"

**Q2: 你的项目和直接用 ChatGPT 有什么区别？**
> "三点区别：1) **跨文件上下文**——ChatGPT 看不到项目其他文件，我的 ContextManager 可以自动提取；2) **知识增强**——我构建了 5000+ Stack Overflow 的 RAG 系统；3) **自动验证**——在 Docker 沙箱中执行验证修复是否成功。"

### 技术深度类

**Q3: Route 和 ReAct 模式的区别？**
> "**Route 模式**：按错误类型直接路由到专用 Handler，流程固定，快速（15s），适合简单明确的错误。**ReAct 模式**：让 LLM 自己决定调用什么工具，Thought→Action→Observation 循环，更灵活（27s），适合复杂问题。测试显示正确率相同，但 Route 更快更稳定。"

**Q4: ContextManager 是怎么实现跨文件上下文提取的？**
> "分三步：1) **扫描项目**——用 AST 解析所有 .py 文件；2) **构建符号表**——提取函数/类定义位置；3) **构建依赖图**——分析 import 关系。当出现 NameError 时在符号表查找定义，ImportError 时查依赖图找模块路径。为了性能实现了懒加载。"

**Q5: RAG 系统的 MRR 怎么达到 1.0 的？**
> "关键是 **Query 改写**。原始 traceback 太长有噪音，我实现了 QueryRewriter：移除样板文本、提取核心错误信息、限制长度。优化后 MRR 从 0.733 提升到 1.0。"

**Q6: 为什么要做循环检测？**
> "LLM 可能重复生成相同的错误修复，陷入死循环。LoopDetector 做两件事：1) 代码相似度检测——超过 90% 就警告；2) 错误重复检测——同一错误 3 次就终止。这是借鉴 Gemini CLI 的设计。"

### 设计决策类

**Q7: 为什么选择 DeepSeek 而不是 OpenAI？**
> "性价比。DeepSeek 价格是 GPT-4 的 1/10，代码能力相当，且兼容 OpenAI API 格式，切换方便。"

**Q8: 为什么用 ChromaDB 而不是 Pinecone/Milvus？**
> "轻量级、嵌入式、不需要额外部署，适合这个规模（5000 条数据）。如果要扩展到百万级会换 Milvus。"

**Q9: 为什么用 Docker 而不是 subprocess？**
> "安全性。用户代码可能有死循环或恶意代码。Docker 提供：内存限制（256MB）、超时（30s）、网络隔离。即使 `while True` 或 `os.system('rm -rf /')` 也不会影响主机。"

### 挑战与改进类

**Q10: 开发过程中最大的挑战是什么？**
> "跨文件上下文的准确提取。最初把所有文件都塞给 LLM，token 爆炸。后来改成：只提取相关符号、懒加载、TokenManager 压缩。既保证上下文完整又控制 token 量。"

**Q11: 如果要做成生产级别，你会怎么改进？**
> "几个方向：1) **缓存**——相同错误的 RAG 结果缓存；2) **增量扫描**——监听文件变化而不是全量扫描；3) **多语言**——扩展到 JavaScript/Go；4) **A/B 测试**——根据错误类型自动选择最优模式。"

### 代码实现类

**Q12: 能简单描述一下 ReAct 的工作流程吗？**
> "循环执行：1) LLM 输出 Thought（思考）和 Action（工具调用）；2) 系统执行工具返回 Observation；3) 把 Observation 追加到消息历史；4) 重复直到 LLM 输出 Final Answer 或达到最大迭代次数。"

**Q13: TokenManager 的压缩策略是什么？**
> "基于优先级截断。优先级：错误文件内容 > 错误消息 > 相关符号 > RAG 结果 > 其他。从低优先级开始截断，保证最重要的信息不丢失。"

---

## 十、项目演示脚本

```python
from src.agent.debug_agent import DebugAgent

# 1. 初始化
agent = DebugAgent(
    api_key="your_key",
    project_path="/path/to/demo_project"
)

# 2. 模拟一个 NameError
buggy_code = """
def calculate_total(items):
    total = 0
    for item in items:
        total += itme.price  # 拼写错误: itme -> item
    return total
"""

error = """
Traceback (most recent call last):
  File "main.py", line 4, in calculate_total
    total += itme.price
NameError: name 'itme' is not defined
"""

# 3. 自动修复
result = agent.debug(buggy_code, error)
print(f"修复成功: {result['success']}")
print(f"修复后代码:\n{result['final_code']}")
```

---

**祝面试顺利！**
