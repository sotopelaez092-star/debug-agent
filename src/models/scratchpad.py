"""Scratchpad 记忆系统 - 代码主导更新"""
from dataclasses import dataclass, field
from typing import List, Any
import re


@dataclass
class Finding:
    """调查发现"""
    file: str
    line: int
    symbol: str
    reason: str


@dataclass
class Scratchpad:
    """记忆系统 - 代码主导更新"""
    todos: List[str] = field(default_factory=list)
    done: List[str] = field(default_factory=list)
    questions: List[str] = field(default_factory=list)
    findings: List[Finding] = field(default_factory=list)
    excluded: List[str] = field(default_factory=list)
    trace: List[str] = field(default_factory=list)

    def update_from_tool(self, tool_name: str, args: dict, result: Any):
        """工具执行后自动更新"""
        if tool_name == "search_symbol":
            symbol = args.get("name", "")
            self._mark_done(f"搜索 {symbol}")
            if hasattr(result, '__iter__') and not isinstance(result, str):
                for match in result:
                    if hasattr(match, 'file') and hasattr(match, 'line'):
                        self.findings.append(Finding(
                            file=match.file,
                            line=match.line,
                            symbol=match.name,
                            reason=f"符号匹配，置信度 {match.confidence:.0%}"
                        ))

        elif tool_name == "read_file":
            file_path = args.get("path", "")
            self._mark_done(f"读取 {file_path}")

        elif tool_name == "get_callers":
            func_name = args.get("name", "")
            self._mark_done(f"查找 {func_name} 调用者")
            if hasattr(result, '__iter__') and not isinstance(result, str):
                for caller in result or []:
                    if isinstance(caller, dict):
                        self.findings.append(Finding(
                            file=caller.get('file', ''),
                            line=caller.get('line', 0),
                            symbol=caller.get('name', ''),
                            reason=f"调用了 {func_name}"
                        ))

        self.add_trace(f"{tool_name}({args})")

    def update_questions_from_llm(self, llm_output: str):
        """从 LLM 输出提取新问题"""
        patterns = [
            r'问题[：:]\s*(.+?)(?:\n|$)',
            r'需要确认[：:]\s*(.+?)(?:\n|$)',
            r'\?\s*(.+\?)',
        ]
        for pattern in patterns:
            for match in re.finditer(pattern, llm_output):
                q = match.group(1).strip()
                if q and q not in self.questions:
                    self.questions.append(q)

    def resolve_question(self, question: str):
        """解决问题"""
        if question in self.questions:
            self.questions.remove(question)

    def _mark_done(self, task: str):
        """标记任务完成"""
        for todo in self.todos:
            if task.lower() in todo.lower() and todo not in self.done:
                self.done.append(todo)
                break

    def add_trace(self, action: str):
        """添加探索轨迹"""
        self.trace.append(f"[Turn {len(self.trace)+1}] {action}")

    def is_complete(self) -> bool:
        """检查调查是否完成"""
        return len(self.findings) > 0 and len(self.questions) == 0

    def has_enough_context(self) -> bool:
        """检查是否有足够的上下文"""
        return len(self.findings) >= 1

    def to_markdown(self) -> str:
        """转换为 Markdown 格式"""
        lines = ["## 当前探索状态", ""]

        lines.append("### 待办")
        if self.todos:
            for todo in self.todos:
                mark = "✅" if todo in self.done else "⬜"
                lines.append(f"- {mark} {todo}")
        else:
            lines.append("- 无待办事项")

        lines.append("\n### 待解决问题")
        if self.questions:
            for q in self.questions:
                lines.append(f"- ❓ {q}")
        else:
            lines.append("- ✅ 无待解决问题")

        lines.append("\n### 关键发现")
        if self.findings:
            for f in self.findings:
                lines.append(f"- 📍 {f.file}:{f.line} - `{f.symbol}`: {f.reason}")
        else:
            lines.append("- 暂无发现")

        if self.excluded:
            lines.append("\n### 已排除")
            for p in self.excluded:
                lines.append(f"- 🚫 {p}")

        return "\n".join(lines)
