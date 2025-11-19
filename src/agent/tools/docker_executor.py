"""
DockerExecutor - Docker代码执行器
在隔离的Docker容器中安全执行Python代码
"""

import time
import docker
import logging

logger = logging.getLogger(__name__)

class DockerExecutor:
    """
    Docker代码执行器

    功能：
    1. 执行Python代码在隔离的Docker容器中
    2. 支持代码输入和输出的重定向
    3. 提供容器日志记录功能
    """

    def __init__(
        self,
        image: str = "python:3.11-alpine",
        timeout: int = 30,
        memory_limit: str = "256m"
        ):
        """
        初始化DockerExecutor

        参数：
            image: Docker镜像名称
        """
        logger.info("初始化DockerExcutor...")

        self.image = image
        self.timeout = timeout
        self.memory_limit = memory_limit
        
        # 链接Docker
        try:
            self.client = docker.from_env()
            self.client.ping()
            logger.info("✅ Docker守护进程连接成功")
        except Exception as e:
            logger.error(f"初始化DockerExecutor失败: {e}")
            raise RuntimeError(f"初始化DockerExecutor失败: {e}")

        logger.info(f"✅ DockerExecutor初始化完成，镜像: {image}, 超时: {timeout}秒, 内存限制: {memory_limit}")

    def execute(self, code: str) -> dict:
        """
        在Docker中执行Python代码

        Args:
            code: Python代码字符串

        Returns:
            {
                "success": True/False,
                "stdout": "输出内容",
                "stderr": "错误内容",
                "exit_code": 0
            }
        """
        # 1. 输入验证
        if not code or not isinstance(code, str):
            raise ValueError("code必须是非空字符串")

        logger.info("开始执行代码...")

        # 2. 运行容器
        try:
            container = self.client.containers.run(
                image=self.image,
                command=["python", "-c", code],

                # 安全配置
                mem_limit=self.memory_limit,
                network_disabled=True,

                # 执行配置
                detach=True,
                remove=False,
                stdout=True,
                stderr=True
            )
            # 3. 等待执行完成，设置超时
            try:
                result = container.wait(timeout=self.timeout)
                exit_code = result['StatusCode']
            except Exception as timeout_err:  
                # 超时了，强制停止容器
                logger.warning(f"执行超时（>{self.timeout}秒），强制停止容器")
                try:
                    container.stop(timeout=1)
                    container.remove(force=True)
                except:
                    pass
                
                return {
                    "success": False,
                    "stdout": "",
                    "stderr": f"执行超时（超过{self.timeout}秒限制）",
                    "exit_code": -1
                }

            # 4. 获取输出
            stdout = container.logs(stdout=True, stderr=False).decode('utf-8')
            stderr = container.logs(stdout=False, stderr=True).decode('utf-8')

            logger.info(f"执行完成 - exit_code: {exit_code}")

            # 5. 手动删除容器
            container.remove()
            logger.info("容器已清理")

            return {
                "success": exit_code == 0,
                "stdout": stdout,
                "stderr": stderr,
                "exit_code": exit_code
            }
        except Exception as e:
            logger.error(f"执行失败: {e}")
            return {
                "success": False,
                "stdout": "",
                "stderr": str(e),
                "exit_code": -1
            }


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    
    executor = DockerExecutor()
    
    # 测试1: Hello World
    print("\n" + "="*60)
    print("测试1: Hello World")
    print("="*60)
    
    code = 'print("Hello from Docker!")'
    result = executor.execute(code)
    
    print(f"✅ 成功: {result['success']}")
    print(f"📤 输出: {result['stdout']}")
    print(f"🔢 退出码: {result['exit_code']}")

        # 测试2: 错误代码
    print("\n" + "="*60)
    print("测试2: 错误代码（NameError）")
    print("="*60)

    code2 = 'print(undefined_variable)'
    result2 = executor.execute(code2)

    print(f"✅ 成功: {result2['success']}")
    print(f"❌ 错误: {result2['stderr']}")
    print(f"🔢 退出码: {result2['exit_code']}")


    # 测试3: 简单计算
    print("\n" + "="*60)
    print("测试3: 简单计算")
    print("="*60)

    code3 = "numbers = [1, 2, 3, 4, 5]\ntotal = sum(numbers)\naverage = total / len(numbers)\nprint(f'平均值: {average}')"

    result3 = executor.execute(code3)

    print(f"✅ 成功: {result3['success']}")
    print(f"📤 输出: {result3['stdout']}")
    print(f"🔢 退出码: {result3['exit_code']}")

    # 测试4: 超时测试（死循环）
    print("\n" + "="*60)
    print("测试4: 超时测试（死循环）")
    print("="*60)

    code4 = "import time\nwhile True:\n    time.sleep(0.1)"
    start = time.time()
    result4 = executor.execute(code4)
    elapsed = time.time() - start

    print(f"✅ 成功: {result4['success']}")
    print(f"❌ 错误: {result4['stderr']}")
    print(f"⏱️  实际耗时: {elapsed:.1f}秒（应该约10秒）")
    print(f"🔢 退出码: {result4['exit_code']}")


    # 测试5: 网络禁用测试
    print("\n" + "="*60)
    print("测试5: 网络禁用测试")
    print("="*60)

    code5 = "import urllib.request\ntry:\n    urllib.request.urlopen('http://www.google.com', timeout=5)\n    print('网络可访问')\nexcept:\n    print('网络被禁用')"
    result5 = executor.execute(code5)

    print(f"✅ 成功: {result5['success']}")
    print(f"📤 输出: {result5['stdout']}")
    print(f"💡 期望输出: '网络被禁用'")
    print(f"🔢 退出码: {result5['exit_code']}")


    # 测试6: 简单耗时任务（不超时）
    print("\n" + "="*60)
    print("测试6: 简单耗时任务（3秒内完成）")
    print("="*60)

    code6 = "import time\nfor i in range(3):\n    print(f'计算中... {i+1}/3')\n    time.sleep(0.5)\nprint('完成!')"
    result6 = executor.execute(code6)

    print(f"✅ 成功: {result6['success']}")
    print(f"📤 输出: {result6['stdout']}")
    print(f"🔢 退出码: {result6['exit_code']}")