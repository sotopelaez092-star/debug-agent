"""
CodeFixer - 代码修复器
使用LLM生成代码修复方案
"""

import os 
import logging
from typing import Dict, List, Optional
from dotenv import load_dotenv
from openai import OpenAI

# 加载环境变量
load_dotenv()

logger = logging.getLogger(__name__)

class CodeFixer:
    """
    代码修复器

    功能：
    1. 接受错误代码和错误信息
    2. 调用LLM生成修复方案
    3. 返回修复后的代码和说明
    """

    def __init__(
        self,
        api_key: Optional[str] = None,
        model: str = "deepseek-chat",
        temperature: float = 0.3,
        max_tokens: int = 2000
    ):
        """
        初始化CodeFixer

        Args:
            api_key: Deepseek API密钥（如果不提供则从环境变量读取）
            model: 使用的模型名称
            temperature: LLM温度参数
            max_tokens: 最大生成token数
        """
        # 1. 获取API Key（优先使用参数，否则从环境变量获取）
        self.api_key = api_key or os.getenv("DEEPSEEK_API_KEY")

        # 2. 验证API Key（必须有，否则报错）
        if not self.api_key:
            raise ValueError(
                "DeppSeek API Key未找到。"
                "请在.env文件中设置DEEPSEEK_API_KEY,"
                "或在初始化时传入api_key参数"
            )
        # 3. 保存配置参数
        self.model = model
        self.temperature = temperature
        self.max_tokens = max_tokens

        # 4. 初始化OpenAI客户端（DeepSeek兼容OpenAI接口）
        self.client = OpenAI(
            api_key=self.api_key,
            base_url="https://api.deepseek.com/v1"
        )

        # 5. 记录日志
        logger.info(
            f"CodeFixer初始化完成。"
            f"模型：{self.model}，"
            f"温度：{self.temperature}，"
            f"最大token数：{self.max_tokens}"
        )


    def fix_code(
        self,
        buggy_code: str,
        error_message: str,
        context: Optional[str] = None,
        solutions: Optional[List[Dict]] = None
    ) -> Dict[str, str]:
        """
        修复错误代码

        Args:
            buggy_code: 包含错误的代码字符串
            error_message: 错误信息字符串
            context: 可选的上下文信息（例如函数定义、类定义等）
            solutions: 可选的修复方案列表，每个方案包含"code"和"explanation"键

        Returns:
            {
                "fixed_code": "修复后的代码",
                "explanation": "恢复说明",
                "changes": ["改动1", "改动2"]
            }

        Raises:
            ValueError: 当输入为空时
        """
        # 1. 输入验证
        if not buggy_code or not isinstance(buggy_code, str):
            raise ValueError("buggy_code必须是非空字符串")

        if not error_message or not isinstance(error_message, str):
            raise ValueError("error_message必须是非空字符串")

        # 限制代码长度（防止token超限）
        if len(buggy_code) > 10000:
            logger.warning("buggy_code长度超过10000字符，已截断")
            buggy_code = buggy_code[:10000]

        logger.info(f"修复错误代码，错误信息：{error_message}")

        # 2. 构造Prompt
        # 2.1 处理solutions
        solutions_text = ""
        if solutions and len(solutions) > 0:
            solutions_text = "\n[参考解决方案]\n"
            for i, sol in enumerate(solutions[:3], 1):
                solutions_text += f"\n方案{i}:\n{sol.get('content', '')[:500]}\n"
        # 2.2 构造完整Prompt
        prompt = f"""你是一位经验丰富的Python专家

    【任务】
    分析以下代码的错误，并提供详细的修复方案。

    【错误代码】
    ```python
    {buggy_code}
    ```

    【错误信息】
    {error_message}

    {solutions_text}

    【要求】
    1. 找出错误的根本原因
    2. 提供修复后的完整代码
    3. 详细解释为什么会出错
    4. 说明你做了哪些修改

    【输出格式】
    请严格按照以下格式输出：

    ===FIXED_CODE===
    （修复后的完整代码，不要包含```python标记）
    ===END_CODE===

    ===EXPLANATION===
    （详细解释：错误原因 + 修复方案）
    ===END_EXPLANATION===

    ===CHANGES===
    - 改动1
    - 改动2
    ===END_CHANGES===
        """

        logger.debug(f"Prompt构造完成，长度: {len(prompt)}")
        # 3. 调用API
        try:
            logger.info("正在调用DeepSeek API...")

            response = self.client.chat.completions.create(
                model=self.model,
                messages=[
                {
                    "role": "system",
                    "content": "你是一位经验丰富的Python代码修复专家。"
                },
                {
                    "role": "user",
                    "content": prompt
                }
                ],
                temperature=self.temperature,
                max_tokens=self.max_tokens,
                timeout=30.0
            )

            # 提取LLM返回的文本
            llm_response = response.choices[0].message.content

            logger.info(f"LLM返回文本长度：{len(llm_response)}")
            logger.debug(f"LLM返回原始文本：{llm_response[:200]}...")

        except TimeoutError as e:
            logger.error(f"API调用超时: {e}")
            raise RuntimeError("DeepSeek API调用超时，请稍后重试")

        except Exception as e:
            logger.error(f"API调用失败: {e}", exc_info=True)
            raise RuntimeError(f"DeepSeek API调用失败: {str(e)}")

        # 4. 解析结果
        try:
            # 4.1 提取修复后的代码
            fixed_code = self._extract_section(
                llm_response,
                "===FIXED_CODE===",
                "===END_CODE==="
            )
            # 4.2 提取解释
            explanation = self._extract_section(
                llm_response,
                "===EXPLANATION===",
                "===END_EXPLANATION==="
            )
            # 4.3 提取改动列表
            changes_text = self._extract_section(
                llm_response,
                "===CHANGES===",
                "===END_CHANGES==="
            )
            # 解析changes为列表（按行分割，去除空行）
            changes = [
                line.strip("- ")
                for line in changes_text.splitlines()
                if line.strip("- ")
            ]
            
            logger.info(f"解析成功 - 修复代码长度: {len(fixed_code)}, 改动数: {len(changes)}")

        except Exception as e:
            logger.error(f"解析LLM返回结果失败: {e}", exc_info=True)
            return {
                "fixed_code": llm_response,
                "explanation": "解析失败，以下是LLM原始返回",
                "changes": ["解析失败"]
            }
        # 5. 返回
        return {
            "fixed_code": fixed_code.strip(),
            "explanation": explanation.strip(),
            "changes": changes
        }
            

    def _extract_section(
        self, 
        text: str, 
        start_marker: str, 
        end_marker: str
    ) -> str:
        """
        从文本中提取指定标记之间的内容
        
        Args:
            text: 原始文本
            start_marker: 开始标记
            end_marker: 结束标记
            
        Returns:
            提取的内容（如果没找到标记，返回空字符串）
        """
        try:
            start_idx = text.find(start_marker)
            end_idx = text.find(end_marker)
            
            if start_idx == -1 or end_idx == -1:
                logger.warning(f"未找到标记: {start_marker} 或 {end_marker}")
                return ""
            
            # 提取标记之间的内容
            content = text[start_idx + len(start_marker):end_idx]
            return content.strip()
            
        except Exception as e:
            logger.error(f"提取section失败: {e}")
            return ""
# 测试代码
if __name__ == "__main__":
    # 简单测试
    fixer = CodeFixer()

    test_code = """
def greet(name):
    print(f"Hello, {nane}")
"""

    test_error = "NameError: name 'name' is not defined"

    result = fixer.fix_code(test_code, test_error)
    print(result)
