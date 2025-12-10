"""
ReAct Agent
Thought -> Action -> Observation 循环

优化特性（Gemini CLI 模式）：
- LoopDetector: 检测重复修复模式，防止无限循环
- TokenManager: 上下文压缩，优化 Token 使用
- 延迟加载: 按需初始化工具模块
"""

import os
import logging
import re
from typing import Dict, List, Any, Optional
from dotenv import load_dotenv
from openai import OpenAI

# 加载环境变量
load_dotenv()

logger = logging.getLogger(__name__)

# 导入优化模块
from src.agent.loop_detector import LoopDetector
from src.agent.token_manager import TokenManager

class ReActAgent:
    """
    ReAct Agent: 让LLM自主决定调用哪个工具
    """

    TOOLS_DESCRIPTION = """
你可以使用以下工具：

1. analyze_error
   功能: 从traceback中提取错误类型、文件名、行号
   参数: {"traceback": "完整的错误traceback"}
   返回: 错误类型、错误信息、文件名、行号
   
   使用示例:
   Action: analyze_error
   Action Input: {"traceback": "Traceback (most recent call last)...\\nNameError: name 'x' is not defined"}
   
   适用场景: 刚开始分析时，需要了解错误的具体类型

2. get_project_context
   功能: 分析项目结构，找到未定义符号的定义位置，生成import建议
   参数: {
     "error_file": "出错的文件名（如main.py）",
     "error_name": "未定义的名称",
     "error_type": "错误类型（如NameError）"
   }
   返回: 符号定义位置、相关代码、import建议
   
   使用示例:
   Action: get_project_context
   Action Input: {"error_file": "main.py", "error_name": "calculate", "error_type": "NameError"}
   
   适用场景: 
   - NameError（找函数/变量定义）
   - ImportError（找模块路径）
   - AttributeError（找类定义）

3. search_solutions
   功能: 从Stack Overflow知识库搜索相关解决方案
   参数: {"query": "搜索关键词", "top_k": 5}
   返回: 相关解决方案列表
   
   使用示例:
   Action: search_solutions
   Action Input: {"query": "Python NameError undefined variable", "top_k": 5}
   
   适用场景: 不确定如何修复，需要参考Stack Overflow案例

4. fix_code
   功能: 生成修复后的代码
   参数: {
     "buggy_code": "有错误的代码",
     "error_message": "错误信息"
   }
   返回: 修复后的代码、修复说明、变更列表
   
   使用示例:
   Action: fix_code
   Action Input: {"buggy_code": "def greet():\\n    print(nme)", "error_message": "NameError: name 'nme' is not defined"}
   
   适用场景: 已经了解错误原因，准备生成修复代码

5. execute_code
   功能: 在Docker沙箱中执行代码，验证修复是否成功
   参数: {"code": "要执行的代码"}（可选，默认使用最近的fix_code结果）
   返回: 执行结果（成功/失败）、标准输出、错误信息
   
   使用示例:
   Action: execute_code
   Action Input: {}
   
   适用场景: 生成修复后，必须执行此工具验证是否真的修复成功

6. fix_multi_file
   功能: 修改依赖文件（如类定义、函数定义）
   参数: {"error_file": "出错的文件", "error_message": "错误信息"}
   返回: 修复方案和修改后的文件内容
   
   使用示例:
   Action: fix_multi_file
   Action Input: {"error_file": "main.py", "error_message": "AttributeError: 'User' object has no attribute 'age'"}
   
   适用场景: AttributeError等需要修改其他文件（如类定义）的错误

==========================================
推荐的工作流程（重要！）
==========================================

阶段1: 理解错误
  → analyze_error（分析错误类型）

阶段2: 收集信息（根据错误类型选择）
  → 如果是NameError/ImportError: get_project_context（找定义位置）
  → 如果不确定怎么修: search_solutions（找参考方案）（可选）

阶段3: 修复代码
  → fix_code（生成修复）

阶段4: 验证修复（必须！）
  → execute_code（验证是否成功）
  → 如果失败: 回到阶段3，尝试不同思路
  → 如果成功: 输出Final Answer

==========================================
关键规则（必须遵守！）
==========================================

1. 修复后必须用execute_code验证
   - ❌ 错误做法: fix_code后直接输出Final Answer
   - ✅ 正确做法: fix_code → execute_code → 成功后才Final Answer

2. 验证失败后换思路
   - 不要重复相同的修复方案
   - 分析失败原因，尝试不同的修复思路

3. 简单优先
   - 优先尝试最简单的修复方案
   - 不要过度复杂化

4. 不要重复调用同一工具（fix_code除外）
   - analyze_error只需调用1次
   - get_project_context只需调用1次（除非需要查找不同的符号）
   - search_solutions只需调用1次
   - execute_code可以多次（每次fix_code后都要执行）

==========================================
常见错误类型处理策略
==========================================

NameError（变量/函数未定义）:
  1. analyze_error
  2. get_project_context（找定义位置）
  3. fix_code（添加import或定义变量）
  4. execute_code（验证）

ImportError（导入错误）:
  1. analyze_error
  2. get_project_context（找正确的模块路径）
  3. fix_code（修正import语句）
  4. execute_code（验证）

AttributeError（属性不存在）:
  1. analyze_error
  2. get_project_context（找类定义）
  3. fix_multi_file（修改类定义）或 fix_code（添加属性检查）
  4. execute_code（验证）

TypeError/ValueError（类型/值错误）:
  1. analyze_error
  2. search_solutions（找参考方案）（可选）
  3. fix_code（修复类型转换或值检查）
  4. execute_code（验证）
"""

    SYSTEM_PROMPT = """你是一个专业的Python Debug专家，使用ReAct模式解决问题。

{tools_description}

==========================================
工作方式
==========================================

你通过 Thought → Action → Observation 循环来解决问题：

1. Thought: 分析当前情况，思考下一步该做什么
2. Action: 选择一个工具执行
3. Observation: 观察工具返回的结果
4. 重复1-3，直到问题解决

==========================================
输出格式（严格遵守）
==========================================

每次回复必须按照以下格式：

Thought: [你的思考：当前是什么情况？下一步该做什么？为什么？]
Action: [工具名称]
Action Input: {{"param1": "value1", "param2": "value2"}}

当确认代码已修复并验证成功后，输出：

Thought: [总结修复过程：修复了什么问题，如何修复的]
Final Answer: {{"fixed_code": "完整的修复后代码", "explanation": "修复说明"}}

==========================================
示例（参考）
==========================================

示例1: NameError修复流程

Thought: 首先需要分析错误类型，看看是什么错误
Action: analyze_error
Action Input: {{"traceback": "NameError: name 'calculate' is not defined"}}

[观察到: 错误类型是NameError，未定义的名称是calculate]

Thought: 这是NameError，说明calculate未定义。需要查找项目中是否有calculate的定义
Action: get_project_context
Action Input: {{"error_file": "main.py", "error_name": "calculate", "error_type": "NameError"}}

[观察到: calculate定义在utils.py中，建议添加 from utils import calculate]

Thought: 找到了定义位置，现在修复代码，添加import语句
Action: fix_code
Action Input: {{"buggy_code": "...", "error_message": "NameError: name 'calculate' is not defined"}}

[观察到: 已生成修复代码]

Thought: 修复完成，必须验证是否真的成功
Action: execute_code
Action Input: {{}}

[观察到: 执行成功！]

Thought: 验证成功，代码已修复。添加了from utils import calculate解决了NameError
Final Answer: {{"fixed_code": "...", "explanation": "添加了from utils import calculate导入语句"}}

==========================================
重要提醒
==========================================

1. 每次只输出一个Action
2. Action Input必须是有效的JSON
3. 修复后必须execute_code验证
4. 验证成功后才能输出Final Answer
5. 如果验证失败，分析原因，尝试不同的修复思路
6. 简洁高效，不要做无用的工具调用
"""

    def __init__(
        self,
        api_key: Optional[str] = None,
        model: str = "deepseek-chat",
        max_iterations: int = 15,
        temperature: float = 0.1,
        progress_callback=None
    ):
        """
        初始化ReAct Agent
        
        Args:
            api_key: OpenAI API密钥（如果为空，从环境变量中获取）
            model: 使用的模型名称（默认deepseek-chat）
            max_iterations: 最大迭代次数（默认10）
        """
        # 1. 初始化LLM客户端
        self.api_key = api_key or os.getenv("DEEPSEEK_API_KEY")
        if not self.api_key:
            raise ValueError("DEEPSEEK_API_KEY未设置")

        self.client = OpenAI(
            api_key=self.api_key,
            base_url="https://api.deepseek.com/v1"
        )
        self.model = model
        self.max_iterations = max_iterations
        self.temperature = temperature
        self.progress_callback = progress_callback
        
        logger.info(f"LLM客户端初始化完成，模型: {model}")

        # 2. 初始化Tools（延迟加载，用时再初始化）
        self._error_identifier = None
        self._rag_searcher = None
        self._context_manager = None
        self._code_fixer = None
        self._docker_executor = None
        self._multi_file_fixer = None

        # 3. 初始化优化模块
        self.loop_detector = LoopDetector(
            max_similar_code=2,  # 连续2次相似代码视为循环
            max_same_error=3     # 连续3次相同错误视为循环
        )
        self.token_manager = TokenManager(
            max_context_tokens=6000,
            reserve_for_response=2000
        )

        logger.info("ReActAgent初始化完成（含LoopDetector, TokenManager）")

    # ============ 延迟加载Tools ============
    @property
    def error_identifier(self):
        """延迟加载ErrorIdentifier"""
        if self._error_identifier is None:
            from src.agent.tools.error_identifier import ErrorIdentifier
            self._error_identifier = ErrorIdentifier()
        return self._error_identifier
    
    @property
    def rag_searcher(self):
        """延迟加载RAGSearcher"""
        if self._rag_searcher is None:
            from src.agent.tools.rag_searcher import RAGSearcher
            self._rag_searcher = RAGSearcher()
        return self._rag_searcher
    
    @property
    def code_fixer(self):
        """延迟加载CodeFixer"""
        if self._code_fixer is None:
            from src.agent.tools.code_fixer import CodeFixer
            self._code_fixer = CodeFixer(api_key=self.api_key)
        return self._code_fixer
    
    @property
    def docker_executor(self):
        """延迟加载DockerExecutor"""
        if self._docker_executor is None:
            from src.agent.tools.docker_executor import DockerExecutor
            self._docker_executor = DockerExecutor()
        return self._docker_executor
    
    @property
    def multi_file_fixer(self):
        """延迟加载MultiFileFixer"""
        if self._multi_file_fixer is None:
            from src.agent.tools.multi_file_fixer import MultiFileFixer
            self._multi_file_fixer = MultiFileFixer()
        return self._multi_file_fixer
    

    def _get_context_manager(self, project_path: str):
        """获取ContextManager（需要project_path）"""
        from src.agent.context_manager import ContextManager
        return ContextManager(project_path)
        

    def debug(
        self,
        buggy_code: str,
        error_traceback: str,
        project_path: Optional[str] = None,
        max_iterations: int = 20
    ) -> Dict[str, Any]:
        """
        执行ReAct Debug流程
        
        Args:
            buggy_code: 有错误的代码
            error_traceback: 错误traceback
            project_path: 项目路径（跨文件调试用）
            max_iterations: 最大迭代次数
            
        Returns:
            {
                "success": bool,
                "fixed_code": str,
                "explanation": str,
                "iterations": int,
                "history": [...]  # Thought-Action-Observation历史
            }
        """
        # 1. 输入验证
        if not buggy_code or not isinstance(buggy_code, str):
            raise ValueError("buggy_code必须是非空字符串")
        if not error_traceback or not isinstance(error_traceback, str):
            raise ValueError("error_traceback必须是非空字符串")

        logger.info("=" * 60)
        logger.info("开始ReAct Debug")
        logger.info(f"代码长度: {len(buggy_code)}")
        logger.info(f"错误信息: {error_traceback[:100]}...")
        logger.info(f"项目路径: {project_path or '(无)'}")
        logger.info("=" * 60)

        # 2. 运行ReAct循环
        result = self._run_react_loop(
            buggy_code=buggy_code,
            error_traceback=error_traceback,
            project_path=project_path
        )

        # 3. 记录结果
        if result.get("success"):
            logger.info(f"✅ Debug成功，迭代次数: {result.get('iterations')}")
        else:
            logger.warning(f"❌ Debug失败: {result.get('error', '未知错误')}")
        
        return result

    def _run_react_loop(
        self,
        buggy_code: str,
        error_traceback: str,
        project_path: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        运行ReAct循环
        
        Args:
            buggy_code: 有错误的代码
            error_traceback: 错误traceback
            project_path: 项目路径
            
        Returns:
            {
                "success": bool,
                "fixed_code": str,
                "explanation": str,
                "iterations": int,
                "history": list
            }
        """
        # 1. 初始化上下文
        context = {
            "buggy_code": buggy_code,
            "error_traceback": error_traceback,
            "project_path": project_path,
            "error_file": "main.py",      # ⭐ 添加：主文件名
            "last_fixed_code": None,
            "related_files": {}           # ⭐ 添加：相关文件字典
        }

        # ⭐ 优化：重置循环检测器
        self.loop_detector.reset()

        messages = [
            {
                "role": "system",
                "content": self.SYSTEM_PROMPT.format(
                    tools_description=self.TOOLS_DESCRIPTION
                )
            },
            {
                "role": "user",
                "content": f"""请帮我修复以下Python代码错误：

## 错误代码
```python
{buggy_code}
```

## 错误信息
```
{error_traceback}
```

{"## 项目路径" + chr(10) + project_path if project_path else "（单文件，无项目路径）"}

请使用ReAct模式，逐步分析并修复这个错误。"""
            }
        ]

        # 3. 记录历史
        history = []

        # ⭐ 新增：工具调用历史（用于循环检测）
        tool_history = []

        # 4. ReAct循环
        for iteration in range(1, self.max_iterations + 1):
            logger.info(f"=== 迭代 {iteration}/{self.max_iterations} ===")

            #⭐ 新增：调用进度回调
            if self.progress_callback:
                self.progress_callback(iteration, "thinking")
            # 4.1 调用LLM
            try:
                llm_response = self._call_llm(messages)
                logger.info(f"LLM响应: {llm_response[:100]}...")
                # ⭐ 新增：显示Thought（verbose模式）
                if self.progress_callback:
                    thought_match = re.search(r'Thought:\s*(.+?)(?=\nAction:|$)', llm_response, re.DOTALL)
                    if thought_match:
                        self.progress_callback(iteration, "thought", {"thought": thought_match.group(1).strip()})
            except Exception as e:
                logger.error(f"LLM调用失败: {e}")
                return {
                    "success": False,
                    "error": str(e),
                    "iterations": iteration,
                    "history": history,
                    "loop_detector_stats": self.loop_detector.get_stats()  # ⭐ 优化统计
                }

            # 4.2 解析Action
            action = self._parse_action(llm_response)
            
            # 记录到历史
            history.append({
                "iteration": iteration,
                "llm_response": llm_response,
                "action": action
            })

            # 4.3 检查是否完成
            if action["type"] == "final":
                logger.info("✅ 任务完成")
                result = action.get("result", {})
                return {
                    "success": True,
                    "fixed_code": result.get("fixed_code", context.get("last_fixed_code", "")),
                    "explanation": result.get("explanation", ""),
                    "iterations": iteration,
                    "history": history,
                    "loop_detector_stats": self.loop_detector.get_stats()  # ⭐ 优化统计
                }

            # 4.4 检查解析错误
            if action["type"] == "error":
                logger.warning(f"解析错误: {action.get('message')}")
                # 告诉LLM格式不对，继续
                messages.append({"role": "assistant", "content": llm_response})
                messages.append({
                    "role": "user",
                    "content": f"格式错误：{action.get('message')}\n请严格按照格式输出：Thought -> Action -> Action Input"
                })
                continue

            # 4.5 执行工具
            tool_name = action.get("tool", "")
            params = action.get("params", {})
            
            # ⭐ 新增：显示工具调用（verbose模式）
            if self.progress_callback:
                self.progress_callback(iteration, "tool_call", {"tool": tool_name})
            
            # ⭐ 新增：循环检测
            tool_history.append(tool_name)
            if len(tool_history) >= 3:
                # 检查最近3次调用
                recent_3 = tool_history[-3:]
                
                # fix_code和execute_code允许重复，其他工具不允许
                if len(set(recent_3)) == 1 and recent_3[0] not in ["fix_code", "execute_code"]:
                    logger.warning(f"⚠️ 检测到循环：连续3次调用 {recent_3[0]}")
                    
                    # 给LLM一个警告，让它换思路
                    messages.append({"role": "assistant", "content": llm_response})
                    messages.append({
                        "role": "user",
                        "content": f"⚠️ 警告：你已经连续3次调用 {recent_3[0]}，这没有帮助。请换一个工具或思路。"
                    })
                    
                    # 跳过本次工具执行，直接进入下一轮
                    continue

            observation = self._execute_tool(tool_name, params, context)
            logger.info(f"Observation: {observation[:100]}...")

            # ⭐ 新增：显示结果（verbose模式）
            if self.progress_callback:
                self.progress_callback(iteration, "observation", {"result": observation})
            # 记录observation
            history[-1]["observation"] = observation
            
            # 4.6 更新消息历史
            messages.append({"role": "assistant", "content": llm_response})
            messages.append({
                "role": "user",
                "content": f"Observation: {observation}"
            })

        # 5. 超过最大迭代次数
        logger.warning(f"超过最大迭代次数 {self.max_iterations}")
        return {
            "success": False,
            "error": f"超过最大迭代次数 {self.max_iterations}",
            "fixed_code": context.get("last_fixed_code", ""),
            "iterations": self.max_iterations,
            "history": history,
            "loop_detector_stats": self.loop_detector.get_stats()  # ⭐ 优化统计
        }
            




    def _call_llm(self, messages: List[Dict]) -> str:
        """
        调用LLM
        
        Args:
            messages: OpenAI格式的消息列表
            
        Returns:
            LLM的响应文本
        """
        try:
            response = self.client.chat.completions.create(
                model=self.model,
                messages=messages,
                temperature=self.temperature,
                max_tokens=2000
            )
            return response.choices[0].message.content
        
        except Exception as e:
            logger.error(f"LLM调用失败: {e}", exc_info=True)
            raise RuntimeError(f"LLM调用失败: {e}")

    def _parse_action(self, llm_response: str) -> Dict:
        """
        解析LLM响应，提取Action
        """
        import json
        import re
        
        logger.debug(f"解析LLM响应: {llm_response[:200]}...")
        
        # 1. 检查是否是Final Answer
        final_match = re.search(r'Final Answer:\s*', llm_response)
        if final_match:
            # 从Final Answer:之后提取JSON
            json_start = final_match.end()
            json_str = self._extract_json(llm_response[json_start:])
            if json_str:
                try:
                    result = json.loads(json_str)
                    logger.info("检测到Final Answer")
                    return {"type": "final", "result": result}
                except json.JSONDecodeError:
                    pass
            # JSON解析失败，返回原文
            return {"type": "final", "result": {"raw_response": llm_response}}
        
        # 2. 解析Action
        action_match = re.search(r'Action:\s*(\w+)', llm_response)
        if not action_match:
            return {"type": "error", "message": "未找到Action", "raw_response": llm_response}
        
        tool_name = action_match.group(1).strip()
        
        # 3. 解析Action Input
        input_match = re.search(r'Action Input:\s*', llm_response)
        params = {}
        if input_match:
            json_start = input_match.end()
            json_str = self._extract_json(llm_response[json_start:])
            if json_str:
                try:
                    params = json.loads(json_str)
                except json.JSONDecodeError as e:
                    logger.warning(f"Action Input JSON解析失败: {e}")
                    params = {}
        
        logger.info(f"解析到Action: {tool_name}, 参数: {list(params.keys())}")
        return {"type": "action", "tool": tool_name, "params": params}


    def _extract_json(self, text: str) -> Optional[str]:
        """
        从文本中提取完整的JSON对象（处理嵌套括号）
        
        Args:
            text: 以JSON开头的文本
            
        Returns:
            完整的JSON字符串，如果提取失败返回None
        """
        text = text.strip()
        if not text.startswith('{'):
            return None
        
        depth = 0
        in_string = False
        escape = False
        
        for i, char in enumerate(text):
            if escape:
                escape = False
                continue
            
            if char == '\\':
                escape = True
                continue
            
            if char == '"' and not escape:
                in_string = not in_string
                continue
            
            if in_string:
                continue
            
            if char == '{':
                depth += 1
            elif char == '}':
                depth -= 1
                if depth == 0:
                    return text[:i+1]
        
        return None

    def _execute_tool(
        self,
        tool_name: str,
        params: Dict[str, Any],
        context: Dict[str, Any]
    ) -> str:
        """
        执行指定工具，返回Observation
        
        Args:
            tool_name: 工具名称
            params: 工具参数
            context: 运行时上下文（包含project_path等）
            
        Returns:
            工具执行结果的字符串描述（作为Observation返回给LLM）
        """
        logger.info(f"执行工具: {tool_name}, 参数: {list(params.keys())}")
        
        try:
            # -------- 1. analyze_error --------
            if tool_name == "analyze_error":
                traceback = params.get("traceback", "")
                if not traceback:
                    return "错误：缺少traceback参数"
                
                result = self.error_identifier.identify(traceback)
                return (
                    f"错误分析结果:\n"
                    f"- 错误类型: {result.get('error_type')}\n"
                    f"- 错误信息: {result.get('error_message')}\n"
                    f"- 文件: {result.get('file')}\n"
                    f"- 行号: {result.get('line')}"
                )
            
            # -------- 2. search_solutions --------
            elif tool_name == "search_solutions":
                query = params.get("query", "")
                top_k = params.get("top_k", 5)
                if not query:
                    return "错误：缺少query参数"
                
                results = self.rag_searcher.search(query, top_k=top_k)
                
                if not results:
                    return "未找到相关解决方案"
                
                # 格式化结果
                output = f"找到 {len(results)} 个相关解决方案:\n"
                for i, r in enumerate(results[:3], 1):
                    content = r.get("content", "")[:300]
                    similarity = r.get("similarity", 0)
                    output += f"\n方案{i} (相似度:{similarity:.2f}):\n{content}...\n"
                
                context["rag_solutions"] = results
                return output
            
            # -------- 3. get_project_context --------
            elif tool_name == "get_project_context":
                project_path = context.get("project_path") or params.get("project_path")
                error_file = params.get("error_file") or context.get("error_file")
                error_line = params.get("error_line") or context.get("error_line", 1)
                error_type = params.get("error_type", "NameError")
                error_name = params.get("error_name", "")
                
                if not project_path:
                    return "错误：缺少project_path参数"
                if not error_file:
                    return "错误：缺少error_file参数（错误发生的文件）"
                
                cm = self._get_context_manager(project_path)
                
                try:
                    ctx = cm.get_context_for_error(
                        error_file=error_file,
                        error_line=int(error_line),
                        error_type=error_type,
                        undefined_name=error_name if error_name else None
                    )
                except ValueError as e:
                    return f"错误：{str(e)}"
                
                # ⭐ 优化：使用 TokenManager 压缩上下文
                ctx = self.token_manager.compress_context(ctx)

                # 保存related_files到context，供execute_code使用
                context["code_context"] = ctx
                context["related_files"] = ctx.get("related_files", {})
                
                # 格式化结果
                output = "项目上下文分析结果:\n"
                
                if ctx.get("related_symbols"):
                    output += "\n相关符号定义:\n"
                    for name, info in ctx["related_symbols"].items():
                        output += f"- {name} ({info.get('type')}) 在 {info.get('file')}\n"
                        if info.get("definition"):
                            output += f"  定义:\n{info['definition'][:200]}...\n"
                
                if ctx.get("import_suggestions"):
                    output += "\nImport建议:\n"
                    for suggestion in ctx["import_suggestions"]:
                        output += f"- {suggestion}\n"
                
                if not ctx.get("related_symbols") and not ctx.get("import_suggestions"):
                    output += "未找到相关上下文信息"
                
                return output
            
            # -------- 4. fix_code --------
            elif tool_name == "fix_code":
                buggy_code = params.get("buggy_code") or context.get("buggy_code")
                error_message = params.get("error_message", "")
                code_context = context.get("context")
                rag_solutions = context.get("rag_solutions")
                
                if not buggy_code:
                    return "错误：缺少buggy_code参数"
                if not error_message:
                    return "错误：缺少error_message参数"
                
                # ⭐ 新增：验证rag_solutions格式
                if rag_solutions and not isinstance(rag_solutions, list):
                    rag_solutions = None  # 格式不对就忽略
                    logger.warning("fix_code参数rag_solutions格式错误，已忽略")
                
                result = self.code_fixer.fix_code(
                    buggy_code=buggy_code,
                    error_message=error_message,
                    context=code_context,
                    rag_solutions=rag_solutions
                )
                
                # 保存到context供后续使用
                fixed_code = result.get("fixed_code", "")
                context["last_fixed_code"] = fixed_code

                # ⭐ 优化：使用 LoopDetector 检测重复修复
                loop_check = self.loop_detector.check({
                    'fixed_code': fixed_code,
                    'explanation': result.get('explanation', '')
                })

                if loop_check['is_loop']:
                    logger.warning(f"⚠️ LoopDetector 检测到循环: {loop_check['message']}")
                    return (
                        f"⚠️ 循环警告: {loop_check['message']}\n"
                        f"建议: {loop_check['suggestion']}\n"
                        f"请尝试完全不同的修复思路。"
                    )

                return (
                    f"代码修复完成:\n"
                    f"修复说明: {result.get('explanation', '')}\n"
                    f"变更: {result.get('changes', [])}\n"
                    f"修复后代码已保存，可以使用execute_code验证"
                )
            
            # -------- 5. execute_code --------
            elif tool_name == "execute_code":
                # 确定主文件名
                main_file = context.get("error_file", "main.py")
                
                # 获取要执行的主文件代码（优先级：参数 > related_files > last_fixed_code > buggy_code）
                code = params.get("code")
                
                if not code:
                    # 优先从related_files获取主文件（fix_multi_file会更新到这里）
                    if main_file in context.get("related_files", {}):
                        code = context["related_files"][main_file]
                    elif context.get("last_fixed_code"):
                        code = context["last_fixed_code"]
                    else:
                        code = context.get("buggy_code")
                
                if not code:
                    return "错误：缺少code参数，也没有之前的修复代码"

                # 获取相关文件（排除主文件，避免重复写入）
                related_files = {}
                for filename, content in context.get("related_files", {}).items():
                    if filename != main_file:
                        related_files[filename] = content
                
                # 执行代码
                if related_files:
                    # 多文件执行
                    result = self.docker_executor.execute_with_context(
                        main_code=code,
                        related_files=related_files,
                        main_filename=main_file
                    )
                else:
                    # 单文件执行
                    result = self.docker_executor.execute(code)
                
                if result.get("success"):
                    return (
                        f"✅ 执行成功!\n"
                        f"输出: {result.get('stdout', '(无输出)')}"
                    )
                else:
                    # ⭐ 优化：记录失败错误到 LoopDetector
                    error_msg = result.get('stderr', '未知错误')
                    self.loop_detector.check({
                        'fixed_code': code,
                        'error': error_msg
                    })

                    return (
                        f"❌ 执行失败\n"
                        f"错误: {error_msg}\n"
                        f"退出码: {result.get('exit_code')}"
                    )

            # -------- 6. fix_multi_file --------
            elif tool_name == "fix_multi_file":
                error_file = params.get("error_file")
                error_message = params.get("error_message", "") or context.get("error_traceback", "")
                
                if not error_file:
                    return "错误：缺少error_file参数"
                if not error_message:
                    return "错误：缺少error_message参数"
                
                # 获取所有文件（从context中获取，由get_project_context填充）
                all_files = context.get("related_files", {}).copy()
                
                # 加上出错的主文件本身
                main_file = context.get("error_file", "main.py")
                if context.get("buggy_code"):
                    all_files[main_file] = context["buggy_code"]
                
                if not all_files:
                    return "错误：没有可用的项目文件，请先调用get_project_context"
                
                # 调用多文件修复器
                result = self.multi_file_fixer.fix(
                    error_file=error_file,
                    error_message=error_message,
                    all_files=all_files
                )
                
                if not result.get("success"):
                    return f"多文件修复失败: {result.get('error', '未知错误')}"
                
                # ⭐ 关键修复：所有文件都更新到related_files
                fixed_files = result.get("fixed_files", {})
                for filename, content in fixed_files.items():
                    context["related_files"][filename] = content
                
                # ⭐ 只有主文件才更新last_fixed_code
                if main_file in fixed_files:
                    context["last_fixed_code"] = fixed_files[main_file]
                
                # 格式化输出
                output = f"多文件修复完成:\n"
                output += f"分析: {result.get('analysis', '')}\n"
                output += f"修改的文件: {list(fixed_files.keys())}\n"
                output += f"说明: {result.get('explanation', '')}\n"
                output += f"\n修复后的文件已更新，可以使用execute_code验证"
                
                return output
            
            # -------- 未知工具 --------
            else:
                return f"错误：未知工具 '{tool_name}'，可用工具: analyze_error, search_solutions, get_project_context, fix_code, execute_code"
        
        except Exception as e:
            logger.error(f"工具执行失败: {tool_name}, 错误: {e}", exc_info=True)
            return f"工具执行出错: {str(e)}"

