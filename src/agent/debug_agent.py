import sys
from pathlib import Path

# 添加项目根目录到路径
sys.path.append(str(Path(__file__).parent.parent))

from src.agent.tools.error_identifier import ErrorIdentifier
from src.agent.tools.rag_searcher import RAGSearcher
from src.agent.tools.code_fixer import CodeFixer
from src.agent.tools.docker_executor  import DockerExecutor



from typing import Dict, List, Optional, Any

import logging
logger = logging.getLogger(__name__)

class DebugAgent:
    """
    DebugAgent是一个调试代理，负责识别错误、检索解决方案、修复代码并执行。
    """

    def __init__(
        self,
        api_key: str,
        project_path: Optional[str] = None
    ):
        """
        初始化Debug Agent
        
        Args:
            api_key: DeepSeek API密钥
            project_path: 项目路径（可选，用于多文件上下文提取）
        """
        logger.info("初始化Debug Agent...")
        
        # 保存项目路径
        self.project_path = project_path
        
        # 初始化ContextManager（如果提供了项目路径）
        self.context_manager = None
        if project_path:
            logger.info(f"初始化ContextManager: {project_path}")
            from src.agent.context_manager import ContextManager
            self.context_manager = ContextManager(project_path)
        else:
            logger.info("未提供project_path，将进行单文件debug")
        
        # 初始化工具
        self.error_identifier = ErrorIdentifier()
        self.rag_searcher = RAGSearcher()
        self.code_fixer = CodeFixer(api_key=api_key)
        self.docker_executor = DockerExecutor()
        
        logger.info("Debug Agent初始化完成")

    def debug(
        self,
        buggy_code: str,
        error_traceback: str,
        error_file: Optional[str] = None,
        max_retries: int = 2
    ) -> Dict[str, Any]:
        """
        执行完整的Debug流程

        Args:
            buggy_code: 包含错误的原始代码
            error_traceback: 错误的Traceback信息
            max_retries: 最大重试次数, 默认2次
        
        Returns:
            Dict: 包含以下字段的字典
                - success (bool)：是否修复成功
                - original_error (dict): 原始错误信息
                - solutions (list): 检索到的解决方案
                - attempts (list): 所有尝试的记录
                - final_code (str): 最终代码
                - total_attempts (int): 总尝试次数

        Raises:
            ValueError: 如果输入参数无效
            RuntimeError: 如果修复或执行过程中发生错误
        """

        # 1. 输入验证
        logger.info("开始Debug流程...")

        if not buggy_code or not isinstance(buggy_code, str):
            raise ValueError("buggy_code必须是非空字符串")
        
        if not error_traceback or not isinstance(error_traceback, str):
            raise ValueError("error_traceback必须是非空字符串")
        
        if max_retries <= 0 or not isinstance(max_retries, int):
            raise ValueError("max_retries必须是大于0的整数")

        # 2. 错误识别
        logger.info("步骤1: 识别错误类型...")

        try:
            error_info = self.error_identifier.identify(error_traceback)
            logger.info(f"错误识别完成，错误类型: {error_info['error_type']}")
        except Exception as e:
            logger.error(f"错误识别失败: {e}", exc_info=True)
            raise RuntimeError(f"错误识别失败: {e}")

        # 3. 提取上下文（如果有ContextManager）
        context = None
        if self.context_manager and error_file:
            logger.info("步骤2: 提取项目上下文")
            try:
                # 从error_info中提取undefined_name
                undefined_name = self._extract_undefined_name(
                    error_info['error_type'],
                    error_info['error_message']
                )
                
                context = self.context_manager.get_context_for_error(
                    error_file=error_file,
                    error_line=error_info.get('line', 1),
                    error_type=error_info['error_type'],
                    undefined_name=undefined_name
                )
                
                logger.info(f"找到 {len(context.get('related_symbols', {}))} 个相关符号")
            except Exception as e:
                logger.warning(f"上下文提取失败: {e}")
                context = None
        else:
            logger.info("步骤2: 跳过上下文提取（单文件模式）")

        # 4. RAG检索解决方案
        logger.info("步骤3: 检索解决方案...")

        try:
            query = f"{error_info['error_type']}: {error_info['error_message']}"
            solutions = self.rag_searcher.search(
                query=query,
                top_k=10
            )
            logger.info(f"检索到{len(solutions)}个解决方案")
        except Exception as e:
            logger.error(f"RAG检索失败: {e}", exc_info=True)
            solutions = []
            logger.warning("将在没有RAG方案的情况下继续尝试修复")

        # 5. 重试循环
        attempts = []  # 记录所有尝试
        success = False  # 是否成功
        final_code = buggy_code  # 初始化为原始代码
        
        # ⭐ 关键：累积失败历史，但始终基于原始代码修复
        failure_history = []  # 记录每次失败的尝试信息
        
        logger.info(f"开始重试循环，最大{max_retries + 1}次")

        for i in range(max_retries + 1):
            attempt_number = i + 1
            logger.info(f"第{attempt_number}次尝试修复...")
            
            # ⭐ 构建错误提示（包含失败历史）
            if i == 0:
                # 第1次：只有原始错误
                current_error = f"{error_info['error_type']}: {error_info['error_message']}"
            else:
                # 第2次及以后：添加失败历史
                history_text = self._format_failure_history(failure_history)
                current_error = f"""原始错误: {error_info['error_type']}: {error_info['error_message']}

    已尝试的修复方案（都失败了）：
    {history_text}

    请分析失败原因，尝试完全不同的修复思路。"""
            
            logger.info(f"当前错误提示长度: {len(current_error)} 字符")

            # 5.1 调用CodeFixer生成修复（⭐ 始终基于原始代码）
            try:
                fixed_result = self.code_fixer.fix_code(
                    buggy_code=buggy_code,  # ⭐ 关键：始终是原始代码，不是上次的修复！
                    error_message=current_error,
                    context=context,
                    rag_solutions=solutions if i == 0 else None  # 只在第一次提供RAG方案
                )

                fixed_code = fixed_result["fixed_code"]
                explanation = fixed_result["explanation"]
                changes = fixed_result["changes"]
                
                logger.info("生成代码修复成功")
            except Exception as e:
                logger.error(f"CodeFixer修复失败: {e}", exc_info=True)
                # 记录失败的尝试
                attempt_record = {
                    'attempt_number': attempt_number,
                    'fixed_code': None,
                    'explanation': f"修复生成失败: {str(e)}",
                    'changes': [],
                    'verification': {'success': False, 'error': str(e)}
                }
                attempts.append(attempt_record)
                
                # 添加到失败历史
                failure_history.append({
                    'attempt': attempt_number,
                    'explanation': f"修复生成失败: {str(e)}",
                    'new_error': str(e)
                })
                continue

            # 5.2 在docker中验证修复
            try:
                logger.info("开始在docker中验证修复代码...")
                verification = self.docker_executor.execute(code=fixed_code)
                logger.info(f"验证完成，成功: {verification['success']}")

            except Exception as e:
                logger.error(f"docker验证修复失败: {e}", exc_info=True)
                verification = {
                    "success": False,
                    "stdout": "",
                    "stderr": str(e),
                    "exit_code": -1
                }

            # 5.3 记录本次尝试
            attempt_record = {
                'attempt_number': attempt_number,
                'fixed_code': fixed_code,
                'explanation': explanation,
                'changes': changes,
                'verification': verification
            }
            attempts.append(attempt_record)

            # 5.4 判断是否成功
            if verification['success']:
                success = True
                final_code = fixed_code
                logger.info("✅ 修复成功！")
                break
            else:
                logger.warning(f"❌ 第 {attempt_number} 次尝试失败")
                
                # ⭐ 记录失败历史（供下一次尝试参考）
                failure_info = {
                    'attempt': attempt_number,
                    'explanation': explanation[:200],  # 限制长度
                    'changes': changes[:3] if changes else [],  # 只记录前3个改动
                    'new_error': verification.get('stderr', '未知错误')[:300]  # 限制长度
                }
                failure_history.append(failure_info)
                
                logger.info(f"已记录失败历史，下次将尝试不同思路")

        # 循环结束，构建返回结果
        logger.info(f"Debug流程完成，成功: {success}, 总尝试次数: {len(attempts)}")

        if success:
            logger.info(f"✅ Debug成功！最终代码已生成")
            final_code = attempts[-1]['fixed_code']
            explanation = attempts[-1].get('explanation', '')
            changes = attempts[-1].get('changes', [])
            execution_result = attempts[-1].get('execution_result', {})
        else:
            logger.info(f"❌ Debug失败，已尝试{len(attempts)}次")
            final_code = buggy_code
            explanation = ''
            changes = []
            execution_result = attempts[-1].get('execution_result', {}) if attempts else {} 
        
        return {
            "success": success,
            "original_error": error_info,
            "solutions": solutions,
            "attempts": attempts,
            "final_code": final_code,
            "total_attempts": len(attempts)
        }

    def _format_failure_history(self, failure_history: List[Dict]) -> str:
        """
        格式化失败历史为可读文本
        
        Args:
            failure_history: 失败历史列表
            
        Returns:
            格式化的文本
        """
        if not failure_history:
            return "无"
        
        formatted = []
        for fail in failure_history:
            attempt_num = fail['attempt']
            explanation = fail['explanation']
            new_error = fail['new_error']
            
            formatted.append(
                f"第{attempt_num}次尝试:\n"
                f"  修复思路: {explanation}\n"
                f"  执行结果: 失败\n"
                f"  新错误: {new_error[:200]}..."
            )
        
        return "\n\n".join(formatted)

    def _extract_undefined_name(
        self,
        error_type: str,
        error_message: str
    ) -> Optional[str]:
        """
        从错误信息中提取未定义的名称
        
        Args:
            error_type: 错误类型
            error_message: 错误信息
            
        Returns:
            未定义的名称，如果提取失败返回None
        """
        if error_type == "NameError":
            # NameError: name 'calculate' is not defined
            import re
            match = re.search(r"name '(\w+)' is not defined", error_message)
            if match:
                return match.group(1)
        
        elif error_type in ["ImportError", "ModuleNotFoundError"]:
            # ModuleNotFoundError: No module named 'utils'
            import re
            match = re.search(r"No module named '(\w+)'", error_message)
            if match:
                return match.group(1)
        
        return None