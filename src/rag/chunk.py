"""文本分块器"""
from typing import List, Dict
import re


class TextChunker:
    """文本分块器
    
    将长文本切分成固定大小的块，支持重叠
    """
    
    def __init__(self, chunk_size: int = 500, chunk_overlap: int = 50):
        """
        Args:
            chunk_size: 每个块的最大字符数
            chunk_overlap: 块之间的重叠字符数
        """
        self.chunk_size = chunk_size
        self.chunk_overlap = chunk_overlap
        
        # 验证参数
        if chunk_overlap >= chunk_size:
            raise ValueError("chunk_overlap必须小于chunk_size")
        
        print(f"✅ TextChunker初始化: chunk_size={chunk_size}, overlap={chunk_overlap}")
    
    def split_text(self, text: str) -> List[str]:
        """将单个文本切分成多个块
        
        Args:
            text: 要切分的文本
            
        Returns:
            文本块列表
        """
        if not text or len(text.strip()) == 0:
            return []
        
        # 清理文本
        text = text.strip()
        chunks = []
        start = 0
        
        while start < len(text):
            # 计算当前块的结束位置
            end = start + self.chunk_size
            
            # 如果不是最后一块，尝试在合适的位置断开
            if end < len(text):
                # 确保至少前进这么多字符
                min_progress = self.chunk_overlap + 50
                # 查找最近的句号、换行符或空格
                for sep in ['\n\n', '\n', '. ', ' ']:
                    last_sep = text.rfind(sep, start, end)
                    # 确保分隔符位置足够靠后，避免死循环
                    if last_sep != -1 and last_sep >= start + min_progress:
                        end = last_sep + len(sep)
                        break
            
            # 提取块
            chunk = text[start:end].strip()
            if chunk:
                chunks.append(chunk)
            
            # 更新起始位置（确保前进）
            start = max(start + 1, end - self.chunk_overlap)
            if start >= len(text):
                break
        
        return chunks
    
    def process_qa_data(self, qa_list: List[Dict]) -> List[Dict]:
        """批量处理QA数据
        
        Args:
            qa_list: QA数据列表，每项包含 question, answer, combined
            
        Returns:
            处理后的文本块列表，包含元数据
        """
        all_chunks = []
        
        for idx, qa in enumerate(qa_list):
            # 对combined字段进行分块
            text = qa.get('combined', '')
            chunks = self.split_text(text)
            
            # 为每个块添加元数据
            for chunk_idx, chunk in enumerate(chunks):
                all_chunks.append({
                    'text': chunk,
                    'source_id': qa.get('id', idx),
                    'chunk_index': chunk_idx,
                    'total_chunks': len(chunks),
                    'question': qa.get('question', '')[:100]  # 保留前100字符作为参考
                })
            
            if (idx + 1) % 100 == 0:
                print(f"  已处理: {idx + 1}/{len(qa_list)}")
        
        print(f"✅ 总共生成 {len(all_chunks)} 个文本块")
        return all_chunks