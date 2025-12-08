# CLAUDE.md - AI Debug Assistant

> This document provides comprehensive guidance for AI assistants working with the debug-agent codebase.

## Project Overview

**AI Debug Assistant** is an automated Python code debugging tool powered by LLM (DeepSeek API). It automatically identifies errors, retrieves solutions from a knowledge base, generates code fixes, and validates them in a secure Docker sandbox.

### Key Differentiator
The **ContextManager** module provides automatic cross-file context extraction - something ChatGPT/Claude cannot do natively. This allows one-shot debugging of multi-file Python projects.

## Technology Stack

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

## Project Structure

```
debug-agent/
├── src/
│   ├── agent/                      # Core agent modules
│   │   ├── debug_agent.py          # Main orchestrator - coordinates the debug workflow
│   │   ├── context_manager.py      # Cross-file context extraction (core innovation)
│   │   └── tools/
│   │       ├── code_fixer.py       # LLM-powered code repair
│   │       ├── error_identifier.py # Traceback parsing
│   │       ├── rag_searcher.py     # Knowledge retrieval wrapper
│   │       └── docker_executor.py  # Secure code execution
│   ├── rag/                        # RAG system components
│   │   ├── retriever.py            # Base vector retriever
│   │   ├── query_rewriter.py       # Query preprocessing
│   │   ├── embedder.py             # Embedding generation
│   │   ├── vector_store.py         # ChromaDB interface
│   │   ├── hybrid_retriever.py     # Combined retrieval strategies
│   │   ├── bm25_retriever.py       # Keyword-based retrieval
│   │   ├── reranker_retriever.py   # Result reranking
│   │   ├── config.py               # RAG configuration
│   │   └── evaluator.py            # Retrieval evaluation
│   ├── api/                        # FastAPI endpoints
│   │   ├── main.py                 # API entry point
│   │   └── models.py               # Pydantic models
│   ├── utils/                      # Utility modules
│   │   ├── config.py               # Application configuration
│   │   ├── logger.py               # Logging setup
│   │   ├── llm_factory.py          # LLM client factory
│   │   ├── code_analyzer.py        # Code analysis utilities
│   │   └── error_parser.py         # Error parsing helpers
│   └── evaluation/                 # Evaluation tools
│       └── retrieval_eval.py       # RAG evaluation metrics
├── tests/                          # Test suite
│   ├── test_end_to_end.py          # Full pipeline tests
│   ├── test_context_manager*.py    # Context extraction tests
│   ├── test_debug_agent.py         # Agent tests
│   ├── test_code_fixer*.py         # CodeFixer tests
│   └── ...
├── data/
│   ├── vectorstore/                # ChromaDB vector stores
│   │   └── chroma_s1/              # Default collection
│   ├── evaluation/                 # Evaluation datasets
│   └── test_cases/                 # Test case definitions
├── docs/                           # Documentation
│   ├── week3/                      # RAG system documentation
│   ├── week4/                      # Core modules documentation
│   └── week5/                      # ContextManager documentation
├── demo/                           # Demo application
│   └── app.py                      # Streamlit/Gradio demo
├── backups/                        # Data backups
├── requirements.txt                # Python dependencies
├── .env.example                    # Environment variables template
└── .gitignore
```

## Core Workflow

The debug pipeline follows this sequence:

```
1. ErrorIdentifier.identify(traceback)
   └── Extracts: error_type, error_message, file, line

2. ContextManager.get_context_for_error() [if multi-file]
   └── Returns: related_symbols, related_files, import_suggestions

3. RAGSearcher.search(error_query)
   └── Returns: Stack Overflow solutions (top-k)

4. CodeFixer.fix_code(buggy_code, error, context, solutions)
   └── Returns: fixed_code, explanation, changes

5. DockerExecutor.execute_with_context(fixed_code, related_files)
   └── Returns: success, stdout, stderr, exit_code

6. Retry loop (up to max_retries) if verification fails
```

## Key Classes and Their Responsibilities

### `DebugAgent` (src/agent/debug_agent.py)
Main orchestrator that coordinates the entire debug workflow.
```python
agent = DebugAgent(api_key="...", project_path="/path/to/project")
result = agent.debug(buggy_code, error_traceback, error_file="main.py")
```

### `ContextManager` (src/agent/context_manager.py)
**Core innovation** - Automatically extracts cross-file context:
- `_scan_project()`: Scans all .py files in project
- `_build_symbol_table()`: Uses AST to extract function/class definitions
- `_build_import_graph()`: Analyzes import relationships
- `get_context_for_error()`: Smart context extraction based on error type

Handles error types:
- `NameError`: Finds undefined symbol definitions
- `ImportError/ModuleNotFoundError`: Locates module files, fuzzy-matches typos
- `AttributeError`: Finds class definitions

### `CodeFixer` (src/agent/tools/code_fixer.py)
LLM-powered code repair using DeepSeek API:
- Builds detailed prompts with context
- Requests JSON-formatted responses
- Parses and validates LLM output

### `DockerExecutor` (src/agent/tools/docker_executor.py)
Secure code execution sandbox:
- Memory limit: 256MB
- Timeout: 30 seconds (configurable)
- Network: Disabled
- Supports multi-file execution via volume mounts

### `RAGSearcher` (src/agent/tools/rag_searcher.py)
Knowledge retrieval from Stack Overflow corpus:
- Query rewriting for better results
- Vector similarity search
- Returns formatted solutions

## Environment Setup

### Required Environment Variables
Create a `.env` file (see `.env.example`):

```bash
# Required
DEEPSEEK_API_KEY=your_deepseek_api_key
DEEPSEEK_BASE_URL=https://api.deepseek.com/v1

# Optional
LLM_PROVIDER=deepseek
LLM_MODEL=deepseek-chat
LLM_TEMPERATURE=0.7
EMBEDDING_MODEL=BAAI/bge-small-en-v1.5
CHROMA_PERSIST_DIR=./data/vectorstore/chroma_s1
```

### Installation
```bash
# Create virtual environment
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Ensure Docker is running
docker pull python:3.11-alpine
```

## Development Guidelines

### Code Style
- Use Python type hints
- Follow PEP 8 conventions
- Use `logging` module (not print statements)
- Chinese comments are acceptable (project originated in Chinese)

### Logging
```python
import logging
logger = logging.getLogger(__name__)

logger.info("Informational message")
logger.debug("Debug details")
logger.warning("Warning message")
logger.error("Error message", exc_info=True)
```

### Error Handling
- Validate inputs at method entry
- Raise `ValueError` for invalid parameters
- Raise `RuntimeError` for execution failures
- Log errors with `exc_info=True` for stack traces

### Testing
```bash
# Run all tests
pytest tests/

# Run specific test file
pytest tests/test_end_to_end.py -v

# Run with logging output
pytest tests/test_debug_agent.py -v --log-cli-level=INFO
```

### Key Test Files
- `tests/test_end_to_end.py`: Full pipeline integration tests
- `tests/test_context_manager.py`: Context extraction tests
- `tests/test_code_fixer_with_context.py`: LLM fix generation tests
- `tests/test_docker_multifile.py`: Multi-file execution tests

## RAG System Details

### Vector Store
- Located at: `data/vectorstore/chroma_s1/`
- Contains: 5000+ Stack Overflow Q&A pairs
- Embedding: bge-small-en-v1.5 (384 dimensions)

### Performance Metrics
```
MRR: 1.0 (perfect first-hit rate after query rewriting)
Recall@5: 63.54%
Recall@10: 78.86%
Average retrieval time: <500ms
```

### Query Rewriting Strategy
The `QueryRewriter` transforms error messages into optimized search queries:
1. Removes traceback boilerplate
2. Extracts error type and message
3. Limits query length to 500 chars

## Docker Sandbox Configuration

```python
DockerExecutor(
    image="python:3.11-alpine",  # Lightweight Python image
    timeout=30,                   # Execution timeout in seconds
    memory_limit="256m"          # Memory constraint
)
```

### Multi-file Execution
Use `execute_with_context()` for projects with dependencies:
```python
executor.execute_with_context(
    main_code="...",
    related_files={"utils.py": "...", "models.py": "..."},
    main_filename="main.py"
)
```

## Common Issues and Solutions

### "DEEPSEEK_API_KEY not found"
Ensure `.env` file exists with valid API key.

### "Vector store not found"
The ChromaDB store must exist at `data/vectorstore/chroma_s1/`. Check if the data was properly initialized.

### Docker connection errors
Ensure Docker daemon is running:
```bash
docker info
docker pull python:3.11-alpine
```

### Import errors in tests
Add project root to Python path:
```python
import sys
from pathlib import Path
sys.path.append(str(Path(__file__).parent.parent))
```

## API Usage

### Basic Usage
```python
from src.agent.debug_agent import DebugAgent

# Initialize agent
agent = DebugAgent(
    api_key="your_deepseek_key",
    project_path="/path/to/project"  # Optional, for multi-file support
)

# Debug code
result = agent.debug(
    buggy_code="def greet(name):\n    print(f'Hello, {nane}')",
    error_traceback="NameError: name 'nane' is not defined",
    error_file="main.py",  # Optional
    max_retries=2
)

# Result structure
{
    "success": True,
    "original_error": {...},
    "solutions": [...],
    "attempts": [...],
    "final_code": "...",
    "total_attempts": 1
}
```

### Individual Tool Usage
```python
# Error identification
from src.agent.tools.error_identifier import ErrorIdentifier
identifier = ErrorIdentifier()
error_info = identifier.identify(traceback_text)

# RAG search
from src.agent.tools.rag_searcher import RAGSearcher
searcher = RAGSearcher()
solutions = searcher.search("NameError: name 'x' is not defined", top_k=5)

# Code fixing
from src.agent.tools.code_fixer import CodeFixer
fixer = CodeFixer(api_key="...")
result = fixer.fix_code(buggy_code, error_message, context, rag_solutions)

# Docker execution
from src.agent.tools.docker_executor import DockerExecutor
executor = DockerExecutor()
result = executor.execute("print('Hello')")
```

## Performance Benchmarks

### End-to-End Tests (Week 5)
- Success rate: 100% (5/5 cases)
- First-attempt success: 100%
- Average time: 7.17 seconds
- Supported error types: NameError, ImportError, AttributeError

### Docker Sandbox
- Basic execution: Pass
- Timeout mechanism: 10s precise termination
- Network isolation: Verified
- Memory limits: 256MB enforced

## Future Development Areas

### Planned Features
- [ ] Web interface (React + Tailwind CSS)
- [ ] REST API endpoints
- [ ] More error type support (TypeError, IndexError, KeyError)
- [ ] Incremental project scanning
- [ ] Caching for performance

### Known Limitations
1. Python-only support (no other languages)
2. Large projects (>100 files) not optimized
3. Some complex AttributeError cases may need improvement

## File Naming Conventions

- Source files: `snake_case.py`
- Test files: `test_*.py`
- Config files: `config.py`, `.env`
- Documentation: `*.md`

## Important Directories to Ignore

When scanning projects, ContextManager ignores:
- `venv/`, `env/`, `.venv/`
- `__pycache__/`, `.pytest_cache/`
- `.git/`, `.svn/`
- `node_modules/`
- `dist/`, `build/`
- `.idea/`, `.vscode/`
