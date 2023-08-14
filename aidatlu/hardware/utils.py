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
    packed_bits = 0x0
    temp_int = 0x0
    for channel in range(len(vector)):
        temp_int = int(vector[channel]) << channel*5
        packed_bits = packed_bits | temp_int
    return packed_bits

from pathlib import Path
def find_latest_file(path: str, index: str):
    """Find latest file that includes a given subset of strings called index in directory.
    Args:
        path (str): Path to directory. For same directory as python script use for e.q. './target_dir'.
        index (str): (Optional) Find if specific characters are in Pathfile
    Returns:
        path: Path to file in target Director. Use str(find_path(.)) to obtain path as string.
    """
    p = Path(path)
    return max([x for x in p.iterdir() if x.is_file() and index in str(x)], key=lambda item: item.stat().st_ctime)