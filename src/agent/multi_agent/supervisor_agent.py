# src/agent/multi_agent/supervisor_agent.py
"""
Supervisor Agent - 协调Multi-Agent工作流
"""
from typing import Dict, Any
import logging

from .multi_agent_state import DebugState

logger = logging.getLogger(__name__)


def supervisor_node(state: DebugState) -> Dict[str, Any]:
    """
    Supervisor节点：决定下一步调用哪个Agent
    
    决策规则：
    1. 如果还没分析错误 → analyzer
    2. 如果已分析但还没修复
       - 需要RAG且还没检索 → searcher
       - 否则 → fixer
    3. 如果已修复但还没测试 → tester
    4. 如果已测试
       - 成功 → END
       - 失败且attempts<3 → 重试fixer
       - 失败且attempts>=3 → END
    
    Returns:
        Dict: 包含next_agent和is_finished字段
    """
    logger.info("👔 Supervisor开始决策...")
    
    error_info = state.get("error_info")
    fixed_code = state.get("fixed_code")
    test_result = state.get("test_result")
    attempts = state.get("attempts", 0)
    
    # 规则1: 还没分析错误
    if error_info is None:
        logger.info("  决策: 还没分析错误 → analyzer")
        return {
            "next_agent": "analyzer",
            "is_finished": False
        }
    
    # 规则2: 已分析但还没修复
    if fixed_code is None:
        # 判断是否需要RAG检索
        if _need_rag_search(error_info) and state.get("rag_results") is None:
            logger.info("  决策: 需要RAG检索 → searcher")
            return {
                "next_agent": "searcher",
                "is_finished": False
            }
        else:
            logger.info("  决策: 开始修复代码 → fixer")
            return {
                "next_agent": "fixer",
                "is_finished": False
            }
    
    # 规则3: 已修复但还没测试
    if test_result is None:
        logger.info("  决策: 验证修复 → tester")
        return {
            "next_agent": "tester",
            "is_finished": False
        }
    
    # 规则4: 已测试，判断成功/失败
    if test_result.get("success"):
        logger.info("  决策: 修复成功！ → END")
        return {
            "next_agent": "END",
            "is_finished": True
        }
    else:
        # 失败，判断是否重试
        if attempts < 3:
            logger.info(f"  决策: 修复失败，重试第{attempts + 1}次 → fixer")
            # 清空之前的修复结果，让fixer重新生成
            return {
                "next_agent": "fixer",
                "is_finished": False,
                "fixed_code": None,  # ⭐ 清空之前的修复
                "test_result": None  # ⭐ 清空之前的测试结果
            }
        else:
            logger.info("  决策: 修复失败且已达最大重试次数 → END")
            return {
                "next_agent": "END",
                "is_finished": True
            }


def _need_rag_search(error_info: Dict[str, Any]) -> bool:
    """
    判断是否需要RAG检索
    
    简单规则：
    - 语法错误：不需要（直接修改语法即可）
    - NameError但有import建议：不需要（直接添加import）
    - 其他错误：需要（查找Stack Overflow方案）
    """
    error_type = error_info.get("error_type", "")
    
    # 不需要RAG的情况
    if error_type in ["SyntaxError", "IndentationError"]:
        return False
    
    # NameError但有import建议，不需要RAG
    if error_type == "NameError":
        context = error_info.get("context")
        if context and context.get("import_suggestions"):
            return False
    
    # 其他情况都需要RAG
    return True