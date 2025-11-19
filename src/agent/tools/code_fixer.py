"""
CodeFixer - 代码修复器
使用LLM生成代码修复方案
"""

import os 
import logging
from typing import Dict, List, Optional, Any
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
        context: Optional[Dict[str, Any]] = None,
        rag_solutions: Optional[List[Dict]] = None
    ) -> Dict[str, Any]:
        """
        使用LLM生成代码修复
        
        Args:
            buggy_code: 包含错误的代码
            error_message: 错误信息
            context: ContextManager提供的上下文（包含相关符号定义和import建议）
            rag_solutions: RAG检索的解决方案列表
            
        Returns:
            Dict包含:
                - fixed_code: 修复后的代码
                - explanation: 修复说明
                - changes: 变更列表
                
        Raises:
            ValueError: 如果输入参数无效
            RuntimeError: 如果LLM调用失败
        """
        # 1. 输入验证
        if not buggy_code or not isinstance(buggy_code, str):
            raise ValueError("buggy_code必须是非空字符串")
        
        if not error_message or not isinstance(error_message, str):
            raise ValueError("error_message必须是非空字符串")
        
        logger.info(f"开始生成修复代码，错误信息: {error_message[:100]}...")
        
        # 2. 构建Prompt
        prompt = self._build_prompt(buggy_code, error_message, context, rag_solutions)
        
        # 3. 调用LLM
        try:
            response = self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {
                        "role": "system",
                        "content": "你是一个专业的Python代码调试专家。"
                    },
                    {
                        "role": "user",
                        "content": prompt
                    }
                ],
                temperature=0.3,
                max_tokens=2000
            )
            
            response_text = response.choices[0].message.content
            logger.info("LLM响应成功")

        except Exception as e:
            logger.error(f"LLM调用失败: {e}", exc_info=True)
            raise RuntimeError(f"LLM调用失败: {e}")
        
        # 4. 解析响应
        try:
            result = self._parse_response(response_text)
            logger.info("修复代码生成成功")
            return result
            
        except Exception as e:
            logger.error(f"解析LLM响应失败: {e}", exc_info=True)
            raise RuntimeError(f"解析LLM响应失败: {e}")

    def _build_prompt(
        self,
        buggy_code: str,
        error_message: str,
        context: Optional[Dict[str, Any]],
        rag_solutions: Optional[List[Dict]]
    ) -> str:
        """
        构建完整的修复Prompt
        
        Args:
            buggy_code: 有错误的代码
            error_message: 错误信息
            context: 上下文信息
            rag_solutions: RAG解决方案
            
        Returns:
            完整的Prompt字符串
        """
        prompt_parts = []
        
        # 1. 错误代码
        prompt_parts.append("# 当前代码（有错误）")
        prompt_parts.append("```python")
        prompt_parts.append(buggy_code)
        prompt_parts.append("```")
        prompt_parts.append("")
        
        # 2. 错误信息
        prompt_parts.append("# 错误信息")
        prompt_parts.append(error_message)
        prompt_parts.append("")
        
        # 3. 上下文信息（如果有）
        if context and context.get("related_symbols"):
            prompt_parts.append("# 相关符号定义（项目中找到的）")
            
            for symbol_name, symbol_info in context["related_symbols"].items():
                prompt_parts.append(f"\n## {symbol_name} (来自 {symbol_info['file']})")
                prompt_parts.append("```python")
                prompt_parts.append(symbol_info["definition"])
                prompt_parts.append("```")
            
            prompt_parts.append("")
        
        # 4. Import建议（如果有）
        if context and context.get("import_suggestions"):
            prompt_parts.append("# Import建议")
            for suggestion in context["import_suggestions"]:
                prompt_parts.append(f"- {suggestion}")
            prompt_parts.append("")
        
        # 5. RAG解决方案（如果有）
        if rag_solutions and len(rag_solutions) > 0:
            prompt_parts.append("# Stack Overflow相关解决方案")
            
            for i, solution in enumerate(rag_solutions[:3], 1):  # 只取前3个
                prompt_parts.append(f"\n## 解决方案 {i}")
                content = solution.get("content", "")
                if len(content) > 500:
                    content = content[:500] + "..."
                prompt_parts.append(content)
            
            prompt_parts.append("")
        
        # 6. 任务说明
        prompt_parts.append("# 请修复代码")
        prompt_parts.append("""
    请分析上述错误，并提供修复方案。

    要求：
    1. 如果有相关符号定义和import建议，优先使用它们
    2. 提供完整的修复后代码
    3. 解释修复思路
    4. 列出具体修改点

    请以JSON格式返回，格式如下：
    {
        "fixed_code": "完整的修复后代码",
        "explanation": "修复思路说明",
        "changes": ["修改点1", "修改点2", ...]
    }

    重要：只返回JSON，不要有其他内容。
    """)
        
        return "\n".join(prompt_parts)

            

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

    def _parse_response(self, response_text: str) -> Dict[str, Any]:
        """
        解析LLM的JSON响应
        
        Args:
            response_text: LLM返回的文本
            
        Returns:
            包含fixed_code, explanation, changes的字典
            
        Raises:
            RuntimeError: 如果解析失败
        """
        import json
        import re
        
        try:
            # 1. 先尝试提取```json...```代码块
            json_block_match = re.search(r'```json\s*(.*?)\s*```', response_text, re.DOTALL)
            if json_block_match:
                json_str = json_block_match.group(1).strip()
                logger.info("从```json```代码块中提取JSON")
                result = json.loads(json_str)
                
                # 验证必需字段
                if 'fixed_code' not in result:
                    raise ValueError("响应缺少fixed_code字段")
                
                # 设置默认值
                result.setdefault('explanation', '未提供说明')
                result.setdefault('changes', [])
                
                return result
            
            # 2. 如果没有代码块，尝试直接解析JSON
            logger.info("尝试直接解析JSON")
            result = json.loads(response_text)
            
            # 验证必需字段
            if 'fixed_code' not in result:
                raise ValueError("响应缺少fixed_code字段")
            
            # 设置默认值
            result.setdefault('explanation', '未提供说明')
            result.setdefault('changes', [])
            
            return result
            
        except json.JSONDecodeError as e:
            logger.error(f"JSON解析失败: {e}")
            logger.error(f"尝试解析的内容: {response_text[:200]}...")
            
            # 3. 最后的fallback：作为纯文本处理
            logger.warning("无法解析为JSON，作为纯文本处理")
            return {
                'fixed_code': response_text,
                'explanation': '无法解析LLM响应为JSON，返回原始文本',
                'changes': []
            }
        
        except Exception as e:
            logger.error(f"解析响应时出错: {e}")
            raise RuntimeError(f"解析响应失败: {e}")

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
