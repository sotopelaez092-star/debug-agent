# src/agent/multi_agent/debug_graph.py
"""
Multi-Agent Debug System - LangGraph实现

将Supervisor和4个Agent组装成完整的图
"""
import logging
from langgraph.graph import StateGraph, END

from .multi_agent_state import DebugState
from .supervisor_agent import supervisor_node
from .analyzer_agent import analyzer_node
from .searcher_agent import searcher_node
from .fixer_agent import fixer_node
from .tester_agent import tester_node

logger = logging.getLogger(__name__)


def create_debug_graph():
    """创建Multi-Agent Debug工作流图"""
    logger.info("🔧 构建Multi-Agent Debug Graph...")
    
    # 创建StateGraph
    workflow = StateGraph(DebugState)
    
    # ========== 添加节点 ==========
    logger.info("  添加节点...")
    workflow.add_node("supervisor", supervisor_node)
    workflow.add_node("analyzer", analyzer_node)
    workflow.add_node("searcher", searcher_node)
    workflow.add_node("fixer", fixer_node)
    workflow.add_node("tester", tester_node)
    
    # ========== 设置入口点 ==========
    workflow.set_entry_point("supervisor")
    
    # ========== 添加条件边 ==========
    logger.info("  添加条件边...")
    
    # ✅ 创建路由函数（从State中读取next_agent）
    def route_after_supervisor(state: DebugState) -> str:
        """
        根据Supervisor的决策路由到下一个节点
        
        Supervisor已经更新了state["next_agent"]，
        这个函数只是读取它并返回
        """
        next_agent = state.get("next_agent", "END")
        logger.info(f"  路由: supervisor → {next_agent}")
        return next_agent
    
    # Supervisor根据决策分派任务
    workflow.add_conditional_edges(
        "supervisor",
        route_after_supervisor,  # ✅ 使用路由函数
        {
            "analyzer": "analyzer",
            "searcher": "searcher",
            "fixer": "fixer",
            "tester": "tester",
            "END": END
        }
    )
    
    # ========== 添加普通边 ==========
    logger.info("  添加普通边...")
    # 所有worker agent完成后回到supervisor
    workflow.add_edge("analyzer", "supervisor")
    workflow.add_edge("searcher", "supervisor")
    workflow.add_edge("fixer", "supervisor")
    workflow.add_edge("tester", "supervisor")
    
    # ========== 编译图 ==========
    logger.info("  编译图...")
    compiled_graph = workflow.compile()
    
    logger.info("✅ Multi-Agent Debug Graph构建完成！")
    
    return compiled_graph


# ========== 便捷函数：直接运行debug ==========

def debug_code(
    buggy_code: str,
    error_traceback: str,
    project_path: str = None,
    run_name: str = None,      # ✅ 新增
    tags: list = None,         # ✅ 新增
    metadata: dict = None      # ✅ 新增
) -> dict:
    """
    执行完整的Debug流程
    """
    # ✅ 直接在这里构建workflow，不调用不存在的函数
    from langgraph.graph import StateGraph, END
    from .multi_agent_state import DebugState
    from .supervisor_agent import supervisor_node
    from .analyzer_agent import analyzer_node
    from .searcher_agent import searcher_node
    from .fixer_agent import fixer_node
    from .tester_agent import tester_node
    
    # 构建workflow
    workflow = StateGraph(DebugState)
    
    # 添加节点
    workflow.add_node("supervisor", supervisor_node)
    workflow.add_node("analyzer", analyzer_node)
    workflow.add_node("searcher", searcher_node)
    workflow.add_node("fixer", fixer_node)
    workflow.add_node("tester", tester_node)
    
    # 设置入口
    workflow.set_entry_point("supervisor")
    
    # 路由函数
    def route_after_supervisor(state: DebugState) -> str:
        return state.get("next_agent", "END")
    
    # 添加条件边
    workflow.add_conditional_edges(
        "supervisor",
        route_after_supervisor,
        {
            "analyzer": "analyzer",
            "searcher": "searcher",
            "fixer": "fixer",
            "tester": "tester",
            "END": END
        }
    )
    
    # 其他节点回到supervisor
    workflow.add_edge("analyzer", "supervisor")
    workflow.add_edge("searcher", "supervisor")
    workflow.add_edge("fixer", "supervisor")
    workflow.add_edge("tester", "supervisor")
    
    # 编译
    graph = workflow.compile()
    
    # 初始化State
    initial_state = {
        "original_code": buggy_code,
        "error_traceback": error_traceback,
        "project_path": project_path,
        "messages": [],
        "next_agent": None,
        "error_analysis": None,
        "context": None,
        "rag_results": [],
        "fixed_code": None,
        "explanation": None,
        "test_result": None,
        "error_message": None,
        "attempts": 0,
        "max_attempts": 3,
        "is_finished": False
    }
    
    # ✅ 构建LangSmith配置
    config = {}
    if run_name:
        config["run_name"] = run_name
    if tags:
        config["tags"] = tags
    if metadata:
        config["metadata"] = metadata
    
    # 执行Graph
    try:
        if config:
            final_state = graph.invoke(initial_state, config=config)
        else:
            final_state = graph.invoke(initial_state)
        
        return final_state
        
    except Exception as e:
        logger.error(f"Debug流程执行失败: {e}", exc_info=True)
        return {
            **initial_state,
            "is_finished": True,
            "error_message": f"系统错误: {str(e)}"
        }