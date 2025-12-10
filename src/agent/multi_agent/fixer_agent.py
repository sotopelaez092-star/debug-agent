# src/agent/multi_agent/fixer_agent.py
"""
Fixer Agent - 代码修复专家

职责：
生成修复代码
"""
import logging
from typing import Dict, Any

from ..tools.code_fixer import CodeFixer
from .multi_agent_state import DebugState

logger = logging.getLogger(__name__)


def fixer_node(state: DebugState) -> Dict[str, Any]:
    """
    Fixer Agent节点
    
    Args:
        state: 当前的DebugState
        
    Returns:
        更新的state字段（fixed_code, attempts）
    """
    logger.info("🔧 Fixer Agent开始工作...")
    
    try:
        # ========== 1. 获取必需的输入 ==========
        original_code = state.get('original_code')
        if not original_code:
            raise ValueError("original_code不存在")
        
        error_info = state.get('error_info')
        if not error_info:
            raise ValueError("error_info不存在，需要先运行Analyzer Agent")
        
        # ========== 2. 获取可选的输入 ==========
        context = state.get('context')  # 可能是None
        rag_results = state.get('rag_results')  # 可能是None
        attempts = state.get('attempts', 0)
        
        # ========== 3. 构造error_message ==========
        error_type = error_info.get('error_type', '')
        error_msg = error_info.get('error_message', '')
        error_message = f"{error_type}: {error_msg}"
        
        # ========== 4. 日志输出 ==========
        logger.info(f"  原始代码长度: {len(original_code)} 字符")
        logger.info(f"  错误信息: {error_message}")
        logger.info(f"  上下文: {'有' if context else '无'}")
        logger.info(f"  RAG方案: {len(rag_results) if rag_results else 0} 个")
        logger.info(f"  当前尝试: 第 {attempts + 1} 次")
        
        # ========== 5. 调用CodeFixer ==========
        logger.info("  步骤1: 调用CodeFixer生成修复")
        code_fixer = CodeFixer()
        
        result = code_fixer.fix_code(
            buggy_code=original_code,
            error_message=error_message,
            context=context,          # 可能是None
            rag_solutions=rag_results  # 可能是None
        )
        
        fixed_code = result.get('fixed_code', '')
        explanation = result.get('explanation', '')
        
        logger.info(f"  ✅ 修复代码生成完成")
        logger.info(f"  修复说明: {explanation[:100]}...")  # 只打印前100字符
        
        # ========== 6. 返回结果 ==========
        logger.info("✅ Fixer Agent完成工作")
        
        return {
            'fixed_code': fixed_code,
            'attempts': attempts + 1  # 增加尝试次数
        }
        
    except Exception as e:
        logger.error(f"❌ Fixer Agent失败: {e}", exc_info=True)
        raise RuntimeError(f"Fixer Agent执行失败: {e}")