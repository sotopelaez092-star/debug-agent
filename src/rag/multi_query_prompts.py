# src/rag/multi_query_prompts.py
"""
Multi-Query检索的Prompt模板
"""

MULTI_QUERY_GENERATION_PROMPT = """你是一个Python错误检索专家，专门帮助开发者在Stack Overflow中找到相关解决方案。

任务：给定一个Python错误查询，生成3个不同角度的改写版本，用于检索相关文档。

改写要求：
1. 使用不同的词汇和表达方式（同义词、技术术语、口语化等）
2. 从不同角度描述问题（错误原因、解决方法、代码示例、场景描述等）
3. 保持核心意思不变
4. 每个改写都应该能独立检索到相关文档
5. 改写应该自然、符合实际搜索习惯

示例1：
原始查询: AttributeError怎么办
改写1: 如何解决Python中的AttributeError错误
改写2: 对象属性访问失败NoneType object has no attribute
改写3: AttributeError异常的常见原因和修复方法

示例2：
原始查询: ImportError: No module named requests
改写1: Python导入requests模块失败如何解决
改写2: 找不到模块ImportError修复方法pip install
改写3: 模块已安装但仍然报No module named错误

示例3：
原始查询: list index out of range
改写1: Python列表索引越界错误怎么处理
改写2: 访问列表元素时IndexError index out of range
改写3: 如何避免列表下标超出范围的问题

现在，请为以下查询生成3个改写。要求每行一个改写，不要编号，不要额外解释：

原始查询: {query}"""


# 简化版Prompt（如果上面的效果不好可以试这个）
SIMPLE_MULTI_QUERY_PROMPT = """给定一个Python错误查询，生成3个不同的改写版本。

要求：使用不同的词汇，从不同角度描述，保持核心意思。

示例：
原始: AttributeError怎么办
改写1: 如何解决AttributeError错误
改写2: Python属性访问异常修复
改写3: NoneType对象AttributeError处理

原始查询: {query}
改写（每行一个，不要编号）:"""
