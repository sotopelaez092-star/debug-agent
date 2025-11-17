import sys
from pathlib import Path

# 添加项目根目录到路径
sys.path.append(str(Path(__file__).parent.parent))

from src.agent.tools.error_identifier import ErrorIdentifier
from src.agent.tools.rag_searcher import RAGSearcher
from src.agent.tools.code_fixer import CodeFixer
from src.agent.tools.docker_executor  import DockerExecutor



from typing import Dict, List, Optional

import logging
logger = logging.getLogger(__name__)