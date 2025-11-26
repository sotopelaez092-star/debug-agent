"""测试跨文件案例（带error_file参数）"""
import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

import json
import tempfile
import shutil
from src.agent.debug_agent import DebugAgent
from dotenv import load_dotenv

load_dotenv()


def setup_project_files(project_path, project_files):
    """设置项目文件"""
    os.makedirs(project_path, exist_ok=True)
    
    for file_path, content in project_files.items():
        full_path = os.path.join(project_path, file_path)
        
        # 创建子目录
        dir_name = os.path.dirname(full_path)
        if dir_name:
            os.makedirs(dir_name, exist_ok=True)
        
        # 写入文件
        with open(full_path, 'w', encoding='utf-8') as f:
            f.write(content)


def test_single_case(case):
    """测试单个案例"""
    
    print("\n" + "="*60)
    print(f"测试案例: {case['name']}")
    print(f"类别: {case['category']} | 错误类型: {case['error_type']}")
    print("="*60)
    
    # 创建临时项目
    project_path = tempfile.mkdtemp(prefix=f"test_case_{case['id']}_")
    
    try:
        # 设置项目文件
        setup_project_files(project_path, case['project_files'])
        
        print(f"\n📁 项目文件:")
        for file_path in case['project_files'].keys():
            print(f"  - {file_path}")
        
        # 准备参数
        buggy_code = case['project_files'][case['error_file']]
        error_file = case['error_file']  # ← 关键参数
        error_traceback = f"""Traceback (most recent call last):
  File "{error_file}", line 1, in <module>
{case['error_message']}
"""
        
        # 创建Agent
        api_key = os.getenv('DEEPSEEK_API_KEY')
        agent = DebugAgent(project_path=project_path, api_key=api_key)
        
        # 执行debug
        print(f"\n🔧 开始修复...")
        result = agent.debug(
            buggy_code=buggy_code,
            error_traceback=error_traceback,
            error_file=error_file,  # ← 传递error_file
            max_retries=2
        )
        
        # 显示结果
        print(f"\n📊 结果:")
        print(f"  成功: {result['success']}")
        print(f"  尝试次数: {result['total_attempts']}")
        
        if result['success']:
            final_code = result['final_code']
            print(f"\n📝 最终代码:")
            print(final_code)
            
            # 检查是否使用了import
            has_import = 'import' in final_code
            has_from_import = 'from' in final_code and 'import' in final_code
            
            print(f"\n✅ 分析:")
            if has_from_import or has_import:
                print(f"  ✅ 使用了import语句（真正的跨文件！）")
            else:
                print(f"  ⚠️ 没有使用import（可能是直接定义函数）")
            
            # 显示第一次尝试
            if result['attempts']:
                first_attempt = result['attempts'][0]
                print(f"\n📋 第1次尝试:")
                print(f"  说明: {first_attempt['explanation'][:150]}...")
                print(f"  验证: {'成功' if first_attempt['verification']['success'] else '失败'}")
        else:
            print(f"\n❌ 修复失败")
            if result['attempts']:
                last_attempt = result['attempts'][-1]
                print(f"  最后错误: {last_attempt['verification'].get('stderr', '')[:200]}")
        
        return result
        
    finally:
        # 清理
        shutil.rmtree(project_path)


def main():
    """主函数"""
    
    print("="*60)
    print("测试跨文件案例（带ContextManager + 多文件Docker）")
    print("="*60)
    
    # 读取测试集
    with open('data/test_cases/week6_test_set.json', 'r', encoding='utf-8') as f:
        data = json.load(f)
    
    # 选择跨文件案例（案例16-22）
    crossfile_cases = [
        case for case in data['test_cases']
        if case['category'] == '跨文件'
    ][:3]  # 只测试前3个
    
    print(f"\n将测试 {len(crossfile_cases)} 个跨文件案例\n")
    
    results = []
    for i, case in enumerate(crossfile_cases, 1):
        result = test_single_case(case)
        results.append({
            'case_id': case['id'],
            'case_name': case['name'],
            'success': result['success'],
            'attempts': result['total_attempts'],
            'used_import': 'import' in result.get('final_code', '')
        })
        
        if i < len(crossfile_cases):
            input("\n按Enter继续下一个测试...")
    
    # 总结
    print("\n" + "="*60)
    print("总结")
    print("="*60)
    
    success_count = sum(1 for r in results if r['success'])
    import_count = sum(1 for r in results if r['used_import'])
    
    print(f"总测试: {len(results)}")
    print(f"成功: {success_count}/{len(results)}")
    print(f"使用import: {import_count}/{len(results)}")
    
    print(f"\n详细:")
    for r in results:
        status = "✅" if r['success'] else "❌"
        import_status = "✅ import" if r['used_import'] else "⚠️ 直接定义"
        print(f"  {status} 案例{r['case_id']}: {r['case_name']}")
        print(f"     {import_status} | 尝试{r['attempts']}次")


if __name__ == '__main__':
    main()