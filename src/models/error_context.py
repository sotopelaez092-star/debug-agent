"""错误上下文数据模型"""
from pydantic import BaseModel, Field
from typing import Optional


class ErrorContext(BaseModel):
    """错误上下文信息"""
    error_type: str = Field(..., description="错误类型，如 NameError, ImportError 等")
    error_message: str = Field(..., description="完整错误信息")
    error_file: str = Field(default="", description="出错文件路径")
    error_line: int = Field(default=0, description="出错行号")
    traceback: str = Field(default="", description="完整堆栈跟踪")

    class Config:
        json_schema_extra = {
            "example": {
                "error_type": "NameError",
                "error_message": "name 'nane' is not defined",
                "error_file": "main.py",
                "error_line": 10,
                "traceback": "Traceback (most recent call last):\n  File \"main.py\", line 10, in <module>\n    print(nane)\nNameError: name 'nane' is not defined"
            }
        }
