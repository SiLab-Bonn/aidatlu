import numpy as np
import tables as tb
import aidatlu.main.data_parser as DataParser
from aidatlu.main.config_parser import TLUConfigure


def test_data_parser():
    DataParser.interpret_data("raw_data_test.h5", "interpreted_data_test.h5")


def test_interpreted_data():
    features = np.dtype(
        [
            ("eventnumber", "u4"),
            ("timestamp", "u4"),
            ("overflow", "u4"),
            ("eventtype", "u4"),
            ("input1", "u4"),
            ("input2", "u4"),
            ("input3", "u4"),
            ("input4", "u4"),
            ("inpu5", "u4"),
            ("input6", "u4"),
            ("sc1", "u4"),
            ("sc2", "u4"),
            ("sc3", "u4"),
            ("sc4", "u4"),
            ("sc5", "u4"),
            ("sc6", "u4"),
        ]
    )

    interpreted_data_path = "interpreted_data.h5"
    interpreted_test_data_path = "interpreted_data_test.h5"

    with tb.open_file(interpreted_data_path, "r") as file:
        table = file.root.interpreted_data
        interpreted_data = np.array(table[:], dtype=features)

    with tb.open_file(interpreted_test_data_path, "r") as file:
        table = file.root.interpreted_data
        interpreted_test_data = np.array(table[:], dtype=features)

    assert np.array_equal(interpreted_data, interpreted_test_data)


def test_load_config():
    config_path = "../tlu_configuration.yaml"
    config_parser = TLUConfigure(TLU=None, io_control=None, config_path=config_path)
    _ = config_parser.get_configuration_table()
    _ = config_parser.get_data_handling()
    _ = config_parser.get_output_data_path()
    _ = config_parser.get_stop_condition()
    _ = config_parser.get_zmq_connection()


if __name__ == "__main__":
    test_data_parser()
    test_interpreted_data()
    test_load_config()
