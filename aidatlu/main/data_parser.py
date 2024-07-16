import numpy as np
import tables as tb
from aidatlu import logger
import logging
from tqdm import tqdm

class DataParser(object):
    def __init__(self, chunk_size: int = 2000000) -> None:
        self.log = logger.setup_main_logger(__class__.__name__, logging.DEBUG)
        self.features = np.dtype(
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
        self.raw_features = np.dtype([("raw", "u4")])
        self.chunk_size = chunk_size*6

    def interpret_data(self, filepath_in: str, filepath_out: str) -> None:
        """Interprets raw tlu data. The data is interpreted in chunksizes.
        The data is parsed form filepath_in to filepath_out.
        An event consists of six consecutive raw data entries tha last entry should be a 0.
        The raw data is sliced and the last data entry checked for corrupted data.

        Args:
            filepath_in (str): raw data file path
            filepath_out (str): output path of the interpreted data
        """
        self.log.info('Interpreting Data')
        self.chunk_offset = 0
        with tb.open_file(filepath_in, "r") as file:
            n_words = file.root.raw_data.shape[0]
            self.conf = np.array(file.root.conf[:])
            if n_words == 0:
                self.log.warning('Data is empty. Skip analysis!')
                return

            with tb.open_file(filepath_out, mode="w", title="TLU_interpreted") as h5_file:
                data_table = self._create_table(
                h5_file, name="interpreted_data", title="data", dtype=self.features
                )
                # pbar = tqdm(total=int(n_words/self.chunk_size), unit=' Chunks', unit_scale=True)
                for chunk in tqdm(range(0, n_words, self.chunk_size)):
                    stop = self.chunk_offset+self.chunk_size
                    if chunk + self.chunk_size > n_words:
                        stop = n_words
                    table = file.root.raw_data[self.chunk_offset:stop]
                    raw_data = np.array(table[:], dtype=self.raw_features)
                    data = self._transform_data(
                    raw_data["raw"][::6],
                    raw_data["raw"][1::6],
                    raw_data["raw"][2::6],
                    raw_data["raw"][3::6],
                    raw_data["raw"][4::6],
                    raw_data["raw"][5::6],
                    )
                    data_table.append(data)
                    self.chunk_offset = chunk
                config = np.dtype(
                [
                    ("attribute", "S32"),
                    ("value", "S32"),
                ])
                config_table = h5_file.create_table(
                    h5_file.root,
                    name="conf",
                    description=config,
                )
                config_table.append(self.conf)
        self.log.success('Data parsed from "%s" to "%s"' % (filepath_in, filepath_out))

    def _create_table(self, out_file, name, title, dtype):
        """Create hit table node for storage in out_file.
        Copy configuration nodes from raw data file.
        """
        table = out_file.create_table(
            out_file.root,
            name=name,
            description=dtype,
            title=title,
            #   expectedrows=self.chunk_size,
            filters=tb.Filters(complib="blosc", complevel=5, fletcher32=False),
        )

        return table

    def _transform_data(
        self,
        w0: np.array,
        w1: np.array,
        w2: np.array,
        w3: np.array,
        w4: np.array,
        w5: np.array,
    ) -> np.array:
        """Transforms raw data from the FIFO to a readable dataformat

        Args:
            w0 (np.array): contains information which trigger input fired
            w1 (np.array): contains timestamp information
            w2 (np.array): trigger input information
            w3 (np.array): eventnumber
            w4 (np.array): trigger input information
            w5 (np.array): this should always be 0.

        Returns:
            np.array: array with coloumns
        """
        if np.any(w5) != 0:
            self.log.warning("Corrupted Data found")
        out_array = np.zeros(len(w3), dtype=self.features)
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
        # TODO not sure what these are prob. something from the DACs
        out_array["sc1"] = (w2 >> 24) & 0xFF
        out_array["sc2"] = (w2 >> 16) & 0xFF
        out_array["sc3"] = (w2 >> 8) & 0xFF
        out_array["sc4"] = w2 & 0xFF
        out_array["sc5"] = (w4 >> 24) & 0xFF
        out_array["sc6"] = (w4 >> 16) & 0xFF
        return out_array

    def _parse(self, filepath_in: str, filepath_out: str) -> None:
        """Parse the data from filepath in readable form to filepath out

        Args:
            filepath_in (str): Raw data file from TLU.
            filepath_out (str): New interpreted data file.
        """
        table = self.read_file(filepath_in)
        data = self.transform_data(
            table["raw"][::6],
            table["raw"][1::6],
            table["raw"][2::6],
            table["raw"][3::6],
            table["raw"][4::6],
            table["raw"][5::6],
        )
        self.write_data(filepath_out, data)

        self.log.info('Data parsed from "%s" to "%s"' % (filepath_in, filepath_out))

    def _read_file(self, filepath: str) -> list:
        """Reads raw data file of the TLU

        Args:
            filepath (str): filepath to the data file

        Returns:
            table: pytable of the raw data
        """
        data = np.dtype([("raw", "u4")])
        with tb.open_file(filepath, "r") as file:
            table = file.root.raw_data
            raw_data = np.array(table[:], dtype=data)
            self.conf = np.array(file.root.conf[:])
        return raw_data

    def _write_data(self, filepath: str, data: np.array) -> None:
        """Analyzes the raw data table and writes it into a new .h5 file

        Args:
            filepath (str): Path to the new .h5 file.
            data (table): raw data
        """
        # filter_data = tb.Filters(complib='blosc', complevel=5)
        config = np.dtype(
            [
                ("attribute", "S32"),
                ("value", "S32"),
            ]
        )
        with tb.open_file(filepath, mode="w", title="TLU_interpreted") as h5_file:
            data_table = self._create_table(
                h5_file, name="interpreted_data", title="data", dtype=self.features
            )
            data_table.append(data)
            config_table = h5_file.create_table(
                h5_file.root,
                name="conf",
                description=config,
            )
            config_table.append(self.conf)

if __name__ == "__main__":
    path_in = '../tlu_data/tlu_raw' + '.h5'
    path_out = '../tlu_data/tlu_interpreted' + '.h5'

    data_parser = DataParser()

    data_parser.interpret_data(path_in, path_out)
