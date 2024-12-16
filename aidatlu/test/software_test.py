from pathlib import Path

import numpy as np
import tables as tb

from aidatlu.main.config_parser import TLUConfigure
from aidatlu.main.data_parser import DataParser

BASE_PATH = Path(__file__).parent


def test_interpretation():
    """Test data interpretation and compare to reference file"""

    data_parser = DataParser()
    data_parser.interpret_data(
        BASE_PATH / "raw_data_test.h5", "interpreted_data_test.h5"
    )

    interpreted_data_path = BASE_PATH / "interpreted_data.h5"
    interpreted_test_data_path = BASE_PATH / "interpreted_data_test.h5"

    with tb.open_file(interpreted_data_path, "r") as h5_file:
        interpreted_data = h5_file.root.interpreted_data[:]

    with tb.open_file(interpreted_test_data_path, "r") as h5_file:
        interpreted_test_data = h5_file.root.interpreted_data[:]

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
    test_interpretation()
    test_load_config()
