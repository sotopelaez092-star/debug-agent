# AI Debug Assistant

> 一个支持多文件上下文的智能Python Debug系统

[![Python](https://img.shields.io/badge/Python-3.11+-blue.svg)](https://www.python.org/)
[![Docker](https://img.shields.io/badge/Docker-Required-blue.svg)](https://www.docker.com/)
[![License](https://img.shields.io/badge/License-MIT-green.svg)](LICENSE)

---

## 项目简介

AI Debug Assistant 是一个基于LLM的自动化Python代码调试工具，能够：

- **自动识别错误**：从traceback中提取错误类型、文件名、行号
- **跨文件上下文**：自动提取多文件项目的相关代码上下文
- **知识检索**：从5000+ Stack Overflow问答中检索相关解决方案（MRR=1.0）
- **智能修复**：使用DeepSeek API生成代码修复方案
- **安全验证**：在Docker沙箱中执行修复后的代码，验证是否成功
- **循环检测**：防止重复尝试相同的修复方案
- **端到端流程**：一键完成从错误识别到修复验证的全流程

---

## 核心特性

### 1. 自动上下文提取（ContextManager）
- 懒加载设计，按需扫描文件
- 构建符号表和依赖图
- 智能提取跨文件上下文
- 支持 NameError、ImportError、AttributeError 等错误类型
- **这是ChatGPT/Claude做不到的！**

### 2. 智能循环检测（LoopDetector）
- 检测重复的修复代码
- 识别相同错误的重复出现
- 自动建议新的修复方向
- 防止无效的重试循环

### 3. Token管理与压缩（TokenManager）
- 基于优先级的上下文压缩
- 自动截断过长内容
- 优化LLM输入质量
- 支持RAG结果压缩

### 4. RAG知识库
- 索引5000+ Stack Overflow高质量问答
- 8个实验系统优化
- Query改写策略：MRR 从 0.733 → 1.0
- Recall@10: 78.86%

### 5. Docker安全沙箱
- 超时限制：30秒（可配置）
- 内存限制：256MB
- 网络禁用
- 支持多文件执行

### 6. 项目配置支持
- 支持 `.debugagent.yaml` 配置文件
- 自定义忽略目录
- 配置最大重试次数
- 框架检测（Django、FastAPI、Flask、pytest）

---

## 快速开始

### 环境要求
```bash
Python 3.11+
Docker
```

### 安装
```bash
# 1. 克隆项目
git clone https://github.com/your-username/debug-agent.git
cd debug-agent

# 2. 创建虚拟环境
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate

# 3. 安装依赖
pip install -r requirements.txt

# 4. 配置环境变量
cp .env.example .env
# 编辑 .env 文件，填入你的 DEEPSEEK_API_KEY

# 5. 启动Docker
# 确保Docker Desktop已运行

# 6. 拉取Python镜像
docker pull python:3.11-alpine
```

### 使用示例

#### 完整调试流程
```python
from src.agent.debug_agent import DebugAgent

# 初始化Agent
agent = DebugAgent(
    api_key="your_deepseek_api_key",
    project_path="/path/to/your/project"  # 可选，用于多文件上下文
)

# 执行调试
result = agent.debug(
    buggy_code="""
def greet(name):
    print(f"Hello, {nane}")
""",
    error_traceback="""
Traceback (most recent call last):
  File "main.py", line 2, in greet
    print(f"Hello, {nane}")
NameError: name 'nane' is not defined
""",
    error_file="main.py",
    max_retries=2
)

print(f"修复成功: {result['success']}")
print(f"修复后代码:\n{result['final_code']}")
```

#### 使用单独工具
```python
from src.agent.tools.error_identifier import ErrorIdentifier
from src.agent.tools.rag_searcher import RAGSearcher
from src.agent.tools.code_fixer import CodeFixer
from src.agent.tools.docker_executor import DockerExecutor

# 1. 识别错误
identifier = ErrorIdentifier()
error_info = identifier.identify(traceback)

# 2. 检索解决方案
searcher = RAGSearcher()
solutions = searcher.search(f"{error_info['error_type']}: {error_info['error_message']}")

# 3. 生成修复
fixer = CodeFixer(api_key="your_key")
fix_result = fixer.fix_code(buggy_code, error_traceback, solutions=solutions)

# 4. Docker验证
executor = DockerExecutor()
verification = executor.execute(fix_result['fixed_code'])

print(f"修复成功: {verification['success']}")
```

---

## 项目配置

在项目根目录创建 `.debugagent.yaml` 文件：

```yaml
# 扫描配置
scan:
  ignore_dirs:
    - venv
    - __pycache__
    - .git
    - node_modules
  focus_dirs: []  # 留空则扫描全部

# 调试配置
debug:
  max_retries: 3
  timeout: 30
  enable_rag: true
  enable_docker: true

# 框架类型（自动检测或手动指定）
framework: null  # django, fastapi, flask, pytest

# LLM配置
llm:
  temperature: 0.3
  max_tokens: 2000
```

---

## 技术栈

```yaml
Language: Python 3.11+
LLM Service: DeepSeek API (OpenAI-compatible)
RAG System:
  - Embedding: BAAI/bge-small-en-v1.5 (384-dim)
  - Vector Database: ChromaDB
  - Query Rewriting: Custom strategy
Code Execution: Docker (isolated sandbox)
Backend Framework: FastAPI + Uvicorn
Testing: pytest, pytest-asyncio
```

---

## 项目结构

```
debug-agent/
├── src/
│   ├── agent/                      # 核心代理模块
│   │   ├── debug_agent.py          # 主编排器
│   │   ├── context_manager.py      # 跨文件上下文提取（核心创新）
│   │   ├── loop_detector.py        # 循环检测器
│   │   ├── token_manager.py        # Token管理器
│   │   ├── config_loader.py        # 配置加载器
│   │   └── tools/
│   │       ├── code_fixer.py       # LLM代码修复
│   │       ├── error_identifier.py # 错误识别
│   │       ├── rag_searcher.py     # 知识检索
│   │       └── docker_executor.py  # 安全执行
│   ├── rag/                        # RAG系统
│   │   ├── retriever.py            # 向量检索
│   │   ├── query_rewriter.py       # Query改写
│   │   ├── embedder.py             # Embedding生成
│   │   └── ...
│   ├── handlers/                   # 错误处理器
│   │   ├── base_handler.py         # 基类
│   │   ├── error_router.py         # 错误路由
│   │   ├── name_error_handler.py   # NameError处理
│   │   ├── import_error_handler.py # ImportError处理
│   │   └── type_error_handler.py   # TypeError处理
│   ├── collectors/                 # 信息收集器
│   │   └── env_detector.py         # Python环境检测
│   ├── api/                        # FastAPI接口
│   └── utils/                      # 工具模块
├── tests/                          # 测试套件
├── data/
│   └── vectorstore/chroma_s1/      # 向量数据库
├── docs/                           # 文档
└── CLAUDE.md                       # AI助手指南
```

---

## 性能指标

### 端到端测试
```
成功率: 100% (5/5 cases)
首次尝试成功: 100%
平均耗时: 7.17秒
支持错误类型: NameError, ImportError, AttributeError
```

### RAG系统性能
```
MRR: 1.0 (完美首位命中率)
Recall@5: 63.54%
Recall@10: 78.86%
平均检索时间: <500ms
```

### Docker沙箱测试
```
基础执行: Pass
超时机制: 30秒精确终止
网络隔离: 验证通过
内存限制: 256MB生效
```

---

## 已完成功能

- [x] RAG系统构建与优化（8个实验）
- [x] CodeFixer - LLM代码修复
- [x] ErrorIdentifier - 错误识别
- [x] RAGSearcher - 知识检索
- [x] DockerExecutor - 安全执行
- [x] ContextManager - 跨文件上下文提取（懒加载）
- [x] LoopDetector - 循环检测
- [x] TokenManager - 上下文压缩
- [x] ConfigLoader - 项目配置支持
- [x] ErrorRouter - 错误类型路由
- [x] PythonEnvDetector - 环境检测
- [x] DebugAgent - 完整工作流编排
- [x] 端到端集成测试

## 计划功能

- [ ] Web界面
- [ ] REST API接口
- [ ] 更多错误类型支持（TypeError, IndexError, KeyError）
- [ ] 增量项目扫描
- [ ] 性能缓存优化

---

## 贡献

欢迎提Issue和PR！

---

## License

MIT License

---

## 致谢

- Stack Overflow 社区提供的高质量问答数据
- DeepSeek 提供的高性价比LLM API
- Anthropic 的RAG最佳实践指导

---

**Star 如果这个项目对你有帮助！**
