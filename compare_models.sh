#!/bin/bash
# MiMo vs Claude 对比测试脚本

echo "======================================================================"
echo "MiMo vs Claude V2 Benchmark 对比测试"
echo "======================================================================"
echo ""

# 检查参数
if [ "$1" == "--help" ] || [ "$1" == "-h" ]; then
    echo "用法:"
    echo "  ./compare_models.sh                    # 完整对比测试（30个用例）"
    echo "  ./compare_models.sh --quick            # 快速对比测试（6个用例）"
    echo "  ./compare_models.sh --mimo-only        # 只测试 MiMo"
    echo "  ./compare_models.sh --claude-only      # 只测试 Claude"
    exit 0
fi

QUICK=""
MIMO_ONLY=false
CLAUDE_ONLY=false

if [ "$1" == "--quick" ]; then
    QUICK="--quick"
    echo "模式: 快速测试（6个用例）"
elif [ "$1" == "--mimo-only" ]; then
    MIMO_ONLY=true
    echo "模式: 只测试 MiMo"
elif [ "$1" == "--claude-only" ]; then
    CLAUDE_ONLY=true
    echo "模式: 只测试 Claude"
else
    echo "模式: 完整测试（30个用例）"
fi

echo ""

# 1. 测试 MiMo
if [ "$CLAUDE_ONLY" = false ]; then
    echo "======================================================================"
    echo "1️⃣  测试 MiMo"
    echo "======================================================================"

    if [ -z "$ANTHROPIC_BASE_URL" ]; then
        echo "⚠️  警告: ANTHROPIC_BASE_URL 未设置"
        echo "请先配置 MiMo API:"
        echo "  export ANTHROPIC_BASE_URL=\"https://your-mimo-api.com\""
        echo "  export ANTHROPIC_AUTH_TOKEN=\"your-key\""
        echo ""
        read -p "是否跳过 MiMo 测试? (y/n): " skip
        if [ "$skip" != "n" ]; then
            MIMO_ONLY=false
        fi
    fi

    if [ "$MIMO_ONLY" != false ] || [ -n "$ANTHROPIC_BASE_URL" ]; then
        python3 test_v2_benchmark.py $QUICK
        MIMO_RESULT=$(ls -t v2_test_mimo_*.json 2>/dev/null | head -1)
        echo ""
        echo "✅ MiMo 测试完成"
        echo "   结果文件: $MIMO_RESULT"
        echo ""
    fi
fi

# 2. 测试 Claude
if [ "$MIMO_ONLY" = false ]; then
    echo "======================================================================"
    echo "2️⃣  测试 Claude Sonnet"
    echo "======================================================================"
    echo "正在切换到 Claude 官方 API..."

    # 临时保存 MiMo 配置
    MIMO_BASE_URL=$ANTHROPIC_BASE_URL
    MIMO_TOKEN=$ANTHROPIC_AUTH_TOKEN

    # 清除配置以使用 Claude 官方
    unset ANTHROPIC_BASE_URL
    unset ANTHROPIC_AUTH_TOKEN

    python3 test_v2_benchmark.py $QUICK
    CLAUDE_RESULT=$(ls -t v2_test_claude_*.json 2>/dev/null | head -1)

    # 恢复 MiMo 配置
    export ANTHROPIC_BASE_URL=$MIMO_BASE_URL
    export ANTHROPIC_AUTH_TOKEN=$MIMO_TOKEN

    echo ""
    echo "✅ Claude 测试完成"
    echo "   结果文件: $CLAUDE_RESULT"
    echo ""
fi

# 3. 生成对比报告
if [ "$MIMO_ONLY" = false ] && [ "$CLAUDE_ONLY" = false ]; then
    echo "======================================================================"
    echo "3️⃣  生成对比报告"
    echo "======================================================================"

    if [ -z "$MIMO_RESULT" ]; then
        MIMO_RESULT=$(ls -t v2_test_mimo_*.json 2>/dev/null | head -1)
    fi
    if [ -z "$CLAUDE_RESULT" ]; then
        CLAUDE_RESULT=$(ls -t v2_test_claude_*.json 2>/dev/null | head -1)
    fi

    if [ -n "$MIMO_RESULT" ] && [ -n "$CLAUDE_RESULT" ]; then
        python3 << EOF
import json

print("\n" + "="*70)
print("对比报告")
print("="*70)

try:
    with open('$MIMO_RESULT') as f:
        mimo = json.load(f)
    with open('$CLAUDE_RESULT') as f:
        claude = json.load(f)

    print(f"\n{'指标':<20s} {'MiMo':<20s} {'Claude':<20s} {'差异'}")
    print("-" * 70)

    # 成功率
    mimo_rate = mimo['success_rate']
    claude_rate = claude['success_rate']
    rate_diff = mimo_rate - claude_rate
    print(f"{'成功率':<20s} {mimo_rate:>6.1f}% {claude_rate:>18.1f}% {rate_diff:>18.1f}%")

    # 平均耗时
    mimo_dur = mimo['avg_duration']
    claude_dur = claude['avg_duration']
    dur_diff = mimo_dur - claude_dur
    print(f"{'平均耗时':<20s} {mimo_dur:>6.1f}s {claude_dur:>18.1f}s {dur_diff:>+18.1f}s")

    # 平均置信度
    mimo_conf = mimo.get('avg_confidence', 0)
    claude_conf = claude.get('avg_confidence', 0)
    conf_diff = mimo_conf - claude_conf
    print(f"{'平均置信度':<20s} {mimo_conf:>6.3f} {claude_conf:>21.3f} {conf_diff:>+18.3f}")

    print("\n" + "="*70)

    # 评价
    print("\n💡 评价:")
    if rate_diff > 5:
        print(f"   🎉 MiMo 成功率明显更高 (+{rate_diff:.1f}%)")
    elif rate_diff < -5:
        print(f"   ⚠️  MiMo 成功率较低 ({rate_diff:.1f}%)")
    else:
        print(f"   ✅ 两者成功率接近 (差异 {rate_diff:.1f}%)")

    if dur_diff < -5:
        print(f"   ⚡ MiMo 速度更快 ({dur_diff:.1f}s)")
    elif dur_diff > 5:
        print(f"   🐌 MiMo 速度较慢 (+{dur_diff:.1f}s)")
    else:
        print(f"   ✅ 两者速度接近 (差异 {dur_diff:.1f}s)")

    print()

except FileNotFoundError as e:
    print(f"\n❌ 找不到结果文件: {e}")
except Exception as e:
    print(f"\n❌ 生成报告失败: {e}")
EOF
    else
        echo "⚠️  缺少结果文件，无法生成对比报告"
        echo "   MiMo: $MIMO_RESULT"
        echo "   Claude: $CLAUDE_RESULT"
    fi
fi

echo ""
echo "======================================================================"
echo "✅ 测试完成"
echo "======================================================================"
echo ""
echo "结果文件:"
[ -n "$MIMO_RESULT" ] && echo "  MiMo:   $MIMO_RESULT"
[ -n "$CLAUDE_RESULT" ] && echo "  Claude: $CLAUDE_RESULT"
echo ""
