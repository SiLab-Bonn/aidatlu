import sys
sys.path.insert(1, '..')

import yaml
import numpy as np
import tables as tb
from main.data_parser import DataParser

def test_data_parser():
    data_parser = DataParser()
    data_parser.parse('raw_data_test.h5', 'interpreted_data_test.h5')

def test_interpreted_data():
    features = np.dtype([('eventnumber', 'u4'), ('timestamp', 'u4'), ('overflow', 'u4'), ('eventtype', 'u4'), ('input1', 'u4'), ('input2', 'u4'), ('input3', 'u4'), 
        ('input4', 'u4'), ('inpu5', 'u4'), ('input6', 'u4'), ('sc1', 'u4'), ('sc2', 'u4'), ('sc3', 'u4'), ('sc4', 'u4'), ('sc5', 'u4'), ('sc6', 'u4')])

    interpreted_data_path = 'interpreted_data.h5'
    interpreted_test_data_path = 'interpreted_data_test.h5'

    with tb.open_file(interpreted_data_path, 'r') as file:
        table = file.root.interpreted_data
        interpreted_data = np.array(table[:], dtype=features)

    with tb.open_file(interpreted_test_data_path, 'r') as file:
        table = file.root.interpreted_data
        interpreted_test_data = np.array(table[:], dtype=features)    

    # numpy equal should do everything. But this could help for debugging.
    assert np.array_equiv(interpreted_data, interpreted_test_data)
    assert np.array_equal(interpreted_data, interpreted_test_data)
    assert (interpreted_data==interpreted_test_data).all()

def test_load_config():
    config_path = '../conf.yaml' 
    with open(config_path, 'r') as file:
        conf = yaml.full_load(file)