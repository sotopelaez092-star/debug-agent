# 🎓 Week 2 复习文档 - RAG检索系统

> **适合打印复习** | 生成日期：2025-11-07  
> **完成内容**：BaseRetriever + RerankerRetriever  
> **代码量**：约350行生产级代码

---

## 📋 目录

1. [Week 2 完成总览](#week-2-完成总览)
2. [系统架构](#系统架构)
3. [BaseRetriever 核心代码](#baseretriever-核心代码)
4. [RerankerRetriever 核心代码](#rerankerretriever-核心代码)
5. [关键知识点](#关键知识点)
6. [常见问题和解决方案](#常见问题和解决方案)
7. [Week 3 预习](#week-3-预习)

---

## Week 2 完成总览

### ✅ 完成的模块

| 模块 | 文件 | 代码量 | 功能 |
|------|------|--------|------|
| **BaseRetriever** | `src/rag/retriever.py` | ~200行 | 基础向量检索 |
| **RerankerRetriever** | `src/rag/reranker_retriever.py` | ~150行 | 两阶段检索 |
| **测试** | `tests/test_retriever.py` | ~100行 | 单元测试 |
| **测试** | `tests/test_reranker.py` | ~100行 | 对比测试 |

**总计**：约550行生产级代码

---

### 🎯 核心成果

1. **完整的检索流程**
   - 查询预处理
   - 向量检索
   - 结果过滤
   - 格式化输出

2. **两阶段检索**
   - 第一阶段：快速召回（向量检索）
   - 第二阶段：精细排序（Reranker）

3. **生产级代码质量**
   - 完整的输入验证
   - 异常处理
   - 日志记录
   - 类型提示
   - 文档字符串

---

## 系统架构

### 整体流程

```
用户输入错误信息
    ↓
[1. 查询预处理]
    清理 Traceback
    提取关键信息
    限制长度
    ↓
[2. 向量检索] ← BaseRetriever
    召回 20 个候选
    ↓
[3. 相似度过滤]
    过滤低分结果
    ↓
[4. Reranker精排] ← RerankerRetriever (可选)
    重新打分
    精细排序
    ↓
[5. 返回Top-K]
    返回最终结果
```

---

### 类关系图

```
BaseRetriever (基类)
    │
    ├── __init__()          # 初始化
    ├── search()            # 主接口
    ├── _preprocess_query() # 预处理
    ├── _vector_search()    # 向量检索
    ├── _filter_by_similarity() # 过滤
    └── _format_results()   # 格式化
    
    ↑ 继承
    
RerankerRetriever (子类)
    │
    ├── __init__()          # 初始化 + 加载Reranker
    ├── search()            # 覆盖：两阶段检索
    └── _rerank()           # 新增：Reranker精排
```

---

## BaseRetriever 核心代码

### 1. `__init__` - 初始化

```python
def __init__(
    self,
    collection: Collection,      # ChromaDB collection
    min_similarity: float = 0.5, # 最低相似度阈值
    recall_factor: int = 4       # 召回倍数
):
    """
    关键点：
    1. 参数验证（防御性编程）
    2. 保存配置
    3. 记录日志
    """
    
    # 验证 collection
    if not collection:
        raise ValueError('collection不能为空')
    
    # 验证 min_similarity（允许负数，因为可能有embedding不匹配）
    if not isinstance(min_similarity, (int, float)):
        raise ValueError('min_similarity必须是数字')
    if min_similarity < -1 or min_similarity > 1:
        raise ValueError('min_similarity必须在-1到1之间')
    
    # 验证 recall_factor
    if not isinstance(recall_factor, int):
        raise TypeError('recall_factor必须是整数')
    if recall_factor < 1:
        raise ValueError('recall_factor必须 >= 1')
    
    # 保存配置
    self.collection = collection
    self.min_similarity = min_similarity
    self.recall_factor = recall_factor
```

**设计原则**：
- ✅ **输入验证优先**：在函数入口验证所有参数
- ✅ **明确的错误信息**：告诉用户哪里错了
- ✅ **类型检查**：不只检查值，还检查类型

---

### 2. `_preprocess_query` - 查询预处理

```python
def _preprocess_query(self, query: str) -> str:
    """
    目标：清理错误信息，提取关键部分
    
    处理：
    1. 去除 Traceback 行
    2. 去除文件路径 (File "xxx", line xxx)
    3. 保留错误类型和消息
    4. 限制长度 (500字符)
    """
    
    # 按行分割
    lines = query.split('\n')
    
    # 过滤无用行
    cleaned_lines = []
    for line in lines:
        # 跳过这些行
        if line.strip().startswith('Traceback'):
            continue
        if line.strip().startswith('File'):
            continue
        if not line.strip():  # 空行
            continue
        
        # 保留有用的行
        cleaned_lines.append(line.strip())
    
    # 重新组合
    cleaned = '\n'.join(cleaned_lines)
    
    # 限制长度
    MAX_LENGTH = 500
    if len(cleaned) > MAX_LENGTH:
        logger.warning(f"查询文本过长，截断")
        cleaned = cleaned[:MAX_LENGTH]
    
    return cleaned
```

**为什么需要预处理？**
- 用户输入的错误信息很乱（包含路径、行号等）
- Embedding模型有token限制（通常512或1024）
- 只保留关键信息能提高检索准确率

**示例**：
```
输入：
Traceback (most recent call last):
  File "test.py", line 10
    print(user.name)
AttributeError: 'NoneType' object has no attribute 'name'

输出：
print(user.name)
AttributeError: 'NoneType' object has no attribute 'name'
```

---

### 3. `_vector_search` - 向量检索

```python
def _vector_search(
    self, 
    query: str, 
    n_results: int  # 召回数量 = top_k * recall_factor
) -> Dict[str, List]:
    """
    调用 ChromaDB 进行向量检索
    
    返回格式（嵌套列表）：
    {
        'ids': [['id1', 'id2', ...]],
        'documents': [['doc1', 'doc2', ...]],
        'metadatas': [[{...}, {...}, ...]],
        'distances': [[0.2, 0.3, ...]]
    }
    """
    try:
        logger.debug(f"开始向量检索，n_results={n_results}")
        
        # 调用 ChromaDB
        results = self.collection.query(
            query_texts=[query],  # 注意：必须是列表
            n_results=n_results,
            include=['documents', 'metadatas', 'distances']
        )
        
        # 检查结果数量
        num_results = len(results['ids'][0]) if results['ids'] else 0
        logger.info(f"检索完成，召回{num_results}个文档")
        
        return results
        
    except Exception as e:
        logger.error(f"向量检索失败: {e}", exc_info=True)
        raise
```

**关键点**：
- `query_texts` 必须是列表（即使只查一个）
- 返回结果是嵌套列表（第一层是batch）
- 异常处理：记录完整的错误堆栈（`exc_info=True`）

---

### 4. `_filter_by_similarity` - 过滤低分

```python
def _filter_by_similarity(
    self,
    raw_results: Dict[str, List],
    min_similarity: float
) -> Dict[str, List]:
    """
    过滤相似度低于阈值的结果
    
    核心：distance → similarity
    公式：similarity = 1 - distance
    """
    
    # 1. 解包嵌套列表
    ids = raw_results['ids'][0] if raw_results['ids'] else []
    documents = raw_results['documents'][0] if raw_results['documents'] else []
    metadatas = raw_results['metadatas'][0] if raw_results['metadatas'] else []
    distances = raw_results['distances'][0] if raw_results['distances'] else []
    
    # 2. 过滤
    filtered_ids = []
    filtered_documents = []
    filtered_metadatas = []
    filtered_distances = []
    
    for id, doc, meta, dist in zip(ids, documents, metadatas, distances):
        # 计算相似度
        similarity = 1 - dist
        
        # 过滤
        if similarity >= min_similarity:
            filtered_ids.append(id)
            filtered_documents.append(doc)
            filtered_metadatas.append(meta)
            filtered_distances.append(dist)
    
    # 3. 重新打包（保持ChromaDB格式）
    return {
        'ids': [filtered_ids],
        'documents': [filtered_documents],
        'metadatas': [filtered_metadatas],
        'distances': [filtered_distances]
    }
```

**理解 distance vs similarity**：

| 度量 | 范围 | 含义 | 越小/越大越好 |
|------|------|------|---------------|
| **distance** | [0, 2] | 距离 | 越小越好 |
| **similarity** | [-1, 1] | 相似度 | 越大越好 |

**转换公式**：`similarity = 1 - distance`

**示例**：
- distance = 0.2 → similarity = 0.8 (很相似)
- distance = 1.5 → similarity = -0.5 (不相似)

---

### 5. `_format_results` - 格式化输出

```python
def _format_results(
    self,
    raw_results: Dict[str, List],
    top_k: int
) -> List[Dict[str, Any]]:
    """
    把 ChromaDB 的嵌套列表格式
    转换成清晰的字典列表
    """
    
    # 1. 解包
    ids = raw_results['ids'][0] if raw_results['ids'] else []
    documents = raw_results['documents'][0] if raw_results['documents'] else []
    metadatas = raw_results['metadatas'][0] if raw_results['metadatas'] else []
    distances = raw_results['distances'][0] if raw_results['distances'] else []
    
    # 2. 转换成字典
    results = []
    for id, doc, meta, dist in zip(ids, documents, metadatas, distances):
        results.append({
            'id': id,
            'content': doc,         # 注意字段名
            'metadata': meta,       # 单数
            'similarity': 1 - dist,
            'distance': dist
        })
    
    # 3. 排序（按相似度降序）
    results.sort(key=lambda x: x['similarity'], reverse=True)
    
    # 4. 取Top-K + 添加rank
    final_results = []
    for rank, result in enumerate(results[:top_k], start=1):
        result['rank'] = rank
        final_results.append(result)
    
    return final_results
```

**为什么需要格式化？**
- ChromaDB的返回格式很复杂（嵌套列表）
- 后续Agent需要清晰的数据结构
- 添加rank方便展示

---

### 6. `search` - 主流程

```python
def search(
    self,
    query: str,
    top_k: int = 5
) -> List[Dict[str, Any]]:
    """
    主接口：完整的检索流程
    
    流程：
    1. 输入验证
    2. 查询预处理
    3. 向量检索（召回更多）
    4. 过滤低分
    5. 格式化输出
    """
    
    # 1. 输入验证
    if not query or not isinstance(query, str):
        raise ValueError('query必须是非空字符串')
    if not isinstance(top_k, int) or top_k < 1 or top_k > 100:
        raise ValueError('top_k必须在1-100之间')
    
    logger.info(f"开始检索，query长度={len(query)}，top_k={top_k}")
    
    # 2. 预处理
    cleaned_query = self._preprocess_query(query)
    
    # 3. 向量检索（召回 top_k * recall_factor 个）
    n_results = top_k * self.recall_factor
    raw_results = self._vector_search(cleaned_query, n_results)
    
    # 4. 过滤
    filtered_results = self._filter_by_similarity(
        raw_results, 
        self.min_similarity
    )
    
    # 5. 格式化
    final_results = self._format_results(filtered_results, top_k)
    
    logger.info(f"检索完成，返回{len(final_results)}个结果")
    
    return final_results
```

**设计模式：模板方法**
- `search()` 是模板，定义了整体流程
- 每个步骤是一个私有方法
- 子类可以覆盖某些步骤（如 RerankerRetriever 覆盖 search）

---

## RerankerRetriever 核心代码

### 为什么需要 Reranker？

**问题**：向量检索不够精准
- 向量相似度只是粗略的语义匹配
- 不能理解细粒度的语义关系

**解决**：两阶段检索
```
阶段1：向量检索（快速召回）
    从 10,000 个文档中召回 20 个候选
    速度：毫秒级
    
阶段2：Reranker（精细排序）
    从 20 个候选中精选 5 个
    速度：秒级
    精度：更高
```

---

### 1. `__init__` - 初始化 + 加载模型

```python
def __init__(
    self,
    collection,
    reranker_model_name: str = "BAAI/bge-reranker-base",
    min_similarity: float = 0.5,
    recall_factor: int = 4
):
    """
    核心：加载 Reranker 模型
    """
    
    # 1. 验证
    if not reranker_model_name or not isinstance(reranker_model_name, str):
        raise ValueError("reranker_model_name必须是非空字符串")
    
    # 2. 调用父类初始化
    super().__init__(collection, min_similarity, recall_factor)
    
    # 3. 加载 Reranker 模型
    logger.info(f"加载Reranker模型: {reranker_model_name}")
    try:
        self.reranker = FlagReranker(
            reranker_model_name, 
            use_fp16=True  # 使用半精度，节省内存
        )
        logger.info("✅ Reranker模型加载完成")
    except Exception as e:
        logger.error(f"❌ Reranker模型加载失败: {e}", exc_info=True)
        raise
```

**关键点**：
- 继承了 BaseRetriever，复用了所有基础方法
- 只需要额外加载 Reranker 模型
- 异常处理：模型加载可能失败（网络、磁盘空间等）

**使用的模型**：
- `BAAI/bge-reranker-base`：278MB，效果好
- 第一次运行会自动下载

---

### 2. `search` - 两阶段检索

```python
def search(self, query: str, top_k: int = 5) -> List[Dict[str, Any]]:
    """
    覆盖父类的 search 方法
    
    流程：
    1. 向量检索（召回更多候选）
    2. Reranker 精排
    """
    
    logger.info(f"开始两阶段检索，top_k={top_k}")
    
    # 阶段1：向量检索（召回 top_k * recall_factor 个）
    n_candidates = top_k * self.recall_factor
    candidates = super().search(query, top_k=n_candidates)
    
    # 阶段2：Rerank
    reranked = self._rerank(query, candidates, top_k)
    
    logger.info(f"检索完成，返回{len(reranked)}个结果")
    
    return reranked
```

**为什么要召回更多候选？**
- 目标：返回 5 个结果
- 召回：5 × 4 = 20 个候选
- 原因：给 Reranker 更多选择，提高精排效果

**继承的妙处**：
- 调用 `super().search()` 复用了父类的全部逻辑
- 只需要加一个 Rerank 步骤

---

### 3. `_rerank` - Reranker精排

```python
def _rerank(
    self,
    query: str,
    candidates: List[Dict[str, Any]],
    top_k: int
) -> List[Dict[str, Any]]:
    """
    使用 Reranker 模型重新打分和排序
    """
    
    # 1. 边界检查
    if not candidates:
        logger.warning("没有候选文档需要rerank")
        return []
    
    # 2. 准备输入格式
    # Reranker 需要 [[query, doc1], [query, doc2], ...]
    pairs = [[query, doc['content']] for doc in candidates]
    
    # 3. 调用 Reranker 打分
    try:
        scores = self.reranker.compute_score(pairs)
    except Exception as e:
        logger.error(f"Rerank失败：{e}", exc_info=True)
        return candidates[:top_k]  # 失败时返回原始排序
    
    # 4. 处理单个结果的情况
    if not isinstance(scores, list):
        scores = [scores]
    
    # 5. 将分数添加到文档中
    for doc, score in zip(candidates, scores):
        doc['rerank_score'] = float(score)
    
    # 6. 按 rerank_score 排序（降序）
    reranked = sorted(
        candidates,
        key=lambda x: x['rerank_score'],
        reverse=True
    )
    
    # 7. 取 Top-K + 更新rank
    final_results = []
    for rank, doc in enumerate(reranked[:top_k], start=1):
        doc['rank'] = rank
        final_results.append(doc)
    
    logger.info(f"Rerank完成，最高分：{final_results[0]['rerank_score']:.3f}")
    
    return final_results
```

**Reranker 输入格式**：
```python
[
    [query, document1],
    [query, document2],
    [query, document3],
    ...
]
```

**Reranker 输出**：
```python
[score1, score2, score3, ...]  # 每个文档的相关性分数
```

**关键设计**：
- ✅ 异常处理：Rerank失败时有fallback（返回原始排序）
- ✅ 类型处理：单个结果时转成列表
- ✅ 失败友好：不会因为Rerank失败导致整个检索失败

---

## 关键知识点

### 1. 向量检索 vs Reranker

| 特性 | 向量检索 | Reranker |
|------|---------|----------|
| **速度** | 快（毫秒级） | 慢（秒级） |
| **精度** | 中等 | 高 |
| **原理** | 向量相似度（余弦等） | 深度模型（理解语义） |
| **适用** | 海量数据快速召回 | 少量候选精细排序 |
| **计算** | 简单数值计算 | Transformer模型推理 |

**类比**：
- 向量检索 = 初试（快速筛掉不合格的）
- Reranker = 复试（从候选中挑最好的）

---

### 2. 为什么需要召回倍数（recall_factor）？

**问题**：如果直接召回5个，准确率可能不够

**解决**：先召回20个，再精选5个

```python
# 不好的做法
candidates = vector_search(query, top_k=5)  # 只召回5个

# 好的做法
candidates = vector_search(query, top_k=20)  # 先召回20个
final = rerank(candidates, top_k=5)         # 再精选5个
```

**效果**：
- 向量检索可能把相关文档排到第10位
- 先召回20个，Reranker有机会把它排到前5

---

### 3. Distance vs Similarity

**ChromaDB 返回的是 distance（距离）**：
- 距离 = 两个向量之间的"远近"
- 越小越相似
- 范围：[0, 2]（cosine距离）

**我们需要的是 similarity（相似度）**：
- 相似度 = 两个向量的"相似程度"
- 越大越相似
- 范围：[-1, 1]

**转换公式**：
```python
similarity = 1 - distance
```

**示例**：
```
distance = 0.1  → similarity = 0.9  (非常相似)
distance = 0.5  → similarity = 0.5  (一般相似)
distance = 1.2  → similarity = -0.2 (不相似)
```

---

### 4. 生产级代码 vs 能跑的代码

| 标准 | 能跑的代码 | 生产级代码 |
|------|-----------|-----------|
| **输入验证** | 可能没有 | ✅ 必须有 |
| **异常处理** | try-except | try-except + 日志 + 降级 |
| **日志** | print() | logger (分级) |
| **类型提示** | 没有 | ✅ 所有参数和返回值 |
| **文档** | 没有或简单 | ✅ 详细的docstring |
| **边界情况** | 可能崩溃 | ✅ 优雅处理 |
| **测试** | 手动测试 | ✅ 自动化测试 |

**例子**：

```python
# ❌ 能跑的代码
def search(query, top_k):
    results = db.query(query, top_k)
    return results

# ✅ 生产级代码
def search(
    self,
    query: str,
    top_k: int = 5
) -> List[Dict[str, Any]]:
    """
    检索相关文档
    
    Args:
        query: 查询文本
        top_k: 返回结果数量
        
    Returns:
        相关文档列表
        
    Raises:
        ValueError: 当query为空时
    """
    # 输入验证
    if not query:
        raise ValueError("query不能为空")
    if top_k < 1:
        raise ValueError("top_k必须 >= 1")
    
    # 异常处理 + 日志
    try:
        logger.info(f"开始检索，top_k={top_k}")
        results = self.db.query(query, top_k)
        logger.info(f"检索完成，返回{len(results)}个结果")
        return results
    except Exception as e:
        logger.error(f"检索失败: {e}", exc_info=True)
        raise
```

---

### 5. 继承的妙处

**不用继承**（代码重复）：
```python
class BaseRetriever:
    def search(self, query, top_k):
        # 1. 验证
        # 2. 预处理
        # 3. 检索
        # 4. 过滤
        # 5. 格式化
        return results

class RerankerRetriever:
    def search(self, query, top_k):
        # 1. 验证 ← 重复代码
        # 2. 预处理 ← 重复代码
        # 3. 检索 ← 重复代码
        # 4. 过滤 ← 重复代码
        # 5. 格式化 ← 重复代码
        # 6. Rerank ← 新增
        return results
```

**用继承**（代码复用）：
```python
class BaseRetriever:
    def search(self, query, top_k):
        # 完整流程
        return results

class RerankerRetriever(BaseRetriever):
    def search(self, query, top_k):
        # 复用父类
        candidates = super().search(query, top_k * 4)
        # 只加新功能
        return self._rerank(candidates, top_k)
```

**好处**：
- ✅ 代码复用
- ✅ 易维护（改一处，两个类都更新）
- ✅ 符合DRY原则（Don't Repeat Yourself）

---

## 常见问题和解决方案

### 问题1：相似度是负数

**现象**：
```
similarity=-0.162
similarity=-0.205
```

**原因**：
- Embedding函数不匹配
- 存储时用模型A，查询时用模型B
- distance > 1，导致 similarity = 1 - distance < 0

**解决方案**：
```python
# Week 3 会解决：统一 embedding 函数
# 方案1：降低阈值（临时）
retriever = BaseRetriever(collection, min_similarity=-0.5)

# 方案2：重新生成数据（推荐）
# - 创建 collection 时指定 embedding_function
# - 让 ChromaDB 自动生成 embedding
```

---

### 问题2：检索结果不相关

**现象**：
- 查询 "AttributeError"
- 返回的都是其他错误类型

**原因**：
- 数据质量问题（Week 1的数据不够好）
- Embedding 模型不匹配

**解决方案**：
- Week 3 重新准备高质量数据
- 使用统一的 embedding 函数
- 增加更多 Stack Overflow 数据

---

### 问题3：Reranker 加载失败

**现象**：
```
ImportError: cannot import name 'BaseReranker'
```

**原因**：
- 类名错误（应该是 `FlagReranker`）

**解决**：
```python
from FlagEmbedding import FlagReranker  # ✅ 正确
```

---

### 问题4：ChromaDB 返回格式混淆

**问题**：为什么是嵌套列表？

```python
results = {
    'ids': [['id1', 'id2']],  # ← 为什么有两层？
    'documents': [['doc1', 'doc2']],
    ...
}
```

**原因**：
- ChromaDB 支持批量查询
- 第一层是 batch，第二层是每个 batch 的结果

**处理**：
```python
# 我们只查一个，所以取 [0]
ids = results['ids'][0]
documents = results['documents'][0]
```

---

## Week 3 预习

### 📅 Week 3 任务概览

| 日期 | 任务 | 目标 |
|------|------|------|
| **Mon** | 数据重建 | 统一 embedding，提高质量 |
| **Tue** | HyDE 实现 | 假设性文档增强 |
| **Wed** | Multi-Query | 多查询策略 |
| **Thu** | Self-Query | 自然语言过滤 |
| **Fri** | 混合检索 | 语义 + 关键词 |
| **Sat** | A/B 测试 | 对比4种策略 |
| **Sun** | Week3 总结 | 选最优方案 |

---

### 重点学习：高级 RAG 策略

#### 1. HyDE (Hypothetical Document Embeddings)

**原理**：
```
传统检索：
    query → embedding → 搜索

HyDE：
    query → LLM生成假设答案 → embedding → 搜索
```

**为什么有效？**
- 查询和文档的语义空间不同
- 假设答案更接近真实文档
- 提高召回率

**示例**：
```python
query = "AttributeError: 'NoneType'"

# 传统：直接用 query 检索

# HyDE：先生成假设答案
hypothetical = """
这个错误是因为尝试访问 None 对象的属性。
解决方法：
1. 检查对象是否为 None
2. 使用 if obj is not None: ...
"""

# 用假设答案检索（更容易找到相关文档）
```

---

#### 2. Multi-Query

**原理**：
```
一个查询 → 生成多个变体 → 分别检索 → 合并结果
```

**为什么有效？**
- 一个查询可能表达不完整
- 多个角度提高覆盖率

**示例**：
```python
原始查询："AttributeError: 'NoneType'"

生成变体：
1. "How to fix NoneType attribute error?"
2. "Prevent accessing None object attributes"
3. "Check if object is None before use"

# 分别检索，合并结果
```

---

#### 3. 混合检索 (Hybrid Search)

**原理**：
```
向量检索（语义）+ 关键词检索（精确匹配）
```

**为什么需要？**
- 向量检索：理解语义
- 关键词检索：精确匹配专业术语

**示例**：
```python
query = "pandas DataFrame AttributeError"

# 向量检索：理解"数据框架属性错误"
# 关键词检索：精确匹配"pandas"、"DataFrame"

# 两者结合，效果更好
```

---

### Week 3 目标

**核心指标**：
- ✅ Top-5 召回率从 60% 提升到 75%+
- ✅ 对比 4 种高级策略
- ✅ 选出最优组合

**预期成果**：
- 实现 4 个高级 Retriever
- 完整的 A/B 测试报告
- 明确的策略选择依据

---

## 🎯 复习建议

### 课上看什么？（按优先级）

**高优先级**（必看）：
1. ✅ **系统架构** - 理解整体流程
2. ✅ **BaseRetriever 的 5 个方法** - 核心逻辑
3. ✅ **向量检索 vs Reranker** - 为什么需要两阶段
4. ✅ **Distance vs Similarity** - 容易混淆

**中优先级**（建议看）：
5. ✅ **RerankerRetriever 实现** - 继承的妙处
6. ✅ **生产级代码标准** - 提升代码质量
7. ✅ **常见问题** - 避免踩坑

**低优先级**（有时间再看）：
8. ✅ Week 3 预习
9. ✅ 详细代码注释

---

### 复习重点问题（自测）

**理解检查**：
1. 为什么需要预处理查询？
2. recall_factor 的作用是什么？
3. distance 和 similarity 的关系？
4. 为什么 Reranker 比向量检索准？
5. 继承 BaseRetriever 的好处？

**实践检查**：
1. 能画出完整的检索流程吗？
2. 能解释每个方法的作用吗？
3. 知道如何添加日志和异常处理吗？
4. 理解为什么要先召回 20 个再精选 5 个吗？

**答案在文档中**，看完应该都能回答！

---

## 📊 Week 2 vs Week 3 对比

| 维度 | Week 2 | Week 3 |
|------|--------|--------|
| **重点** | 流程搭建 | 效果优化 |
| **目标** | 跑通完整流程 | 提升检索准确率 |
| **代码** | BaseRetriever + RerankerRetriever | 4种高级策略 |
| **指标** | 能检索到结果 | 召回率 75%+ |
| **难度** | ⭐⭐⭐ | ⭐⭐⭐⭐ |

**Week 2 是基础，Week 3 是提升**

---

## ✅ 总结

### 你已经完成了：
1. ✅ 完整的向量检索系统（BaseRetriever）
2. ✅ 两阶段检索系统（RerankerRetriever）
3. ✅ 约 550 行生产级代码
4. ✅ 理解了 RAG 的核心原理

### 你掌握了：
1. ✅ 输入验证、异常处理、日志记录
2. ✅ 向量检索的工作原理
3. ✅ Reranker 的作用和实现
4. ✅ 继承和代码复用

### 下周要做：
1. ⏳ 重建高质量数据
2. ⏳ 实现 4 种高级 RAG 策略
3. ⏳ A/B 测试和策略选择

---

## 🎓 课上愉快！

**记住**：
- 💡 理解原理比记住代码重要
- 💡 知道为什么这样设计
- 💡 能画出流程图就说明懂了

**加油！周一见！** 🚀

---

*生成时间：2025-11-07*  
*文档版本：v1.0*  
*适用对象：课上复习*