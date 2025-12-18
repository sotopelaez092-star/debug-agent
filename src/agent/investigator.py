"""CodebaseInvestigator - ReAct 风格的代码库调查员"""
import re
import json
import logging
from enum import Enum, auto
from dataclasses import dataclass, field
from typing import List, Optional, TYPE_CHECKING

from src.models.error_context import ErrorContext
from src.models.investigation_report import InvestigationReport, RelevantLocation
from src.models.scratchpad import Scratchpad
from src.tools_new.registry import ToolRegistry
from src.utils.conversation_compressor import ConversationCompressor

if TYPE_CHECKING:
    from src.tools_new.context_tools import ContextTools

logger = logging.getLogger(__name__)


class Phase(Enum):
    """调查阶段"""
    INIT = auto()
    EXPLORE = auto()
    ANALYZE = auto()
    DONE = auto()
    FAILED = auto()


@dataclass
class LoopContext:
    """事件循环上下文"""
    error: ErrorContext
    phase: Phase = Phase.INIT
    turn: int = 0
    scratchpad: Scratchpad = field(default_factory=Scratchpad)
    messages: List[dict] = field(default_factory=list)
    max_turns: int = 5  # 从10减少到5，加快调查速度
    report: Optional[InvestigationReport] = None


class CodebaseInvestigator:
    """代码库调查员 - ReAct 风格事件循环"""

    SYSTEM_PROMPT = """你是专业的代码库调查员，专门分析 Python 跨文件错误。

## 可用工具

1. **search_symbol(name, fuzzy=True)**: 搜索符号定义（函数/类/变量），支持模糊匹配
   - 返回: 符号名、文件路径、行号、置信度

2. **read_file(path, start_line=1, end_line=None)**: 读取文件内容
   - 返回: 带行号的文件内容

3. **grep(pattern, path=".", use_regex=False)**: 搜索关键词
   - 返回: 匹配的文件、行号和内容

4. **get_callers(name)**: 获取调用某函数的所有位置
   - 返回: 调用者文件、行号、函数名

5. **set_investigation_phase(phase, reason)**: 切换调查阶段
   - phase: "EXPLORE" 或 "ANALYZE"
   - 只有信息完整时才切换到 ANALYZE

6. **complete_investigation(report)**: 提交最终报告（必须调用此工具结束调查）
   - report 必须包含: summary, relevant_locations, root_cause, suggested_fix, confidence

## 工作流程

### 阶段 1: EXPLORE（探索）
- 使用 search_symbol 搜索错误中提到的符号
- 使用 read_file 查看相关文件内容
- 使用 get_callers 追踪调用链
- 使用 grep 搜索相关代码模式

### 阶段 2: ANALYZE（分析）
- 综合所有发现
- 确定根本原因
- 准备修复建议

### 阶段 3: 提交报告
- 调用 complete_investigation 提交最终报告
- **必须调用此工具才能结束调查**

## 重要规则

1. **每轮对话会显示 Scratchpad 状态**，包含：
   - 待办事项和完成情况
   - 待解决问题
   - 关键发现
   - 已排除项

2. **基于 Scratchpad 状态决定下一步行动**

3. **信息完整后立即调用 complete_investigation**

4. **报告格式严格要求**：
   - summary: 至少 10 个字符
   - relevant_locations: 至少 1 个位置
   - root_cause: 根本原因分析
   - suggested_fix: 具体修复建议
   - confidence: 0-1 之间的数值

5. **每个 relevant_location 包含**：
   - file_path: 文件路径（**重要**：对于 ImportError，应该是被导入的模块文件，不是错误发生的文件）
   - line: 行号
   - symbol: 符号名称
   - reasoning: 选择此位置的原因
   - code_snippet: 代码片段（可选）

6. **relevant_locations 的选择原则**：
   - ImportError/ModuleNotFoundError: 返回**应该被导入的模块文件**（如 utils.py，而不是 main.py）
   - NameError: 返回**符号定义的文件**
   - AttributeError: 返回**类/对象定义的文件**
   - 目标是找到**提供所需符号/模块的文件**，以便后续修复时可以读取它们

## 示例调查流程

### 示例 1: NameError
```
Turn 1: search_symbol(name="undefined_var", fuzzy=True)
→ 发现 3 个候选，最高置信度 0.95

Turn 2: read_file(path="utils/helpers.py", start_line=10, end_line=30)
→ 确认符号定义位置

Turn 3: complete_investigation(report={
  "relevant_locations": [{"file_path": "utils/helpers.py", "line": 15, "symbol": "undefined_var", ...}],
  ...
})
→ 提交报告，调查完成
```

### 示例 2: ImportError
```
错误: ModuleNotFoundError: No module named 'utls'

Turn 1: search_symbol(name="utls", fuzzy=True)
→ 发现相似的模块 "utils"

Turn 2: read_file(path="utils.py", start_line=1, end_line=20)
→ 确认模块存在并包含需要的符号

Turn 3: complete_investigation(report={
  "relevant_locations": [{"file_path": "utils.py", "line": 1, "symbol": "helper", ...}],
  "suggested_fix": "将 'from utls import helper' 改为 'from utils import helper'",
  ...
})
→ 提交报告，调查完成
```

开始调查吧！"""

    def __init__(self, llm_client, context_tools: "ContextTools"):
        """
        初始化调查员

        Args:
            llm_client: LLM 客户端
            context_tools: ContextTools 实例
        """
        self.llm = llm_client
        self.context_tools = context_tools
        self.tool_registry = ToolRegistry()
        self.tool_registry.register_all_defaults(
            context_tools,
            str(context_tools.project_path)
        )
        self.compressor = ConversationCompressor()

    async def investigate(self, error: ErrorContext) -> InvestigationReport:
        """
        执行代码库调查

        Args:
            error: 错误上下文

        Returns:
            调查报告
        """
        logger.info(f"开始调查 {error.error_type}: {error.error_message}")

        ctx = self._init_context(error)

        # ReAct 事件循环
        while ctx.turn < ctx.max_turns and ctx.phase not in (Phase.DONE, Phase.FAILED):
            ctx.turn += 1
            logger.info(f"Turn {ctx.turn}/{ctx.max_turns}, Phase: {ctx.phase.name}")

            # 压缩对话（如果需要）
            ctx.messages = await self.compressor.compress_if_needed(
                ctx.messages, self.llm, ctx.scratchpad
            )

            # 构建提示
            prompt = self._build_prompt(ctx)
            ctx.messages.append({"role": "user", "content": prompt})

            # 调用 LLM
            try:
                response = await self.llm.chat(
                    messages=ctx.messages,
                    tools=self.tool_registry.get_all_schemas()
                )

                # 添加 LLM 响应
                assistant_msg = {
                    "role": "assistant",
                    "content": response.get("content", "")
                }

                # 检查是否有 tool_calls（转换为标准格式）
                if "tool_calls" in response and response["tool_calls"]:
                    # 转换为 OpenAI 标准格式
                    tool_calls_formatted = []
                    for tc in response["tool_calls"]:
                        tool_calls_formatted.append({
                            "id": tc["id"],
                            "type": "function",  # 添加必需的 type 字段
                            "function": {
                                "name": tc["name"],
                                "arguments": tc["arguments"] if isinstance(tc["arguments"], str) else json.dumps(tc["arguments"])
                            }
                        })
                    assistant_msg["tool_calls"] = tool_calls_formatted

                ctx.messages.append(assistant_msg)

                # 处理工具调用
                if "tool_calls" in response and response["tool_calls"]:
                    for tool_call in response["tool_calls"]:
                        await self._handle_tool_call(tool_call, ctx)

                        # 检查是否完成
                        if ctx.phase == Phase.DONE and ctx.report:
                            logger.info("调查完成")
                            return ctx.report

                # 更新 Scratchpad 中的问题
                if response.get("content"):
                    ctx.scratchpad.update_questions_from_llm(response["content"])

            except Exception as e:
                logger.error(f"LLM 调用失败: {e}", exc_info=True)
                ctx.phase = Phase.FAILED
                break

        # 超时或失败，尝试恢复
        if ctx.phase != Phase.DONE:
            logger.warning(f"调查未正常完成，阶段: {ctx.phase.name}")
            return await self._recovery_attempt(ctx)

        return ctx.report or self._build_partial_report(ctx)

    def _init_context(self, error: ErrorContext) -> LoopContext:
        """初始化循环上下文"""
        ctx = LoopContext(error=error)

        # 初始化消息
        ctx.messages = [{"role": "system", "content": self.SYSTEM_PROMPT}]

        # 初始化 Scratchpad
        symbol = self._extract_symbol(error)
        ctx.scratchpad.todos = [
            f"搜索 '{symbol}' 的定义",
            "确认错误原因",
            "找到所有相关文件",
        ]
        ctx.scratchpad.questions = [
            f"'{symbol}' 在哪里定义？",
            "是拼写错误还是不存在？",
        ]

        ctx.phase = Phase.EXPLORE
        return ctx

    def _build_prompt(self, ctx: LoopContext) -> str:
        """构建提示"""
        phase_hints = {
            Phase.EXPLORE: "请继续探索，使用工具搜索更多相关信息。",
            Phase.ANALYZE: "请分析根因，准备提交报告。",
        }

        return f"""## Turn {ctx.turn}/{ctx.max_turns}

### 错误信息
- **类型**: {ctx.error.error_type}
- **消息**: {ctx.error.error_message}
- **文件**: {ctx.error.error_file}:{ctx.error.error_line}

{ctx.scratchpad.to_markdown()}

### 当前阶段
**{ctx.phase.name}** - {phase_hints.get(ctx.phase, "")}

### 下一步行动
请使用工具继续调查。信息完整后调用 **complete_investigation** 提交报告。
"""

    async def _handle_tool_call(self, tool_call: dict, ctx: LoopContext):
        """处理工具调用"""
        tool_name = tool_call.get("name") or tool_call.get("function", {}).get("name")
        tool_args = tool_call.get("arguments") or tool_call.get("function", {}).get("arguments", {})

        # 如果 arguments 是字符串，解析为 dict
        if isinstance(tool_args, str):
            import json
            try:
                tool_args = json.loads(tool_args)
            except:
                tool_args = {}

        logger.debug(f"执行工具: {tool_name}({tool_args})")

        tool = self.tool_registry.get(tool_name)
        if not tool:
            result = {"error": f"未知工具: {tool_name}"}
            ctx.messages.append({
                "role": "tool",
                "tool_call_id": tool_call.get("id", ""),
                "content": str(result)
            })
            return result

        # 执行工具
        try:
            result = await tool.execute(**tool_args)
        except Exception as e:
            logger.error(f"工具执行失败: {e}", exc_info=True)
            result = {"error": str(e)}

        # 特殊处理
        if tool_name == "complete_investigation":
            if isinstance(result, dict) and result.get("success"):
                ctx.report = result["report"]
                ctx.phase = Phase.DONE
                logger.info("调查报告已提交")
            else:
                error_msg = result.get("error", "未知错误")
                ctx.messages.append({
                    "role": "tool",
                    "tool_call_id": tool_call.get("id", ""),
                    "content": f"❌ 报告格式错误:\n{error_msg}\n\n请修正后重试。"
                })
            return result

        if tool_name == "set_investigation_phase":
            if isinstance(result, dict) and result.get("success"):
                new_phase = result["phase"]
                ctx.phase = Phase[new_phase]
                ctx.scratchpad.add_trace(f"阶段切换: {new_phase} - {result['reason']}")
                logger.info(f"阶段切换到: {new_phase}")

        # 普通工具：更新 Scratchpad
        ctx.scratchpad.update_from_tool(tool_name, tool_args, result)

        # 添加工具响应消息
        ctx.messages.append({
            "role": "tool",
            "tool_call_id": tool_call.get("id", ""),
            "content": self._format_tool_result(result)
        })

        return result

    def _format_tool_result(self, result) -> str:
        """格式化工具结果"""
        if isinstance(result, str):
            return result
        elif isinstance(result, list):
            if not result:
                return "无结果"
            # 格式化列表结果
            if hasattr(result[0], '__dict__'):
                # SymbolMatch 等对象
                lines = []
                for item in result[:10]:  # 最多显示 10 条
                    if hasattr(item, 'to_dict'):
                        lines.append(str(item.to_dict()))
                    else:
                        lines.append(str(item.__dict__))
                if len(result) > 10:
                    lines.append(f"... 以及其他 {len(result) - 10} 条结果")
                return "\n".join(lines)
            else:
                # 普通字典列表
                import json
                return json.dumps(result[:10], ensure_ascii=False, indent=2)
        elif isinstance(result, dict):
            import json
            return json.dumps(result, ensure_ascii=False, indent=2)
        else:
            return str(result)

    async def _recovery_attempt(self, ctx: LoopContext) -> InvestigationReport:
        """超时恢复"""
        logger.warning(f"尝试恢复调查（Turn {ctx.turn}/{ctx.max_turns}）")

        ctx.messages.append({
            "role": "user",
            "content": f"""⚠️ 已达到最大轮次限制 ({ctx.max_turns})。

请**立即**调用 **complete_investigation** 提交报告。
即使信息不完整也要提交，在 summary 中说明。

{ctx.scratchpad.to_markdown()}
"""
        })

        try:
            response = await self.llm.chat(
                messages=ctx.messages,
                tools=[self.tool_registry.get("complete_investigation").to_schema()]
            )

            if "tool_calls" in response and response["tool_calls"]:
                for tool_call in response["tool_calls"]:
                    if tool_call.get("name") == "complete_investigation":
                        result = await self._handle_tool_call(tool_call, ctx)
                        if result.get("success"):
                            return result["report"]
        except Exception as e:
            logger.error(f"恢复失败: {e}", exc_info=True)

        # 最后兜底
        return self._build_partial_report(ctx)

    def _build_partial_report(self, ctx: LoopContext) -> InvestigationReport:
        """构建部分报告（兜底）"""
        locations = [
            RelevantLocation(
                file_path=f.file,
                line=f.line,
                symbol=f.symbol,
                reasoning=f.reason
            )
            for f in ctx.scratchpad.findings
        ]

        # 如果没有任何发现，创建一个占位符
        if not locations:
            locations = [
                RelevantLocation(
                    file_path=ctx.error.error_file or "unknown",
                    line=ctx.error.error_line or 0,
                    symbol="unknown",
                    reasoning="调查未完成，无法确定具体位置"
                )
            ]

        return InvestigationReport(
            summary=f"调查未完成（{ctx.turn}/{ctx.max_turns}轮），发现 {len(ctx.scratchpad.findings)} 个位置",
            relevant_locations=locations,
            root_cause="未能确定（调查超时或失败）",
            suggested_fix="建议人工检查相关位置",
            confidence=0.3,
            exploration_trace=ctx.scratchpad.trace
        )

    def _extract_symbol(self, error: ErrorContext) -> str:
        """从错误中提取符号名"""
        patterns = [
            r"name '(\w+)'",
            r"module named '([\w.]+)'",
            r"attribute '(\w+)'",
            r"'(\w+)' is not defined",
        ]
        for pattern in patterns:
            match = re.search(pattern, error.error_message)
            if match:
                return match.group(1)
        return "unknown"
