#!/bin/bash

echo "Verifying all ImportError test cases..."
echo "========================================"

for case_dir in /home/user/gemini-cli/benchmark/test_cases_v2/import_error/case_*/; do
    case_name=$(basename "$case_dir")
    echo ""
    echo "Testing: $case_name"
    echo "---"
    cd "$case_dir"
    
    # Run main.py and capture error
    if python main.py 2>&1 | grep -E "(ImportError|ModuleNotFoundError|AttributeError)" | head -1; then
        echo "✓ Error triggered successfully"
    else
        echo "✗ No expected error found"
    fi
done

echo ""
echo "========================================"
echo "Verification complete!"
