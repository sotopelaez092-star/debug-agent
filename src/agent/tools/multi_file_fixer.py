"""
多文件修复器 - 支持跨文件代码修复

用于处理需要修改多个文件才能修复的错误，
如：类定义不完整、跨文件依赖等
"""

import json
import logging
import re
import os
from typing import Dict, List, Any, Optional
from dotenv import load_dotenv
from openai import OpenAI

# 加载环境变量
load_dotenv()

logger = logging.getLogger(__name__)


MULTI_FILE_FIX_PROMPT = """你是一个专业的Python Debug专家。用户的代码出现了跨文件错误，需要你分析并修复。

## 错误信息
{error_message}

## 出错文件
{error_file}

## 项目所有文件
{all_files_content}

## 任务
1. 分析错误的根本原因
2. 确定需要修改哪些文件（可能是出错文件，也可能是其他文件）
3. 使用代码块替换的方式描述修改

## 输出格式
请严格按照以下JSON格式输出：
```json
{{
    "analysis": "错误原因分析（简短）",
    "fixed_files": {{
        "文件名": [
            {{
                "old": "需要被替换的原始代码块",
                "new": "替换后的新代码块"
            }}
        ]
    }},
    "explanation": "给用户的修复说明"
}}
```

## 重要规则
1. old字段必须是文件中精确存在的代码，包括缩进和换行
2. 只修改真正需要改的文件，不要修改无关文件
3. 如果错误是类/函数定义不完整，应修改定义所在的文件
4. 每个文件可以有多个替换块
5. 不要输出任何JSON以外的内容

现在请分析并修复："""


class MultiFileFixer:
    """
    多文件代码修复器
    
    使用LLM分析跨文件错误，生成代码块替换方案，
    支持同时修改多个文件。
    """
    
    def __init__(
        self,
        model: str = "deepseek-chat",
        temperature: float = 0.3,
        max_tokens: int = 2000
    ):
        """
        初始化多文件修复器
        
        Args:
            model: LLM模型名称
            temperature: 生成温度
            max_tokens: 最大token数
        """
        api_key = os.getenv("DEEPSEEK_API_KEY")
        if not api_key:
            raise ValueError("未设置DEEPSEEK_API_KEY环境变量")
        
        self.client = OpenAI(
            api_key=api_key,
            base_url="https://api.deepseek.com/v1"
        )
        self.model = model
        self.temperature = temperature
        self.max_tokens = max_tokens
        
        logger.info(f"MultiFileFixer初始化完成。模型：{model}")
    
    def fix(
        self,
        error_file: str,
        error_message: str,
        all_files: Dict[str, str]
    ) -> Dict[str, Any]:
        """
        分析错误并生成多文件修复方案
        
        Args:
            error_file: 出错的文件名
            error_message: 错误信息
            all_files: 所有项目文件 {文件名: 内容}
            
        Returns:
            {
                "success": bool,
                "analysis": "错误分析",
                "fixed_files": {"文件名": "修复后完整内容"},
                "explanation": "修复说明",
                "changes": {"文件名": [{"old": "", "new": ""}]}
            }
        """
        # 输入验证
        if not error_file:
            raise ValueError("error_file不能为空")
        if not error_message:
            raise ValueError("error_message不能为空")
        if not all_files:
            raise ValueError("all_files不能为空")
        
        logger.info(f"开始多文件修复，错误文件: {error_file}")
        logger.info(f"项目文件数: {len(all_files)}")
        
        try:
            # 1. 构建prompt
            prompt = self._build_prompt(error_file, error_message, all_files)
            
            # 2. 调用LLM
            response = self.client.chat.completions.create(
                model=self.model,
                messages=[{"role": "user", "content": prompt}],
                temperature=self.temperature,
                max_tokens=self.max_tokens
            )
            
            llm_response = response.choices[0].message.content
            logger.info(f"LLM响应长度: {len(llm_response)}")
            
            # 3. 解析响应
            parsed = self._parse_response(llm_response)
            if not parsed:
                return {
                    "success": False,
                    "error": "无法解析LLM响应",
                    "raw_response": llm_response
                }
            
            # 4. 应用修复
            fix_instructions = parsed.get("fixed_files", {})
            fixed_files = self._apply_fixes(all_files, fix_instructions)
            
            return {
                "success": True,
                "analysis": parsed.get("analysis", ""),
                "fixed_files": fixed_files,
                "explanation": parsed.get("explanation", ""),
                "changes": fix_instructions
            }
            
        except Exception as e:
            logger.error(f"多文件修复失败: {e}", exc_info=True)
            return {
                "success": False,
                "error": str(e)
            }
    
    def _build_prompt(
        self,
        error_file: str,
        error_message: str,
        all_files: Dict[str, str]
    ) -> str:
        """构建LLM prompt"""
        files_content = self._format_files_content(all_files)
        
        return MULTI_FILE_FIX_PROMPT.format(
            error_message=error_message,
            error_file=error_file,
            all_files_content=files_content
        )
    
    def _format_files_content(self, files: Dict[str, str]) -> str:
        """格式化文件内容供prompt使用"""
        output = []
        for filename, content in files.items():
            output.append(f"### {filename}\n```python\n{content}\n```")
        return "\n\n".join(output)
    
    def _parse_response(self, response: str) -> Optional[Dict[str, Any]]:
        """解析LLM响应"""
        try:
            # 尝试从markdown代码块中提取JSON
            json_match = re.search(r'```json\s*(.*?)\s*```', response, re.DOTALL)
            if json_match:
                json_str = json_match.group(1)
            else:
                # 尝试直接解析
                json_str = response.strip()
            
            # 尝试提取完整的JSON对象
            json_str = self._extract_json(json_str)
            if not json_str:
                logger.error("无法提取JSON")
                return None
            
            parsed = json.loads(json_str)
            logger.info(f"解析成功，需要修改的文件: {list(parsed.get('fixed_files', {}).keys())}")
            return parsed
            
        except json.JSONDecodeError as e:
            logger.error(f"JSON解析失败: {e}")
            return None
    
    def _extract_json(self, text: str) -> Optional[str]:
        """从文本中提取完整的JSON对象"""
        # 找到第一个 {
        start = text.find('{')
        if start == -1:
            return None
        
        # 使用括号计数找到匹配的 }
        depth = 0
        in_string = False
        escape = False
        
        for i, char in enumerate(text[start:], start):
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
                    return text[start:i+1]
        
        return None
    
    def _apply_fixes(
        self,
        original_files: Dict[str, str],
        fix_instructions: Dict[str, List[Dict[str, str]]]
    ) -> Dict[str, str]:
        """
        应用代码块替换
        
        Args:
            original_files: 原始文件内容
            fix_instructions: 替换指令 {"文件名": [{"old": "", "new": ""}]}
            
        Returns:
            修复后的文件内容 {"文件名": "完整内容"}
        """
        fixed_files = {}
        
        for filename, changes in fix_instructions.items():
            if filename not in original_files:
                logger.warning(f"文件 {filename} 不在项目中，跳过")
                continue
            
            content = original_files[filename]
            
            for change in changes:
                old_code = change.get("old", "")
                new_code = change.get("new", "")
                
                if not old_code:
                    logger.warning(f"文件 {filename} 的替换指令缺少old字段")
                    continue
                
                # 执行替换
                if old_code in content:
                    content = content.replace(old_code, new_code, 1)
                    logger.info(f"文件 {filename}: 替换成功")
                else:
                    # 尝试忽略空白差异
                    normalized_old = ' '.join(old_code.split())
                    normalized_content = ' '.join(content.split())
                    
                    if normalized_old in normalized_content:
                        logger.warning(f"文件 {filename}: 空白差异，尝试模糊替换")
                        # 这里简化处理，实际可能需要更复杂的匹配
                        content = content.replace(old_code.strip(), new_code.strip(), 1)
                    else:
                        logger.error(f"文件 {filename}: 找不到要替换的代码块")
                        logger.debug(f"old_code: {repr(old_code[:100])}")
            
            fixed_files[filename] = content
        
        return fixed_files