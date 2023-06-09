import numpy as np
import tables as tb
import logger
import logging

class DataParser(object):
    
    def __init__(self) -> None:
        self.log = logger.setup_main_logger(__class__.__name__, logging.DEBUG)

        
    def parse(self, filepath_in: str,  filepath_out: str) -> None:
        """ Parse the data from filepath in readable form to filepath out

        Args:
            filepath_in (str): Raw data file from TLU.
            filepath_out (str): New interpreted data file.
        """
        table = self.read_file(filepath_in)
        features = np.dtype([('eventnumber', 'u4'), ('timestamp', 'u4'), ('eventtype', 'u4'), ('input1', 'u4'), ('input2', 'u4'), ('input3', 'u4'), 
        ('input4', 'u4'), ('inpu5', 'u4'), ('input6', 'u4'), ('sc1', 'u4'), ('sc2', 'u4'), ('sc3', 'u4'), ('sc4', 'u4'), ('sc5', 'u4'), ('sc6', 'u4')])
        data = np.rec.fromarrays(self.transform_data(table['w0'], table['w1'], table['w2'], table['w3'], table['w4'], table['w5']), dtype=features)
        self.write_data(filepath_out, data, features)

        self.log.info('Data parsed from "%s" to "%s"' %(filepath_in, filepath_out))

    def read_file(self, filepath: str) -> tb:
        """Reads raw data file of the TLU

        Args:
            filepath (str): filepath to the data file

        Returns:
            table: pytable of the raw data
        """
        data = np.dtype([('w0', 'u4'), ('w1', 'u4'), ('w2', 'u4'), ('w3', 'u4'), ('w4', 'u4'), ('w5', 'u4')])
        with tb.open_file(filepath, 'r') as file:
            table = file.root.raw_data
            raw_data = np.array(table[:], dtype=data)
            self.config = str(file.root.configuration).split(' ', 2)[2]
        return raw_data
    
    def transform_data(self, w0: np.array, w1: np.array, w2: np.array, w3: np.array, w4: np.array, w5: np.array) -> np.array:
        """Transforms raw data to a readable dataformat

        Args:
            w0 (np.array): raw data from FIFO
            w1 (np.array): raw data from FIFO
            w2 (np.array): raw data from FIFO
            w3 (np.array): raw data from FIFO
            w4 (np.array): raw data from FIFO
            w5 (np.array): raw data from FIFO

        Returns:
            np.array: array with coloumns 
        """
        event_number = w3
        timestamp = ((w0 & 0x0000FFFF << 32) + w1)
        #TODO not sure what this is per. mode?
        event_type = (w0 >> 28) & 0xF
        #Which trigger input produced the event.
        input_1 = (w0 >> 16) & 0x1
        input_2 = (w0 >> 17) & 0x1
        input_3 = (w0 >> 18) & 0x1
        input_4 = (w0 >> 19) & 0x1
        input_5 = (w0 >> 20) & 0x1
        input_6 = (w0 >> 21) & 0x1
        #TODO not sure what these are prob. something from the DACs
        sc_1 = (w2 >> 24) & 0xFF
        sc_2 = (w2 >> 16) & 0xFF
        sc_3 = (w2 >> 8) & 0xFF
        sc_4 = w2 & 0xFF
        sc_5 = (w4 >> 24) & 0xFF
        sc_6 = (w4 >> 16) & 0xFF
        return np.array([event_number, timestamp, event_type, input_1, input_2, input_3, input_4, input_5, input_6, sc_1, sc_2, sc_3, sc_4, sc_5, sc_6])

    def write_data(self, filepath: str, data: np.array, features: np.dtype) -> None:
        """Analyzes the raw data table and writes it into a new .h5 file

        Args:
            filepath (str): Path to the new .h5 file.
            data (table): raw data 
        """
        filter_data = tb.Filters(complib='blosc', complevel=5)

        with tb.open_file(filepath,  mode='w', title='TLU_interpreted') as h5_file:
            data_table = h5_file.create_table(h5_file.root, name='interpreted_data', description=features , title='data', filters=filter_data)
            data_table.append(data)
            h5_file.create_group(h5_file.root, 'configuration', self.config)