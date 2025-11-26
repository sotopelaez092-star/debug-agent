"""测试改进后的Prompt - 只测试Case 18, 24, 29"""
import json
import os
import sys
import time
from datetime import datetime

from dotenv import load_dotenv
load_dotenv()

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from src.agent.debug_agent import DebugAgent
import tempfile
import shutil


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


def test_case(case, case_num):
    """测试单个案例"""
    
    print(f"\n{'='*60}")
    print(f"测试 Case {case['id']}: {case['name']}")
    print(f"类别: {case['category']} | 错误: {case['error_type']} | 难度: {case['difficulty']}")
    print(f"{'='*60}")
    
    # 创建临时项目目录
    project_path = tempfile.mkdtemp(prefix=f"test_case_{case['id']}_")
    
    try:
        # 设置项目文件
        setup_project_files(project_path, case['project_files'])
        
        # 准备buggy_code
        buggy_code = case['project_files'][case['error_file']]
        error_file = case['error_file']
        
        # 构造error_traceback
        error_traceback = f"""Traceback (most recent call last):
  File "{case['error_file']}", line 1, in <module>
{case['error_message']}
"""
        
        api_key = os.getenv('DEEPSEEK_API_KEY')
        if not api_key:
            raise ValueError("请设置环境变量: export DEEPSEEK_API_KEY='your-key'")
        
        # 创建Agent
        agent = DebugAgent(project_path=project_path, api_key=api_key)
        
        # 记录开始时间
        start_time = time.time()
        
        # 执行debug
        result = agent.debug(
            buggy_code=buggy_code,
            error_traceback=error_traceback,
            error_file=error_file,
            max_retries=2
        )
        
        elapsed_time = time.time() - start_time
        
        # 详细输出每次尝试
        print(f"\n📊 结果:")
        print(f"  成功: {'✅' if result['success'] else '❌'}")
        print(f"  尝试次数: {result['total_attempts']}")
        print(f"  耗时: {elapsed_time:.2f}秒")
        
        # 显示每次尝试的详情
        for attempt in result['attempts']:
            num = attempt['attempt_number']
            success = attempt['verification']['success']
            
            print(f"\n  第{num}次尝试: {'✅ 成功' if success else '❌ 失败'}")
            print(f"    修复思路: {attempt['explanation'][:100]}...")
            print(f"    改动: {attempt['changes'][:2]}")  # 只显示前2个改动
            
            if not success:
                stderr = attempt['verification'].get('stderr', '')
                if stderr:
                    print(f"    新错误: {stderr[:150]}...")
        
        if result['success']:
            print(f"\n✅ 最终修复代码:")
            print(result['final_code'])
        
        return {
            'case_id': case['id'],
            'success': result['success'],
            'attempts': result['total_attempts'],
            'elapsed_time': elapsed_time,
            'first_try_success': result['total_attempts'] == 1
        }
        
    except Exception as e:
        print(f"❌ 执行失败: {e}")
        import traceback
        traceback.print_exc()
        
        return {
            'case_id': case['id'],
            'success': False,
            'attempts': 0,
            'elapsed_time': 0,
            'first_try_success': False,
            'error': str(e)
        }
    
    finally:
        # 清理临时目录
        try:
            shutil.rmtree(project_path)
        except:
            pass


def main():
    """主函数"""
    
    print("="*60)
    print("测试改进后的Prompt效果")
    print(f"时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("="*60)
    
    # 1. 读取测试集
    test_file = 'data/test_cases/week6_test_set.json'
    with open(test_file, 'r', encoding='utf-8') as f:
        data = json.load(f)
    
    # 2. 只测试Case 18, 24, 29
    target_cases = [18, 24, 29]
    test_cases = [c for c in data['test_cases'] if c['id'] in target_cases]
    
    print(f"\n目标: 测试 {len(test_cases)} 个之前需要重试的案例")
    print(f"Case IDs: {target_cases}")
    
    # 用户确认
    response = input("\n是否开始测试？(y/n): ")
    if response.lower() != 'y':
        print("取消测试")
        return
    
    # 3. 执行测试
    results = []
    
    for i, case in enumerate(test_cases, 1):
        result = test_case(case, i)
        results.append(result)
        
        # 暂停一下，看结果
        if i < len(test_cases):
            input("\n按Enter继续下一个测试...")
    
    # 4. 总结
    print("\n" + "="*60)
    print("测试完成！")
    print("="*60)
    
    success_count = sum(1 for r in results if r['success'])
    first_try_count = sum(1 for r in results if r.get('first_try_success', False))
    
    print(f"\n总体结果:")
    print(f"  测试案例: {len(results)}")
    print(f"  成功: {success_count}/{len(results)}")
    print(f"  第一次成功: {first_try_count}/{len(results)} ⭐")
    
    print(f"\n详细:")
    for r in results:
        status = "✅ 成功" if r['success'] else "❌ 失败"
        first_try = "⭐ 第一次!" if r.get('first_try_success') else f"({r['attempts']}次)"
        print(f"  Case {r['case_id']}: {status} {first_try}")
    
    # 5. 对比之前
    print(f"\n📊 对比:")
    print(f"  之前: Case 18 (2次), Case 24 (3次), Case 29 (2次)")
    
    case_18 = next((r for r in results if r['case_id'] == 18), None)
    case_24 = next((r for r in results if r['case_id'] == 24), None)
    case_29 = next((r for r in results if r['case_id'] == 29), None)
    
    if case_18:
        print(f"  现在: Case 18 ({case_18['attempts']}次) {'⬆️ 改进!' if case_18['attempts'] == 1 else ''}")
    if case_24:
        print(f"  现在: Case 24 ({case_24['attempts']}次) {'⬆️ 改进!' if case_24['attempts'] <= 2 else ''}")
    if case_29:
        print(f"  现在: Case 29 ({case_29['attempts']}次) {'⬆️ 改进!' if case_29['attempts'] == 1 else ''}")
    
    # 6. 保存结果
    output_file = 'data/evaluation/prompt_improvement_test.json'
    os.makedirs('data/evaluation', exist_ok=True)
    
    output_data = {
        'timestamp': datetime.now().isoformat(),
        'test_cases': target_cases,
        'results': results,
        'summary': {
            'total': len(results),
            'success': success_count,
            'first_try_success': first_try_count
        }
    }
    
    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(output_data, f, indent=2, ensure_ascii=False)
    
    print(f"\n✅ 结果已保存到: {output_file}")


if __name__ == '__main__':
    main()