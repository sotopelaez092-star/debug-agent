# 🐛 Debug Agent

> An intelligent debugging assistant that automatically fixes Python bugs using RAG and LLM agents.

[![Python](https://img.shields.io/badge/Python-3.11+-blue.svg)](https://www.python.org/downloads/)
[![License](https://img.shields.io/badge/License-MIT-green.svg)](LICENSE)
[![Status](https://img.shields.io/badge/Status-In%20Development-yellow.svg)]()

## 🎯 Project Overview

**Development Progress**: Week 1/12 (Project Initialization) 🚧

An AI-powered debugging system that:
- 🔍 Analyzes Python code and error messages
- 📚 Searches solutions from Stack Overflow knowledge base (RAG)
- 🐳 Executes code in secure Docker sandbox
- 🔧 Automatically generates and verifies fixes
- 📊 Provides detailed explanations

**Key Differentiators vs ChatGPT/Copilot:**
- ✅ Actually **executes code** to verify fixes
- ✅ **Iterative fixing** (up to 3 retry attempts)
- ✅ **RAG-enhanced** with Stack Overflow knowledge
- ✅ Target: **60%+ auto-fix success rate**

## 🛠️ Tech Stack
```yaml
Backend: Python 3.11 + FastAPI
LLM: DeepSeek (cost-effective) / Claude 3.5 Sonnet (optional)
RAG: LangChain + ChromaDB + BGE-reranker
Agent: LangGraph
Executor: Docker (secure sandbox)
Frontend: React + Tailwind (Week 9-10)
```

## 📁 Project Structure
```
debug-agent/
├── data/              # Data pipeline
│   ├── raw/          # Raw data (Stack Overflow)
│   ├── processed/    # Processed data
│   └── test_cases/   # Test cases
├── src/               # Source code
│   ├── rag/          # RAG system
│   ├── agent/        # Agent system
│   ├── executor/     # Code executor
│   ├── api/          # FastAPI
│   └── utils/        # Utilities
├── tests/             # Unit tests
├── docs/              # Documentation
├── scripts/           # Helper scripts
└── notebooks/         # Jupyter notebooks
```

## 🚀 Quick Start

### Prerequisites
- Python 3.11+
- DeepSeek API Key (or OpenAI/Claude)

### Installation
```bash
# 1. Clone repository
git clone git@github.com:sotopelaez092-star/debug-agent.git
cd debug-agent

# 2. Create virtual environment
python -m venv venv
source venv/bin/activate  # Mac/Linux
# Windows: venv\Scripts\activate

# 3. Install dependencies
pip install --upgrade pip
pip install -r requirements.txt

# 4. Configure environment
cp .env.example .env
# Edit .env and add your DEEPSEEK_API_KEY
```

### Get DeepSeek API Key

1. Visit https://platform.deepseek.com/
2. Sign up and create API key
3. Copy key to `.env` file

### Test Setup
```bash
# Test configuration
python src/utils/config.py

# Test LLM connection
python src/utils/llm_factory.py
```

## 📅 Development Roadmap

- [x] **Week 1**: Project setup + Data preparation ✅
- [ ] **Week 2**: Basic RAG system
- [ ] **Week 3**: Advanced RAG strategies
- [ ] **Week 4**: Knowledge Graph RAG
- [ ] **Week 5-6**: Agent system
- [ ] **Week 7**: Evaluation framework
- [ ] **Week 8**: Performance optimization
- [ ] **Week 9-11**: Frontend + Deployment
- [ ] **Week 12**: Documentation + Demo

## 💰 Cost Comparison

| Provider | Model | Cost (1M tokens) |
|----------|-------|------------------|
| DeepSeek | deepseek-chat | $0.14 (input) / $0.28 (output) |
| OpenAI | gpt-4-turbo | $10 (input) / $30 (output) |
| Claude | claude-3.5-sonnet | $3 (input) / $15 (output) |

**Estimated Project Cost**: ~$5-10 with DeepSeek 💰

## 📝 License

MIT License

## 👤 Author

**Your Name**
- GitHub: [@sotopelaez092-star](https://github.com/sotopelaez092-star)
- Email: your.email@example.com

---

⭐ Star this repo if you find it helpful!
