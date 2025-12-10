#!/usr/bin/env python3
"""
AI Debug CLI - 自动检测并修复代码错误

用法:
    ai-debug <file>              # 运行文件，自动检测错误
    ai-debug <file> --project .  # 指定项目路径（跨文件调试）
"""
import sys
import argparse
import subprocess
from pathlib import Path
import shutil

# Rich库用于彩色输出
from rich.console import Console
from rich.panel import Panel
from rich.syntax import Syntax
from rich.progress import Progress, SpinnerColumn, TextColumn
from rich.table import Table

# 创建全局console对象
console = Console()

# ⭐ 修改：进度回调函数（支持verbose）
def create_progress_callback(verbose: bool):
    """创建进度回调函数"""
    def callback(iteration: int, action: str, details: dict = None):
        """
        进度回调
        
        Args:
            iteration: 迭代次数
            action: 动作类型 (thinking/tool_call/observation)
            details: 详细信息（仅verbose模式使用）
        """
        if action == "thinking":
            console.print(f"[cyan]  ├─ 第 {iteration} 次迭代...[/cyan]")
        
        if verbose and details:
            if action == "thought":
                thought = details.get("thought", "")[:100]
                console.print(f"[dim]      💭 Thought: {thought}...[/dim]")
            elif action == "tool_call":
                tool = details.get("tool", "")
                console.print(f"[dim]      🔧 Action: {tool}[/dim]")
            elif action == "observation":
                result = details.get("result", "")[:100]
                console.print(f"[dim]      📊 Result: {result}...[/dim]")
    
    return callback

# 添加项目根目录到path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from src.agent.react_agent import ReActAgent

def run_python_file(file_path: str) -> dict:
    """
    运行Python文件，捕获输出和错误
    
    Returns:
        {
            'success': bool,
            'stdout': str,
            'stderr': str,
            'returncode': int
        }
    """
    console.print(f"[blue]🚀 运行:[/blue] python {file_path}")
    console.print("-" * 60)
    
    try:
        result = subprocess.run(
            ['python', file_path],
            capture_output=True,
            text=True,
            timeout=10  # 10秒超时
        )
        
        return {
            'success': result.returncode == 0,
            'stdout': result.stdout,
            'stderr': result.stderr,
            'returncode': result.returncode
        }
    
    except subprocess.TimeoutExpired:
        return {
            'success': False,
            'stdout': '',
            'stderr': 'Error: 程序运行超时（>10秒）',
            'returncode': -1
        }
    except Exception as e:
        return {
            'success': False,
            'stdout': '',
            'stderr': f'Error: 无法运行文件 - {str(e)}',
            'returncode': -1
        }

def main():
    # 1. 解析命令行参数
    parser = argparse.ArgumentParser(
        description='AI Debug - 自动检测并修复Python代码错误'
    )
    parser.add_argument(
        'file',
        help='要调试的Python文件'
    )
    parser.add_argument(
        '--project',
        help='项目根目录（用于跨文件调试）',
        default=None
    )
    parser.add_argument(
        '--verbose',
        action='store_true',
        help='显示详细的调试信息'
    )
    
    args = parser.parse_args()
    
    # 2. 验证文件存在
    file_path = Path(args.file)
    if not file_path.exists():
        console.print(f"[red]❌ 错误: 文件不存在 - {args.file}[/red]")
        sys.exit(1)
    
    if not file_path.suffix == '.py':
        console.print(f"[red]❌ 错误: 不是Python文件 - {args.file}[/red]")
        sys.exit(1)
    
    # 3. 显示文件信息
    console.print(f"[cyan]📝 文件:[/cyan] {file_path}")
    if args.project:
        console.print(f"[cyan]📁 项目:[/cyan] {args.project}")
    console.print()
    
    # 4. 运行文件
    result = run_python_file(str(file_path))
    
    # 5. 显示标准输出
    if result['stdout']:
        console.print(Panel(
            result['stdout'],
            title="[blue]标准输出[/blue]",
            border_style="blue"
        ))
        console.print()
    
    # 6. 检查是否有错误
    if result['success']:
        console.print("[green bold]✅ 程序运行成功，无错误[/green bold]")
        sys.exit(0)
    
    # 7. 有错误 - 显示错误信息
    console.print("[red bold]❌ 程序运行失败[/red bold]")
    console.print()
    
    # 使用Panel显示错误信息
    console.print(Panel(
        result['stderr'],
        title="[red]错误信息[/red]",
        border_style="red"
    ))
    console.print()
    
    # 8. 读取源代码
    with open(file_path, 'r', encoding='utf-8') as f:
        buggy_code = f.read()

    # 9. 调用ReActAgent修复
    console.print("[yellow]🤖 正在分析错误并生成修复方案...[/yellow]")
    console.print()

    try:
        # 确定项目路径
        project_path = args.project
        if project_path:
            project_path = str(Path(project_path).resolve())
        else:
            # 使用文件所在目录作为项目路径
            project_path = str(file_path.parent.resolve())

        # 创建agent
        callback = create_progress_callback(args.verbose)
        agent = ReActAgent(progress_callback=callback)

        # 调用debug
        debug_result = agent.debug(
            buggy_code=buggy_code,
            error_traceback=result['stderr'],
            project_path=project_path
        )
        console.print(f"[green]  └─ ✅ 完成！[/green]")

        # 10. 显示结果
        console.print()
        console.print("=" * 60)
        
        if debug_result['success']:
            console.print("[green bold]✅ 修复成功！[/green bold]")
            console.print("=" * 60)
            console.print()
            
            # 显示迭代次数
            console.print(f"[cyan]🔄 迭代次数:[/cyan] {debug_result['iterations']}")
            console.print()
            
            # 使用Syntax显示修复后的代码（带语法高亮）
            console.print("[blue bold]修复后的代码:[/blue bold]")
            syntax = Syntax(
                debug_result['fixed_code'],
                "python",
                theme="monokai",
                line_numbers=True
            )
            console.print(syntax)
            console.print()
            
            # 11. 询问是否应用修复
            console.print("[yellow]是否应用修复？[y/n]:[/yellow] ", end='')
            response = input().strip().lower()
            
            if response == 'y':
                # 备份原文件
                backup_path = file_path.with_suffix('.py.bak')
                shutil.copy(file_path, backup_path)
                console.print(f"[green]✅ 已备份原文件到:[/green] {backup_path}")
                
                # 写入修复后的代码
                with open(file_path, 'w', encoding='utf-8') as f:
                    f.write(debug_result['fixed_code'])
                console.print(f"[green]✅ 已保存修复后的代码到:[/green] {file_path}")
                
                # 重新运行验证
                console.print()
                console.print("[yellow]🔍 验证修复...[/yellow]")
                verify_result = run_python_file(str(file_path))
                
                console.print()
                if verify_result['success']:
                    console.print("[green bold]🎉 验证成功！程序现在可以正常运行了[/green bold]")
                    if verify_result['stdout']:
                        console.print()
                        console.print(Panel(
                            verify_result['stdout'],
                            title="[green]程序输出[/green]",
                            border_style="green"
                        ))
                else:
                    console.print("[red]⚠️ 验证失败，修复后仍有错误[/red]")
                    console.print(Panel(
                        verify_result['stderr'],
                        title="[red]验证错误[/red]",
                        border_style="red"
                    ))
                    console.print()
                    console.print(f"[yellow]原文件已备份到:[/yellow] {backup_path}")
            else:
                console.print("[yellow]❌ 已取消修复[/yellow]")
        
        else:
            console.print("[red bold]❌ 修复失败[/red bold]")
            console.print("=" * 60)
            console.print(f"[red]原因:[/red] {debug_result.get('error', '未知错误')}")
            console.print(f"[cyan]尝试次数:[/cyan] {debug_result.get('iterations', 0)}")
            sys.exit(1)
    
    except Exception as e:
        console.print(f"[red bold]❌ 发生错误:[/red bold] {e}")
        console.print_exception()
        sys.exit(1)

if __name__ == '__main__':
    main()