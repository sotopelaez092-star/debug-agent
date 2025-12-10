from .common import (
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
