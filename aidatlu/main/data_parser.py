import numpy as np
import tables as tb
import logger
import logging


class DataParser(object):
    def __init__(self) -> None:
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

    def parse(self, filepath_in: str, filepath_out: str) -> None:
        """Parse the data from filepath in readable form to filepath out

        Args:
            filepath_in (str): Raw data file from TLU.
            filepath_out (str): New interpreted data file.
        """
        table = self.read_file(filepath_in)
        data = self.transform_data(
            table["w0"], table["w1"], table["w2"], table["w3"], table["w4"], table["w5"]
        )
        self.write_data(filepath_out, data)

        self.log.info('Data parsed from "%s" to "%s"' % (filepath_in, filepath_out))

    def read_file(self, filepath: str) -> tb:
        """Reads raw data file of the TLU

        Args:
            filepath (str): filepath to the data file

        Returns:
            table: pytable of the raw data
        """
        data = np.dtype(
            [
                ("w0", "u4"),
                ("w1", "u4"),
                ("w2", "u4"),
                ("w3", "u4"),
                ("w4", "u4"),
                ("w5", "u4"),
            ]
        )
        with tb.open_file(filepath, "r") as file:
            table = file.root.raw_data
            raw_data = np.array(table[:], dtype=data)
            self.config = str(file.root.configuration).split(" ", 2)[2]
        return raw_data

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

    def transform_data(
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

    def write_data(self, filepath: str, data: np.array) -> None:
        """Analyzes the raw data table and writes it into a new .h5 file

        Args:
            filepath (str): Path to the new .h5 file.
            data (table): raw data
        """
        # filter_data = tb.Filters(complib='blosc', complevel=5)
        with tb.open_file(filepath, mode="w", title="TLU_interpreted") as h5_file:
            data_table = self._create_table(
                h5_file, name="interpreted_data", title="data", dtype=self.features
            )
            # data_table = h5_file.create_table(h5_file.root, name='interpreted_data', description=features , title='data', filters=filter_data)
            data_table.append(data)
            h5_file.create_group(h5_file.root, "configuration", self.config)
