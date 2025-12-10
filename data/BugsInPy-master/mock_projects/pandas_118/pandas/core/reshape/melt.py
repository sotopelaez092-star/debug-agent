import numpy as np
from pandas.core.dtypes.missing import notna
from pandas.core.arrays import Categorical
# 缺少: import pandas.core.common as com
from pandas.core.frame import DataFrame
from pandas.core.indexes.base import Index

def melt(frame, id_vars=None, value_vars=None):
    """
    将DataFrame从宽格式转换为长格式
    """
    cols = ['col1', 'col2', 'col3']
    
    if id_vars is not None:
        if not isinstance(id_vars, (list, tuple)):
            id_vars = [id_vars]
        else:
            id_vars = list(id_vars)
            # 使用com.flatten但没有import
            missing = Index(com.flatten(id_vars)).difference(cols)  # ❌ NameError!
            if not missing.empty:
                raise KeyError("id_vars not found")
    
    if value_vars is not None:
        value_vars = list(value_vars)
        missing = Index(com.flatten(value_vars)).difference(cols)  # ❌ NameError!
        if not missing.empty:
            raise KeyError("value_vars not found")
    
    return frame
