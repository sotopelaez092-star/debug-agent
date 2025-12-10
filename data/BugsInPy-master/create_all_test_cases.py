#!/usr/bin/env python3
"""
从BugsInPy数据批量创建所有测试案例
"""

import json
import os
import re

def extract_buggy_code_from_patch(patch_file):
    """从patch文件提取buggy版本的代码"""
    with open(patch_file, 'r') as f:
        content = f.read()
    
    # 这里需要解析diff，提取-行（删除的）和context
    # 简化版：返回patch内容让人工处理
    return content

def create_test_cases():
    """创建所有9个测试案例"""
    
    base_path = "projects"
    
    test_cases = []
    
    # ========== Pandas Bugs ==========
    
    # Pandas Bug 108
    test_cases.append({
        "id": "bugsinpy_pandas_108",
        "source": "BugsInPy",
        "project": "pandas",
        "bug_id": 108,
        "description": "Missing import: IntervalDtype",
        "file": "pandas/core/dtypes/cast.py",
        "missing_import": "from .dtypes import IntervalDtype",
        "undefined_name": "IntervalDtype",
        "notes": "Needs manual code extraction from patch"
    })
    
    # Pandas Bug 113
    test_cases.append({
        "id": "bugsinpy_pandas_113",
        "source": "BugsInPy",
        "project": "pandas",
        "bug_id": 113,
        "description": "Missing import: invalid_comparison",
        "file": "pandas/core/arrays/integer.py",
        "missing_import": "from pandas.core.ops import invalid_comparison",
        "undefined_name": "invalid_comparison",
        "notes": "Modified 2 files, need to check which one has the error"
    })
    
    # Pandas Bug 114
    test_cases.append({
        "id": "bugsinpy_pandas_114",
        "source": "BugsInPy",
        "project": "pandas",
        "bug_id": 114,
        "description": "Missing import: extract_array",
        "file": "pandas/core/indexes/base.py",
        "missing_import": "from pandas.core.construction import extract_array",
        "undefined_name": "extract_array",
        "notes": "Needs manual code extraction from patch"
    })
    
    # Pandas Bug 118
    test_cases.append({
        "id": "bugsinpy_pandas_118",
        "source": "BugsInPy",
        "project": "pandas",
        "bug_id": 118,
        "description": "Missing import: pandas.core.common as com",
        "file": "pandas/core/reshape/melt.py",
        "missing_import": "import pandas.core.common as com",
        "undefined_name": "com",
        "notes": "Needs manual code extraction from patch"
    })
    
    # ========== FastAPI Bugs ==========
    
    # FastAPI Bug 7 (already done, but include for completeness)
    test_cases.append({
        "id": "bugsinpy_fastapi_7",
        "source": "BugsInPy",
        "project": "fastapi",
        "bug_id": 7,
        "description": "Missing import: jsonable_encoder",
        "file": "fastapi/exception_handlers.py",
        "missing_import": "from fastapi.encoders import jsonable_encoder",
        "undefined_name": "jsonable_encoder",
        "status": "completed"
    })
    
    # ========== Scrapy Bugs ==========
    
    # Scrapy Bug 3
    test_cases.append({
        "id": "bugsinpy_scrapy_3",
        "source": "BugsInPy",
        "project": "scrapy",
        "bug_id": 3,
        "description": "Missing import: urljoin, urlparse",
        "file": "scrapy/downloadermiddlewares/redirect.py",
        "missing_import": "from six.moves.urllib.parse import urljoin, urlparse",
        "undefined_name": "urljoin",
        "notes": "Needs manual code extraction from patch"
    })
    
    # Scrapy Bug 7
    test_cases.append({
        "id": "bugsinpy_scrapy_7",
        "source": "BugsInPy",
        "project": "scrapy",
        "bug_id": 7,
        "description": "Missing import: six, strip_html5_whitespace",
        "file": "scrapy/http/request/form.py",
        "missing_import": "import six; from w3lib.html import strip_html5_whitespace",
        "undefined_name": "six",
        "notes": "Two imports missing"
    })
    
    # Scrapy Bug 9
    test_cases.append({
        "id": "bugsinpy_scrapy_9",
        "source": "BugsInPy",
        "project": "scrapy",
        "bug_id": 9,
        "description": "Missing import: arg_to_iter",
        "file": "scrapy/mail.py",
        "missing_import": "from .utils.misc import arg_to_iter",
        "undefined_name": "arg_to_iter",
        "notes": "Needs manual code extraction from patch"
    })
    
    # Scrapy Bug 10
    test_cases.append({
        "id": "bugsinpy_scrapy_10",
        "source": "BugsInPy",
        "project": "scrapy",
        "bug_id": 10,
        "description": "Missing import: safe_url_string",
        "file": "scrapy/downloadermiddlewares/redirect.py",
        "missing_import": "from w3lib.url import safe_url_string",
        "undefined_name": "safe_url_string",
        "notes": "Needs manual code extraction from patch"
    })
    
    # 保存元数据
    output_file = "bugsinpy_test_cases_metadata.json"
    with open(output_file, 'w') as f:
        json.dump(test_cases, f, indent=2)
    
    print(f"✅ Created metadata for {len(test_cases)} test cases")
    print(f"📄 Saved to: {output_file}")
    print()
    print("📋 Summary:")
    print(f"  - Pandas: 4 bugs")
    print(f"  - FastAPI: 1 bug (completed)")
    print(f"  - Scrapy: 4 bugs")
    print()
    print("⚠️  Next step: Extract buggy code from each patch file")
    
    return test_cases

if __name__ == "__main__":
    create_test_cases()