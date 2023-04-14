


def _set_bit(value: int, index: int, set: bool=True) -> int:
    """sets bit at given index of given value to bool set

    Args:
        value (int): input value
        index (int): index where to change bit
        set (bool, optional): change bit to bool

    Returns:
        int: value with a set bit at index
    """
    #I stole this from https://stackoverflow.com/questions/12173774/how-to-modify-bits-in-an-integer
    if set:
        return value | (1<<index)
    else:
        return value & ~(1<<index)