#!/bin/bash
# 使用 git 自动还原的 MiMo 测试脚本

echo "======================================================================"
echo "MiMo 真实修复能力测试（使用 git 自动还原）"
echo "======================================================================"
echo ""

# 检查是否在 git 仓库中
if ! git rev-parse --git-dir > /dev/null 2>&1; then
    echo "❌ 错误: 不在 git 仓库中"
    exit 1
fi

# 检查是否有未提交的更改
if ! git diff-index --quiet HEAD --; then
    echo "⚠️  警告: 检测到未提交的更改"
    echo ""
    git status --short
    echo ""
    read -p "是否继续? 测试会创建临时提交并在完成后还原 (y/n): " confirm
    if [ "$confirm" != "y" ]; then
        echo "已取消"
        exit 0
    fi
fi

# 保存当前分支
CURRENT_BRANCH=$(git branch --show-current)
echo "当前分支: $CURRENT_BRANCH"
echo ""

# 测试用例列表
if [ "$1" == "--quick" ]; then
    echo "模式: 快速测试（3个代表性用例）"
    TEST_CASES=(
        "tests/test_cases_v2/name_error/case_01_refactored_function"
        "tests/test_cases_v2/import_error/case_01_typo_module"
        "tests/test_cases_v2/attribute_error/case_01_deep_inheritance"
    )
else
    echo "模式: 完整测试（手动指定用例）"
    TEST_CASES=(
        "tests/test_cases_v2/name_error/case_01_refactored_function"
        "tests/test_cases_v2/import_error/case_01_typo_module"
        "tests/test_cases_v2/attribute_error/case_01_deep_inheritance"
        "tests/test_cases_v2/type_error/case_01_wrong_arg_count"
        "tests/test_cases_v2/key_error/case_01_config_restructure"
        "tests/test_cases_v2/circular_import/case_01_deep_chain"
    )
fi

echo "将测试 ${#TEST_CASES[@]} 个用例"
echo ""

# 结果统计
SUCCESS_COUNT=0
TOTAL_COUNT=0

# 测试每个用例
for case_path in "${TEST_CASES[@]}"; do
    if [ ! -d "$case_path" ]; then
        echo "⚠️  跳过: 目录不存在 $case_path"
        continue
    fi

    TOTAL_COUNT=$((TOTAL_COUNT + 1))
    CASE_NAME=$(basename $case_path)

    echo ""
    echo "======================================================================"
    echo "[$TOTAL_COUNT/${#TEST_CASES[@]}] 测试: $CASE_NAME"
    echo "======================================================================"
    echo "路径: $case_path"
    echo ""

    # 1. 运行测试查看错误
    echo "1️⃣  运行测试用例..."
    cd "$case_path"
    python3 main.py > /tmp/test_output.txt 2>&1
    INITIAL_EXIT_CODE=$?
    cd - > /dev/null

    if [ $INITIAL_EXIT_CODE -eq 0 ]; then
        echo "   ⚠️  程序没有错误，跳过"
        continue
    fi

    echo "   ❌ 检测到错误"
    echo "   错误信息:"
    head -5 /tmp/test_output.txt | sed 's/^/      /'
    echo ""

    # 2. 创建临时提交点
    echo "2️⃣  创建还原点..."
    git add -A > /dev/null 2>&1
    git commit -m "temp: before testing $CASE_NAME" --no-verify > /dev/null 2>&1
    RESTORE_COMMIT=$(git rev-parse HEAD)
    echo "   ✅ 还原点: ${RESTORE_COMMIT:0:8}"
    echo ""

    # 3. 使用 Claude Code (MiMo) 修复
    echo "3️⃣  使用 Claude Code (MiMo) 进行修复..."
    echo ""
    echo "   请在新终端窗口中运行:"
    echo "   ----------------------------------------"
    echo "   cd $case_path"
    echo "   claude"
    echo ""
    echo "   然后发送以下任务:"
    echo "   ----------------------------------------"
    echo "   运行 main.py，分析错误，修复错误，验证修复成功"
    echo "   ----------------------------------------"
    echo ""
    read -p "   修复完成后按回车继续..."
    echo ""

    # 4. 验证修复
    echo "4️⃣  验证修复结果..."
    cd "$case_path"
    python3 main.py > /tmp/test_output_fixed.txt 2>&1
    FIXED_EXIT_CODE=$?
    cd - > /dev/null

    if [ $FIXED_EXIT_CODE -eq 0 ]; then
        echo "   ✅ 修复成功!"
        SUCCESS_COUNT=$((SUCCESS_COUNT + 1))
        echo ""
        echo "   修复后的输出:"
        head -3 /tmp/test_output_fixed.txt | sed 's/^/      /'
    else
        echo "   ❌ 修复失败，程序仍有错误"
        echo ""
        echo "   修复后的错误:"
        head -5 /tmp/test_output_fixed.txt | sed 's/^/      /'
    fi
    echo ""

    # 5. 还原到测试前状态
    echo "5️⃣  还原测试用例到原始状态..."
    git reset --hard $RESTORE_COMMIT > /dev/null 2>&1
    git reset --soft HEAD~1 > /dev/null 2>&1
    echo "   ✅ 已还原"
    echo ""

    echo "📊 当前统计: $SUCCESS_COUNT/$TOTAL_COUNT 成功 ($(echo "scale=1; $SUCCESS_COUNT * 100 / $TOTAL_COUNT" | bc)%)"
done

# 最终统计
echo ""
echo "======================================================================"
echo "测试完成"
echo "======================================================================"
echo ""
echo "总用例数: $TOTAL_COUNT"
echo "成功数: $SUCCESS_COUNT"
echo "成功率: $(echo "scale=1; $SUCCESS_COUNT * 100 / $TOTAL_COUNT" | bc)%"
echo ""

# 保存结果
TIMESTAMP=$(date +%Y%m%d_%H%M%S)
RESULT_FILE="mimo_manual_test_results_$TIMESTAMP.txt"

cat > $RESULT_FILE << EOF
MiMo 真实修复能力测试结果

测试时间: $(date)
模型: MiMo
API: $ANTHROPIC_BASE_URL

总用例数: $TOTAL_COUNT
成功数: $SUCCESS_COUNT
成功率: $(echo "scale=1; $SUCCESS_COUNT * 100 / $TOTAL_COUNT" | bc)%

测试用例:
EOF

for case_path in "${TEST_CASES[@]}"; do
    echo "  - $case_path" >> $RESULT_FILE
done

echo "✅ 结果已保存到: $RESULT_FILE"
echo ""
