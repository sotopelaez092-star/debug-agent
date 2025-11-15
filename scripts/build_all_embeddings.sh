#!/bin/bash
# 批量构建所有Embedding向量库

set -e  # 遇到错误立即退出

echo "🚀 开始批量构建向量库..."
echo ""

# 定义模型列表
declare -A MODELS=(
    ["m1"]="BAAI/bge-small-en-v1.5"
    ["m2"]="BAAI/bge-base-en-v1.5"
    ["m3"]="BAAI/bge-m3"
    ["m4"]="sentence-transformers/all-MiniLM-L6-v2"
)

# 遍历构建
for model_id in "${!MODELS[@]}"; do
    model_name="${MODELS[$model_id]}"
    output_dir="data/vectorstore/embed_${model_id}"
    
    echo "================================"
    echo "📦 构建模型: ${model_id}"
    echo "   ${model_name}"
    echo "================================"
    echo ""
    
    python scripts/build_vectorstore_for_embedding.py \
        --model-name "${model_name}" \
        --output-dir "${output_dir}" \
        --batch-size 16
    
    echo ""
    echo "✅ ${model_id} 完成！"
    echo ""
done

echo "🎉 所有向量库构建完成！"