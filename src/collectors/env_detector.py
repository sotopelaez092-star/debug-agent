"""
PythonEnvDetector - Python 环境检测器

检测项目的 Python 环境、依赖和配置
"""

import os
import sys
import subprocess
import logging
from typing import Dict, List, Optional, Any
from pathlib import Path

logger = logging.getLogger(__name__)


class PythonEnvDetector:
    """
    Python 环境检测器

    功能：
    1. 检测 Python 版本
    2. 检测虚拟环境类型（venv, conda, poetry, pipenv）
    3. 解析依赖文件（requirements.txt, pyproject.toml, Pipfile）
    4. 获取已安装的包列表
    5. 检测常见框架（Django, FastAPI, Flask, pytest）

    Attributes:
        project_path: 项目根目录
    """

    # 常见框架的检测关键词
    FRAMEWORK_PATTERNS = {
        'django': ['django', 'DJANGO_SETTINGS_MODULE'],
        'fastapi': ['fastapi', 'FastAPI'],
        'flask': ['flask', 'Flask'],
        'pytest': ['pytest', 'conftest.py'],
        'unittest': ['unittest', 'TestCase'],
        'celery': ['celery', 'Celery'],
        'sqlalchemy': ['sqlalchemy', 'SQLAlchemy'],
    }

    def __init__(self, project_path: str):
        """
        初始化环境检测器

        Args:
            project_path: 项目根目录
        """
        self.project_path = os.path.abspath(project_path)

        if not os.path.isdir(self.project_path):
            raise ValueError(f"项目路径不存在: {self.project_path}")

        logger.info(f"PythonEnvDetector 初始化: {self.project_path}")

    def detect(self) -> Dict[str, Any]:
        """
        执行完整的环境检测

        Returns:
            环境信息字典
        """
        return {
            'python_version': self._get_python_version(),
            'venv_type': self._detect_venv_type(),
            'dependencies': self._parse_dependencies(),
            'installed_packages': self._get_installed_packages(),
            'frameworks': self._detect_frameworks(),
            'project_type': self._detect_project_type(),
        }

    def _get_python_version(self) -> Dict[str, Any]:
        """
        获取 Python 版本信息

        Returns:
            Python 版本信息
        """
        return {
            'version': f"{sys.version_info.major}.{sys.version_info.minor}.{sys.version_info.micro}",
            'major': sys.version_info.major,
            'minor': sys.version_info.minor,
            'micro': sys.version_info.micro,
            'executable': sys.executable,
        }

    def _detect_venv_type(self) -> Dict[str, Any]:
        """
        检测虚拟环境类型

        Returns:
            虚拟环境信息
        """
        result = {
            'type': 'system',
            'path': None,
            'is_active': False,
        }

        # 检查 venv / .venv
        for venv_name in ['venv', '.venv', 'env', '.env']:
            venv_path = os.path.join(self.project_path, venv_name)
            if os.path.isdir(venv_path):
                # 验证是否是真正的 venv
                if os.path.exists(os.path.join(venv_path, 'pyvenv.cfg')):
                    result['type'] = 'venv'
                    result['path'] = venv_path
                    break

        # 检查 conda
        if os.path.exists(os.path.join(self.project_path, 'environment.yml')):
            result['type'] = 'conda'

        # 检查 poetry
        if os.path.exists(os.path.join(self.project_path, 'poetry.lock')):
            result['type'] = 'poetry'

        # 检查 pipenv
        if os.path.exists(os.path.join(self.project_path, 'Pipfile.lock')):
            result['type'] = 'pipenv'

        # 检查是否在虚拟环境中运行
        result['is_active'] = (
            hasattr(sys, 'real_prefix') or
            (hasattr(sys, 'base_prefix') and sys.base_prefix != sys.prefix)
        )

        logger.info(f"检测到虚拟环境类型: {result['type']}")
        return result

    def _parse_dependencies(self) -> Dict[str, Any]:
        """
        解析依赖文件

        Returns:
            依赖信息
        """
        dependencies = {
            'requirements': None,
            'pyproject': None,
            'pipfile': None,
            'setup_py': None,
        }

        # 解析 requirements.txt
        req_file = os.path.join(self.project_path, 'requirements.txt')
        if os.path.exists(req_file):
            dependencies['requirements'] = self._parse_requirements_txt(req_file)

        # 解析 pyproject.toml
        pyproject_file = os.path.join(self.project_path, 'pyproject.toml')
        if os.path.exists(pyproject_file):
            dependencies['pyproject'] = self._parse_pyproject_toml(pyproject_file)

        # 解析 Pipfile
        pipfile = os.path.join(self.project_path, 'Pipfile')
        if os.path.exists(pipfile):
            dependencies['pipfile'] = self._parse_pipfile(pipfile)

        # 检查 setup.py
        setup_py = os.path.join(self.project_path, 'setup.py')
        if os.path.exists(setup_py):
            dependencies['setup_py'] = True

        return dependencies

    def _parse_requirements_txt(self, file_path: str) -> List[Dict[str, str]]:
        """
        解析 requirements.txt 文件

        Args:
            file_path: 文件路径

        Returns:
            依赖列表
        """
        packages = []

        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                for line in f:
                    line = line.strip()

                    # 跳过空行和注释
                    if not line or line.startswith('#'):
                        continue

                    # 跳过 -r, -e 等选项
                    if line.startswith('-'):
                        continue

                    # 解析包名和版本
                    package = self._parse_requirement_line(line)
                    if package:
                        packages.append(package)

        except Exception as e:
            logger.error(f"解析 requirements.txt 失败: {e}")

        return packages

    def _parse_requirement_line(self, line: str) -> Optional[Dict[str, str]]:
        """
        解析单行依赖

        Args:
            line: 依赖行

        Returns:
            {name, version_spec} 或 None
        """
        # 处理常见的版本说明符
        for sep in ['>=', '<=', '==', '!=', '~=', '>', '<']:
            if sep in line:
                parts = line.split(sep, 1)
                return {
                    'name': parts[0].strip(),
                    'version_spec': sep + parts[1].strip() if len(parts) > 1 else '',
                }

        # 无版本限制
        return {'name': line.strip(), 'version_spec': ''}

    def _parse_pyproject_toml(self, file_path: str) -> Dict[str, Any]:
        """
        解析 pyproject.toml 文件

        Args:
            file_path: 文件路径

        Returns:
            项目配置信息
        """
        result = {
            'build_system': None,
            'project_name': None,
            'dependencies': [],
        }

        try:
            # 简单解析，不使用 toml 库
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()

            # 检测构建系统
            if 'poetry' in content:
                result['build_system'] = 'poetry'
            elif 'setuptools' in content:
                result['build_system'] = 'setuptools'
            elif 'flit' in content:
                result['build_system'] = 'flit'

            # 提取项目名（简单正则）
            import re
            name_match = re.search(r'name\s*=\s*["\']([^"\']+)["\']', content)
            if name_match:
                result['project_name'] = name_match.group(1)

        except Exception as e:
            logger.error(f"解析 pyproject.toml 失败: {e}")

        return result

    def _parse_pipfile(self, file_path: str) -> Dict[str, List[str]]:
        """
        解析 Pipfile

        Args:
            file_path: 文件路径

        Returns:
            依赖信息
        """
        result = {
            'packages': [],
            'dev_packages': [],
        }

        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()

            # 简单解析
            current_section = None

            for line in content.split('\n'):
                line = line.strip()

                if line == '[packages]':
                    current_section = 'packages'
                elif line == '[dev-packages]':
                    current_section = 'dev_packages'
                elif current_section and '=' in line:
                    package_name = line.split('=')[0].strip()
                    if package_name and not package_name.startswith('['):
                        result[current_section].append(package_name)

        except Exception as e:
            logger.error(f"解析 Pipfile 失败: {e}")

        return result

    def _get_installed_packages(self) -> List[Dict[str, str]]:
        """
        获取已安装的包列表

        Returns:
            已安装包列表
        """
        packages = []

        try:
            # 使用 pip list 获取已安装包
            result = subprocess.run(
                [sys.executable, '-m', 'pip', 'list', '--format=json'],
                capture_output=True,
                text=True,
                timeout=30
            )

            if result.returncode == 0:
                import json
                packages = json.loads(result.stdout)

        except subprocess.TimeoutExpired:
            logger.warning("获取已安装包超时")
        except Exception as e:
            logger.error(f"获取已安装包失败: {e}")

        return packages

    def _detect_frameworks(self) -> List[str]:
        """
        检测项目使用的框架

        Returns:
            框架列表
        """
        frameworks = []

        # 检查依赖文件
        req_file = os.path.join(self.project_path, 'requirements.txt')
        if os.path.exists(req_file):
            try:
                with open(req_file, 'r', encoding='utf-8') as f:
                    content = f.read().lower()

                for framework, patterns in self.FRAMEWORK_PATTERNS.items():
                    for pattern in patterns:
                        if pattern.lower() in content:
                            if framework not in frameworks:
                                frameworks.append(framework)
                            break
            except Exception as e:
                logger.error(f"检测框架失败: {e}")

        # 检查源代码文件
        for root, dirs, files in os.walk(self.project_path):
            # 跳过虚拟环境等目录
            dirs[:] = [d for d in dirs if d not in {'venv', '.venv', 'env', '__pycache__', '.git'}]

            for file in files:
                if file.endswith('.py'):
                    file_path = os.path.join(root, file)
                    try:
                        with open(file_path, 'r', encoding='utf-8') as f:
                            content = f.read()

                        for framework, patterns in self.FRAMEWORK_PATTERNS.items():
                            if framework in frameworks:
                                continue
                            for pattern in patterns:
                                if pattern in content:
                                    frameworks.append(framework)
                                    break
                    except Exception:
                        pass

            # 只检查前100个文件
            if len(frameworks) >= 5:
                break

        logger.info(f"检测到框架: {frameworks}")
        return frameworks

    def _detect_project_type(self) -> str:
        """
        检测项目类型

        Returns:
            项目类型
        """
        # 检查是否是包项目
        if os.path.exists(os.path.join(self.project_path, 'setup.py')):
            return 'package'

        if os.path.exists(os.path.join(self.project_path, 'pyproject.toml')):
            return 'package'

        # 检查是否是 Web 项目
        for framework in ['django', 'fastapi', 'flask']:
            if os.path.exists(os.path.join(self.project_path, 'manage.py')):
                return 'web_django'

        # 检查是否有 main.py
        if os.path.exists(os.path.join(self.project_path, 'main.py')):
            return 'application'

        # 检查是否是测试项目
        if os.path.exists(os.path.join(self.project_path, 'tests')):
            return 'library'

        return 'unknown'

    def check_dependency_installed(self, package_name: str) -> bool:
        """
        检查某个依赖是否已安装

        Args:
            package_name: 包名

        Returns:
            是否已安装
        """
        try:
            result = subprocess.run(
                [sys.executable, '-m', 'pip', 'show', package_name],
                capture_output=True,
                text=True,
                timeout=10
            )
            return result.returncode == 0
        except Exception:
            return False

    def get_install_command(self, package_name: str) -> str:
        """
        获取安装包的命令

        Args:
            package_name: 包名

        Returns:
            安装命令
        """
        venv_info = self._detect_venv_type()

        if venv_info['type'] == 'poetry':
            return f"poetry add {package_name}"
        elif venv_info['type'] == 'pipenv':
            return f"pipenv install {package_name}"
        elif venv_info['type'] == 'conda':
            return f"conda install {package_name}"
        else:
            return f"pip install {package_name}"
