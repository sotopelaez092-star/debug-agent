"""
Query改写器
用于扩展和优化检索查询，提高召回率
"""

import logging
import re
from functools import lru_cache
from typing import Dict, List, Set, Tuple

logger = logging.getLogger(__name__)


class QueryRewriter:
    """
    查询改写器：通过错误类型扩展和同义词补充来增强查询
    
    策略：
    1. 错误类型扩展：为常见错误类型添加相关描述
    2. 同义词补充：添加技术术语的同义词
    3. 去重：避免重复添加已存在的词
    4. 长度控制：防止查询过长
    
    Example:
        >>> rewriter = QueryRewriter()
        >>> rewriter.rewrite("AttributeError")
        "AttributeError NoneType object has no attribute"
    """
    
    def __init__(self):
        """
        初始化QueryRewriter，加载词典
        
        加载的词典：
        - error_expansions: 错误类型扩展词典
        - synonyms：同义词词典

        Note:
            词典在初始化时一次性加载，后续可重复使用
        """
        # 初始化错误类型扩展词典
        self.error_expansions: Dict[str, str] = {}
        
        # 初始化同义词词典
        self.synonyms: Dict[str, List[str]] = {}
        
        # 调用加载词典的方法
        self._load_error_expansions()
        self._load_synonyms()
        
        logger.info("QueryRewriter initialized")
    
    def rewrite(self, query: str, max_length: int = 150) -> str:
        """
        改写查询，返回扩展后的查询
        
        Args:
            query: 原始查询字符串
            max_length: 改写后查询的最大字符数（默认150）
            
        Returns:
            改写后的查询字符串
            
        Raises:
            ValueError: 当query为空或类型不正确时
            
        Example:
            >>> rewriter.rewrite("AttributeError")
            "AttributeError NoneType object has no attribute"
        """
        # 输入验证
        if query is None:
            raise ValueError("query不能为None")
        
        if not isinstance(query, str):
            raise ValueError(f"query必须是字符串类型，当前类型: {type(query)}")
        
        if not query.strip():
            raise ValueError("query不能为空字符串")
        
        if max_length < 20:
            raise ValueError(f"max_length必须 >= 20，当前: {max_length}")
        
        # 记录原始查询
        original_query = query.strip()
        logger.info(f"Rewriting query: '{original_query}'")
        
        try:
            # 步骤1: 扩展错误类型
            expanded = self._expand_error_type(original_query)
            
            # 步骤2: 添加同义词
            rewritten = self._add_synonyms(expanded)
            
            # 步骤3: 长度控制
            if len(rewritten) > max_length:
                logger.warning(
                    f"Query too long ({len(rewritten)} chars), "
                    f"truncating to {max_length}"
                )
                rewritten = self._truncate_query(rewritten, max_length)
            
            # 步骤4: 记录统计
            self._log_rewrite_stats(original_query, rewritten)
            
            return rewritten
            
        except Exception as e:
            logger.error(f"Query rewriting failed: {e}", exc_info=True)
            # 发生错误时返回原查询，保证系统可用性
            logger.warning("Returning original query due to error")
            return original_query
    
    def _load_error_expansions(self) -> None:
        """
        加载错误类型扩展词典
        
        格式：{错误类型: 扩展描述}
        Example: {"AttributeError": "NoneType object has no attribute"}
        """
        self.error_expansions = {
            # 属性错误 - 最常见：访问None对象的属性
            "AttributeError": "NoneType object has no attribute",
            
            # 类型错误 - 最常见：操作符或函数参数类型不匹配
            "TypeError": "unsupported operand type wrong argument",
            
            # 索引错误 - 最常见：列表索引越界
            "IndexError": "list index out of range",
            
            # 键错误 - 最常见：字典键不存在
            "KeyError": "key not found in dictionary",
            
            # 值错误 - 最常见：参数值不合法
            "ValueError": "invalid literal value conversion",
            
            # 导入错误 - 最常见：模块未找到
            "ImportError": "module not found no module named",
            "ModuleNotFoundError": "module not found cannot import",
            
            # 名称错误 - 最常见：变量未定义
            "NameError": "name is not defined variable undefined",
            
            # 零除错误
            "ZeroDivisionError": "division by zero",
            
            # 文件错误
            "FileNotFoundError": "no such file or directory",
            
            # 运行时错误
            "RuntimeError": "maximum recursion depth exceeded",
        }
        
        logger.info(f"Loaded {len(self.error_expansions)} error type expansions")
    
    def _load_synonyms(self) -> None:
        """
        加载同义词词典
        
        格式：{术语: [同义词列表]}
        Example: {"import": ["ImportError", "ModuleNotFoundError"]}
        
        Note:
            使用单个关键词而非短语，提高匹配准确率
        """
        self.synonyms = {
            # 导入相关
            "import": ["ImportError", "ModuleNotFoundError", "cannot import"],
            
            # 索引相关
            "index": ["IndexError", "out of range"],
            
            # 类型相关
            "type": ["TypeError", "wrong type", "type mismatch"],
            
            # 属性相关
            "attribute": ["AttributeError", "has no attribute"],
            
            # 键相关
            "key": ["KeyError", "missing key", "key not found"],
            
            # 值相关
            "value": ["ValueError", "invalid value", "wrong value"],
            
            # 名称相关
            "name": ["NameError", "not defined", "undefined"],
            
            # None相关
            "none": ["NoneType", "null value"],
            "null": ["NoneType", "none value"],
            
            # 列表相关
            "list": ["array", "sequence"],
            
            # 字典相关
            "dict": ["dictionary", "mapping"],
            "dictionary": ["dict", "mapping"],
            
            # 错误相关
            "error": ["exception", "failure"],
            "exception": ["error", "failure"],
        }
        
        logger.info(f"Loaded {len(self.synonyms)} synonym groups")
    
    def _expand_error_type(self, query: str) -> str:
        """
        扩展错误类型（使用正则单词边界匹配）
        
        Args:
            query: 查询字符串
            
        Returns:
            扩展后的查询（如果匹配到错误类型）
            
        Example:
            >>> self._expand_error_type("AttributeError")
            "AttributeError NoneType object has no attribute"
        
        Note:
            使用单词边界 \\b 避免误匹配
            例如："TypeError" 不会匹配 "RuntimeError"
        """
        query_lower = query.lower()
        expanded_parts = []
        
        # 检查是否匹配任何错误类型（使用单词边界）
        for error_type, expansion in self.error_expansions.items():
            # 构建正则：\bAttributeError\b（忽略大小写）
            pattern = r'\b' + re.escape(error_type.lower()) + r'\b'
            
            if re.search(pattern, query_lower):
                expanded_parts.append(expansion)
                logger.debug(
                    f"Matched error type: {error_type}, "
                    f"adding expansion: {expansion}"
                )
        
        # 如果有匹配的扩展，添加到原查询后面
        if expanded_parts:
            result = f"{query} {' '.join(expanded_parts)}"
            logger.debug(f"Expanded query: '{query}' -> '{result}'")
            return result
        
        # 没有匹配，返回原查询
        return query
    
    def _add_synonyms(self, query: str) -> str:
        """
        添加同义词（带去重）
        
        Args:
            query: 查询字符串
            
        Returns:
            添加同义词后的查询
            
        Example:
            >>> self._add_synonyms("import error")
            "import error ImportError ModuleNotFoundError"
        
        Note:
            - 避免添加已存在的词
            - 使用单词边界匹配，提高准确率
        """
        query_lower = query.lower()
        
        # 提取查询中已有的词（用于去重）
        existing_words = set(query_lower.split())
        
        synonym_parts = []
        
        # 检查是否匹配任何术语
        for term, synonyms in self.synonyms.items():
            # 使用单词边界匹配
            pattern = r'\b' + re.escape(term.lower()) + r'\b'
            
            if re.search(pattern, query_lower):
                # 添加同义词（去重）
                for syn in synonyms:
                    syn_lower = syn.lower()
                    # 避免添加已存在的词
                    if syn_lower not in query_lower:
                        synonym_parts.append(syn)
                
                logger.debug(
                    f"Matched term: {term}, "
                    f"adding synonyms: {synonyms}"
                )
        
        # 如果有匹配的同义词，添加到原查询后面
        if synonym_parts:
            # 去重（保持顺序）
            unique_synonyms = list(dict.fromkeys(synonym_parts))
            result = f"{query} {' '.join(unique_synonyms)}"
            logger.debug(f"Added synonyms: '{query}' -> '{result}'")
            return result
        
        # 没有匹配，返回原查询
        return query
    
    def _truncate_query(self, query: str, max_length: int) -> str:
        """
        截断查询到指定长度（保留完整单词）
        
        Args:
            query: 查询字符串
            max_length: 最大长度
            
        Returns:
            截断后的查询
            
        Example:
            >>> self._truncate_query("word1 word2 word3 word4", max_length=15)
            "word1 word2"
        """
        if len(query) <= max_length:
            return query
        
        # 截断到max_length，然后找到最后一个空格
        truncated = query[:max_length]
        last_space = truncated.rfind(' ')
        
        if last_space > 0:
            # 在最后一个完整单词处截断
            result = truncated[:last_space]
        else:
            # 如果没有空格，强制截断
            result = truncated
        
        logger.debug(f"Truncated query from {len(query)} to {len(result)} chars")
        return result
    
    def _log_rewrite_stats(self, original: str, rewritten: str) -> None:
        """
        记录改写统计信息
        
        Args:
            original: 原始查询
            rewritten: 改写后的查询
        """
        if rewritten != original:
            original_words = len(original.split())
            rewritten_words = len(rewritten.split())
            expansion_rate = rewritten_words / original_words if original_words > 0 else 0
            
            logger.info(
                f"Query rewritten: '{original}' -> '{rewritten}' | "
                f"words: {original_words}->{rewritten_words} | "
                f"expansion: {expansion_rate:.2f}x"
            )
        else:
            logger.info(f"Query unchanged: '{original}'")


# 简单测试
if __name__ == "__main__":
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    
    rewriter = QueryRewriter()
    
    # 测试用例
    test_cases = [
        "AttributeError",
        "import error",
        "list index out of range",
        "TypeError",
        "cannot import module",
        "RuntimeError",  # 测试不误匹配TypeError
        "AttributeError TypeError ImportError",  # 测试多错误类型
    ]
    
    print("\n" + "="*60)
    print("Query Rewriter Test")
    print("="*60)
    
    for query in test_cases:
        print(f"\n原查询: {query}")
        rewritten = rewriter.rewrite(query)
        print(f"改写后: {rewritten}")
        print(f"长度: {len(query)} -> {len(rewritten)} 字符")