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

### 端到端测试结果
```
测试用例数: 5
成功率: 100%
首次修复成功率: 100%
平均耗时: 7.17 秒
```

### 支持的错误类型
- NameError（变量未定义、拼写错误）
- ImportError / ModuleNotFoundError（导入失败）
- AttributeError（属性不存在）

### 代码统计
```
新增代码: 3,331 行
修改代码: 1,155 行
新增模块: 11 个
测试覆盖: 主要流程
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

### Q1: 为什么选择 DeepSeek 而不是 OpenAI？
> "DeepSeek 的性价比更高，代码生成能力不输 GPT-4，而且 API 兼容 OpenAI 格式，方便切换。"

### Q2: ContextManager 的懒加载是怎么实现的？
> "初始化时只记录项目路径，不扫描文件。当需要查找某个符号时，先从缓存查，没有再从 import 链追踪加载相关文件。这样大项目也不会卡在初始化。"

### Q3: 为什么用 ChromaDB 而不是 Pinecone/Milvus？
> "ChromaDB 是嵌入式数据库，不需要单独部署服务，适合单机项目。如果要扩展到分布式，可以换成 Milvus。"

### Q4: 如何保证 Docker 沙箱的安全性？
> "三重限制：1) 内存限制 256MB 防止内存炸弹；2) 超时 30 秒防止死循环；3) 禁用网络防止恶意请求。"

### Q5: 这个项目最有挑战的部分是什么？
> "ContextManager 的跨文件追踪。Python 的 import 机制很复杂，有相对导入、包导入、动态导入等。我花了很多时间研究 AST 和 importlib 的实现，最终用符号表 + import 图的方式解决。"

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
