#!/usr/bin/env python3
"""
从BugsInPy数据构造Agent测试案例
"""

import json

# FastAPI Bug 7 - 最小案例
test_case = {
    "id": "bugsinpy_fastapi_7",
    "source": "BugsInPy",
    "project": "fastapi",
    "bug_id": 7,
    
    # Buggy代码（缺少import）
    "buggy_code": """from fastapi.exceptions import RequestValidationError
from starlette.exceptions import HTTPException
from starlette.requests import Request
from starlette.responses import JSONResponse
from starlette.status import HTTP_422_UNPROCESSABLE_ENTITY


async def http_exception_handler(request: Request, exc: HTTPException) -> JSONResponse:
    return JSONResponse(
        status_code=exc.status_code,
        content={"detail": exc.detail},
    )


async def request_validation_exception_handler(
    request: Request, exc: RequestValidationError
) -> JSONResponse:
    return JSONResponse(
        status_code=HTTP_422_UNPROCESSABLE_ENTITY,
        content={"detail": jsonable_encoder(exc.errors())},
    )
""",
    
    # 错误信息（模拟的）
    "error_traceback": """Traceback (most recent call last):
  File "fastapi/exception_handlers.py", line 22, in request_validation_exception_handler
    content={"detail": jsonable_encoder(exc.errors())},
NameError: name 'jsonable_encoder' is not defined
""",
    
    # 期望的修复
    "expected_fix": {
        "import_to_add": "from fastapi.encoders import jsonable_encoder",
        "location": "top of file"
    },
    
    # 项目结构（简化，只包含相关文件）
    "project_structure": {
        "fastapi/exception_handlers.py": "buggy_code",
        "fastapi/encoders.py": "# Contains jsonable_encoder function"
    }
}

# 保存
with open("test_case_fastapi_7.json", "w") as f:
    json.dump(test_case, f, indent=2)

print("✅ Test case created: test_case_fastapi_7.json")