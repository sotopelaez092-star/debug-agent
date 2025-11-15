# src/rag/multi_query_retriever.py
"""
Multi-Query检索器实现

原理：
1. 用LLM生成多个查询改写（不同角度、不同词汇）
2. 每个查询独立检索
3. 合并去重，返回Top-K

优势：
- 覆盖更多表达方式
- 增加召回率
- 减少单一查询的偏差
"""

import os
import logging
from typing import List, Dict, Any, Optional
from collections import OrderedDict
from openai import OpenAI
from dotenv import load_dotenv

from .multi_query_prompts import MULTI_QUERY_GENERATION_PROMPT

# 加载环境变量
load_dotenv()

logger = logging.getLogger(__name__)


class MultiQueryRetriever:
    """
    多查询检索器
    
    使用LLM生成多个查询改写，分别检索后合并结果。
    """
    
    def __init__(
        self,
        base_retriever,
        api_key: Optional[str] = None,
        base_url: str = "https://api.deepseek.com",
        model: str = "deepseek-chat",
        num_queries: int = 3,
        top_k_per_query: int = 10,
        temperature: float = 0.7
    ):
        """
        初始化Multi-Query检索器
        
        Args:
            base_retriever: 基础检索器（BaseRetriever实例）
            api_key: DeepSeek API key（不提供则从环境变量读取）
            base_url: API base URL
            model: 模型名称
            num_queries: 生成查询数量
            top_k_per_query: 每个查询检索的文档数
            temperature: LLM生成温度（0.7可以产生多样性）
            
        Raises:
            ValueError: 当API key未提供且环境变量中也没有时
        """
        self.base_retriever = base_retriever
        self.num_queries = num_queries
        self.top_k_per_query = top_k_per_query
        self.model = model
        self.temperature = temperature
        
        # 获取API key
        self.api_key = api_key or os.getenv("DEEPSEEK_API_KEY")
        if not self.api_key:
            raise ValueError(
                "DeepSeek API key未提供。请设置环境变量DEEPSEEK_API_KEY "
                "或在初始化时传入api_key参数"
            )
        
        # 初始化OpenAI客户端（DeepSeek兼容OpenAI接口）
        try:
            self.client = OpenAI(
                api_key=self.api_key,
                base_url=base_url
            )
            logger.info("DeepSeek API客户端初始化成功")
        except Exception as e:
            logger.error(f"DeepSeek API客户端初始化失败: {e}", exc_info=True)
            raise
    
    def generate_queries(self, query: str) -> List[str]:
        """
        用LLM生成多个查询改写
        
        Args:
            query: 原始查询
            
        Returns:
            查询列表（包含原始查询 + 生成的改写）
            
        Raises:
            ValueError: 当query为空时
            RuntimeError: 当LLM调用失败时
        """
        # 输入验证
        if not query or not isinstance(query, str):
            raise ValueError("query必须是非空字符串")
        
        if len(query) > 500:
            logger.warning(f"查询过长({len(query)}字符)，截断至500")
            query = query[:500]
        
        try:
            # 构造prompt
            prompt = MULTI_QUERY_GENERATION_PROMPT.format(query=query)
            
            # 调用LLM
            logger.info(f"生成查询改写: {query}")
            response = self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "user", "content": prompt}
                ],
                temperature=self.temperature,
                max_tokens=500
            )
            
            # 解析响应
            generated_text = response.choices[0].message.content.strip()
            logger.debug(f"LLM响应: {generated_text}")
            
            # 按行分割，过滤空行
            generated_queries = [
                line.strip()
                for line in generated_text.split('\n')
                if line.strip() and not line.strip().startswith('改写')
            ]
            
            # 去除编号（如果有）
            generated_queries = [
                self._remove_numbering(q) for q in generated_queries
            ]
            
            # 过滤太短或太长的查询
            generated_queries = [
                q for q in generated_queries
                if 5 <= len(q) <= 200
            ]
            
            # 取前num_queries个
            generated_queries = generated_queries[:self.num_queries]
            
            # 如果生成失败，使用简单规则
            if len(generated_queries) < self.num_queries:
                logger.warning(
                    f"LLM只生成了{len(generated_queries)}个查询，"
                    f"使用规则补充至{self.num_queries}个"
                )
                generated_queries = self._fallback_generation(
                    query, 
                    self.num_queries
                )
            
            # 将原始查询放在第一位
            all_queries = [query] + [
                q for q in generated_queries if q != query
            ]
            
            logger.info(f"生成{len(all_queries)}个查询: {all_queries}")
            return all_queries[:self.num_queries + 1]  # 最多返回n+1个
            
        except Exception as e:
            logger.error(f"查询生成失败: {e}", exc_info=True)
            # 失败时使用规则生成
            logger.warning("使用规则生成查询")
            return self._fallback_generation(query, self.num_queries + 1)
    
    def _remove_numbering(self, text: str) -> str:
        """
        去除文本开头的编号
        
        Args:
            text: "1. 查询" or "改写1: 查询"
            
        Returns:
            "查询"
        """
        # 去除 "1. " "1) " "改写1: " 等格式
        import re
        text = re.sub(r'^[\d]+[\.\)]\s*', '', text)
        text = re.sub(r'^改写[\d]+[:：]\s*', '', text)
        return text.strip()
    
    def _fallback_generation(self, query: str, n: int) -> List[str]:
        """
        规则生成查询（LLM失败时的备选方案）
        
        Args:
            query: 原始查询
            n: 需要生成的数量
            
        Returns:
            查询列表
        """
        queries = [query]
        
        # 规则1: "如何解决{query}"
        if len(queries) < n:
            queries.append(f"如何解决{query}错误")
        
        # 规则2: "Python {query}修复方法"
        if len(queries) < n:
            queries.append(f"Python {query}修复方法")
        
        # 规则3: "{query}原因和解决方案"
        if len(queries) < n:
            queries.append(f"{query}的原因和解决方案")
        
        return queries[:n]
    
    def search(self, query: str, top_k: int = 10) -> List[Dict[str, Any]]:
        """
        多查询检索
        
        流程：
        1. 生成多个查询
        2. 每个查询独立检索
        3. 合并去重
        4. 返回Top-K
        
        Args:
            query: 原始查询
            top_k: 返回文档数量
            
        Returns:
            文档列表，每个文档包含：
            {
                "id": "doc-1",
                "content": "...",
                "similarity": 0.85,
                "metadata": {...},
                "rank": 1,
                "source_queries": ["query1", "query2"]  # 新增：来自哪些查询
            }
            
        Raises:
            ValueError: 当query为空或top_k不合法时
        """
        # 输入验证
        if not query or not isinstance(query, str):
            raise ValueError("query必须是非空字符串")
        
        if not 1 <= top_k <= 50:
            raise ValueError("top_k必须在1-50之间")
        
        try:
            # 1. 生成多个查询
            queries = self.generate_queries(query)
            logger.info(f"生成{len(queries)}个查询进行检索")
            
            # 2. 每个查询独立检索
            all_results = []
            for idx, q in enumerate(queries):
                try:
                    results = self.base_retriever.search(
                        q, 
                        top_k=self.top_k_per_query
                    )
                    
                    # 标记来源查询
                    for doc in results:
                        if 'source_queries' not in doc:
                            doc['source_queries'] = []
                        doc['source_queries'].append(q)
                    
                    all_results.append(results)
                    logger.debug(f"查询{idx+1}检索到{len(results)}个文档")
                    
                except Exception as e:
                    logger.error(f"查询'{q}'检索失败: {e}", exc_info=True)
                    # 继续处理其他查询
                    continue
            
            if not all_results:
                logger.warning("所有查询都检索失败")
                return []
            
            # 3. 合并去重
            merged = self._merge_results(all_results)
            logger.info(f"合并后共{len(merged)}个唯一文档")
            
            # 4. 返回Top-K
            return merged[:top_k]
            
        except Exception as e:
            logger.error(f"多查询检索失败: {e}", exc_info=True)
            raise
    
    def _merge_results(
        self, 
        all_results: List[List[Dict[str, Any]]]
    ) -> List[Dict[str, Any]]:
        """
        合并多个检索结果（简单去重策略）
        
        策略：
        1. 按doc_id去重（保留第一次出现的）
        2. 保留原始相似度分数
        3. 合并source_queries信息
        
        Args:
            all_results: [
                [doc1, doc2, ...],  # 查询1的结果
                [doc3, doc4, ...],  # 查询2的结果
                ...
            ]
            
        Returns:
            去重后的文档列表
        """
        # 使用OrderedDict保持顺序
        seen_docs = OrderedDict()
        
        for results in all_results:
            for doc in results:
                doc_id = doc.get('id')
                
                if not doc_id:
                    logger.warning("文档缺少id字段，跳过")
                    continue
                
                if doc_id not in seen_docs:
                    # 第一次见到这个文档
                    seen_docs[doc_id] = doc
                else:
                    # 已经见过，合并source_queries
                    existing = seen_docs[doc_id]
                    new_queries = doc.get('source_queries', [])
                    existing_queries = existing.get('source_queries', [])
                    
                    # 合并并去重
                    all_queries = existing_queries + new_queries
                    existing['source_queries'] = list(set(all_queries))
        
        # 转换为列表
        merged = list(seen_docs.values())
        
        # 重新设置rank
        for idx, doc in enumerate(merged, 1):
            doc['rank'] = idx
        
        return merged


# 便捷函数
def create_multi_query_retriever(
    base_retriever,
    **kwargs
) -> MultiQueryRetriever:
    """
    创建Multi-Query检索器的便捷函数
    
    Args:
        base_retriever: 基础检索器
        **kwargs: 其他参数传递给MultiQueryRetriever
        
    Returns:
        MultiQueryRetriever实例
        
    Example:
        retriever = create_multi_query_retriever(
            base_retriever=my_retriever,
            num_queries=3,
            top_k_per_query=10
        )
    """
    return MultiQueryRetriever(base_retriever, **kwargs)