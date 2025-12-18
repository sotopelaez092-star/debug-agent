"""智能重试策略 - 避免重复尝试失败的修复方法"""
import hashlib
import time
import logging
from typing import List, Dict, Set, Optional
from dataclasses import dataclass, field

logger = logging.getLogger(__name__)


@dataclass
class AttemptRecord:
    """单次尝试记录"""
    error_type: str
    approach: str
    fix_hash: str
    success: bool
    error_message: str = ""
    timestamp: float = field(default_factory=time.time)


class SmartRetryStrategy:
    """智能重试策略 - 记录失败方法，建议替代方案"""

    # 各错误类型的修复方案优先级
    SOLUTION_PRIORITIES = {
        'ImportError': [
            ('path_fix', '修复导入路径'),
            ('symbol_fix', '修复导入符号名'),
            ('add_init', '添加 __init__.py'),
            ('lazy_import', '延迟导入'),
            ('relative_import', '使用相对导入'),
        ],
        'ModuleNotFoundError': [
            ('path_fix', '修复模块路径'),
            ('intermediate_fix', '添加缺失的中间包'),
            ('prefix_fix', '添加包前缀'),
        ],
        'NameError': [
            ('typo_fix', '修复拼写错误'),
            ('add_import', '添加缺失的导入'),
            ('add_definition', '添加缺失的定义'),
            ('scope_fix', '修复作用域问题'),
        ],
        'AttributeError': [
            ('method_typo', '修复方法名拼写'),
            ('inheritance_fix', '检查继承链'),
            ('property_fix', '属性访问修复'),
        ],
        'KeyError': [
            ('key_typo', '修复键名拼写'),
            ('nested_access', '使用嵌套访问'),
            ('default_value', '添加默认值'),
        ],
        'CircularImport': [
            ('type_checking', '使用 TYPE_CHECKING'),
            ('late_import', '延迟导入'),
            ('extract_interface', '提取接口'),
            ('restructure', '重构依赖关系'),
        ],
    }

    def __init__(self, max_same_approach: int = 2):
        """
        初始化智能重试策略

        Args:
            max_same_approach: 同一方法最多尝试次数
        """
        self.attempt_history: List[AttemptRecord] = []
        self.failed_approaches: Dict[str, int] = {}  # approach -> 失败次数
        self.failed_fixes: Set[str] = set()  # 失败的修复内容哈希
        self.max_same_approach = max_same_approach

    def record_attempt(
        self,
        error_type: str,
        approach: str,
        fix_content: str,
        success: bool,
        error_message: str = ""
    ):
        """记录一次尝试"""
        fix_hash = self._hash_fix(fix_content)

        record = AttemptRecord(
            error_type=error_type,
            approach=approach,
            fix_hash=fix_hash,
            success=success,
            error_message=error_message
        )
        self.attempt_history.append(record)

        if not success:
            # 记录失败的方法
            approach_key = f"{error_type}:{approach}"
            self.failed_approaches[approach_key] = \
                self.failed_approaches.get(approach_key, 0) + 1

            # 记录失败的修复内容
            self.failed_fixes.add(fix_hash)

            logger.debug(f"记录失败尝试: {approach_key}, 已失败 {self.failed_approaches[approach_key]} 次")

    def should_try_approach(
        self,
        error_type: str,
        approach: str,
        proposed_fix: str = ""
    ) -> bool:
        """判断是否应该尝试某个方法"""
        approach_key = f"{error_type}:{approach}"

        # 检查同一方法是否已经失败太多次
        if self.failed_approaches.get(approach_key, 0) >= self.max_same_approach:
            logger.info(f"方法 '{approach}' 已失败 {self.max_same_approach} 次，跳过")
            return False

        # 检查相同的修复内容是否已经失败过
        if proposed_fix:
            fix_hash = self._hash_fix(proposed_fix)
            if fix_hash in self.failed_fixes:
                logger.info(f"相同的修复内容已经失败过，跳过")
                return False

        return True

    def suggest_alternative(self, error_type: str) -> Optional[str]:
        """当当前方法失败时，建议替代方案"""
        solutions = self.SOLUTION_PRIORITIES.get(error_type, [])

        for approach, desc in solutions:
            approach_key = f"{error_type}:{approach}"
            if self.failed_approaches.get(approach_key, 0) < self.max_same_approach:
                return f"建议尝试: {desc} ({approach})"

        return "所有常规方法已尝试，建议人工审查代码结构"

    def get_untried_approaches(self, error_type: str) -> List[str]:
        """获取尚未尝试的方法"""
        solutions = self.SOLUTION_PRIORITIES.get(error_type, [])
        untried = []

        for approach, desc in solutions:
            approach_key = f"{error_type}:{approach}"
            if approach_key not in self.failed_approaches:
                untried.append(f"{approach}: {desc}")

        return untried

    def get_retry_report(self) -> Dict:
        """生成重试报告"""
        total = len(self.attempt_history)
        successful = sum(1 for a in self.attempt_history if a.success)

        # 按错误类型统计
        by_error_type = {}
        for record in self.attempt_history:
            if record.error_type not in by_error_type:
                by_error_type[record.error_type] = {'total': 0, 'success': 0}
            by_error_type[record.error_type]['total'] += 1
            if record.success:
                by_error_type[record.error_type]['success'] += 1

        return {
            'total_attempts': total,
            'successful': successful,
            'success_rate': successful / total if total > 0 else 0,
            'unique_approaches': len(set(a.approach for a in self.attempt_history)),
            'failed_approaches': dict(self.failed_approaches),
            'by_error_type': by_error_type,
        }

    def reset(self):
        """重置策略状态（用于新的调试会话）"""
        self.attempt_history.clear()
        self.failed_approaches.clear()
        self.failed_fixes.clear()

    def _hash_fix(self, fix_content: str) -> str:
        """生成修复内容的哈希"""
        # 标准化内容（去除空白差异）
        normalized = ' '.join(fix_content.split())
        return hashlib.md5(normalized.encode()).hexdigest()[:12]


class AdaptiveRetryStrategy(SmartRetryStrategy):
    """自适应重试策略 - 根据历史数据调整策略"""

    def __init__(self, max_same_approach: int = 2):
        super().__init__(max_same_approach)
        # 方法成功率统计
        self.approach_stats: Dict[str, Dict[str, int]] = {}

    def record_attempt(
        self,
        error_type: str,
        approach: str,
        fix_content: str,
        success: bool,
        error_message: str = ""
    ):
        """记录尝试并更新统计"""
        super().record_attempt(error_type, approach, fix_content, success, error_message)

        # 更新方法成功率统计
        approach_key = f"{error_type}:{approach}"
        if approach_key not in self.approach_stats:
            self.approach_stats[approach_key] = {'success': 0, 'total': 0}

        self.approach_stats[approach_key]['total'] += 1
        if success:
            self.approach_stats[approach_key]['success'] += 1

    def get_recommended_approach(self, error_type: str) -> Optional[str]:
        """根据历史成功率推荐最佳方法"""
        solutions = self.SOLUTION_PRIORITIES.get(error_type, [])
        best_approach = None
        best_score = -1

        for approach, desc in solutions:
            approach_key = f"{error_type}:{approach}"

            # 如果已经失败太多次，跳过
            if self.failed_approaches.get(approach_key, 0) >= self.max_same_approach:
                continue

            # 计算得分（成功率 + 未尝试奖励）
            stats = self.approach_stats.get(approach_key, {'success': 0, 'total': 0})
            if stats['total'] == 0:
                score = 0.5  # 未尝试的方法给中等分数
            else:
                score = stats['success'] / stats['total']

            if score > best_score:
                best_score = score
                best_approach = (approach, desc)

        if best_approach:
            return f"{best_approach[1]} ({best_approach[0]}) - 历史成功率: {best_score:.0%}"

        return None
