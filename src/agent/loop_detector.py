"""
LoopDetector - 循环检测器

检测 Debug Agent 是否陷入重复修复的循环，避免无限重试
"""

import hashlib
import logging
from typing import Dict, List, Optional, Any
from collections import defaultdict

logger = logging.getLogger(__name__)


class LoopDetector:
    """
    循环检测器

    功能：
    1. 检测重复的修复代码（相同的fix被生成多次）
    2. 检测重复的错误（相同的错误反复出现）
    3. 检测无效的修复尝试模式
    4. 提供跳出循环的建议

    Attributes:
        max_similar_code: 允许相似代码的最大次数
        max_same_error: 允许相同错误的最大次数
        attempt_history: 尝试历史记录
    """

    def __init__(
        self,
        max_similar_code: int = 2,
        max_same_error: int = 3,
        similarity_threshold: float = 0.9
    ):
        """
        初始化循环检测器

        Args:
            max_similar_code: 允许生成相似代码的最大次数
            max_same_error: 允许出现相同错误的最大次数
            similarity_threshold: 代码相似度阈值（0-1）
        """
        self.max_similar_code = max_similar_code
        self.max_same_error = max_same_error
        self.similarity_threshold = similarity_threshold

        # 历史记录
        self.attempt_history: List[Dict[str, Any]] = []
        self.code_hashes: List[str] = []
        self.error_hashes: List[str] = []

        # 统计信息
        self.stats = {
            'total_attempts': 0,
            'code_loops_detected': 0,
            'error_loops_detected': 0,
        }

        logger.info(f"LoopDetector初始化: max_similar_code={max_similar_code}, "
                   f"max_same_error={max_same_error}")

    def _hash_code(self, code: str) -> str:
        """
        计算代码的hash值（忽略空白差异）

        Args:
            code: 代码字符串

        Returns:
            hash值
        """
        # 标准化代码：移除空行，统一空白
        normalized = '\n'.join(
            line.strip() for line in code.split('\n')
            if line.strip()
        )
        return hashlib.md5(normalized.encode()).hexdigest()

    def _hash_error(self, error: str) -> str:
        """
        计算错误的hash值

        Args:
            error: 错误信息

        Returns:
            hash值
        """
        # 只取错误类型和核心消息，忽略行号等变化的部分
        # 例如: "NameError: name 'x' is not defined" -> hash
        normalized = error.strip().lower()
        return hashlib.md5(normalized.encode()).hexdigest()

    def _calculate_similarity(self, code1: str, code2: str) -> float:
        """
        计算两段代码的相似度

        Args:
            code1: 第一段代码
            code2: 第二段代码

        Returns:
            相似度（0-1）
        """
        # 简单的基于行的相似度计算
        lines1 = set(line.strip() for line in code1.split('\n') if line.strip())
        lines2 = set(line.strip() for line in code2.split('\n') if line.strip())

        if not lines1 and not lines2:
            return 1.0
        if not lines1 or not lines2:
            return 0.0

        intersection = lines1 & lines2
        union = lines1 | lines2

        return len(intersection) / len(union)

    def check(self, attempt: Dict[str, Any]) -> Dict[str, Any]:
        """
        检查当前尝试是否构成循环

        Args:
            attempt: 尝试信息，包含：
                - fixed_code: 修复后的代码
                - error: 执行后的错误（如果有）
                - explanation: 修复说明

        Returns:
            检查结果：
                - is_loop: 是否检测到循环
                - loop_type: 循环类型（'code', 'error', None）
                - message: 描述信息
                - suggestion: 建议
        """
        self.stats['total_attempts'] += 1

        result = {
            'is_loop': False,
            'loop_type': None,
            'message': '',
            'suggestion': '',
        }

        fixed_code = attempt.get('fixed_code', '')
        error = attempt.get('error', '')

        # 1. 检查代码重复
        if fixed_code:
            code_hash = self._hash_code(fixed_code)

            # 检查完全相同的代码
            same_code_count = self.code_hashes.count(code_hash)
            if same_code_count >= self.max_similar_code:
                self.stats['code_loops_detected'] += 1
                result['is_loop'] = True
                result['loop_type'] = 'code'
                result['message'] = f"检测到代码循环：相同的修复代码已生成 {same_code_count + 1} 次"
                result['suggestion'] = self._get_code_loop_suggestion()
                logger.warning(result['message'])
                return result

            # 检查相似的代码
            for i, prev_attempt in enumerate(self.attempt_history[-3:]):
                prev_code = prev_attempt.get('fixed_code', '')
                if prev_code:
                    similarity = self._calculate_similarity(fixed_code, prev_code)
                    if similarity >= self.similarity_threshold:
                        logger.info(f"代码相似度: {similarity:.2f}")

            self.code_hashes.append(code_hash)

        # 2. 检查错误重复
        if error:
            error_hash = self._hash_error(error)

            same_error_count = self.error_hashes.count(error_hash)
            if same_error_count >= self.max_same_error:
                self.stats['error_loops_detected'] += 1
                result['is_loop'] = True
                result['loop_type'] = 'error'
                result['message'] = f"检测到错误循环：相同的错误已出现 {same_error_count + 1} 次"
                result['suggestion'] = self._get_error_loop_suggestion()
                logger.warning(result['message'])
                return result

            self.error_hashes.append(error_hash)

        # 3. 检查无效修复模式（连续失败）
        if len(self.attempt_history) >= 3:
            recent_failures = sum(
                1 for a in self.attempt_history[-3:]
                if a.get('error')
            )
            if recent_failures >= 3 and error:
                result['is_loop'] = True
                result['loop_type'] = 'failure_pattern'
                result['message'] = "检测到连续失败模式：最近3次尝试都失败了"
                result['suggestion'] = self._get_failure_pattern_suggestion()
                logger.warning(result['message'])
                return result

        # 记录这次尝试
        self.attempt_history.append(attempt)

        return result

    def _get_code_loop_suggestion(self) -> str:
        """获取代码循环的建议"""
        suggestions = [
            "1. LLM 可能对这个问题的理解有限，尝试提供更多上下文",
            "2. 考虑手动分析错误原因，给出更具体的修复提示",
            "3. 检查是否是环境问题而非代码问题",
            "4. 尝试分解问题，逐步修复",
        ]
        return '\n'.join(suggestions)

    def _get_error_loop_suggestion(self) -> str:
        """获取错误循环的建议"""
        suggestions = [
            "1. 相同的错误反复出现，修复方向可能不对",
            "2. 检查是否遗漏了必要的依赖或配置",
            "3. 考虑这个错误是否需要修改多个文件",
            "4. 尝试查看错误的根本原因而不是表面症状",
        ]
        return '\n'.join(suggestions)

    def _get_failure_pattern_suggestion(self) -> str:
        """获取连续失败模式的建议"""
        suggestions = [
            "1. 连续多次修复都失败，建议暂停自动修复",
            "2. 检查项目环境是否正确配置",
            "3. 确认错误信息是否完整",
            "4. 考虑是否需要人工介入分析",
        ]
        return '\n'.join(suggestions)

    def reset(self) -> None:
        """重置检测器状态"""
        self.attempt_history = []
        self.code_hashes = []
        self.error_hashes = []
        logger.info("LoopDetector 已重置")

    def get_stats(self) -> Dict[str, Any]:
        """获取统计信息"""
        return {
            **self.stats,
            'history_length': len(self.attempt_history),
        }

    def get_history_summary(self) -> str:
        """获取历史摘要（用于提供给 LLM）"""
        if not self.attempt_history:
            return "无历史记录"

        summary_parts = []
        for i, attempt in enumerate(self.attempt_history, 1):
            error = attempt.get('error', '')
            explanation = attempt.get('explanation', '')[:100]

            if error:
                summary_parts.append(f"尝试 {i}: 失败 - {error[:100]}")
            else:
                summary_parts.append(f"尝试 {i}: 说明 - {explanation}")

        return '\n'.join(summary_parts)
