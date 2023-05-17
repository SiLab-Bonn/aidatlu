


def _set_bit(value: int, index: int, set: bool=True) -> int:
    """sets bit at given index of given value to bool set

    Args:
        value (int): input value
        index (int): index where to change bit
        set (bool, optional): change bit to bool

    Returns:
        int: value with a set bit at index
    """
    
    if set:
        return value | (1<<index)
    else:
        return value & ~(1<<index)
    
def _pack_bits(vector: list) -> int:
    """Pack Vector of bits using 5-bits for each element. 

    Args:
        vector (list): Vector of bits with variable length.

    Returns:
        int: 32-bit word representation of the input vector. 
    """
    #TODO Numpy would prob. be more elegant for this.
    packed_bits = 0x0
    temp_int = 0x0
    for channel in range(len(vector)):
        temp_int = int(vector[channel]) << channel*5
        packed_bits = packed_bits | temp_int
    return packed_bits