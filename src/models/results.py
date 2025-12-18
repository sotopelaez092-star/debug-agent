"""各种结果类型定义"""
from pydantic import BaseModel, Field
from typing import Optional, Dict, List
from dataclasses import dataclass


class SearchResult(BaseModel):
    """快速路径搜索结果"""
    symbol: str = Field(..., description="符号名称")
    file: str = Field(default="", description="文件路径")
    line: int = Field(default=0, description="行号")
    confidence: float = Field(..., ge=0, le=1, description="置信度")
    suggestion: str = Field(..., description="修复建议")


class FixResult(BaseModel):
    """代码修复结果"""
    success: bool = Field(..., description="是否成功")
    fixed_code: str = Field(default="", description="修复后的代码")
    explanation: str = Field(default="", description="修复说明")
    changes: List[str] = Field(default_factory=list, description="变更列表")
    related_files: Dict[str, str] = Field(default_factory=dict, description="相关文件内容")
    cached: bool = Field(default=False, description="是否来自缓存")
    cache_strategy: Optional[str] = Field(default=None, description="缓存的修复策略")
    used_pattern_fixer: bool = Field(default=False, description="是否使用了 PatternFixer")
    target_file: Optional[str] = Field(default=None, description="修复的目标文件（用于验证）")


class ExecutionResult(BaseModel):
    """代码执行结果"""
    success: bool = Field(..., description="是否执行成功")
    stdout: str = Field(default="", description="标准输出")
    stderr: str = Field(default="", description="标准错误")
    exit_code: int = Field(default=0, description="退出码")
    timeout: bool = Field(default=False, description="是否超时")


class DebugResult(BaseModel):
    """最终调试结果"""
    success: bool = Field(..., description="是否调试成功")
    original_error: Optional[Dict] = Field(default=None, description="原始错误信息")
    fixed_code: str = Field(default="", description="修复后的代码")
    explanation: str = Field(default="", description="修复说明")
    attempts: int = Field(default=0, description="尝试次数")
    investigation_summary: str = Field(default="", description="调查总结")
    solutions: List[Dict] = Field(default_factory=list, description="RAG 检索到的解决方案")
    related_files: Dict[str, str] = Field(default_factory=dict, description="相关文件（跨文件修复）")


@dataclass
class SymbolMatch:
    """符号匹配结果"""
    name: str
    file: str
    line: int
    symbol_type: str  # function, class, variable
    confidence: float = 1.0

    def to_dict(self) -> dict:
        return {
            "name": self.name,
            "file": self.file,
            "line": self.line,
            "symbol_type": self.symbol_type,
            "confidence": self.confidence
        }
