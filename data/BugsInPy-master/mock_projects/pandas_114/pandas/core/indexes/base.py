import pandas.core.algorithms as algos
from pandas.core.arrays import ExtensionArray
from pandas.core.base import IndexOpsMixin, PandasObject
import pandas.core.common as com
# 缺少: from pandas.core.construction import extract_array

class Index:
    def __init__(self, data):
        self.data = data
    
    def get_value(self, series, key):
        """从series中获取值"""
        # 使用extract_array但没有import
        s = getattr(series, "_values", series)
        
        if isinstance(s, (ExtensionArray, Index)):
            try:
                iloc = self.get_loc(key)
                # 使用extract_array提取数组
                arr = extract_array(s, extract_numpy=True)  # ❌ NameError!
                return arr[iloc]
            except KeyError:
                raise
        
        return s[key]
    
    def get_loc(self, key):
        """获取位置"""
        return 0
