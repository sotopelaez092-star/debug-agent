#!/usr/bin/env python3
class Config:
    def __init__(self):
        self.settings = {"debug": True, "port": 8000}
    
    def get_config(self, key):
        """获取配置"""
        return self.settings.get(key)

def main():
    config = Config()
    # 拼写错误：get_confg (少了 i)
    debug_mode = config.get_confg("debug")
    print(f"Debug: {debug_mode}")

if __name__ == "__main__":
    main()
