from datetime import datetime
from typing import List, Dict, Any, Optional  # ← 修复1
import json
import logging
import os  # ← 修复2: 统一import

logger = logging.getLogger(__name__)

class PerformanceMonitor:
    """
    性能监控器 - 记录Agent执行的性能数据

    监控3类指标：
    1. 时间：总时间、各阶段耗时
    2. 成本：Token消耗、估算成本
    3. 错误类型：成功率、失败原因

    Example:
        >>> monitor = PerformanceMonitor()
        >>> monitor.record_execution({
        ...     "error_type": "NameError",
        ...     "success": True,
        ...     "total_time": 7.5,
        ...     # ... 其他数据
        ... })
        >>> report = monitor.generate_report()
    """

    def __init__(self):
        """初始化监控器"""
        # 存储所有执行记录
        self.executions: List[Dict[str, Any]] = []

        # 监控开始时间
        self.start_time = datetime.now()

        # 统计信息
        self._stats_cache: Optional[Dict] = None  # ← 这里用Optional是对的

        logger.info("PerformanceMonitor初始化成功")

    def record_execution(self, data: Dict[str, Any]) -> None:
        """
        记录一次Debug执行的数据

        Args:
            data: 执行数据，包含时间、成本、错误类型等指标
                - error_type (str): 错误类型
                - success (bool): 是否成功
                - attempts (int): 尝试次数  # ← 修复3
                - total_time (float): 总耗时 (秒)
                - stage_times (dict): 各阶段耗时
                - llm_calls (int): LLM调用次数
                - total_tokens (int): Token总数
                - prompt_tokens (int): 输入Token
                - completion_tokens (int): 输出Token
        
        Raises：
            ValueError: 如果data格式无效

        Example:
            >>> monitor.record_execution({
            ...     "error_type": "NameError",
            ...     "success": True,
            ...     "total_time": 7.5,
            ...     "attempts": 1
            ... })
        """
        # 1. 输入验证
        if not data or not isinstance(data, dict):
            raise ValueError("data必须是非空字典")

        # 验证必须字段
        required_fields = ["error_type", "success", "total_time"]
        missing_fields = [f for f in required_fields if f not in data]
        if missing_fields:
            raise ValueError(f"缺少必需字段: {missing_fields}")

        # 2. 添加时间戳
        if "timestamp" not in data:
            data["timestamp"] = datetime.now().isoformat()

        # 3. 添加到执行记录  # ← 修复4
        try:
            self.executions.append(data.copy())
            logger.info(
                f"记录执行数据: {data['error_type']}, "
                f"成功={data['success']}, "
                f"耗时={data['total_time']:.2f}s"
            )
        except Exception as e:
            logger.error(f"记录执行数据失败: {e}", exc_info=True)
            raise RuntimeError(f"记录执行数据失败: {e}")

        # 4. 清除统计缓存
        self._stats_cache = None

    def generate_report(self) -> Dict[str, Any]:
        """
        生成统计报告
        
        Returns:
            包含以下部分的报告：
            - summary: 总体统计（成功率、平均时间等）
            - by_error_type: 按错误类型的详细统计
            - metadata: 元数据（开始时间、报告时间等）
            
        Example:
            >>> report = monitor.generate_report()
            >>> print(f"成功率: {report['summary']['success_rate']:.1%}")
        """
        # 检查是否有数据
        if not self.executions:
            logger.warning("没有执行记录，无法生成报告")
            return {
                "error": "没有执行记录",
                "summary": {},
                "by_error_type": {},
                "metadata": {}
            }
        
        # 使用缓存（性能优化）
        if self._stats_cache is not None:
            logger.debug("使用缓存的统计结果")
            return self._stats_cache
        
        try:
            # 计算统计
            summary = self._calculate_summary()
            by_error_type = self._calculate_by_error_type()
            metadata = self._generate_metadata()
            
            # 组合报告
            report = {
                "summary": summary,
                "by_error_type": by_error_type,
                "metadata": metadata
            }
            
            # 缓存结果
            self._stats_cache = report
            
            logger.info("统计报告生成成功")
            return report
            
        except Exception as e:
            logger.error(f"生成报告失败: {e}", exc_info=True)
            raise RuntimeError(f"生成报告失败: {e}")
    
    def _calculate_summary(self) -> Dict[str, Any]:
        """计算总体统计"""
        total = len(self.executions)
        successful = sum(1 for e in self.executions if e.get("success", False))
        failed = total - successful
        
        # 计算平均值（安全处理）
        avg_time = sum(e.get("total_time", 0) for e in self.executions) / total
        total_tokens = sum(e.get("total_tokens", 0) for e in self.executions)
        avg_attempts = sum(e.get("attempts", 1) for e in self.executions) / total
        
        # 估算成本（DeepSeek价格：$0.14 per 1M tokens input, $0.28 per 1M output）
        total_prompt_tokens = sum(e.get("prompt_tokens", 0) for e in self.executions)
        total_completion_tokens = sum(e.get("completion_tokens", 0) for e in self.executions)
        total_cost = (total_prompt_tokens * 0.14 + total_completion_tokens * 0.28) / 1_000_000
        
        return {
            "total_executions": total,
            "successful": successful,
            "failed": failed,
            "success_rate": successful / total if total > 0 else 0,
            "avg_time": round(avg_time, 2),
            "total_tokens": total_tokens,
            "total_cost": round(total_cost, 6),
            "avg_attempts": round(avg_attempts, 2)
        }

    def _calculate_by_error_type(self) -> Dict[str, Dict[str, Any]]:
        """按错误类型统计"""
        # 按错误类型分组
        error_groups = {}
        for execution in self.executions:
            error_type = execution.get("error_type", "Unknown")
            if error_type not in error_groups:
                error_groups[error_type] = []
            error_groups[error_type].append(execution)
        
        # 计算每种错误类型的统计
        result = {}
        for error_type, executions in error_groups.items():
            count = len(executions)
            success = sum(1 for e in executions if e.get("success", False))
            failed = count - success
            avg_time = sum(e.get("total_time", 0) for e in executions) / count
            avg_attempts = sum(e.get("attempts", 1) for e in executions) / count
            
            result[error_type] = {
                "count": count,
                "success": success,
                "failed": failed,
                "success_rate": success / count if count > 0 else 0,
                "avg_time": round(avg_time, 2),
                "avg_attempts": round(avg_attempts, 2)
            }
        
        return result
    
    def _generate_metadata(self) -> Dict[str, Any]:
        """生成元数据"""
        now = datetime.now()
        duration = (now - self.start_time).total_seconds() / 3600  # 转换为小时
        
        return {
            "start_time": self.start_time.isoformat(),
            "report_time": now.isoformat(),
            "duration_hours": round(duration, 2)
        }

    def save_to_file(self, filepath: str) -> None:
        """
        保存监控数据到JSON文件

        Args:
            filepath: 保存路径 (例如: 'data/performance.json')

        Raises:
            ValueError: 如果filepath无效
            RuntimeError: 如果保存失败

        Example:
            >>> monitor.save_to_file('data/performance.json')
        """
        # 1. 输入验证
        if not filepath or not isinstance(filepath, str):
            raise ValueError("filepath必须是非空字符串")

        # 2. 确保目录存在
        directory = os.path.dirname(filepath)  # ← 不用再import os了
        if directory and not os.path.exists(directory):
            try:
                os.makedirs(directory, exist_ok=True)
                logger.info(f"已创建目录: {directory}")
            except Exception as e:
                logger.error(f"创建目录失败: {e}")
                raise RuntimeError(f"创建目录失败: {e}")

        # 3. 准备保存的数据
        data = {
            "executions": self.executions,
            "start_time": self.start_time.isoformat(),
            "save_time": datetime.now().isoformat()
        }

        # 4. 保存到文件
        try:
            with open(filepath, 'w', encoding='utf-8') as f:
                json.dump(data, f, indent=2, ensure_ascii=False)
            
            logger.info(f"监控数据已保存: {filepath} ({len(self.executions)}条记录)")

        except Exception as e:
            logger.error(f"保存数据失败: {e}", exc_info=True)
            raise RuntimeError(f"保存数据失败: {e}")

    def load_from_file(self, filepath: str) -> None:
        """
        从JSON文件加载监控数据
        
        Args:
            filepath: 文件路径
            
        Raises:
            ValueError: 如果filepath无效
            FileNotFoundError: 如果文件不存在
            RuntimeError: 如果加载失败
            
        Example:
            >>> monitor = PerformanceMonitor()
            >>> monitor.load_from_file('data/performance.json')
        """
        # 1. 输入验证
        if not filepath or not isinstance(filepath, str):
            raise ValueError("filepath必须是非空字符串")

        # 2. 检查文件是否存在
        if not os.path.exists(filepath):  # ← 现在os已经import了
            raise FileNotFoundError(f"文件不存在: {filepath}")

        # 3. 加载数据
        try:
            with open(filepath, 'r', encoding='utf-8') as f:
                data = json.load(f)
            
            # 4. 验证数据格式
            if not isinstance(data, dict) or "executions" not in data:
                raise ValueError("文件格式无效：缺少executions字段")
            
            # 5. 恢复数据
            self.executions = data["executions"]
            
            # 恢复开始时间（如果有）
            if "start_time" in data:
                self.start_time = datetime.fromisoformat(data["start_time"])
            
            # 清除缓存
            self._stats_cache = None
            
            logger.info(f"监控数据已加载: {filepath} ({len(self.executions)}条记录)")
            
        except json.JSONDecodeError as e:
            logger.error(f"JSON解析失败: {e}")
            raise RuntimeError(f"JSON解析失败: {e}")
        except Exception as e:
            logger.error(f"加载数据失败: {e}", exc_info=True)
            raise RuntimeError(f"加载数据失败: {e}")