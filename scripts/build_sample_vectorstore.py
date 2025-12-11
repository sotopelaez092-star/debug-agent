#!/usr/bin/env python3
"""
构建示例向量数据库

用于测试 RAG 功能的小型知识库
包含常见 Python 错误的 Stack Overflow 风格解答
"""

import sys
from pathlib import Path

project_root = Path(__file__).resolve().parent.parent
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))

import logging
import chromadb
from chromadb.config import Settings
from src.rag.embedder import Embedder

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# 示例 Stack Overflow 风格的问答数据
SAMPLE_QA_DATA = [
    # NameError
    {
        "id": "so_001",
        "content": """Q: NameError: name 'variable' is not defined

A: This error occurs when you try to use a variable that hasn't been defined yet. Common causes:
1. Typo in variable name (e.g., 'nme' instead of 'name')
2. Variable defined in different scope
3. Variable defined after usage

Solution: Check spelling, ensure variable is defined before use, or check scope.""",
        "metadata": {"error_type": "NameError", "source": "stackoverflow"}
    },
    {
        "id": "so_002",
        "content": """Q: Python NameError in f-string

A: When using f-strings, make sure variable names inside {} are spelled correctly.
Wrong: f"Hello {nme}"  # NameError if 'nme' not defined
Right: f"Hello {name}"

Common fix: Check variable spelling in f-string expressions.""",
        "metadata": {"error_type": "NameError", "source": "stackoverflow"}
    },

    # TypeError
    {
        "id": "so_003",
        "content": """Q: TypeError: can only concatenate str (not "int") to str

A: This happens when you try to concatenate a string with a non-string type.

Wrong: "Age: " + 25
Right: "Age: " + str(25)  # Convert int to str
Or: f"Age: {25}"  # Use f-string

Solutions:
1. Use str() to convert: "text" + str(number)
2. Use f-strings: f"text {number}"
3. Use format(): "text {}".format(number)""",
        "metadata": {"error_type": "TypeError", "source": "stackoverflow"}
    },
    {
        "id": "so_004",
        "content": """Q: TypeError when adding string and integer

A: Python doesn't allow implicit type conversion in concatenation.

Example fix:
# Wrong
x = "5"
result = x + 3  # TypeError

# Right - convert string to int
result = int(x) + 3  # = 8

# Or convert int to string
result = x + str(3)  # = "53" """,
        "metadata": {"error_type": "TypeError", "source": "stackoverflow"}
    },

    # AttributeError
    {
        "id": "so_005",
        "content": """Q: AttributeError: 'str' object has no attribute 'uper'

A: This is a typo - the correct method name is 'upper()', not 'uper()'.

Common string method typos:
- uper() → upper()
- repalce() → replace()
- stirp() → strip()
- splti() → split()

Fix: Check the exact spelling of the method name.""",
        "metadata": {"error_type": "AttributeError", "source": "stackoverflow"}
    },
    {
        "id": "so_006",
        "content": """Q: AttributeError: 'list' object has no attribute 'srot'

A: Common list method typo. Correct spelling is 'sort()', not 'srot()'.

Common list method typos:
- srot() → sort()
- apend() → append()
- extnend() → extend()
- reomve() → remove()

Solution: Use correct method name: my_list.sort()""",
        "metadata": {"error_type": "AttributeError", "source": "stackoverflow"}
    },

    # IndexError
    {
        "id": "so_007",
        "content": """Q: IndexError: list index out of range

A: You're trying to access an index that doesn't exist in the list.

Example:
nums = [1, 2, 3]  # valid indices: 0, 1, 2
print(nums[3])    # IndexError! Index 3 doesn't exist

Solutions:
1. Use len() to check: if i < len(nums): nums[i]
2. Use try-except
3. For last element: nums[-1] instead of nums[len(nums)]""",
        "metadata": {"error_type": "IndexError", "source": "stackoverflow"}
    },
    {
        "id": "so_008",
        "content": """Q: How to get last element without IndexError

A: Common mistake is using nums[len(nums)] which causes IndexError.

Wrong: nums[len(nums)]  # Out of range!
Right: nums[len(nums) - 1]  # Last element
Better: nums[-1]  # Python negative indexing

Negative indexing:
- nums[-1] = last element
- nums[-2] = second to last""",
        "metadata": {"error_type": "IndexError", "source": "stackoverflow"}
    },

    # KeyError
    {
        "id": "so_009",
        "content": """Q: KeyError when accessing dictionary

A: KeyError means the key doesn't exist in the dictionary.

Common cause: Typo in key name
user = {"name": "Tom", "email": "t@t.com"}
print(user["emial"])  # KeyError! Should be "email"

Solutions:
1. Check key spelling
2. Use .get(): user.get("email", "default")
3. Check if key exists: if "email" in user:""",
        "metadata": {"error_type": "KeyError", "source": "stackoverflow"}
    },

    # RecursionError
    {
        "id": "so_010",
        "content": """Q: RecursionError: maximum recursion depth exceeded

A: Your recursive function doesn't have a proper base case.

Wrong:
def factorial(n):
    return n * factorial(n - 1)  # Never stops!

Right:
def factorial(n):
    if n <= 1:  # Base case!
        return 1
    return n * factorial(n - 1)

Always add a base case that stops recursion.""",
        "metadata": {"error_type": "RecursionError", "source": "stackoverflow"}
    },

    # ImportError
    {
        "id": "so_011",
        "content": """Q: ImportError: No module named 'xxx'

A: The module you're trying to import doesn't exist or isn't installed.

Solutions:
1. Check spelling: from utlis import x → from utils import x
2. Install missing package: pip install module_name
3. Check if module is in the correct directory
4. Check PYTHONPATH includes the module location""",
        "metadata": {"error_type": "ImportError", "source": "stackoverflow"}
    },
    {
        "id": "so_012",
        "content": """Q: ModuleNotFoundError vs ImportError

A: ModuleNotFoundError is a subclass of ImportError (Python 3.6+).

Common fixes for import issues:
1. Check file name matches import (case-sensitive)
2. Add __init__.py for packages
3. Use relative imports: from . import module
4. Check circular imports""",
        "metadata": {"error_type": "ImportError", "source": "stackoverflow"}
    },

    # ValueError
    {
        "id": "so_013",
        "content": """Q: ValueError: invalid literal for int() with base 10

A: You're trying to convert a non-numeric string to int.

Wrong: int("hello")  # ValueError
Wrong: int("3.14")   # ValueError (use float first)
Right: int("42")     # Works

For floats: int(float("3.14"))  # Convert to float first""",
        "metadata": {"error_type": "ValueError", "source": "stackoverflow"}
    },

    # ZeroDivisionError
    {
        "id": "so_014",
        "content": """Q: ZeroDivisionError: division by zero

A: You're dividing by zero, which is undefined.

Fix: Check for zero before dividing
if divisor != 0:
    result = number / divisor
else:
    result = 0  # or handle error

Or use try-except:
try:
    result = a / b
except ZeroDivisionError:
    result = float('inf')  # or handle appropriately""",
        "metadata": {"error_type": "ZeroDivisionError", "source": "stackoverflow"}
    },

    # FileNotFoundError
    {
        "id": "so_015",
        "content": """Q: FileNotFoundError: No such file or directory

A: The file path is incorrect or file doesn't exist.

Solutions:
1. Check file path spelling
2. Use absolute path: /full/path/to/file.txt
3. Check current working directory: import os; print(os.getcwd())
4. Use pathlib: Path(__file__).parent / "file.txt" """,
        "metadata": {"error_type": "FileNotFoundError", "source": "stackoverflow"}
    },
]


def build_vectorstore(output_path: str = "data/vectorstore/chroma_s1"):
    """构建示例向量数据库"""

    logger.info("=" * 60)
    logger.info("构建示例 RAG 向量数据库")
    logger.info("=" * 60)

    # 1. 初始化 Embedder
    logger.info("\n1. 初始化 Embedding 模型...")
    embedder = Embedder(model_name="BAAI/bge-small-en-v1.5")
    logger.info("   ✅ 模型加载完成")

    # 2. 初始化 ChromaDB
    logger.info(f"\n2. 初始化 ChromaDB: {output_path}")

    # 确保目录存在
    Path(output_path).mkdir(parents=True, exist_ok=True)

    client = chromadb.PersistentClient(
        path=output_path,
        settings=Settings(anonymized_telemetry=False, allow_reset=True)
    )

    # 删除已存在的 collection
    try:
        client.delete_collection("stackoverflow_kb")
        logger.info("   删除已存在的 collection")
    except:
        pass

    collection = client.create_collection(
        name="stackoverflow_kb",
        metadata={"description": "Stack Overflow Python 错误问答知识库"}
    )
    logger.info("   ✅ Collection 创建完成")

    # 3. 生成 Embeddings 并添加数据
    logger.info(f"\n3. 添加 {len(SAMPLE_QA_DATA)} 条知识...")

    ids = [item["id"] for item in SAMPLE_QA_DATA]
    documents = [item["content"] for item in SAMPLE_QA_DATA]
    metadatas = [item["metadata"] for item in SAMPLE_QA_DATA]

    # 生成 embeddings
    embeddings = embedder.encode_batch(documents)

    # 添加到 collection
    collection.add(
        ids=ids,
        documents=documents,
        metadatas=metadatas,
        embeddings=embeddings.tolist()
    )

    # 4. 验证
    count = collection.count()
    logger.info(f"\n4. 验证: {count} 条数据已添加")

    # 测试检索
    logger.info("\n5. 测试检索...")
    test_query = "NameError variable not defined"
    test_embedding = embedder.encode_text(test_query)

    results = collection.query(
        query_embeddings=[test_embedding.tolist()],
        n_results=3
    )

    logger.info(f"   查询: '{test_query}'")
    logger.info(f"   返回 {len(results['ids'][0])} 条结果")

    logger.info("\n" + "=" * 60)
    logger.info("✅ 向量数据库构建完成！")
    logger.info(f"   路径: {output_path}")
    logger.info(f"   文档数: {count}")
    logger.info("=" * 60)


if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser(description="构建示例向量数据库")
    parser.add_argument("--output", type=str, default="data/vectorstore/chroma_s1",
                        help="输出路径")
    args = parser.parse_args()

    build_vectorstore(args.output)
