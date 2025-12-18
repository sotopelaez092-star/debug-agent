"""调查报告数据模型"""
from pydantic import BaseModel, Field, field_validator
from typing import List


class RelevantLocation(BaseModel):
    """相关代码位置"""
    file_path: str = Field(..., description="文件路径")
    line: int = Field(..., description="行号")
    symbol: str = Field(..., description="符号名称")
    reasoning: str = Field(..., description="选择此位置的原因")
    code_snippet: str = Field(default="", description="代码片段")

    class Config:
        json_schema_extra = {
            "example": {
                "file_path": "utils/helpers.py",
                "line": 42,
                "symbol": "calculate_total",
                "reasoning": "函数定义位置，可能是拼写错误",
                "code_snippet": "def calculate_total(items):\n    return sum(items)"
            }
        }


class InvestigationReport(BaseModel):
    """代码库调查报告"""
    summary: str = Field(..., min_length=10, description="调查总结")
    relevant_locations: List[RelevantLocation] = Field(..., description="相关代码位置列表")
    root_cause: str = Field(..., description="根本原因分析")
    suggested_fix: str = Field(..., description="建议的修复方案")
    confidence: float = Field(..., ge=0, le=1, description="置信度 (0-1)")
    exploration_trace: List[str] = Field(default_factory=list, description="探索轨迹")

    @field_validator('relevant_locations')
    @classmethod
    def at_least_one_location(cls, v):
        if not v:
            raise ValueError('must have at least one relevant location')
        return v

    class Config:
        json_schema_extra = {
            "example": {
                "summary": "发现 'nane' 是 'name' 的拼写错误，在 utils.py:15 定义",
                "relevant_locations": [
                    {
                        "file_path": "utils.py",
                        "line": 15,
                        "symbol": "name",
                        "reasoning": "符号匹配，编辑距离为 1",
                        "code_snippet": "name = 'John'"
                    }
                ],
                "root_cause": "变量名拼写错误：'nane' 应为 'name'",
                "suggested_fix": "将 'nane' 修改为 'name'",
                "confidence": 0.95,
                "exploration_trace": [
                    "[Turn 1] search_symbol({'name': 'nane', 'fuzzy': True})",
                    "[Turn 2] read_file({'path': 'utils.py', 'start_line': 10, 'end_line': 20})"
                ]
            }
        }
