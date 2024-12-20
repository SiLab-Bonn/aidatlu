import numpy as np
import tables as tb
import yaml
from pathlib import Path
from aidatlu.main.data_parser import interpret_data
from aidatlu.main.config_parser import TLUConfigure


FILEPATH = Path(__file__).parent


def test_data_parser():
    interpret_data("raw_data_test.h5", "interpreted_data_test.h5")


def test_interpreted_data():
    interpreted_data_path = FILEPATH / "interpreted_data.h5"
    interpreted_test_data_path = FILEPATH / "interpreted_data_test.h5"

    with tb.open_file(interpreted_data_path, "r") as file:
        interpreted_data = file.root.interpreted_data[:]
        config_table = file.root.conf[:]

    with tb.open_file(interpreted_test_data_path, "r") as file:
        interpreted_test_data = file.root.interpreted_data[:]
        config_table_test = file.root.conf[:]

    assert np.array_equal(interpreted_data, interpreted_test_data)
    assert np.array_equal(config_table, config_table_test)


if __name__ == "__main__":
    test_data_parser()
    test_interpreted_data()
