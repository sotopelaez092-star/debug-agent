def flatten(seq):
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
