"""LLM 响应缓存 - 基于错误模式复用修复策略"""
import json
import hashlib
import logging
import time
from pathlib import Path
from typing import Optional, Dict, Any
from dataclasses import dataclass, asdict

logger = logging.getLogger(__name__)


@dataclass
class CacheEntry:
    """缓存条目"""
    error_pattern: str      # 错误模式 (类型+关键信息)
    fix_strategy: str       # 修复策略
    fixed_code: str         # 修复后的代码模板
    explanation: str        # 解释
    success_count: int      # 成功次数
    fail_count: int         # 失败次数
    created_at: float       # 创建时间
    last_used: float        # 最后使用时间

    @property
    def confidence(self) -> float:
        """缓存置信度"""
        total = self.success_count + self.fail_count
        if total == 0:
            return 0.5
        return self.success_count / total


class LLMCache:
    """
    LLM 响应缓存

    基于错误模式（error_type + 关键特征）缓存修复策略，
    相同模式的错误可以直接复用缓存，跳过 LLM 调用。
    """

    def __init__(self, cache_dir: Optional[Path] = None, max_entries: int = 1000):
        """
        初始化缓存

        Args:
            cache_dir: 缓存目录，默认 .debug_agent_cache
            max_entries: 最大缓存条目数
        """
        self.cache_dir = cache_dir or Path(".debug_agent_cache")
        self.cache_dir.mkdir(exist_ok=True)
        self.cache_file = self.cache_dir / "llm_cache.json"
        self.max_entries = max_entries

        # 内存缓存
        self._cache: Dict[str, CacheEntry] = {}
        self._load_cache()

        logger.info(f"LLM 缓存初始化: {len(self._cache)} 条目")

    def _load_cache(self):
        """从磁盘加载缓存"""
        if self.cache_file.exists():
            try:
                data = json.loads(self.cache_file.read_text(encoding='utf-8'))
                for key, entry_data in data.items():
                    self._cache[key] = CacheEntry(**entry_data)
            except Exception as e:
                logger.warning(f"加载缓存失败: {e}")

    def _save_cache(self):
        """保存缓存到磁盘"""
        try:
            data = {k: asdict(v) for k, v in self._cache.items()}
            self.cache_file.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding='utf-8')
        except Exception as e:
            logger.warning(f"保存缓存失败: {e}")

    def _generate_key(self, error_type: str, error_message: str, code_context: str = "") -> str:
        """
        生成缓存键

        基于错误类型和关键特征生成唯一键，
        忽略具体变量名等细节，只保留模式。
        """
        # 提取错误模式（忽略具体名称）
        pattern = self._extract_pattern(error_type, error_message)

        # 生成哈希
        content = f"{error_type}:{pattern}"
        return hashlib.md5(content.encode()).hexdigest()[:16]

    def _extract_pattern(self, error_type: str, error_message: str) -> str:
        """
        提取错误模式（泛化具体名称）

        例如：
        - "name 'foo' is not defined" -> "name '<VAR>' is not defined"
        - "No module named 'maath'" -> "No module named '<MOD>'"
        """
        import re

        pattern = error_message

        # 泛化变量名
        pattern = re.sub(r"name '(\w+)'", "name '<VAR>'", pattern)

        # 泛化模块名
        pattern = re.sub(r"module named '([\w.]+)'", "module named '<MOD>'", pattern)

        # 泛化属性名
        pattern = re.sub(r"attribute '(\w+)'", "attribute '<ATTR>'", pattern)

        # 泛化键名
        pattern = re.sub(r"KeyError: '(\w+)'", "KeyError: '<KEY>'", pattern)

        # 泛化文件路径
        pattern = re.sub(r'File "([^"]+)"', 'File "<FILE>"', pattern)

        # 泛化行号
        pattern = re.sub(r'line \d+', 'line <N>', pattern)

        return pattern

    def get(self, error_type: str, error_message: str, code_context: str = "") -> Optional[CacheEntry]:
        """
        查找缓存

        Args:
            error_type: 错误类型
            error_message: 错误消息
            code_context: 代码上下文（可选）

        Returns:
            CacheEntry 如果命中且置信度足够，否则 None
        """
        key = self._generate_key(error_type, error_message, code_context)

        if key in self._cache:
            entry = self._cache[key]
            # 只返回置信度 > 0.7 的缓存
            if entry.confidence > 0.7:
                entry.last_used = time.time()
                logger.info(f"缓存命中: {error_type} (置信度: {entry.confidence:.0%})")
                return entry
            else:
                logger.debug(f"缓存置信度不足: {entry.confidence:.0%}")

        return None

    def put(self, error_type: str, error_message: str, fix_strategy: str,
            fixed_code: str, explanation: str, code_context: str = ""):
        """
        添加缓存

        Args:
            error_type: 错误类型
            error_message: 错误消息
            fix_strategy: 修复策略
            fixed_code: 修复后的代码
            explanation: 解释
            code_context: 代码上下文
        """
        key = self._generate_key(error_type, error_message, code_context)
        pattern = self._extract_pattern(error_type, error_message)

        now = time.time()

        if key in self._cache:
            # 更新现有条目
            entry = self._cache[key]
            entry.success_count += 1
            entry.last_used = now
        else:
            # 创建新条目
            entry = CacheEntry(
                error_pattern=pattern,
                fix_strategy=fix_strategy,
                fixed_code=fixed_code,
                explanation=explanation,
                success_count=1,
                fail_count=0,
                created_at=now,
                last_used=now
            )
            self._cache[key] = entry

        # 如果超过最大条目数，清理旧条目
        if len(self._cache) > self.max_entries:
            self._cleanup()

        self._save_cache()
        logger.debug(f"缓存已添加: {error_type}")

    def mark_failed(self, error_type: str, error_message: str, code_context: str = ""):
        """标记缓存失败（修复未通过验证）"""
        key = self._generate_key(error_type, error_message, code_context)

        if key in self._cache:
            self._cache[key].fail_count += 1
            self._save_cache()
            logger.debug(f"缓存标记失败: {error_type}")

    def _cleanup(self):
        """清理旧缓存条目"""
        # 按最后使用时间排序，删除最旧的 20%
        sorted_keys = sorted(
            self._cache.keys(),
            key=lambda k: self._cache[k].last_used
        )

        to_remove = sorted_keys[:len(sorted_keys) // 5]
        for key in to_remove:
            del self._cache[key]

        logger.info(f"清理了 {len(to_remove)} 条旧缓存")

    def stats(self) -> Dict[str, Any]:
        """获取缓存统计"""
        if not self._cache:
            return {"total": 0, "hit_rate": 0}

        total_success = sum(e.success_count for e in self._cache.values())
        total_fail = sum(e.fail_count for e in self._cache.values())

        return {
            "total_entries": len(self._cache),
            "total_hits": total_success,
            "total_fails": total_fail,
            "hit_rate": total_success / (total_success + total_fail) if (total_success + total_fail) > 0 else 0,
            "avg_confidence": sum(e.confidence for e in self._cache.values()) / len(self._cache)
        }
