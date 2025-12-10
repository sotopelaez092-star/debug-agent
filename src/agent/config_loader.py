"""
ConfigLoader - 项目配置加载器

支持 .debugagent.yaml 配置文件
"""

import os
import logging
from typing import Dict, List, Optional, Any

logger = logging.getLogger(__name__)


# 默认配置
DEFAULT_CONFIG = {
    # 扫描配置
    'scan': {
        'ignore_dirs': [
            'venv', '.venv', 'env',
            '__pycache__', '.pytest_cache',
            '.git', '.svn',
            'node_modules',
            'dist', 'build',
            '.idea', '.vscode',
        ],
        'ignore_files': [
            '*.pyc', '*.pyo',
            '.DS_Store',
        ],
        'focus_dirs': [],  # 如果指定，只扫描这些目录
        'max_file_size': 1048576,  # 1MB
    },

    # 调试配置
    'debug': {
        'max_retries': 3,
        'timeout': 30,
        'enable_rag': True,
        'enable_docker': True,
    },

    # 框架配置
    'framework': None,  # 自动检测，或指定：django, fastapi, flask, pytest

    # LLM 配置
    'llm': {
        'temperature': 0.3,
        'max_tokens': 2000,
    },

    # 自定义错误模式
    'custom_patterns': [],
}


class ConfigLoader:
    """
    配置加载器

    功能：
    1. 从项目目录加载 .debugagent.yaml 配置
    2. 合并默认配置和用户配置
    3. 验证配置有效性

    Attributes:
        project_path: 项目路径
        config: 合并后的配置
    """

    CONFIG_FILENAMES = [
        '.debugagent.yaml',
        '.debugagent.yml',
        'debugagent.yaml',
        'debugagent.yml',
    ]

    def __init__(self, project_path: str):
        """
        初始化配置加载器

        Args:
            project_path: 项目根目录
        """
        self.project_path = os.path.abspath(project_path)
        self.config = DEFAULT_CONFIG.copy()
        self._config_file = None

        # 尝试加载配置文件
        self._load_config()

    def _load_config(self):
        """加载配置文件"""
        # 查找配置文件
        for filename in self.CONFIG_FILENAMES:
            config_path = os.path.join(self.project_path, filename)
            if os.path.exists(config_path):
                self._config_file = config_path
                break

        if not self._config_file:
            logger.info("未找到配置文件，使用默认配置")
            return

        logger.info(f"找到配置文件: {self._config_file}")

        try:
            # 尝试使用 PyYAML
            import yaml

            with open(self._config_file, 'r', encoding='utf-8') as f:
                user_config = yaml.safe_load(f)

            if user_config:
                self._merge_config(user_config)
                logger.info("配置文件加载成功")

        except ImportError:
            logger.warning("未安装 PyYAML，尝试简单解析")
            self._simple_parse()
        except Exception as e:
            logger.error(f"加载配置文件失败: {e}")

    def _simple_parse(self):
        """简单的 YAML 解析（不依赖 PyYAML）"""
        try:
            with open(self._config_file, 'r', encoding='utf-8') as f:
                content = f.read()

            # 简单解析关键配置
            lines = content.split('\n')

            for line in lines:
                line = line.strip()
                if not line or line.startswith('#'):
                    continue

                # 解析 framework
                if line.startswith('framework:'):
                    value = line.split(':', 1)[1].strip()
                    if value and value != 'null':
                        self.config['framework'] = value

                # 解析 max_retries
                if 'max_retries:' in line:
                    try:
                        value = int(line.split(':', 1)[1].strip())
                        self.config['debug']['max_retries'] = value
                    except ValueError:
                        pass

        except Exception as e:
            logger.error(f"简单解析失败: {e}")

    def _merge_config(self, user_config: Dict[str, Any]):
        """
        合并用户配置到默认配置

        Args:
            user_config: 用户配置字典
        """
        def deep_merge(base: dict, override: dict) -> dict:
            result = base.copy()
            for key, value in override.items():
                if key in result and isinstance(result[key], dict) and isinstance(value, dict):
                    result[key] = deep_merge(result[key], value)
                else:
                    result[key] = value
            return result

        self.config = deep_merge(self.config, user_config)

    def get(self, key: str, default: Any = None) -> Any:
        """
        获取配置值（支持点号分隔的嵌套键）

        Args:
            key: 配置键，如 'scan.ignore_dirs' 或 'framework'
            default: 默认值

        Returns:
            配置值
        """
        keys = key.split('.')
        value = self.config

        try:
            for k in keys:
                value = value[k]
            return value
        except (KeyError, TypeError):
            return default

    def get_ignore_dirs(self) -> List[str]:
        """获取忽略的目录列表"""
        return self.get('scan.ignore_dirs', [])

    def get_focus_dirs(self) -> List[str]:
        """获取关注的目录列表"""
        return self.get('scan.focus_dirs', [])

    def get_framework(self) -> Optional[str]:
        """获取框架类型"""
        return self.get('framework')

    def get_max_retries(self) -> int:
        """获取最大重试次数"""
        return self.get('debug.max_retries', 3)

    def get_timeout(self) -> int:
        """获取超时时间"""
        return self.get('debug.timeout', 30)

    def is_rag_enabled(self) -> bool:
        """是否启用 RAG"""
        return self.get('debug.enable_rag', True)

    def is_docker_enabled(self) -> bool:
        """是否启用 Docker"""
        return self.get('debug.enable_docker', True)

    def get_custom_patterns(self) -> List[Dict]:
        """获取自定义错误模式"""
        return self.get('custom_patterns', [])

    def to_dict(self) -> Dict[str, Any]:
        """返回完整配置字典"""
        return self.config.copy()

    def __repr__(self) -> str:
        return f"ConfigLoader(project_path='{self.project_path}', config_file='{self._config_file}')"


def create_example_config(project_path: str) -> str:
    """
    创建示例配置文件

    Args:
        project_path: 项目路径

    Returns:
        配置文件路径
    """
    example_content = """# Debug Agent 配置文件
# 将此文件放在项目根目录，命名为 .debugagent.yaml

# 扫描配置
scan:
  # 忽略的目录
  ignore_dirs:
    - venv
    - .venv
    - __pycache__
    - .git
    - node_modules
    - dist
    - build

  # 只扫描这些目录（留空则扫描全部）
  focus_dirs: []
  #  - src
  #  - tests

  # 最大文件大小（字节）
  max_file_size: 1048576

# 调试配置
debug:
  max_retries: 3
  timeout: 30
  enable_rag: true
  enable_docker: true

# 框架类型（自动检测或手动指定）
# 可选值：django, fastapi, flask, pytest, null（自动检测）
framework: null

# LLM 配置
llm:
  temperature: 0.3
  max_tokens: 2000

# 自定义错误模式
custom_patterns: []
#  - name: "数据库连接错误"
#    pattern: "OperationalError.*Connection refused"
#    suggestion: "检查数据库服务是否启动"
"""

    config_path = os.path.join(project_path, '.debugagent.yaml')

    with open(config_path, 'w', encoding='utf-8') as f:
        f.write(example_content)

    logger.info(f"创建示例配置文件: {config_path}")
    return config_path
