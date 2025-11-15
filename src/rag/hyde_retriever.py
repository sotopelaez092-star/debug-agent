# src/rag/hyde_retriever.py

# src/rag/hyde_retriever.py

from typing import List, Dict, Any, Optional
import logging
from langchain_openai import ChatOpenAI
from langchain_core.messages import HumanMessage
import os

from .retriever import BaseRetriever

from dotenv import load_dotenv

# 在文件开头就加载 .env
load_dotenv()

logger = logging.getLogger(__name__)

# HyDE Prompt模板
HYDE_PROMPT_TEMPLATE = """You are an expert Python developer on Stack Overflow.

Given this Python error, generate a typical high-quality Stack Overflow answer. 
The answer does NOT need to be factually accurate - it just needs to SOUND like 
a real Stack Overflow answer with the right style and terminology.

Error Query: {query}

Generate a concise Stack Overflow style answer (100-200 words) with:
1. Root cause explanation (2-3 sentences)
2. Solution approach (2-3 sentences)  
3. Code example (5-10 lines)

Important: Use proper Python terminology and Stack Overflow conventions.
The answer should feel authentic even if details are hypothetical.

Answer:"""


class HyDERetriever:
    """
    HyDE检索器

    利用HyDE生成查询向量的检索器

    """

    def __init__(
        self,
        base_retriever: BaseRetriever,
        llm: Optional[ChatOpenAI] = None,
        enable_cache: bool = False
    ):
        """
        初始化HyDERetriever

        Args:
            base_retriever: 基础检索器
            llm: 语言模型，默认使用gpt-3.5-turbo
            enable_cache: 是否启用缓存，默认不启用
        """
        self.base_retriever = base_retriever
        self.llm = llm or self._init_default_llm()
        self.enable_cache = enable_cache
        if enable_cache:
            self.cache = {}


    def _init_default_llm(self) -> ChatOpenAI:
        """
        初始化默认LLM配置

        Returns:
            配置好的ChatOpenAI实例

        Raises:
            ValueError: 当API key未设置
        """
        api_key = os.getenv("DEEPSEEK_API_KEY")
        if not api_key:
            raise ValueError("请在 .env 文件中设置 DEEPSEEK_API_KEY")
        return ChatOpenAI(
            base_url="https://api.deepseek.com",
            api_key=api_key,
            model="deepseek-chat",
            temperature=0.7,
            max_tokens=300,
            timeout=30.0
        )

    def generate_hypothetical_doc(self, query: str) -> str:
        """
        生成假设文档

        Args:
            query: 查询文本（错误信息）

        Returns:
            假设文档内容

        Raises:
            ValueError: 当query为空时
        """
        # 输入验证
        if not query or not isinstance(query, str):
            raise ValueError("query必须是非空字符串")

        # 截断过长的query
        if len(query) > 10000:
            logger.warning("query长度超过10000，已截断")
            query = query[:10000]

        # 检查缓存
        if self.enable_cache and query in self.cache:
            logger.info(f"从缓存中获取假设文档: {query}")
            return self.cache[query]

        # 格式化Prompt
        prompt = HYDE_PROMPT_TEMPLATE.format(query=query)
        logger.info(f"生成假设文档，query长度: {len(query)}")

        # 调用LLM + 异常处理
        try:
            # 创建消息
            message = HumanMessage(content=prompt)

            # 调用LLM
            response = self.llm.invoke([message])

            # 提取文本
            hypothetical_doc = response.content.strip()

            # 记录假设文档长度
            logger.info(f"假设文档生成成功，长度: {len(hypothetical_doc)}")

        except TimeoutError:
            logger.error("LLM调用超时")
            raise

        except Exception as e:
            logger.error(f"生成假设文档时出错: {e}", exc_info=True)
            raise
        
        if self.enable_cache:
            self.cache[query] = hypothetical_doc
        
        return hypothetical_doc

    def search(
        self,
        query: str,
        top_k: int = 5,
        fallback_to_base: bool = True
    ) -> List[Dict[str, Any]]:
        """
        搜索假设文档并返回top_k结果

        Args:
            query: 查询文本（错误信息）
            top_k: 返回结果数量，默认5个
            fallback_to_base: 当HyDE失败时是否回退到基础检索器，默认True

        Returns:
            包含假设文档内容和元数据的结果列表

        Raises:
            ValueError: 当query为空时
        """
        logger.info(f"开始HyDE检索：{query[:50]}...")

        # 输入验证
        if not query or not isinstance(query, str):
            raise ValueError("query必须是非空字符串")
        if top_k <= 0 or top_k > 20:
            raise ValueError("top_k必须大于0且不超过20")

        try:
            # 生成假设文档
            hypothetical_doc = self.generate_hypothetical_doc(query)
            
            logger.info(f"假设文档生成成功，长度：{len(hypothetical_doc)}")

            # 使用假设文档进行检索
            results = self.base_retriever.search(
                hypothetical_doc,
                top_k=top_k,
            )
            
            logger.info(f"成功从HyDE检索到 {len(results)} 个结果")
            return results
            
        except Exception as e:
            logger.error(f"HyDE检索失败: {e}", exc_info=True)
            if fallback_to_base:
                logger.info("回退到基础检索器")
                return self.base_retriever.search(
                    query,
                    top_k=top_k,
                )
            raise


if __name__ == "__main__":
    print("=" * 60)
    print("测试 HyDERetriever")
    print("=" * 60)
    
    # 初始化（base_retriever暂时用None）
    hyde = HyDERetriever(base_retriever=None)
    print("✅ HyDERetriever初始化成功\n")
    
    # 测试生成假设文档
    test_query = "AttributeError: 'NoneType' object has no attribute 'name'"
    print(f"测试Query: {test_query}\n")
    
    print("正在生成假设文档...")
    try:
        hypothetical = hyde.generate_hypothetical_doc(test_query)
        print("\n" + "=" * 60)
        print("生成的假设文档:")
        print("=" * 60)
        print(hypothetical)
        print("=" * 60)
        print(f"\n✅ 假设文档生成成功！长度: {len(hypothetical)} 字符")
    except Exception as e:
        print(f"❌ 生成失败: {e}")