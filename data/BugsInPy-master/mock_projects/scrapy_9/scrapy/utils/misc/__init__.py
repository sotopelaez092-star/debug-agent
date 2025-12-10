def arg_to_iter(arg):
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
