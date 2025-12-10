# src/agent/multi_agent/analyzer_agent.py
"""
Analyzer Agent - 错误分析专家

职责：
1. 识别错误类型和位置
2. 提取跨文件上下文
"""
import logging
from typing import Dict, Any

from ..context_manager import ContextManager
from ..tools.error_identifier import ErrorIdentifier
from .multi_agent_state import DebugState

logger = logging.getLogger(__name__)


def analyzer_node(state: DebugState) -> Dict[str, Any]:
    """
    Analyzer Agent节点
    
    Args:
        state: 当前的DebugState
        
    Returns:
        更新的state字段（error_info和context）
    """
    logger.info("🔍 Analyzer Agent开始工作...")
    
    try:
        # ========== 1. 错误识别 ==========
        logger.info("  步骤1: 识别错误类型")
        error_identifier = ErrorIdentifier()
        error_info = error_identifier.identify(state['error_traceback'])
        
        logger.info(f"  ✅ 错误类型: {error_info.get('error_type')}")
        logger.info(f"  ✅ 错误位置: {error_info.get('file')}:{error_info.get('line')}")
        
        # ========== 2. 上下文提取 ==========
        context = None
        project_path = state.get('project_path')
        
        if project_path:
            logger.info("  步骤2: 提取跨文件上下文")
            context_manager = ContextManager(project_path)
            
            # 提取上下文
            context = context_manager.get_context_for_error(
                error_file=error_info.get('file', ''),
                error_line=error_info.get('line', 0),
                undefined_name=error_info.get('undefined_name')  # 对于NameError
            )
            
            logger.info(f"  ✅ 上下文提取完成")
            if context.get('import_suggestions'):
                logger.info(f"  ✅ Import建议: {context['import_suggestions']}")
        else:
            logger.info("  ⏭️  跳过上下文提取（单文件场景）")
        
        # ========== 3. 返回结果 ==========
        logger.info("✅ Analyzer Agent完成工作")
        
        return {
            'error_info': error_info,
            'context': context
        }
        
    except Exception as e:
        logger.error(f"❌ Analyzer Agent失败: {e}", exc_info=True)
        raise RuntimeError(f"Analyzer Agent执行失败: {e}")