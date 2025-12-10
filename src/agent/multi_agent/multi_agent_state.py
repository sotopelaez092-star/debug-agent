# src/agent/multi_agent_state.py
"""
Multi-Agent系统的State定义
"""
from typing import TypedDict, Optional  # ✅ 正确

class DebugState(TypedDict):
    """
    Debug流程的共享状态

    所有Agent通过这个State传递数据
    """
    # ========== 输入 ==========
    original_code: str          # 原始buggy代码
    error_traceback: str        # 完整的错误traceback
    project_path: Optional[str] # 项目路径（如果是单文件可以为None）
    
    # ========== Agent工作结果 ==========
    error_info: Optional[dict]       # ErrorIdentifier的分析结果
    context: Optional[dict]          # ContextManager提取的上下文
    rag_results: Optional[list]      # RAGSearcher的检索结果
    fixed_code: Optional[str]        # CodeFixer生成的修复代码
    test_result: Optional[dict]      # DockerExecutor的测试结果
    
    # ========== 流程控制 ==========
    attempts: int                    # 当前重试次数
    next_agent: Optional[str]        # Supervisor决定的下一个agent
    is_finished: bool                # 是否完成（成功或失败）