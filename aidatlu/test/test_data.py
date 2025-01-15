from pathlib import Path
import numpy as np
import tables as tb
import pytest
from aidatlu.main.data_parser import interpret_data

FILEPATH = Path(__file__).parent


def test_interpreted_data():
    """Test interpreting and parsing data"""

    interpret_data(
        FILEPATH / "fixtures" / "raw_data_test.h5", FILEPATH / "interpreted_data.h5"
    )

    interpreted_data_path = FILEPATH / "interpreted_data.h5"
    interpreted_test_data_path = FILEPATH / "fixtures" / "interpreted_data_test.h5"

    with tb.open_file(interpreted_data_path, "r") as file:
        interpreted_data = file.root.interpreted_data[:]
        config_table = file.root.conf[:]

    with tb.open_file(interpreted_test_data_path, "r") as file:
        interpreted_test_data = file.root.interpreted_data[:]
        config_table_test = file.root.conf[:]

    assert np.array_equal(interpreted_data, interpreted_test_data)
    assert np.array_equal(config_table, config_table_test)


if __name__ == "__main__":
    pytest.main()
