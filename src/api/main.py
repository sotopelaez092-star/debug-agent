"""
FastAPI 入口

提供：
- /health 健康检查
- /api/v1/debug 调试端点
"""

import logging
from typing import List, Dict, Any

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware

from src.api.models import DebugRequest, DebugResponse
from src.agent.debug_agent import DebugAgent

import difflib


# 配置基础日志
logging.basicConfig(
    level=logging.INFO,
    format="[%(asctime)s] [%(levelname)s] %(name)s - %(message)s",
)
logger = logging.getLogger(__name__)


# 1. 创建 FastAPI 实例
app = FastAPI(
    title="AI Debug Assistant API",
    description="提供 AI 调试助手服务，包括错误识别、代码修复和执行结果分析。",
    version="1.0.0"
)

# 2. 配置 CORS（允许跨域）
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # 生产环境建议改为具体域名
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 3. 初始化 DebugAgent（全局单例）
debug_agent: DebugAgent | None = None


@app.on_event("startup")
async def startup_event() -> None:
    """应用启动时初始化 Agent"""
    global debug_agent
    debug_agent = DebugAgent()
    logger.info("DebugAgent 已初始化")


# 4. 健康检查端点
@app.get("/health")
async def health_check() -> Dict[str, Any]:
    """健康检查端点"""
    return {
        "status": "healthy",
        "service": "debug_assistant",
        "version": "1.0.0"
    }


# 5. Debug 端点
@app.post("/api/v1/debug", response_model=DebugResponse)
async def debug_code(request: DebugRequest) -> DebugResponse:
    """Debug 代码端点"""

    if debug_agent is None:
        logger.error("DebugAgent 尚未初始化")
        raise HTTPException(status_code=503, detail="DebugAgent 未就绪")

    try:
        # 1. 调用 DebugAgent
        result = debug_agent.debug(
            buggy_code=request.buggy_code,
            error_traceback=request.error_traceback,
            max_retries=request.max_retries,
        )

        # 2. 生成 diff（只有在有 fixed_code 时生成）
        diff: str | None = None
        if result.get("success") and result.get("fixed_code"):
            diff = generate_diff(request.buggy_code, result["fixed_code"])

        # 3. 生成 debug_logs
        debug_logs = extract_debug_logs(result.get("all_attempts", []))

        # 4. 映射到 DebugResponse
        return DebugResponse(
            success=result["success"],
            fixed_code=result.get("fixed_code"),
            explanation=result.get("explanation"),
            execution_result=result.get("execution_result"),
            attempts=len(result.get("all_attempts", [])),
            diff=diff,
            debug_logs=debug_logs,
            error_message=result.get("error_message"),
        )

    except HTTPException:
        raise
    except Exception as e:
        # 异常处理
        logger.exception("Debug 过程中出现未处理异常")
        raise HTTPException(status_code=500, detail=str(e))


# =============================
# 工具函数
# =============================

def generate_diff(original: str, fixed: str) -> str:
    """生成 unified diff 字符串"""
    diff = difflib.unified_diff(
        original.splitlines(keepends=True),
        fixed.splitlines(keepends=True),
        fromfile="original",
        tofile="fixed",
        lineterm=""
    )
    return "".join(diff)


def extract_debug_logs(all_attempts: List[dict]) -> List[str]:
    """从 all_attempts 中提取关键日志文本"""
    logs: List[str] = []
    for attempt in all_attempts:
        # 尽量从结构化字段取信息，否则直接 str()
        msg = attempt.get("explanation") or attempt.get("message") or str(attempt)
        logs.append(msg)
    return logs
