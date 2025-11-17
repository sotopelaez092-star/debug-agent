# 🐛 AI Debug Assistant

> 一个支持多文件上下文的智能Python Debug系统

[![Python](https://img.shields.io/badge/Python-3.11+-blue.svg)](https://www.python.org/)
[![Docker](https://img.shields.io/badge/Docker-Required-blue.svg)](https://www.docker.com/)
[![License](https://img.shields.io/badge/License-MIT-green.svg)](LICENSE)

---

## 📋 项目简介

AI Debug Assistant 是一个基于LLM的自动化Python代码调试工具，能够：

- 🔍 **自动识别错误**：从traceback中提取错误类型、文件名、行号
- 📚 **知识检索**：从5000+ Stack Overflow问答中检索相关解决方案（MRR=1.0）
- 🤖 **智能修复**：使用DeepSeek API生成代码修复方案
- 🐳 **安全验证**：在Docker沙箱中执行修复后的代码，验证是否成功
- ⚡ **端到端流程**：一键完成从错误识别到修复验证的全流程

---

## ✨ 核心特性

### 1. 自动上下文对齐（计划中）
- 自动扫描项目所有文件
- 构建符号表和依赖图
- 智能提取跨文件上下文
- **这是ChatGPT/Claude做不到的！**

### 2. RAG知识库（已完成）
- 索引5000+ Stack Overflow高质量问答
- 8个实验系统优化
- Query改写策略：MRR 从 0.733 → 1.0
- Recall@10: 78.86%

### 3. Docker安全沙箱（已完成）
- ⏱️ 超时限制：10秒
- 💾 内存限制：256MB
- 🌐 网络禁用
- ✅ 真实执行验证

---

## 🚀 快速开始

### 环境要求
```bash
Python 3.11+
Docker
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
# 创建 .env 文件
echo "DEEPSEEK_API_KEY=your_api_key_here" > .env

# 5. 启动Docker
# 确保Docker Desktop已运行

# 6. 拉取Python镜像
docker pull python:3.11-alpine
```

### 使用示例
```python
from src.agent.tools.code_fixer import CodeFixer
from src.agent.tools.error_identifier import ErrorIdentifier
from src.agent.tools.rag_searcher import RAGSearcher
from src.agent.tools.docker_executor import DockerExecutor

# 1. 识别错误
identifier = ErrorIdentifier()
error_info = identifier.identify(traceback)

# 2. 检索解决方案
searcher = RAGSearcher()
solutions = searcher.search(error_info['error_type'])

# 3. 生成修复
fixer = CodeFixer()
fix_result = fixer.fix_code(buggy_code, error_traceback, solutions)

# 4. Docker验证
executor = DockerExecutor()
verification = executor.execute(fix_result['fixed_code'])

print(f"修复成功: {verification['success']}")
```

---

## 📊 技术栈
```yaml
LLM服务: DeepSeek API
RAG系统: 
  - Embedding: bge-small-en-v1.5 (384维)
  - 向量数据库: ChromaDB
  - Query改写: 自研策略
代码执行: Docker (安全沙箱)
后端框架: Python 3.11 + FastAPI
前端: React + Tailwind CSS (计划中)
```

---

## 🎯 项目进度

### ✅ 已完成 (Week 1-4)

- [x] RAG系统构建与优化（8个实验）
- [x] CodeFixer - LLM代码修复
- [x] ErrorIdentifier - 错误识别
- [x] RAGSearcher - 知识检索
- [x] DockerExecutor - 安全执行
- [x] 端到端集成测试

### 🚧 进行中 (Week 5)

- [ ] ContextManager - 自动上下文提取（核心创新）
- [ ] DebugAgent - 完整工作流编排

### 📅 计划中 (Week 6-8)

- [ ] Web界面
- [ ] API接口
- [ ] 评估体系
- [ ] 文档完善

---

## 📈 性能指标

### RAG系统性能
```
MRR: 1.0 (完美首位命中率)
Recall@5: 63.54%
Recall@10: 78.86%
平均检索时间: <500ms
```

### Docker沙箱测试
```
✅ 基础执行: 3/3 通过
✅ 超时机制: 10秒精确终止
✅ 网络隔离: 验证通过
✅ 内存限制: 256MB生效
```

---

## 🏗️ 项目结构
```
debug-agent/
├── src/
│   ├── agent/
│   │   └── tools/
│   │       ├── code_fixer.py          # LLM代码修复
│   │       ├── error_identifier.py    # 错误识别
│   │       ├── rag_searcher.py        # 知识检索
│   │       └── docker_executor.py     # 安全执行
│   └── rag/                            # RAG系统
│       ├── retriever.py
│       ├── query_rewriter.py
│       ├── embedder.py
│       └── ...
├── tests/
│   └── test_agent_integration.py      # 集成测试
├── data/
│   └── vectorstore/chroma_s1/         # 向量数据库
└── docs/                               # 文档
```

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

- Stack Overflow 社区提供的高质量问答数据
- DeepSeek 提供的高性价比LLM API
- Anthropic 的RAG最佳实践指导

---

**Star ⭐ 如果这个项目对你有帮助！**