"""LoopDetector - 检测循环修复，避免无限重试"""
import hashlib
import logging
from typing import List, Dict, Optional, Set
from dataclasses import dataclass, field
from enum import Enum

logger = logging.getLogger(__name__)


class LoopAction(Enum):
    """循环检测后的建议动作"""
    CONTINUE = "continue"           # 继续当前修复流程
    ESCALATE = "escalate"          # 升级到更高层级
    SWITCH_STRATEGY = "switch"     # 切换修复策略
    ABORT = "abort"                # 放弃修复，交给人工


@dataclass
class LoopCheckResult:
    """循环检测结果"""
    action: LoopAction
    reason: str
    suggestion: str = ""
    escalate_to_layer: Optional[int] = None


@dataclass
class FixAttempt:
    """修复尝试记录"""
    code_hash: str
    error_hash: str
    error_type: str
    error_message: str
    layer: int
    success: bool
    timestamp: float = field(default_factory=lambda: __import__('time').time())


class LoopDetector:
    """
    循环检测器 - 识别重复失败模式，防止无限重试

    检测条件:
    1. 相同修复代码出现 2 次 -> 切换策略
    2. 相同错误出现 3 次 -> 升级到更高层级
    3. 总尝试次数 > 8 次 -> 人工接管
    """

    # 阈值配置
    SAME_FIX_THRESHOLD = 2       # 相同修复代码出现次数阈值
    SAME_ERROR_THRESHOLD = 3     # 相同错误出现次数阈值
    MAX_TOTAL_ATTEMPTS = 8       # 最大总尝试次数

    def __init__(self):
        self.attempts: List[FixAttempt] = []
        self.fix_hashes: Dict[str, int] = {}    # code_hash -> count
        self.error_hashes: Dict[str, int] = {}  # error_hash -> count
        self.current_layer = 1  # 当前所在层级

    def record_attempt(
        self,
        fixed_code: str,
        error_type: str,
        error_message: str,
        layer: int,
        success: bool
    ):
        """记录一次修复尝试"""
        code_hash = self._hash_content(fixed_code)
        error_hash = self._hash_content(f"{error_type}:{error_message[:200]}")

        attempt = FixAttempt(
            code_hash=code_hash,
            error_hash=error_hash,
            error_type=error_type,
            error_message=error_message[:500],
            layer=layer,
            success=success
        )
        self.attempts.append(attempt)

        if not success:
            # 更新计数
            self.fix_hashes[code_hash] = self.fix_hashes.get(code_hash, 0) + 1
            self.error_hashes[error_hash] = self.error_hashes.get(error_hash, 0) + 1

            logger.debug(
                f"记录失败尝试: layer={layer}, "
                f"fix_count={self.fix_hashes[code_hash]}, "
                f"error_count={self.error_hashes[error_hash]}, "
                f"total={len(self.attempts)}"
            )

        self.current_layer = layer

    def check_loop(self, proposed_fix: str = "") -> LoopCheckResult:
        """
        检查是否陷入循环

        Args:
            proposed_fix: 即将应用的修复代码（可选，用于预检）

        Returns:
            LoopCheckResult 包含建议动作
        """
        total_attempts = len(self.attempts)

        # 检查 1: 总尝试次数过多
        if total_attempts >= self.MAX_TOTAL_ATTEMPTS:
            return LoopCheckResult(
                action=LoopAction.ABORT,
                reason=f"已尝试 {total_attempts} 次，超过最大尝试次数 {self.MAX_TOTAL_ATTEMPTS}",
                suggestion="建议人工检查代码结构，可能存在深层次问题"
            )

        # 检查 2: 预检即将应用的修复是否已经失败过
        if proposed_fix:
            fix_hash = self._hash_content(proposed_fix)
            if self.fix_hashes.get(fix_hash, 0) >= self.SAME_FIX_THRESHOLD:
                return LoopCheckResult(
                    action=LoopAction.SWITCH_STRATEGY,
                    reason=f"相同修复代码已尝试 {self.fix_hashes[fix_hash]} 次",
                    suggestion="切换到不同的修复策略"
                )

        # 检查 3: 相同错误重复出现
        for error_hash, count in self.error_hashes.items():
            if count >= self.SAME_ERROR_THRESHOLD:
                return LoopCheckResult(
                    action=LoopAction.ESCALATE,
                    reason=f"相同错误已出现 {count} 次",
                    suggestion="升级到更深入的调查层级",
                    escalate_to_layer=min(self.current_layer + 1, 5)
                )

        # 检查 4: 相同修复代码重复
        for fix_hash, count in self.fix_hashes.items():
            if count >= self.SAME_FIX_THRESHOLD:
                return LoopCheckResult(
                    action=LoopAction.SWITCH_STRATEGY,
                    reason=f"相同修复代码已尝试 {count} 次",
                    suggestion="当前策略无效，尝试其他方法"
                )

        # 正常继续
        return LoopCheckResult(
            action=LoopAction.CONTINUE,
            reason="未检测到循环模式",
            suggestion=""
        )

    def should_escalate(self) -> Optional[int]:
        """检查是否应该升级到更高层级"""
        result = self.check_loop()
        if result.action == LoopAction.ESCALATE:
            return result.escalate_to_layer
        return None

    def is_fix_attempted(self, fix_code: str) -> bool:
        """检查某个修复是否已经尝试过"""
        fix_hash = self._hash_content(fix_code)
        return fix_hash in self.fix_hashes

    def get_attempt_count(self) -> int:
        """获取总尝试次数"""
        return len(self.attempts)

    def get_failed_attempts(self) -> int:
        """获取失败尝试次数"""
        return sum(1 for a in self.attempts if not a.success)

    def get_unique_errors(self) -> Set[str]:
        """获取遇到的不同错误类型"""
        return {a.error_type for a in self.attempts if not a.success}

    def get_summary(self) -> Dict:
        """获取检测摘要"""
        return {
            "total_attempts": len(self.attempts),
            "successful": sum(1 for a in self.attempts if a.success),
            "failed": sum(1 for a in self.attempts if not a.success),
            "unique_fixes": len(self.fix_hashes),
            "unique_errors": len(self.error_hashes),
            "current_layer": self.current_layer,
            "loop_status": self.check_loop().action.value
        }

    def reset(self):
        """重置检测器状态（新调试会话）"""
        self.attempts.clear()
        self.fix_hashes.clear()
        self.error_hashes.clear()
        self.current_layer = 1

    def _hash_content(self, content: str) -> str:
        """生成内容哈希（标准化后）"""
        # 标准化：移除多余空白
        normalized = ' '.join(content.split())
        return hashlib.md5(normalized.encode()).hexdigest()[:16]
