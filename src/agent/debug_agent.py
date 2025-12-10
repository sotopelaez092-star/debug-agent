"""
DebugAgent - AI 调试代理

核心调试流程编排器，集成所有模块完成自动化调试
"""

import sys
from pathlib import Path

# 添加项目根目录到路径
sys.path.append(str(Path(__file__).parent.parent))

from typing import Dict, List, Optional, Any
import logging

from src.agent.tools.error_identifier import ErrorIdentifier
from src.agent.tools.rag_searcher import RAGSearcher
from src.agent.tools.code_fixer import CodeFixer
from src.agent.tools.docker_executor import DockerExecutor
from src.agent.context_manager import ContextManager
from src.agent.loop_detector import LoopDetector
from src.agent.token_manager import TokenManager
from src.agent.config_loader import ConfigLoader

logger = logging.getLogger(__name__)


class DebugAgent:
    """
    DebugAgent - 调试代理

    功能：
    1. 识别错误类型和位置
    2. 提取跨文件上下文
    3. 检索相关解决方案
    4. 生成代码修复
    5. 在 Docker 中验证
    6. 循环检测和重试

    Attributes:
        api_key: DeepSeek API 密钥
        project_path: 项目路径
        context_manager: 上下文管理器
        loop_detector: 循环检测器
        token_manager: Token 管理器
        config: 配置加载器
    """

    def __init__(
        self,
        api_key: str,
        project_path: Optional[str] = None,
        config_path: Optional[str] = None
    ):
        """
        初始化 Debug Agent

        Args:
            api_key: DeepSeek API 密钥
            project_path: 项目路径（可选，用于多文件上下文提取）
            config_path: 配置文件路径（可选）
        """
        logger.info("初始化 DebugAgent...")

        # 保存配置
        self.api_key = api_key
        self.project_path = project_path

        # 加载项目配置
        self.config = None
        if project_path:
            try:
                self.config = ConfigLoader(project_path)
                logger.info(f"加载项目配置: {self.config}")
            except Exception as e:
                logger.warning(f"加载配置失败: {e}")

        # 初始化上下文管理器（懒加载版本）
        self.context_manager = None
        if project_path:
            logger.info(f"初始化 ContextManager: {project_path}")
            self.context_manager = ContextManager(project_path)
        else:
            logger.info("未提供 project_path，将进行单文件调试")

        # 初始化循环检测器
        self.loop_detector = LoopDetector(
            max_similar_code=2,
            max_same_error=3
        )

        # 初始化 Token 管理器
        self.token_manager = TokenManager(
            max_context_tokens=6000,
            reserve_for_response=2000
        )

        # 初始化工具
        self.error_identifier = ErrorIdentifier()
        self.code_fixer = CodeFixer(api_key=api_key)
        self.docker_executor = DockerExecutor(
            timeout=self.config.get_timeout() if self.config else 30
        )

        # RAG 搜索器（可选）
        self.rag_searcher = None
        if not self.config or self.config.is_rag_enabled():
            try:
                self.rag_searcher = RAGSearcher()
                logger.info("RAG 搜索器初始化成功")
            except Exception as e:
                logger.warning(f"RAG 搜索器初始化失败: {e}")

        logger.info("DebugAgent 初始化完成")

    def debug(
        self,
        buggy_code: str,
        error_traceback: str,
        error_file: Optional[str] = None,
        max_retries: Optional[int] = None
    ) -> Dict[str, Any]:
        """
        执行完整的调试流程

        Args:
            buggy_code: 包含错误的原始代码
            error_traceback: 错误的 Traceback 信息
            error_file: 错误文件路径（可选）
            max_retries: 最大重试次数（可选，默认从配置读取）

        Returns:
            调试结果字典，包含：
                - success: 是否修复成功
                - original_error: 原始错误信息
                - solutions: 检索到的解决方案
                - attempts: 所有尝试的记录
                - final_code: 最终代码
                - total_attempts: 总尝试次数

        Raises:
            ValueError: 如果输入参数无效
            RuntimeError: 如果修复过程中发生错误
        """
        # 1. 输入验证
        logger.info("开始调试流程...")

        if not buggy_code or not isinstance(buggy_code, str):
            raise ValueError("buggy_code 必须是非空字符串")

        if not error_traceback or not isinstance(error_traceback, str):
            raise ValueError("error_traceback 必须是非空字符串")

        # 获取最大重试次数
        if max_retries is None:
            max_retries = self.config.get_max_retries() if self.config else 2

        if max_retries <= 0 or not isinstance(max_retries, int):
            raise ValueError("max_retries 必须是大于 0 的整数")

        # 重置循环检测器
        self.loop_detector.reset()

        # 2. 错误识别
        logger.info("步骤 1: 识别错误类型...")
        try:
            error_info = self.error_identifier.identify(error_traceback)
            logger.info(f"错误识别完成: {error_info['error_type']}")
        except Exception as e:
            logger.error(f"错误识别失败: {e}", exc_info=True)
            raise RuntimeError(f"错误识别失败: {e}")

        # 3. 提取上下文
        context = None
        if self.context_manager and error_file:
            logger.info("步骤 2: 提取项目上下文...")
            try:
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

                # 压缩上下文
                context = self.token_manager.compress_context(context)

                logger.info(f"找到 {len(context.get('related_symbols', {}))} 个相关符号")
            except Exception as e:
                logger.warning(f"上下文提取失败: {e}")
                context = None
        else:
            logger.info("步骤 2: 跳过上下文提取（单文件模式）")

        # 4. RAG 检索解决方案
        solutions = []
        if self.rag_searcher:
            logger.info("步骤 3: 检索解决方案...")
            try:
                query = f"{error_info['error_type']}: {error_info['error_message']}"
                solutions = self.rag_searcher.search(query=query, top_k=10)

                # 压缩解决方案
                solutions = self.token_manager.compress_rag_solutions(
                    solutions, max_solutions=3
                )

                logger.info(f"检索到 {len(solutions)} 个解决方案")
            except Exception as e:
                logger.error(f"RAG 检索失败: {e}", exc_info=True)
                logger.warning("将在没有 RAG 方案的情况下继续尝试修复")
        else:
            logger.info("步骤 3: 跳过 RAG 检索")

        # 5. 重试循环
        attempts = []
        success = False
        final_code = buggy_code
        failure_history = []

        logger.info(f"开始重试循环，最大 {max_retries + 1} 次")

        for i in range(max_retries + 1):
            attempt_number = i + 1
            logger.info(f"第 {attempt_number} 次尝试修复...")

            # 构建错误提示
            if i == 0:
                current_error = f"{error_info['error_type']}: {error_info['error_message']}"
            else:
                history_text = self._format_failure_history(failure_history)
                current_error = f"""原始错误: {error_info['error_type']}: {error_info['error_message']}

已尝试的修复方案（都失败了）：
{history_text}

请分析失败原因，尝试完全不同的修复思路。"""

            # 5.1 调用 CodeFixer 生成修复
            try:
                fixed_result = self.code_fixer.fix_code(
                    buggy_code=buggy_code,  # 始终基于原始代码
                    error_message=current_error,
                    context=context,
                    rag_solutions=solutions if i == 0 else None
                )

                fixed_code = fixed_result["fixed_code"]
                explanation = fixed_result["explanation"]
                changes = fixed_result["changes"]

                logger.info("代码修复生成成功")

            except Exception as e:
                logger.error(f"CodeFixer 修复失败: {e}", exc_info=True)
                attempt_record = {
                    'attempt_number': attempt_number,
                    'fixed_code': None,
                    'explanation': f"修复生成失败: {str(e)}",
                    'changes': [],
                    'verification': {'success': False, 'error': str(e)}
                }
                attempts.append(attempt_record)
                failure_history.append({
                    'attempt': attempt_number,
                    'explanation': f"修复生成失败: {str(e)}",
                    'new_error': str(e)
                })
                continue

            # 5.2 循环检测
            loop_check = self.loop_detector.check({
                'fixed_code': fixed_code,
                'explanation': explanation,
            })

            if loop_check['is_loop']:
                logger.warning(f"检测到循环: {loop_check['message']}")
                attempt_record = {
                    'attempt_number': attempt_number,
                    'fixed_code': fixed_code,
                    'explanation': explanation,
                    'changes': changes,
                    'verification': {
                        'success': False,
                        'error': loop_check['message'],
                        'suggestion': loop_check['suggestion']
                    }
                }
                attempts.append(attempt_record)
                break  # 跳出循环

            # 5.3 在 Docker 中验证修复
            try:
                logger.info("在 Docker 中验证修复代码...")
                related_files = {}
                if context and 'related_files' in context:
                    related_files = context['related_files']

                verification = self.docker_executor.execute_with_context(
                    main_code=fixed_code,
                    related_files=related_files,
                    main_filename="main.py"
                )
                logger.info(f"验证完成，成功: {verification['success']}")

            except Exception as e:
                logger.error(f"Docker 验证失败: {e}", exc_info=True)
                verification = {
                    "success": False,
                    "stdout": "",
                    "stderr": str(e),
                    "exit_code": -1
                }

            # 5.4 记录本次尝试
            attempt_record = {
                'attempt_number': attempt_number,
                'fixed_code': fixed_code,
                'explanation': explanation,
                'changes': changes,
                'verification': verification
            }
            attempts.append(attempt_record)

            # 更新循环检测器
            self.loop_detector.check({
                'fixed_code': fixed_code,
                'error': verification.get('stderr', '') if not verification['success'] else '',
            })

            # 5.5 判断是否成功
            if verification['success']:
                success = True
                final_code = fixed_code
                logger.info("✅ 修复成功！")
                break
            else:
                logger.warning(f"❌ 第 {attempt_number} 次尝试失败")

                # 记录失败历史
                failure_info = {
                    'attempt': attempt_number,
                    'explanation': explanation[:200],
                    'changes': changes[:3] if changes else [],
                    'new_error': verification.get('stderr', '未知错误')[:300]
                }
                failure_history.append(failure_info)

        # 6. 构建返回结果
        logger.info(f"调试流程完成，成功: {success}，总尝试次数: {len(attempts)}")

        if success:
            final_code = attempts[-1]['fixed_code']
        else:
            final_code = buggy_code

        return {
            "success": success,
            "original_error": error_info,
            "solutions": solutions,
            "attempts": attempts,
            "final_code": final_code,
            "total_attempts": len(attempts),
            "loop_detector_stats": self.loop_detector.get_stats(),
        }

    def _format_failure_history(self, failure_history: List[Dict]) -> str:
        """格式化失败历史"""
        if not failure_history:
            return "无"

        formatted = []
        for fail in failure_history:
            attempt_num = fail['attempt']
            explanation = fail['explanation']
            new_error = fail['new_error']

            formatted.append(
                f"第 {attempt_num} 次尝试:\n"
                f"  修复思路: {explanation}\n"
                f"  执行结果: 失败\n"
                f"  新错误: {new_error[:200]}..."
            )

        return "\n\n".join(formatted)

    def _extract_undefined_name(
        self,
        error_type: str,
        error_message: str
    ) -> Optional[Any]:
        """从错误信息中提取未定义的名称"""
        import re

        if error_type == "NameError":
            match = re.search(r"name '(\w+)' is not defined", error_message)
            if match:
                return match.group(1)

        elif error_type in ["ImportError", "ModuleNotFoundError"]:
            # 函数导入错误
            match = re.search(r"cannot import name '(\w+)' from '(\w+)'", error_message)
            if match:
                return {
                    'function': match.group(1),
                    'module': match.group(2)
                }

            # 模块不存在
            match = re.search(r"No module named '(\w+)'", error_message)
            if match:
                return match.group(1)

        elif error_type == "AttributeError":
            # 对象属性错误
            match = re.search(r"'(\w+)' object has no attribute '(\w+)'", error_message)
            if match:
                return {
                    'type': 'object_attribute',
                    'class': match.group(1),
                    'attribute': match.group(2)
                }

            # 模块属性错误
            match = re.search(r"module '(\w+)' has no attribute '(\w+)'", error_message)
            if match:
                return {
                    'type': 'module_attribute',
                    'module': match.group(1),
                    'attribute': match.group(2)
                }

        return None

    def get_stats(self) -> Dict[str, Any]:
        """获取统计信息"""
        stats = {
            'loop_detector': self.loop_detector.get_stats(),
        }

        if self.context_manager:
            stats['context_manager'] = self.context_manager.get_scan_summary()

        return stats
