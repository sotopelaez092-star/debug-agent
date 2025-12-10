#!/usr/bin/env python3
"""
从BugsInPy patch中提取真实的buggy代码
创建最小但真实的项目结构
"""

import os
import re

def create_pandas_bug_108():
    """Pandas Bug 108 - IntervalDtype"""
    
    # 创建目录
    os.makedirs("mock_projects/pandas_108/pandas/core/dtypes", exist_ok=True)
    
    # 1. buggy文件 - cast.py (缺少IntervalDtype import)
    buggy_code = '''from .common import (
    is_unsigned_integer_dtype,
    pandas_dtype,
)
from .dtypes import DatetimeTZDtype, ExtensionDtype, PeriodDtype
# 缺少: from .dtypes import IntervalDtype

class lib:
    @staticmethod
    def is_period(val):
        return hasattr(val, 'freq')
    
    @staticmethod
    def is_interval(val):
        return hasattr(val, 'left')

def infer_dtype_from_scalar(val, pandas_dtype=False):
    """从标量值推断dtype"""
    dtype = None
    
    if lib.is_period(val):
        dtype = PeriodDtype(freq=val.freq)
        val = val.ordinal
    elif lib.is_interval(val):
        subtype = infer_dtype_from_scalar(val.left, pandas_dtype=True)[0]
        dtype = IntervalDtype(subtype=subtype)  # ❌ NameError!
    
    return dtype, val
'''
    
    with open("mock_projects/pandas_108/pandas/core/dtypes/cast.py", "w") as f:
        f.write(buggy_code)
    
    # 2. 定义文件 - dtypes.py (包含IntervalDtype定义)
    dtypes_code = '''class DatetimeTZDtype:
    pass

class ExtensionDtype:
    pass

class PeriodDtype:
    def __init__(self, freq=None):
        self.freq = freq

class IntervalDtype:
    """区间数据类型"""
    def __init__(self, subtype=None):
        self.subtype = subtype
'''
    
    with open("mock_projects/pandas_108/pandas/core/dtypes/dtypes.py", "w") as f:
        f.write(dtypes_code)
    
    # 3. __init__.py
    open("mock_projects/pandas_108/pandas/__init__.py", "w").close()
    open("mock_projects/pandas_108/pandas/core/__init__.py", "w").close()
    open("mock_projects/pandas_108/pandas/core/dtypes/__init__.py", "w").close()
    
    print("✅ Created: pandas_108")
    
    return {
        "id": "pandas_108",
        "project_path": "mock_projects/pandas_108",
        "error_file": "pandas/core/dtypes/cast.py",
        "undefined_name": "IntervalDtype",
        "expected_import": "from .dtypes import IntervalDtype"
    }


def create_pandas_bug_114():
    """Pandas Bug 114 - extract_array"""
    
    os.makedirs("mock_projects/pandas_114/pandas/core/indexes", exist_ok=True)
    os.makedirs("mock_projects/pandas_114/pandas/core/construction", exist_ok=True)
    
    # 1. buggy文件 - base.py
    buggy_code = '''import pandas.core.algorithms as algos
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
'''
    
    with open("mock_projects/pandas_114/pandas/core/indexes/base.py", "w") as f:
        f.write(buggy_code)
    
    # 2. 定义文件 - construction.py
    construction_code = '''def extract_array(obj, extract_numpy=False):
    """
    从对象中提取数组
    
    Parameters
    ----------
    obj : array-like
    extract_numpy : bool, default False
    
    Returns
    -------
    array
    """
    if hasattr(obj, '_values'):
        return obj._values
    return obj
'''
    
    with open("mock_projects/pandas_114/pandas/core/construction/__init__.py", "w") as f:
        f.write(construction_code)
    
    # __init__.py
    open("mock_projects/pandas_114/pandas/__init__.py", "w").close()
    open("mock_projects/pandas_114/pandas/core/__init__.py", "w").close()
    open("mock_projects/pandas_114/pandas/core/indexes/__init__.py", "w").close()
    
    print("✅ Created: pandas_114")
    
    return {
        "id": "pandas_114",
        "project_path": "mock_projects/pandas_114",
        "error_file": "pandas/core/indexes/base.py",
        "undefined_name": "extract_array",
        "expected_import": "from pandas.core.construction import extract_array"
    }


def create_pandas_bug_118():
    """Pandas Bug 118 - com.flatten"""
    
    os.makedirs("mock_projects/pandas_118/pandas/core/reshape", exist_ok=True)
    os.makedirs("mock_projects/pandas_118/pandas/core/common", exist_ok=True)
    
    # 1. buggy文件 - melt.py
    buggy_code = '''import numpy as np
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
'''
    
    with open("mock_projects/pandas_118/pandas/core/reshape/melt.py", "w") as f:
        f.write(buggy_code)
    
    # 2. 定义文件 - common.py
    common_code = '''def flatten(seq):
    """
    展平嵌套序列
    
    Parameters
    ----------
    seq : sequence
    
    Returns
    -------
    generator
    """
    for item in seq:
        if isinstance(item, (list, tuple)):
            for sub in flatten(item):
                yield sub
        else:
            yield item
'''
    
    with open("mock_projects/pandas_118/pandas/core/common/__init__.py", "w") as f:
        f.write(common_code)
    
    # __init__.py
    open("mock_projects/pandas_118/pandas/__init__.py", "w").close()
    open("mock_projects/pandas_118/pandas/core/__init__.py", "w").close()
    open("mock_projects/pandas_118/pandas/core/reshape/__init__.py", "w").close()
    
    print("✅ Created: pandas_118")
    
    return {
        "id": "pandas_118",
        "project_path": "mock_projects/pandas_118",
        "error_file": "pandas/core/reshape/melt.py",
        "undefined_name": "com",
        "expected_import": "import pandas.core.common as com"
    }


def create_scrapy_bug_9():
    """Scrapy Bug 9 - arg_to_iter"""
    
    os.makedirs("mock_projects/scrapy_9/scrapy/utils", exist_ok=True)
    
    # 1. buggy文件 - mail.py
    buggy_code = '''import logging
from email.mime.multipart import MIMEMultipart
from email.mime.nonmultipart import MIMENonMultipart
from email.utils import formatdate

# 缺少: from .utils.misc import arg_to_iter

logger = logging.getLogger(__name__)
COMMASPACE = ', '

class MailSender:
    """邮件发送器"""
    
    def __init__(self, mailfrom='noreply@example.com'):
        self.mailfrom = mailfrom
    
    def send(self, to, cc=None, subject='', body='', mimetype='text/plain'):
        """
        发送邮件
        
        Parameters
        ----------
        to : str or list
        cc : str or list
        """
        if '/' in mimetype:
            msg = MIMEMultipart()
        else:
            msg = MIMENonMultipart(*mimetype.split('/', 1))
        
        # 使用arg_to_iter但没有import
        to = list(arg_to_iter(to))  # ❌ NameError!
        cc = list(arg_to_iter(cc))  # ❌ NameError!
        
        msg['From'] = self.mailfrom
        msg['To'] = COMMASPACE.join(to)
        msg['Date'] = formatdate(localtime=True)
        msg['Subject'] = subject
        
        return msg
'''
    
    with open("mock_projects/scrapy_9/scrapy/mail.py", "w") as f:
        f.write(buggy_code)
    
    # 2. 定义文件 - utils/misc.py
    misc_code = '''def arg_to_iter(arg):
    """
    将参数转换为可迭代对象
    
    Parameters
    ----------
    arg : str, list, tuple, or None
    
    Returns
    -------
    list or tuple
    """
    if arg is None:
        return []
    elif isinstance(arg, (list, tuple)):
        return arg
    else:
        return [arg]
'''
    
    os.makedirs("mock_projects/scrapy_9/scrapy/utils/misc", exist_ok=True)
    with open("mock_projects/scrapy_9/scrapy/utils/misc/__init__.py", "w") as f:
        f.write(misc_code)
    
    # __init__.py
    open("mock_projects/scrapy_9/scrapy/__init__.py", "w").close()
    open("mock_projects/scrapy_9/scrapy/utils/__init__.py", "w").close()
    
    print("✅ Created: scrapy_9")
    
    return {
        "id": "scrapy_9",
        "project_path": "mock_projects/scrapy_9",
        "error_file": "scrapy/mail.py",
        "undefined_name": "arg_to_iter",
        "expected_import": "from .utils.misc import arg_to_iter"
    }


# Main
if __name__ == "__main__":
    print("🚀 Creating all mock projects...")
    print()
    
    cases = []
    
    # Pandas
    cases.append(create_pandas_bug_108())
    cases.append(create_pandas_bug_114())
    cases.append(create_pandas_bug_118())
    
    # Scrapy
    cases.append(create_scrapy_bug_9())
    
    print()
    print(f"✅ Created {len(cases)} mock projects")
    print()
    
    # 保存案例信息
    import json
    with open("test_cases_info.json", "w") as f:
        json.dump(cases, f, indent=2)
    
    print("📄 Saved test cases info to: test_cases_info.json")
