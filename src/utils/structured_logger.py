"""结构化日志系统 - 提供可追踪、可分析的调试日志"""
import json
import logging
import time
from datetime import datetime
from pathlib import Path
from typing import Optional, Dict, Any, List
from dataclasses import dataclass, asdict, field
from enum import Enum


class DebugPhase(Enum):
    """调试阶段"""
    INIT = "init"
    ERROR_PARSE = "error_parse"
    SCOPE_DETECT = "scope_detect"
    INVESTIGATION = "investigation"
    RAG_SEARCH = "rag_search"
    CODE_FIX = "code_fix"
    VERIFICATION = "verification"
    COMPLETE = "complete"


class FixMethod(Enum):
    """修复方法"""
    PATTERN_MATCH = "pattern_match"  # 模式匹配快速修复
    CACHE_HIT = "cache_hit"          # 缓存命中
    LLM_CALL = "llm_call"            # LLM 调用
    TRACEBACK_FAST = "traceback_fast"  # Traceback 快速路径


@dataclass
class PhaseLog:
    """阶段日志"""
    phase: str
    start_time: float
    end_time: float = 0
    duration_ms: float = 0
    success: bool = True
    details: Dict[str, Any] = field(default_factory=dict)

    def complete(self, success: bool = True, **details):
        """完成阶段"""
        self.end_time = time.time()
        self.duration_ms = (self.end_time - self.start_time) * 1000
        self.success = success
        self.details.update(details)


@dataclass
class DebugSession:
    """调试会话日志"""
    session_id: str
    start_time: float
    error_type: str = ""
    error_message: str = ""
    error_file: str = ""
    is_cross_file: bool = False
    fix_method: str = ""
    phases: List[PhaseLog] = field(default_factory=list)
    attempts: int = 0
    success: bool = False
    end_time: float = 0
    total_duration_ms: float = 0

    def to_dict(self) -> dict:
        """转换为字典"""
        return {
            "session_id": self.session_id,
            "start_time": datetime.fromtimestamp(self.start_time).isoformat(),
            "end_time": datetime.fromtimestamp(self.end_time).isoformat() if self.end_time else None,
            "total_duration_ms": self.total_duration_ms,
            "error_type": self.error_type,
            "error_message": self.error_message[:200],  # 截断
            "error_file": self.error_file,
            "is_cross_file": self.is_cross_file,
            "fix_method": self.fix_method,
            "attempts": self.attempts,
            "success": self.success,
            "phases": [asdict(p) for p in self.phases]
        }


class StructuredLogger:
    """
    结构化日志记录器

    提供：
    1. 阶段计时
    2. 会话追踪
    3. 性能分析
    4. JSON 日志输出
    """

    def __init__(self, log_dir: Optional[Path] = None, enable_file_log: bool = True):
        """
        初始化日志记录器

        Args:
            log_dir: 日志目录
            enable_file_log: 是否启用文件日志
        """
        self.log_dir = log_dir or Path(".debug_agent_cache/logs")
        self.enable_file_log = enable_file_log

        if enable_file_log:
            self.log_dir.mkdir(parents=True, exist_ok=True)

        # 当前会话
        self._current_session: Optional[DebugSession] = None
        self._current_phase: Optional[PhaseLog] = None

        # 标准 logger
        self.logger = logging.getLogger("debug_agent.structured")

    def start_session(self, session_id: Optional[str] = None) -> DebugSession:
        """开始新的调试会话"""
        if session_id is None:
            session_id = f"debug_{int(time.time() * 1000)}"

        self._current_session = DebugSession(
            session_id=session_id,
            start_time=time.time()
        )

        self.logger.info(f"[{session_id}] 调试会话开始")
        return self._current_session

    def end_session(self, success: bool = False) -> Optional[DebugSession]:
        """结束调试会话"""
        if not self._current_session:
            return None

        session = self._current_session
        session.end_time = time.time()
        session.total_duration_ms = (session.end_time - session.start_time) * 1000
        session.success = success

        # 写入文件日志
        if self.enable_file_log:
            self._write_session_log(session)

        # 输出摘要
        self.logger.info(
            f"[{session.session_id}] 调试会话结束 | "
            f"{'成功' if success else '失败'} | "
            f"耗时: {session.total_duration_ms:.0f}ms | "
            f"尝试: {session.attempts}次 | "
            f"方法: {session.fix_method}"
        )

        self._current_session = None
        return session

    def start_phase(self, phase: DebugPhase, **details) -> PhaseLog:
        """开始新阶段"""
        # 结束之前的阶段
        if self._current_phase and self._current_phase.end_time == 0:
            self._current_phase.complete()

        phase_log = PhaseLog(
            phase=phase.value,
            start_time=time.time(),
            details=details
        )

        if self._current_session:
            self._current_session.phases.append(phase_log)

        self._current_phase = phase_log
        self.logger.debug(f"阶段开始: {phase.value}")
        return phase_log

    def end_phase(self, success: bool = True, **details):
        """结束当前阶段"""
        if self._current_phase:
            self._current_phase.complete(success, **details)
            self.logger.debug(
                f"阶段结束: {self._current_phase.phase} | "
                f"耗时: {self._current_phase.duration_ms:.1f}ms | "
                f"{'成功' if success else '失败'}"
            )
            self._current_phase = None

    def set_error_info(self, error_type: str, error_message: str, error_file: str = ""):
        """设置错误信息"""
        if self._current_session:
            self._current_session.error_type = error_type
            self._current_session.error_message = error_message
            self._current_session.error_file = error_file

    def set_cross_file(self, is_cross_file: bool):
        """设置是否跨文件"""
        if self._current_session:
            self._current_session.is_cross_file = is_cross_file

    def set_fix_method(self, method: FixMethod):
        """设置修复方法"""
        if self._current_session:
            self._current_session.fix_method = method.value

    def increment_attempt(self):
        """增加尝试次数"""
        if self._current_session:
            self._current_session.attempts += 1

    def log_event(self, event: str, **data):
        """记录事件"""
        if self._current_session:
            self.logger.info(f"[{self._current_session.session_id}] {event}")
        else:
            self.logger.info(event)

        if data:
            self.logger.debug(f"  详情: {json.dumps(data, ensure_ascii=False, default=str)}")

    def _write_session_log(self, session: DebugSession):
        """写入会话日志到文件"""
        try:
            log_file = self.log_dir / f"{session.session_id}.json"
            log_file.write_text(
                json.dumps(session.to_dict(), ensure_ascii=False, indent=2),
                encoding='utf-8'
            )
        except Exception as e:
            self.logger.warning(f"写入日志失败: {e}")

    def get_session_stats(self, last_n: int = 100) -> Dict[str, Any]:
        """获取最近 N 个会话的统计"""
        if not self.log_dir.exists():
            return {"total": 0}

        sessions = []
        for log_file in sorted(self.log_dir.glob("debug_*.json"))[-last_n:]:
            try:
                data = json.loads(log_file.read_text(encoding='utf-8'))
                sessions.append(data)
            except:
                continue

        if not sessions:
            return {"total": 0}

        # 计算统计
        success_count = sum(1 for s in sessions if s.get("success"))
        total_time = sum(s.get("total_duration_ms", 0) for s in sessions)

        # 按修复方法分类
        by_method = {}
        for s in sessions:
            method = s.get("fix_method", "unknown")
            if method not in by_method:
                by_method[method] = {"count": 0, "success": 0, "total_time_ms": 0}
            by_method[method]["count"] += 1
            if s.get("success"):
                by_method[method]["success"] += 1
            by_method[method]["total_time_ms"] += s.get("total_duration_ms", 0)

        # 按错误类型分类
        by_error = {}
        for s in sessions:
            err_type = s.get("error_type", "unknown")
            if err_type not in by_error:
                by_error[err_type] = {"count": 0, "success": 0}
            by_error[err_type]["count"] += 1
            if s.get("success"):
                by_error[err_type]["success"] += 1

        return {
            "total": len(sessions),
            "success_count": success_count,
            "success_rate": success_count / len(sessions) if sessions else 0,
            "avg_duration_ms": total_time / len(sessions) if sessions else 0,
            "by_fix_method": by_method,
            "by_error_type": by_error
        }


# 全局实例
_logger_instance: Optional[StructuredLogger] = None


def get_structured_logger() -> StructuredLogger:
    """获取全局日志实例"""
    global _logger_instance
    if _logger_instance is None:
        _logger_instance = StructuredLogger()
    return _logger_instance
