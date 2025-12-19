"""CodeFixer - 代码修复器（新架构）"""
import json
import re
import logging
from typing import Optional, Dict, Any, List
from openai import AsyncOpenAI

from src.models.results import FixResult
from src.utils.config import get_settings
from src.core.pattern_fixer import PatternFixer
from src.core.llm_cache import LLMCache
from src.core.llm_error_handler import (
    call_llm_with_retry,
    LLMError,
    LLMAuthError,
    LLMRateLimitError,
    LLMTimeoutError
)

logger = logging.getLogger(__name__)


class CodeFixer:
    """使用 LLM 生成代码修复"""

    def __init__(
        self,
        api_key: Optional[str] = None,
        model: str = "deepseek-chat",
        temperature: float = 0.3,
        max_tokens: int = 2000
    ):
        """
        初始化 CodeFixer

        Args:
            api_key: API 密钥
            model: 模型名称
            temperature: 温度参数（0-1，越低越确定）
            max_tokens: 最大 token 数
        """
        settings = get_settings()

        self.api_key = api_key or settings.deepseek_api_key
        self.model = model
        self.temperature = temperature
        self.max_tokens = max_tokens

        # 创建 OpenAI 客户端
        self.client = AsyncOpenAI(
            api_key=self.api_key,
            base_url=settings.deepseek_base_url or "https://api.deepseek.com/v1"
        )

        # 模式匹配快速修复器
        self.pattern_fixer = PatternFixer()

        # LLM 响应缓存
        self.cache = LLMCache()

        # Token 使用统计
        self.token_stats = {
            "total_prompt_tokens": 0,
            "total_completion_tokens": 0,
            "total_tokens": 0,
            "llm_calls": 0,
            "cache_hits": 0,
            "pattern_hits": 0,
            "tokens_saved_by_cache": 0  # 估算：每次缓存命中省约 2500 tokens
        }

        logger.info(f"CodeFixer 初始化: model={self.model}, 缓存条目: {len(self.cache._cache)}")

    async def fix_code(
        self,
        buggy_code: str,
        error_message: str,
        context: Optional[Dict[str, Any]] = None,
        rag_solutions: Optional[List[Dict]] = None,
        error_type: Optional[str] = None,
        force_llm: bool = False
    ) -> FixResult:
        """
        生成代码修复

        Args:
            buggy_code: 包含错误的代码
            error_message: 错误消息
            context: 上下文信息（来自 InvestigationReport）
            rag_solutions: RAG 检索的解决方案（可选）
            error_type: 错误类型（如 NameError, ImportError 等）

        Returns:
            FixResult

        Raises:
            ValueError: 输入验证失败
            RuntimeError: LLM 调用失败
        """
        # 验证输入
        if not buggy_code or not isinstance(buggy_code, str):
            raise ValueError("buggy_code 必须是非空字符串")
        if not error_message or not isinstance(error_message, str):
            raise ValueError("error_message 必须是非空字符串")

        # 尝试从参数或消息中获取错误类型
        if not error_type:
            error_type = self._extract_error_type(error_message)

        # 只有在不强制使用 LLM 时才尝试 PatternFixer
        if error_type and not force_llm:
            pattern_result = self.pattern_fixer.try_fix(buggy_code, error_type, error_message)
            if pattern_result:
                fixed_code, explanation = pattern_result
                logger.info(f"⚡ 模式匹配快速修复: {explanation}")
                self.token_stats["pattern_hits"] += 1
                self.token_stats["tokens_saved_by_cache"] += 2500  # 估算省的 tokens
                return FixResult(
                    success=True,
                    fixed_code=fixed_code,
                    explanation=f"[快速修复] {explanation}",
                    changes=[explanation],
                    used_pattern_fixer=True  # 标记使用了 PatternFixer
                )
        elif force_llm:
            logger.info("🔧 强制使用 LLM（PatternFixer 上次失败）")

        # 缓存命中暂时禁用 - 缓存只存策略描述，无法直接应用
        # TODO: 改进缓存设计，存储可应用的修复模板
        # if error_type:
        #     cache_entry = self.cache.get(error_type, error_message, buggy_code[:200])
        #     if cache_entry:
        #         logger.info(f"💾 缓存命中: {error_type} (置信度: {cache_entry.confidence:.0%})")
        #         ...

        # 构建提示
        prompt = self._build_prompt(buggy_code, error_message, context, rag_solutions)

        try:
            # 调用 LLM（带重试机制）
            response = await call_llm_with_retry(
                client=self.client,
                model=self.model,
                messages=[
                    {
                        "role": "system",
                        "content": "你是专业的 Python 代码修复专家。请仔细分析错误并生成修复后的代码。"
                    },
                    {
                        "role": "user",
                        "content": prompt
                    }
                ],
                temperature=self.temperature,
                max_tokens=self.max_tokens,
                max_retries=3,
                timeout=60.0
            )

            # 记录 token 使用
            if hasattr(response, 'usage') and response.usage:
                self.token_stats["total_prompt_tokens"] += response.usage.prompt_tokens
                self.token_stats["total_completion_tokens"] += response.usage.completion_tokens
                self.token_stats["total_tokens"] += response.usage.total_tokens
                self.token_stats["llm_calls"] += 1
                logger.info(f"📊 Token 使用: {response.usage.total_tokens} (prompt: {response.usage.prompt_tokens}, completion: {response.usage.completion_tokens})")

            # 解析响应
            content = response.choices[0].message.content
            result = self._parse_response(content, buggy_code)

            # 存入缓存
            if error_type and result.fixed_code != buggy_code:
                self.cache.put(
                    error_type=error_type,
                    error_message=error_message,
                    fix_strategy=result.explanation[:200] if result.explanation else "",
                    fixed_code=result.fixed_code[:500],  # 只存储部分代码作为模板
                    explanation=result.explanation or "",
                    code_context=buggy_code[:200]
                )

            return result

        except LLMAuthError as e:
            logger.error(f"API 认证失败: {e}")
            raise RuntimeError(f"API 认证失败，请检查 API Key: {e}")

        except LLMRateLimitError as e:
            logger.error(f"API 速率限制: {e}")
            raise RuntimeError(f"API 速率限制，请稍后重试: {e}")

        except LLMTimeoutError as e:
            logger.error(f"请求超时: {e}")
            raise RuntimeError(f"LLM 请求超时，请检查网络连接: {e}")

        except LLMError as e:
            logger.error(f"LLM 调用失败: {e}", exc_info=True)
            raise RuntimeError(f"代码修复失败: {e}")

        except Exception as e:
            logger.error(f"未预期的错误: {e}", exc_info=True)
            raise RuntimeError(f"代码修复过程中发生错误: {e}")

    def _build_prompt(
        self,
        buggy_code: str,
        error_message: str,
        context: Optional[Dict[str, Any]],
        rag_solutions: Optional[List[Dict]]
    ) -> str:
        """构建修复提示"""
        sections = []

        # 1. 错误代码
        sections.append("## 错误代码")
        sections.append("```python")
        sections.append(buggy_code)
        sections.append("```")

        # 2. 错误信息
        sections.append("\n## 错误信息")
        sections.append(f"```\n{error_message}\n```")

        # 3. 上下文信息（如果有）
        if context:
            sections.append("\n## 上下文信息")

            if "investigation_summary" in context:
                sections.append(f"**调查总结**: {context['investigation_summary']}")

            if "root_cause" in context:
                sections.append(f"**根本原因**: {context['root_cause']}")

            if "suggested_fix" in context:
                sections.append(f"**建议修复**: {context['suggested_fix']}")

            if "relevant_locations" in context:
                sections.append("\n**相关位置**:")
                for loc in context["relevant_locations"]:
                    sections.append(f"- {loc.get('file')}:{loc.get('line')} - {loc.get('symbol')}")
                    sections.append(f"  原因: {loc.get('reasoning')}")

            if "related_symbols" in context:
                sections.append("\n**相关符号定义**:")
                for symbol, info in context["related_symbols"].items():
                    sections.append(f"- `{symbol}` ({info.get('type')}) 在 {info.get('file')}:{info.get('line')}")
                    if info.get("definition"):
                        sections.append(f"  ```python\n  {info['definition']}\n  ```")

            # 策略上下文（用于 CircularImport 和 KeyError）
            if "strategy_context" in context:
                sc = context["strategy_context"]
                sections.append("\n**【重要】具体修复指南**:")

                # CircularImport 策略
                if sc.get("circular_import"):
                    sections.append(f"- 这是循环导入问题")
                    sections.append(f"- 涉及符号: `{sc.get('symbol')}`")
                    sections.append(f"- 涉及模块: `{sc.get('module')}`")
                    sections.append(f"- 推荐策略: **{sc.get('fix_strategy', 'TYPE_CHECKING')}**")
                    if sc.get("fix_instructions"):
                        sections.append("- 修复步骤:")
                        for instr in sc.get("fix_instructions", []):
                            sections.append(f"  {instr}")
                    if sc.get("fix_code_template"):
                        sections.append("- 参考代码模板:")
                        sections.append(f"```python\n{sc.get('fix_code_template')}\n```")

                # KeyError 嵌套结构策略
                if sc.get("fix_type") in ["nested", "restructured"]:
                    sections.append(f"- 这是字典键访问问题")
                    sections.append(f"- 缺失的键: `{sc.get('missing_key')}`")
                    sections.append(f"- 访问路径已变更为嵌套结构")
                    sections.append(f"- **正确访问方式**: `{sc.get('fix_code', '')}`")
                    sections.append(f"- **原错误代码**: `{sc.get('original_code', '')}`")
                    sections.append(f"- 来源: {sc.get('source_file')} 的 {sc.get('source_function')}() 函数")

        # 4. RAG 解决方案（如果有）
        if rag_solutions:
            sections.append("\n## 参考解决方案（Stack Overflow）")
            for i, sol in enumerate(rag_solutions[:3], 1):  # 最多显示 3 个
                sections.append(f"\n### 方案 {i}")
                sections.append(sol.get("content", "")[:500])  # 限制长度

        # 5. 任务说明
        sections.append("\n## 任务")
        sections.append("请修复上述代码中的错误，并返回 JSON 格式的响应。")
        sections.append("\n**要求**:")
        sections.append("1. 仔细分析错误原因")
        sections.append("2. **检查整个代码文件，找出并修复所有类似的错误**（例如：如果有一个方法名拼写错误，检查是否还有其他类似的拼写错误）")
        sections.append("3. 生成修复后的**完整代码**（不要省略任何部分）")
        sections.append("4. 确保修复后的代码可以正常运行")
        sections.append("5. 保持原有的代码结构和逻辑")
        sections.append("6. **重要：不要修改函数名、类名、方法名等公共 API 定义**（其他文件可能依赖这些名称）。只修复函数内部的错误（如 `rnage` → `range`），不要把函数名如 `create_matrx` 改成 `create_matrix`")

        # 特殊错误类型的处理指南
        sections.append("\n## 特殊错误处理指南")
        sections.append("""
**循环导入 (CircularImport/partially initialized module)**:
如果错误是循环导入，请使用以下方案之一：
1. **TYPE_CHECKING 方案**（推荐用于类型注解）:
   ```python
   from typing import TYPE_CHECKING
   if TYPE_CHECKING:
       from module import Class  # 只在类型检查时导入

   def func(param: "Class"):  # 使用字符串注解
       ...
   ```
2. **延迟导入方案**（用于运行时需要的导入）:
   ```python
   def create_something():
       from module import Class  # 移到函数内部
       return Class()
   ```
3. **移除不必要的导入**：如果导入只用于类型注解且可以省略，直接删除。

**KeyError 嵌套字典**:
如果错误是 KeyError 且上下文提到"嵌套结构"或"重构"：
- 检查字典的实际结构（从上下文信息中查看）
- 将 `dict["old_key"]` 改为 `dict["parent"]["child"]`
- 例如: `config["log_level"]` → `config["logging"]["level"]`
""")

        sections.append("\n**返回格式** (严格的 JSON):")
        sections.append("```json")
        sections.append("{")
        sections.append('  "fixed_code": "修复后的完整代码",')
        sections.append('  "explanation": "修复说明（简洁明了）",')
        sections.append('  "changes": ["具体改动1", "具体改动2"]')
        sections.append("}")
        sections.append("```")

        return "\n".join(sections)

    def _parse_response(self, content: str, original_code: str) -> FixResult:
        """解析 LLM 响应"""
        try:
            # 1. 尝试提取 JSON 代码块
            json_match = re.search(r'```json\s*\n(.*?)\n```', content, re.DOTALL)
            if json_match:
                json_str = json_match.group(1)
                data = json.loads(json_str)
            else:
                # 2. 尝试直接解析 JSON
                # 查找第一个 { 和最后一个 }
                start = content.find('{')
                end = content.rfind('}')
                if start != -1 and end != -1:
                    json_str = content[start:end+1]
                    data = json.loads(json_str)
                else:
                    raise ValueError("未找到 JSON 内容")

            # 提取字段
            fixed_code = data.get("fixed_code", "")
            explanation = data.get("explanation", "")
            changes = data.get("changes", [])

            if not fixed_code:
                raise ValueError("fixed_code 为空")

            logger.info("成功解析 LLM 响应")
            return FixResult(
                success=True,
                fixed_code=fixed_code,
                explanation=explanation,
                changes=changes if isinstance(changes, list) else []
            )

        except Exception as e:
            logger.warning(f"JSON 解析失败: {e}，使用回退方案")
            # 回退：提取代码块
            code_match = re.search(r'```python\s*\n(.*?)\n```', content, re.DOTALL)
            if code_match:
                fixed_code = code_match.group(1)
            else:
                # 最后的回退：使用原始代码
                logger.error("无法提取修复代码，返回原始代码")
                fixed_code = original_code

            return FixResult(
                success=True,
                fixed_code=fixed_code,
                explanation=f"LLM 响应解析失败，提取的代码可能不完整",
                changes=[]
            )

    def _extract_error_type(self, error_message: str) -> Optional[str]:
        """从错误消息中提取错误类型"""
        error_types = [
            "NameError", "AttributeError", "TypeError", "ImportError",
            "ModuleNotFoundError", "KeyError", "IndexError", "ValueError",
            "ZeroDivisionError", "FileNotFoundError", "SyntaxError"
        ]
        for err_type in error_types:
            if err_type in error_message:
                return err_type
        return None

    def get_token_stats(self) -> Dict[str, Any]:
        """获取 token 使用统计"""
        stats = self.token_stats.copy()
        # 计算节省比例
        if stats["total_tokens"] > 0:
            total_would_use = stats["total_tokens"] + stats["tokens_saved_by_cache"]
            stats["savings_percent"] = (stats["tokens_saved_by_cache"] / total_would_use * 100) if total_would_use > 0 else 0
        else:
            stats["savings_percent"] = 0
        return stats

    def save_token_stats(self):
        """保存 token 统计到文件"""
        from pathlib import Path
        stats_file = Path(".debug_agent_cache/token_stats.json")
        stats_file.parent.mkdir(exist_ok=True)

        # 读取现有统计并累加
        existing = {}
        if stats_file.exists():
            try:
                existing = json.loads(stats_file.read_text(encoding='utf-8'))
            except:
                pass

        # 累加统计
        for key in ["total_prompt_tokens", "total_completion_tokens", "total_tokens",
                    "llm_calls", "cache_hits", "pattern_hits", "tokens_saved_by_cache"]:
            existing[key] = existing.get(key, 0) + self.token_stats[key]

        stats_file.write_text(json.dumps(existing, indent=2), encoding='utf-8')
        logger.info(f"Token 统计已保存: {existing}")
