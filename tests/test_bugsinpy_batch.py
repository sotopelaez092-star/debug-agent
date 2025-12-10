#!/usr/bin/env python3
"""
批量测试BugsInPy案例
"""

import sys
import os
import json
import ast
import time
import re

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from src.agent.context_manager import ContextManager
from src.agent.tools.error_identifier import ErrorIdentifier
from src.agent.tools.rag_searcher import RAGSearcher
from src.agent.tools.code_fixer import CodeFixer

# API Key
api_key = os.getenv('DEEPSEEK_API_KEY')
if not api_key:
    print("❌ Error: DEEPSEEK_API_KEY not set")
    sys.exit(1)

def extract_undefined_name(error_message):
    """从NameError消息中提取未定义的名称"""
    match = re.search(r"name ['\"](\w+)['\"] is not defined", error_message)
    if match:
        return match.group(1)
    return None

def test_single_case(case_info, base_path):
    """测试单个案例"""
    
    case_id = case_info['id']
    project_path = os.path.join(base_path, case_info['project_path'])
    error_file = case_info['error_file']
    undefined_name = case_info['undefined_name']
    expected_import = case_info['expected_import']
    
    print(f"\n{'='*70}")
    print(f"🧪 Testing: {case_id}")
    print(f"{'='*70}")
    
    start_time = time.time()
    
    try:
        # 读取buggy代码
        buggy_file_path = os.path.join(project_path, error_file)
        with open(buggy_file_path, 'r') as f:
            buggy_code = f.read()
        
        # 构造错误traceback
        error_traceback = f"""Traceback (most recent call last):
  File "{error_file}", line 10, in <module>
    some_function()
NameError: name '{undefined_name}' is not defined
"""
        
        # 1. ContextManager
        print("🔍 Step 1: ContextManager analyzing...")
        context_mgr = ContextManager(project_path)
        
        # 2. ErrorIdentifier
        print("🔍 Step 2: ErrorIdentifier parsing...")
        error_identifier = ErrorIdentifier()
        error_info = error_identifier.identify(error_traceback)
        
        # 提取undefined_name
        extracted_name = extract_undefined_name(error_info['error_message'])
        error_info['undefined_name'] = extracted_name or undefined_name
        
        # 3. 获取上下文
        print("🔍 Step 3: Getting context...")
        context = context_mgr.get_context_for_error(
            error_file=error_file,
            error_line=error_info.get('line', 1),
            error_type=error_info.get('error_type'),
            undefined_name=error_info.get('undefined_name')
        )
        
        # 4. RAGSearcher
        print("🔍 Step 4: RAG searching...")
        rag_searcher = RAGSearcher()
        rag_results = rag_searcher.search(
            query=f"{error_info['error_type']}: {error_info.get('error_message', '')}",
            top_k=5
        )
        
        # 5. CodeFixer
        print("🔍 Step 5: CodeFixer generating fix...")
        code_fixer = CodeFixer(api_key=api_key)
        
        error_msg = f"{error_info['error_type']}: {error_info['error_message']}"
        if context.get('import_suggestions'):
            error_msg += f"\n\n💡 建议的import:\n" + "\n".join(context['import_suggestions'])
        
        fixed_result = code_fixer.fix_code(
            buggy_code=buggy_code,
            error_message=error_msg,
            context=context,
            rag_solutions=rag_results[:3]
        )
        
        # 6. 验证
        print("🔍 Step 6: Syntax validation...")
        try:
            ast.parse(fixed_result['fixed_code'])
            syntax_ok = True
        except SyntaxError as e:
            syntax_ok = False
            print(f"  ❌ Syntax Error: {e}")
        
        # 7. 检查import
        import_added = expected_import in fixed_result['fixed_code']
        
        elapsed = time.time() - start_time
        
        # 输出结果
        print(f"\n{'='*70}")
        print(f"📊 Results for {case_id}:")
        print(f"{'='*70}")
        print(f"✅ Context Found: {len(context.get('related_files', {})) > 0}")
        print(f"✅ Import Suggested: {len(context.get('import_suggestions', [])) > 0}")
        print(f"✅ Syntax Valid: {syntax_ok}")
        print(f"✅ Expected Import Added: {import_added}")
        print(f"⏱️  Time: {elapsed:.2f}s")
        
        if context.get('import_suggestions'):
            print(f"\n💡 Suggested imports:")
            for imp in context['import_suggestions']:
                print(f"  - {imp}")
        
        success = syntax_ok and import_added
        
        return {
            'case_id': case_id,
            'success': success,
            'context_found': len(context.get('related_files', {})) > 0,
            'import_suggested': len(context.get('import_suggestions', [])) > 0,
            'syntax_valid': syntax_ok,
            'import_added': import_added,
            'time': elapsed,
            'expected_import': expected_import,
            'suggested_imports': context.get('import_suggestions', [])
        }
        
    except Exception as e:
        print(f"\n❌ Error: {e}")
        import traceback
        traceback.print_exc()
        return {
            'case_id': case_id,
            'success': False,
            'error': str(e),
            'time': time.time() - start_time
        }


def main():
    """批量测试"""
    
    print("="*70)
    print("🚀 BugsInPy Batch Testing")
    print("="*70)
    
    # 加载测试案例
    base_path = "data/BugsInPy-master"
    cases_file = os.path.join(base_path, "test_cases_info.json")
    
    with open(cases_file, 'r') as f:
        test_cases = json.load(f)
    
    print(f"\n📋 Total test cases: {len(test_cases)}")
    
    # 测试每个案例
    results = []
    for i, case in enumerate(test_cases, 1):
        print(f"\n\n{'#'*70}")
        print(f"# Test {i}/{len(test_cases)}")
        print(f"{'#'*70}")
        
        result = test_single_case(case, base_path)
        results.append(result)
        
        # 短暂休息，避免API限流
        if i < len(test_cases):
            print(f"\n⏸️  Waiting 3 seconds before next test...")
            time.sleep(3)
    
    # 生成总结报告
    print("\n\n" + "="*70)
    print("📊 FINAL SUMMARY")
    print("="*70)
    
    total = len(results)
    success_count = sum(1 for r in results if r.get('success', False))
    context_found = sum(1 for r in results if r.get('context_found', False))
    import_suggested = sum(1 for r in results if r.get('import_suggested', False))
    
    print(f"\n✅ Overall Success Rate: {success_count}/{total} ({success_count/total*100:.1f}%)")
    print(f"✅ Context Found: {context_found}/{total} ({context_found/total*100:.1f}%)")
    print(f"✅ Import Suggested: {import_suggested}/{total} ({import_suggested/total*100:.1f}%)")
    
    avg_time = sum(r.get('time', 0) for r in results) / total
    print(f"⏱️  Average Time: {avg_time:.2f}s")
    
    # 详细结果
    print(f"\n📋 Detailed Results:")
    print("-" * 70)
    for r in results:
        status = "✅ PASS" if r.get('success', False) else "❌ FAIL"
        print(f"{status} | {r['case_id']:15s} | {r.get('time', 0):5.2f}s | Context:{r.get('context_found', False)} | Import:{r.get('import_added', False)}")
    
    # 保存结果
    output_file = "bugsinpy_test_results.json"
    with open(output_file, 'w') as f:
        json.dump({
            'summary': {
                'total': total,
                'success': success_count,
                'success_rate': success_count/total,
                'avg_time': avg_time
            },
            'results': results
        }, f, indent=2)
    
    print(f"\n📄 Results saved to: {output_file}")
    print("="*70)


if __name__ == "__main__":
    main()
