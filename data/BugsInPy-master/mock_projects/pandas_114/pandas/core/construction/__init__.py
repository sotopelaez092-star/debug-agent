def extract_array(obj, extract_numpy=False):
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
