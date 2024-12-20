from pathlib import Path

import yaml
import pytest
from aidatlu.main.config_parser import TLUConfigure
from aidatlu.hardware.ioexpander_controller import IOControl
from aidatlu.main.tlu import AidaTLU
from aidatlu.test.utils import MockI2C

BASE_PATH = Path(__file__).parent

I2C = MockI2C(None)
I2C.init()
IO_CONTROLLER = IOControl(I2C)


TLU = AidaTLU(
    None,
    BASE_PATH / "tlu_test_configuration.yaml",
    BASE_PATH / "../misc/aida_tlu_connection.xml",
)


def test_config_parser():
    """Test parsing the configuration file"""

    config_parser = TLUConfigure(
        TLU=TLU,
        io_control=IO_CONTROLLER,
        config_path=BASE_PATH / "tlu_test_configuration.yaml",
    )
    with open(BASE_PATH / "tlu_test_configuration.yaml") as yaml_file:
        test_config = yaml.safe_load(yaml_file)
    assert isinstance(config_parser.get_configuration_table(), list)
    assert test_config["save_data"] == config_parser.get_data_handling()
    assert test_config["output_data_path"] == config_parser.get_output_data_path()
    assert (None, test_config["timeout"]) == config_parser.get_stop_condition()
    assert test_config["zmq_connection"] == config_parser.get_zmq_connection()


def test_dut_configuration():
    """Test configuration of the DUT interfaces"""
    config_parser = TLUConfigure(
        TLU=TLU,
        io_control=IO_CONTROLLER,
        config_path=BASE_PATH / "tlu_test_configuration.yaml",
    )
    config_parser.conf_dut()


def test_trigger_logic_configuration():
    """Test configuration of the trigger logic"""
    config_parser = TLUConfigure(
        TLU=None,
        io_control=IO_CONTROLLER,
        config_path=BASE_PATH / "tlu_test_configuration.yaml",
    )
    # config_parser.conf_trigger_logic()


def test_trigger_input_configuration():
    """Test configuration of the trigger inputs"""
    config_parser = TLUConfigure(
        TLU=None,
        io_control=IO_CONTROLLER,
        config_path=BASE_PATH / "tlu_test_configuration.yaml",
    )
    # config_parser.conf_trigger_inputs()


if __name__ == "__main__":
    pytest.main()
