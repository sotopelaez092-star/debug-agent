# src/agent/multi_agent/tester_agent.py
"""
Tester Agent - 测试验证专家

职责：
在Docker沙箱中测试修复代码
"""
import logging
from typing import Dict, Any

from ..tools.docker_executor import DockerExecutor
from .multi_agent_state import DebugState

logger = logging.getLogger(__name__)


def tester_node(state: DebugState) -> Dict[str, Any]:
    """
    Tester Agent节点
    
    Args:
        state: 当前的DebugState
        
    Returns:
        更新的state字段（test_result）
    """
    logger.info("🧪 Tester Agent开始工作...")
    
    try:
        # ========== 1. 获取修复后的代码 ==========
        fixed_code = state.get('fixed_code')
        if not fixed_code:
            raise ValueError("fixed_code不存在，需要先运行Fixer Agent")
        
        attempts = state.get('attempts', 0)
        
        # ========== 2. 日志输出 ==========
        logger.info(f"  修复代码长度: {len(fixed_code)} 字符")
        logger.info(f"  当前尝试: 第 {attempts} 次")
        
        # ========== 3. Docker测试 ==========
        logger.info("  步骤1: 在Docker沙箱中执行代码")
        docker_executor = DockerExecutor()
        
        test_result = docker_executor.execute(
            code=fixed_code,
        )
        
        # ========== 4. 分析结果 ==========
        success = test_result.get('success', False)
        
        if success:
            logger.info("  ✅ 测试成功！代码执行正常")
            stdout = test_result.get('stdout', '')
            if stdout:
                logger.info(f"  输出: {stdout[:200]}")  # 只打印前200字符
        else:
            logger.warning("  ❌ 测试失败！代码执行出错")
            stderr = test_result.get('stderr', '')
            if stderr:
                logger.warning(f"  错误: {stderr[:200]}")  # 只打印前200字符
        
        # ========== 5. 返回结果 ==========
        logger.info("✅ Tester Agent完成工作")
        
        return {
            'test_result': test_result
        }
        
    except Exception as e:
        logger.error(f"❌ Tester Agent失败: {e}", exc_info=True)
        raise RuntimeError(f"Tester Agent执行失败: {e}")