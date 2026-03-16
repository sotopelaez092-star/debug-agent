#!/bin/bash
# 使用 Claude Code (配置 MiMo) 测试 V2 Benchmark
# 自动化测试 + 自动还原

set -e

echo "======================================================================"
echo "Claude Code (MiMo) V2 Benchmark 测试"
echo "======================================================================"
echo ""

# 检查 MiMo 配置
if [ -z "$ANTHROPIC_BASE_URL" ]; then
    echo "❌ 错误: ANTHROPIC_BASE_URL 未设置"
    echo "请先配置:"
    echo "  export ANTHROPIC_BASE_URL=\"https://api.xiaomimimo.com/anthropic\""
    echo "  export ANTHROPIC_AUTH_TOKEN=\"your-key\""
    exit 1
fi

echo "✅ MiMo 配置:"
echo "   API: $ANTHROPIC_BASE_URL"
echo ""

# 检查 git
if ! git rev-parse --git-dir > /dev/null 2>&1; then
    echo "❌ 错误: 不在 git 仓库中"
    exit 1
fi

# 测试用例列表
if [ "$1" == "--all" ]; then
    echo "模式: 完整测试（全部用例）"
    TEST_LIMIT=""
elif [ "$1" == "--quick" ]; then
    echo "模式: 快速测试（6个用例）"
    TEST_LIMIT=6
else
    echo "模式: 自定义测试"
    TEST_LIMIT=$1
fi

# 扫描测试用例
echo ""
echo "扫描测试用例..."
CASES=()
COUNT=0

for error_type_dir in tests/test_cases_v2/*/; do
    if [ ! -d "$error_type_dir" ]; then
        continue
    fi

    for case_dir in "$error_type_dir"case_*/; do
        if [ ! -d "$case_dir" ]; then
            continue
        fi

        if [ -f "$case_dir/main.py" ]; then
            CASES+=("$case_dir")
            COUNT=$((COUNT + 1))

            if [ -n "$TEST_LIMIT" ] && [ $COUNT -ge $TEST_LIMIT ]; then
                break 2
            fi
        fi
    done
done

echo "找到 ${#CASES[@]} 个测试用例"
echo ""

# 初始化统计
SUCCESS_COUNT=0
FAILED_COUNT=0
TOTAL_DURATION=0
TIMESTAMP=$(date +%Y%m%d_%H%M%S)
RESULT_FILE="claude_code_mimo_results_$TIMESTAMP.txt"

# 写入结果文件头
cat > $RESULT_FILE << EOF
Claude Code (MiMo) V2 Benchmark 测试结果
========================================
测试时间: $(date)
API: $ANTHROPIC_BASE_URL
总用例数: ${#CASES[@]}

详细结果:
EOF

# 测试每个用例
for i in "${!CASES[@]}"; do
    CASE_DIR="${CASES[$i]}"
    CASE_NUM=$((i + 1))
    CASE_NAME=$(basename "$CASE_DIR")

    echo ""
    echo "======================================================================"
    echo "[$CASE_NUM/${#CASES[@]}] $CASE_NAME"
    echo "======================================================================"
    echo "路径: $CASE_DIR"
    echo ""

    # 1. 运行测试看错误
    echo "1️⃣  运行测试用例..."
    cd "$CASE_DIR"
    if python3 main.py > /tmp/test_output.txt 2>&1; then
        echo "   ⚠️  程序没有错误，跳过"
        cd - > /dev/null
        continue
    fi

    echo "   ❌ 检测到错误:"
    tail -3 /tmp/test_output.txt | sed 's/^/      /'
    echo ""
    cd - > /dev/null

    # 2. 创建还原点
    echo "2️⃣  创建还原点..."
    git add -A > /dev/null 2>&1
    git commit -m "temp: before test $CASE_NAME" --no-verify --quiet > /dev/null 2>&1
    RESTORE_COMMIT=$(git rev-parse HEAD)

    # 3. 创建修复提示
    PROMPT_FILE="$CASE_DIR/.fix_prompt.txt"
    cat > "$PROMPT_FILE" << 'PROMPT_EOF'
这个目录有一个 Python 程序出错了。

请帮我：
1. 运行 main.py 查看错误
2. 分析错误原因
3. 修复错误（直接修改文件）
4. 运行 main.py 验证修复成功

不要只给建议，要实际修复代码。
PROMPT_EOF

    # 4. 使用 Claude Code 修复
    echo "3️⃣  使用 Claude Code (MiMo) 修复..."
    START_TIME=$(date +%s)

    # 使用 claude 命令行（非交互模式）
    cd "$CASE_DIR"

    # 使用 -p 参数进行非交互模式
    if timeout 180 /opt/homebrew/bin/claude -p "$(cat .fix_prompt.txt)" > /tmp/claude_output.txt 2>&1; then
        CLAUDE_EXIT=0
    else
        CLAUDE_EXIT=$?
    fi

    END_TIME=$(date +%s)
    DURATION=$((END_TIME - START_TIME))
    TOTAL_DURATION=$((TOTAL_DURATION + DURATION))

    cd - > /dev/null

    if [ $CLAUDE_EXIT -ne 0 ] && [ $CLAUDE_EXIT -ne 124 ]; then
        echo "   ⚠️  Claude Code 执行异常 (退出码: $CLAUDE_EXIT)"
        echo ""

        # 提供手动修复选项
        echo "   请手动测试此用例:"
        echo "   ----------------------------------------"
        echo "   cd $CASE_DIR"
        echo "   claude"
        echo "   # 然后发送: $(head -1 $PROMPT_FILE)"
        echo "   ----------------------------------------"
        echo ""
        read -p "   修复完成后按 y，跳过按 n (y/n): " manual_result

        if [ "$manual_result" == "y" ]; then
            MANUAL_MODE=true
        else
            echo "   ⏭️  跳过此用例"
            git reset --hard $RESTORE_COMMIT --quiet > /dev/null 2>&1
            git reset --soft HEAD~1 --quiet > /dev/null 2>&1
            continue
        fi
    fi

    # 5. 验证修复
    echo "4️⃣  验证修复结果..."
    cd "$CASE_DIR"
    if python3 main.py > /tmp/test_output_fixed.txt 2>&1; then
        echo "   ✅ 修复成功! (耗时: ${DURATION}s)"
        SUCCESS_COUNT=$((SUCCESS_COUNT + 1))
        RESULT="成功"

        echo "$CASE_NAME: ✅ 成功 (${DURATION}s)" >> "$RESULT_FILE"
    else
        echo "   ❌ 修复失败 (耗时: ${DURATION}s)"
        echo "   错误:"
        tail -2 /tmp/test_output_fixed.txt | sed 's/^/      /'
        FAILED_COUNT=$((FAILED_COUNT + 1))
        RESULT="失败"

        echo "$CASE_NAME: ❌ 失败 (${DURATION}s)" >> "$RESULT_FILE"
    fi
    cd - > /dev/null
    echo ""

    # 6. 还原
    echo "5️⃣  还原测试用例..."
    git reset --hard $RESTORE_COMMIT --quiet > /dev/null 2>&1
    git reset --soft HEAD~1 --quiet > /dev/null 2>&1
    rm -f "$PROMPT_FILE"
    echo "   ✅ 已还原"
    echo ""

    # 当前统计
    TOTAL_TESTED=$((SUCCESS_COUNT + FAILED_COUNT))
    if [ $TOTAL_TESTED -gt 0 ]; then
        SUCCESS_RATE=$(echo "scale=1; $SUCCESS_COUNT * 100 / $TOTAL_TESTED" | bc)
        AVG_DURATION=$(echo "scale=1; $TOTAL_DURATION / $TOTAL_TESTED" | bc)
        echo "📊 当前统计: $SUCCESS_COUNT/$TOTAL_TESTED 成功 (${SUCCESS_RATE}%) | 平均耗时: ${AVG_DURATION}s"
    fi
done

# 最终统计
echo ""
echo "======================================================================"
echo "测试完成"
echo "======================================================================"
echo ""

TOTAL_TESTED=$((SUCCESS_COUNT + FAILED_COUNT))
if [ $TOTAL_TESTED -gt 0 ]; then
    SUCCESS_RATE=$(echo "scale=1; $SUCCESS_COUNT * 100 / $TOTAL_TESTED" | bc)
    AVG_DURATION=$(echo "scale=1; $TOTAL_DURATION / $TOTAL_TESTED" | bc)

    echo "总测试数: $TOTAL_TESTED"
    echo "成功数: $SUCCESS_COUNT"
    echo "失败数: $FAILED_COUNT"
    echo "成功率: ${SUCCESS_RATE}%"
    echo "平均耗时: ${AVG_DURATION}s"
    echo "总耗时: ${TOTAL_DURATION}s"
else
    echo "⚠️  无有效测试结果"
fi

# 写入结果文件
cat >> $RESULT_FILE << EOF

========================================
统计摘要:
========================================
总测试数: $TOTAL_TESTED
成功数: $SUCCESS_COUNT
失败数: $FAILED_COUNT
成功率: ${SUCCESS_RATE}%
平均耗时: ${AVG_DURATION}s
总耗时: ${TOTAL_DURATION}s
EOF

echo ""
echo "✅ 结果已保存到: $RESULT_FILE"
echo ""

# 注意事项
if [ ${#CASES[@]} -gt 0 ] && [ $TOTAL_TESTED -eq 0 ]; then
    echo "⚠️  注意:"
    echo "   Claude Code 可能不支持 --prompt 非交互模式"
    echo "   建议使用手动测试模式"
    echo ""
    echo "   运行: ./test_claude_code_mimo_manual.sh"
fi
