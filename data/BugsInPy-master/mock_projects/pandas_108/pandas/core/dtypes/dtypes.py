class DatetimeTZDtype:
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
