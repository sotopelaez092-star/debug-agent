# src/agent/multi_agent/searcher_agent.py
"""
Searcher Agent - 知识检索专家

职责：
从Stack Overflow检索相关解决方案
"""
import logging
from typing import Dict, Any

from ..tools.rag_searcher import RAGSearcher
from .multi_agent_state import DebugState

logger = logging.getLogger(__name__)


def searcher_node(state: DebugState) -> Dict[str, Any]:
    """
    Searcher Agent节点
    
    Args:
        state: 当前的DebugState
        
    Returns:
        更新的state字段（rag_results）
    """
    logger.info("🔎 Searcher Agent开始工作...")
    
    try:
        # ========== 1. 获取错误信息 ==========
        error_info = state.get('error_info')
        if not error_info:
            raise ValueError("error_info不存在，需要先运行Analyzer Agent")
        
        error_type = error_info.get('error_type', '')
        error_message = error_info.get('error_message', '')
        
        # ========== 2. 构造检索query ==========
        query = f"{error_type}: {error_message}"
        logger.info(f"  检索query: {query}")
        
        # ========== 3. RAG检索 ==========
        logger.info("  步骤1: 调用RAGSearcher")
        rag_searcher = RAGSearcher()
        
        # 检索Top 10结果
        results = rag_searcher.search(query, top_k=10)
        
        logger.info(f"  ✅ 检索到{len(results)}个相关方案")
        
        # 打印前3个结果的相似度（调试用）
        for i, result in enumerate(results[:3], 1):
            similarity = result.get('similarity', 0)
            logger.info(f"  Result {i}: 相似度={similarity:.3f}")
        
        # ========== 4. 返回结果 ==========
        logger.info("✅ Searcher Agent完成工作")
        
        return {
            'rag_results': results
        }
        
    except Exception as e:
        logger.error(f"❌ Searcher Agent失败: {e}", exc_info=True)
        raise RuntimeError(f"Searcher Agent执行失败: {e}")