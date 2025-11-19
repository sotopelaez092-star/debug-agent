"""
API数据模型定义

包含：
- DebugRequest: Debug请求模型
- DebugResponse: Debug响应模型
"""

from pydantic import BaseModel, Field, validator
from typing import Optional, Dict, Any, List


class DebugRequest(BaseModel):
    """Debug请求模型"""
    
    buggy_code: str = Field(
        ...,
        description=(
            "需要被分析、定位错误并进行修复的代码片段。"
            "支持传入任意 Python 代码字符串，可包含语法错误、逻辑错误或潜在风险。"
        ),
        min_length=1,
        max_length=5000,
        example="def greet(name):\n    print(nme)"
    )
    
    error_traceback: str = Field(
        ...,
        description=(
            "该代码在运行过程中产生的完整报错信息（traceback）。"
            "用于帮助调试 Agent 精确定位问题来源。"
        ),
        min_length=1,
        max_length=5000,
        example=(
            "Traceback (most recent call last):\n"
            "  File \"test.py\", line 2, in greet\n"
            "    print(nme)\n"
            "NameError: name 'nme' is not defined"
        )
    )
    
    max_retries: Optional[int] = Field(
        2,
        description="Agent 在自动修复失败时允许的最大重试次数（1-5次）。",
        ge=1,
        le=5,
        example=2
    )
    
    @validator('buggy_code')
    def validate_code(cls, v):
        """验证代码不能为空"""
        if not v.strip():
            raise ValueError('代码不能为空')
        return v
    
    @validator('error_traceback')
    def validate_traceback(cls, v):
        """验证traceback不能为空"""
        if not v.strip():
            raise ValueError('错误信息不能为空')
        return v
    
    class Config:
        json_schema_extra = {
            "example": {
                "buggy_code": "def greet(name):\n    print(nme)",
                "error_traceback": (
                    "Traceback (most recent call last):\n"
                    "  File \"test.py\", line 2, in greet\n"
                    "    print(nme)\n"
                    "NameError: name 'nme' is not defined"
                ),
                "max_retries": 2
            }
        }


class DebugResponse(BaseModel):
    """Debug响应模型"""

    success: bool = Field(
        ...,
        description="表示调试 Agent 是否成功修复了目标代码。"
    )

    fixed_code: Optional[str] = Field(
        None,
        description="修复后的完整代码。如果修复失败则为 None。",
        example="def greet(name):\n    print(name)"
    )

    explanation: Optional[str] = Field(
        None,
        description=(
            "Agent对错误原因和修复方案的自然语言解释。"
            "帮助用户理解问题所在和修复思路。"
        ),
        example="NameError: 变量 'nme' 未定义，已修正为正确的变量名 'name'。"
    )

    execution_result: Optional[Dict[str, Any]] = Field(
        None,
        description=(
            "修复后代码在Docker沙箱中的执行结果。"
            "包含标准输出(stdout)、错误输出(stderr)和退出码(exit_code)。"
        ),
        example={
            "stdout": "Hello, Alice\n",
            "stderr": "",
            "exit_code": 0,
            "success": True
        }
    )

    attempts: int = Field(
        ...,
        description="实际尝试修复的次数，用于观察 Agent 的修复效率。",
        example=1
    )

    diff: Optional[str] = Field(
        None,
        description=(
            "原始代码与修复后代码的差异（unified diff 格式）。"
            "便于用户清晰查看具体的修改内容。"
        ),
        example=(
            "--- original\n"
            "+++ fixed\n"
            "@@ -1,2 +1,2 @@\n"
            " def greet(name):\n"
            "-    print(nme)\n"
            "+    print(name)"
        )
    )

    debug_logs: Optional[List[str]] = Field(
        None,
        description=(
            "Agent在调试过程中的关键步骤记录。"
            "包括错误识别、知识检索、代码修复等环节的日志。"
        ),
        example=[
            "步骤1: 识别错误类型 - NameError",
            "步骤2: 检索到10个相关解决方案",
            "步骤3: 生成修复代码",
            "步骤4: Docker验证通过"
        ]
    )
    
    error_message: Optional[str] = Field(
        None,
        description="修复失败时的错误信息，说明失败原因。",
        example="修复后代码仍然存在语法错误"
    )

    class Config:
        json_schema_extra = {
            "example": {
                "success": True,
                "fixed_code": "def greet(name):\n    print(name)",
                "explanation": "NameError: 变量 'nme' 未定义，已修正为正确的变量名 'name'。",
                "execution_result": {
                    "stdout": "Hello, Alice\n",
                    "stderr": "",
                    "exit_code": 0,
                    "success": True
                },
                "attempts": 1,
                "diff": (
                    "--- original\n"
                    "+++ fixed\n"
                    "@@ -1,2 +1,2 @@\n"
                    " def greet(name):\n"
                    "-    print(nme)\n"
                    "+    print(name)"
                ),
                "debug_logs": [
                    "步骤1: 识别错误类型 - NameError",
                    "步骤2: 检索到10个相关解决方案",
                    "步骤3: 生成修复代码",
                    "步骤4: Docker验证通过"
                ]
            }
        }