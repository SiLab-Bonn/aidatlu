from pathlib import Path

import numpy as np
import tables as tb
from tqdm import tqdm

from aidatlu import logger


def interpret_data(
    filepath_in: str | Path,
    filepath_out: str | Path = None,
    chunk_size: int = 1000000,
) -> None:
    """Interprets raw tlu data. The data is interpreted in chunksizes.
    The data is parsed form filepath_in to filepath_out.
    An event consists of six consecutive raw data entries the last entry should be always 0.
    The raw data is sliced and the last data entry checked for corrupted data.

    Args:
        filepath_in (str | Path): raw data file path as string or Path object
        filepath_out (str | Path): output path of the interpreted data as string or Path object
    """
    log = logger.setup_main_logger("Data Interpreter")
    features = np.dtype(
        [
            ("eventnumber", "u4"),
            ("timestamp", "u8"),
            ("overflow", "u8"),
            ("eventtype", "u4"),
            ("input1", "bool"),
            ("input2", "bool"),
            ("input3", "bool"),
            ("input4", "bool"),
            ("input5", "bool"),
            ("input6", "bool"),
            ("sc1", "u4"),
            ("sc2", "u4"),
            ("sc3", "u4"),
            ("sc4", "u4"),
            ("sc5", "u4"),
            ("sc6", "u4"),
        ]
    )
    raw_features = np.dtype([("raw", "u4")])

    log.info("Interpreting Data")
    chunk_size = chunk_size * 6

    if filepath_out == None:
        filepath_out = filepath_in + "_interpreted.h5"

    with tb.open_file(filepath_in, "r") as in_file:
        n_words = in_file.root.raw_data.shape[0]
        conf = np.array(in_file.root.conf[:])

        if n_words == 0:
            log.warning("Data is empty. Skip analysis!")
            return

        with tb.open_file(filepath_out, mode="w", title="TLU_interpreted") as out_file:
            data_table = _create_table(
                out_file, name="interpreted_data", title="data", dtype=features
            )
            for chunk in tqdm(range(0, n_words, chunk_size)):
                chunk_offset = chunk
                stop = chunk_offset + chunk_size
                if chunk + chunk_size > n_words:
                    stop = n_words
                table = in_file.root.raw_data[chunk_offset:stop]
                raw_data = np.array(table[:], dtype=raw_features)
                data = _transform_data(
                    raw_data["raw"][::6],
                    raw_data["raw"][1::6],
                    raw_data["raw"][2::6],
                    raw_data["raw"][3::6],
                    raw_data["raw"][4::6],
                    raw_data["raw"][5::6],
                    log,
                    features,
                )
                data_table.append(data)

            config = np.dtype(
                [
                    ("attribute", "S32"),
                    ("value", "S32"),
                ]
            )
            config_table = out_file.create_table(
                out_file.root,
                name="conf",
                description=config,
            )
            config_table.append(conf)
    log.success('Data parsed from "%s" to "%s"' % (filepath_in, filepath_out))


def _create_table(out_file, name, title, dtype):
    """Create hit table node for storage in out_file.
    Copy configuration nodes from raw data file.
    """
    table = out_file.create_table(
        out_file.root,
        name=name,
        description=dtype,
        title=title,
        filters=tb.Filters(complib="blosc", complevel=5, fletcher32=False),
    )
    return table


def _transform_data(
    w0: np.array,
    w1: np.array,
    w2: np.array,
    w3: np.array,
    w4: np.array,
    w5: np.array,
    log: logger,
    features: np.dtype,
) -> np.array:
    """Transforms raw data from the FIFO to a readable dataformat

    Args:
        w0 (np.array): contains information which trigger input fired
        w1 (np.array): contains timestamp information
        w2 (np.array): trigger input information
        w3 (np.array): eventnumber
        w4 (np.array): trigger input information
        w5 (np.array): this should always be 0.
        log (logger): logging function
        features (dtype): output array dtype structure

    Returns:
        np.array: array with columns
    """
    if np.any(w5) != 0:
        log.warning("Corrupted Data found")

    # Cast w0 to uint64 for concatenating 2 x 32bit to 64bit later
    w0 = w0.astype(np.uint64)

    out_array = np.zeros(len(w3), dtype=features)
    out_array["eventnumber"] = w3
    out_array["timestamp"] = (w0 & 0x0000FFFF << 32) + w1
    out_array["overflow"] = w0 & 0xFFFF
    # TODO not sure what this is per. mode?
    out_array["eventtype"] = (w0 >> 28) & 0xF
    # Which trigger input produced the event.
    out_array["input1"] = (w0 >> 16) & 0x1
    out_array["input2"] = (w0 >> 17) & 0x1
    out_array["input3"] = (w0 >> 18) & 0x1
    out_array["input4"] = (w0 >> 19) & 0x1
    out_array["input5"] = (w0 >> 20) & 0x1
    out_array["input6"] = (w0 >> 21) & 0x1
    # Finer timestamp for each trigger input sampled with double data rate 640MHz clock (0.78125 ns)
    out_array["sc1"] = (w2 >> 24) & 0xFF
    out_array["sc2"] = (w2 >> 16) & 0xFF
    out_array["sc3"] = (w2 >> 8) & 0xFF
    out_array["sc4"] = w2 & 0xFF
    out_array["sc5"] = (w4 >> 24) & 0xFF
    out_array["sc6"] = (w4 >> 16) & 0xFF
    return out_array


if __name__ == "__main__":
    input_path = "../tlu_data/tlu_raw" + ".h5"
    output_path = "../tlu_data/tlu_interpreted" + ".h5"

    interpret_data(input_path, output_path)
