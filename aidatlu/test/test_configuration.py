from pathlib import Path
import os
import pytest
from aidatlu.main.config_parser import Configure, yaml_parser, toml_parser
from aidatlu.hardware.ioexpander_controller import IOControl
from aidatlu.main.tlu import AidaTLU
from aidatlu.hardware.i2c import I2CCore
from aidatlu.hardware.tlu_controller import TLUControl
from aidatlu.test.utils import MockI2C

FILEPATH = Path(__file__).parent
CONFIG_FILE_PATH = FILEPATH / "fixtures" / "tlu_test_configuration.yaml"
CONFIG_FILE = yaml_parser(CONFIG_FILE_PATH)

try:
    MOCK = not os.environ["HW"] == "True"
except KeyError:
    MOCK = True

if MOCK:
    HW = None
    I2CMETHOD = MockI2C
else:
    import uhal

    uhal.setLogLevelTo(uhal.LogLevel.NOTICE)
    manager = uhal.ConnectionManager(
        "file://" + str(FILEPATH / "../misc/aida_tlu_connection.xml")
    )
    HW = uhal.HwInterface(manager.getDevice("aida_tlu.controlhub"))
    I2CMETHOD = I2CCore

TLU = TLUControl(
    HW,
    i2c=I2CMETHOD,
)


def test_config_parser():
    """Test parsing the configuration file"""

    config_parser = Configure(
        tlu=TLU,
        config_dict=CONFIG_FILE,
    )
    assert isinstance(config_parser.get_configuration_table(), list)
    assert CONFIG_FILE["save_data"] == config_parser.get_data_handling()
    assert CONFIG_FILE["output_data_path"] == config_parser.get_output_data_path()
    assert (None, CONFIG_FILE["timeout"]) == config_parser.get_stop_condition()
    assert CONFIG_FILE["zmq_connection"] == config_parser.get_zmq_connection()

    config_toml_path = FILEPATH / "fixtures" / "tlu_test_configuration.toml"
    assert toml_parser(config_toml_path) == yaml_parser(CONFIG_FILE_PATH)


def test_dut_configuration():
    """Test configuration of the DUT interfaces"""
    config_parser = Configure(
        tlu=TLU,
        config_dict=CONFIG_FILE,
    )
    config_parser.conf_dut()

    assert TLU.i2c.read_register("DUTInterfaces.DUTMaskR") == 0x7
    assert TLU.i2c.read_register("DUTInterfaces.DUTInterfaceModeR") == 0x13
    assert TLU.i2c.read_register("DUTInterfaces.DUTInterfaceModeModifierR") == 0
    assert TLU.i2c.read_register("DUTInterfaces.IgnoreDUTBusyR") == 0
    assert TLU.i2c.read_register("DUTInterfaces.IgnoreShutterVetoR") == 0x1

    # HDMI I/O
    # clock
    assert (
        TLU.io_controller._get_ioexpander_output(io_exp=2, exp_id=2, cmd_byte=2) == 0x50
    )
    # SPARE, TRG, CONT
    assert (
        TLU.io_controller._get_ioexpander_output(io_exp=2, exp_id=1, cmd_byte=2) == 0x77
    )
    assert (
        TLU.io_controller._get_ioexpander_output(io_exp=2, exp_id=1, cmd_byte=3) == 0x77
    )


def test_trigger_logic_configuration():
    """Test configuration of the trigger logic"""
    config_parser = Configure(
        tlu=TLU,
        config_dict=CONFIG_FILE,
    )
    config_parser.conf_trigger_logic()
    if MOCK:
        assert TLU.i2c.read_register("triggerInputs.InvertEdgeW") == 0x1
        assert TLU.i2c.read_register("triggerLogic.InternalTriggerIntervalW") == 0x640
        # Read register does not have the same value as the write register for the mock
        TLU.i2c.write_register(
            "triggerLogic.PulseStretchR",
            TLU.i2c.read_register("triggerLogic.PulseStretchW"),
        )
        TLU.i2c.write_register(
            "triggerLogic.PulseDelayR",
            TLU.i2c.read_register("triggerLogic.PulseDelayW"),
        )

    else:
        # Rounding error in TLU when calculating trigger frequency
        assert TLU.i2c.read_register("triggerLogic.InternalTriggerIntervalR") == 0x63E

    assert TLU.i2c.read_register("triggerLogic.PulseStretchR") == 0x4210C42
    assert TLU.i2c.read_register("triggerLogic.PulseDelayR") == 0x300020

    # Test LEDs
    assert (
        TLU.io_controller._get_ioexpander_output(io_exp=1, exp_id=1, cmd_byte=2) == 0xFF
    )
    assert (
        TLU.io_controller._get_ioexpander_output(io_exp=1, exp_id=1, cmd_byte=3) == 0xFF
    )
    assert (
        TLU.io_controller._get_ioexpander_output(io_exp=1, exp_id=2, cmd_byte=2) == 0x7F
    )
    assert (
        TLU.io_controller._get_ioexpander_output(io_exp=1, exp_id=2, cmd_byte=3) == 0x58
    )


def test_trigger_input_configuration():
    """Test configuration of the trigger inputs"""
    config_parser = Configure(
        tlu=TLU,
        config_dict=CONFIG_FILE,
    )
    config_parser.conf_trigger_inputs()
    if MOCK:
        # Write array concatenates array bitwise, this is not implemented in the mock
        mem_addr = 0x18 + (0 & 0x7)
        assert TLU.i2c.read(TLU.i2c.modules["dac_1"], mem_addr) == [0x6C, 0x4E]
        assert TLU.i2c.read(TLU.i2c.modules["dac_2"], mem_addr) == [0x44, 0xEC]
        mem_addr = 0x18 + (1 & 0x7)
        assert TLU.i2c.read(TLU.i2c.modules["dac_1"], mem_addr) == [0x76, 0x26]
        assert TLU.i2c.read(TLU.i2c.modules["dac_2"], mem_addr) == [0x4E, 0xC4]

    else:
        mem_addr = 0x18 + (0 & 0x7)
        assert TLU.i2c.read(TLU.i2c.modules["dac_1"], mem_addr) == 0xD8
        assert TLU.i2c.read(TLU.i2c.modules["dac_2"], mem_addr) == 0x89
        mem_addr = 0x18 + (1 & 0x7)
        assert TLU.i2c.read(TLU.i2c.modules["dac_1"], mem_addr) == 0x31
        assert TLU.i2c.read(TLU.i2c.modules["dac_2"], mem_addr) == 0x31

    assert TLU.i2c.read_register("triggerLogic.TriggerPattern_lowR") == 0x20000
    assert TLU.i2c.read_register("triggerLogic.TriggerPattern_highR") == 0x0


def test_conf_auxillary():
    """Test PMT power and LEMO clock I/O"""
    config_parser = Configure(
        tlu=TLU,
        config_dict=CONFIG_FILE,
    )
    config_parser.conf_auxillary()

    if MOCK:
        # Write array concatenates array bitwise, this is not implemented in the mock
        mem_addr = 0x18 + (0 & 0x7)
        assert TLU.i2c.read(TLU.i2c.modules["pwr_dac"], mem_addr) == [0, 0]
        mem_addr = 0x18 + (1 & 0x7)
        assert TLU.i2c.read(TLU.i2c.modules["pwr_dac"], mem_addr) == [0xCC, 0xCC]
        mem_addr = 0x18 + (2 & 0x7)
        assert TLU.i2c.read(TLU.i2c.modules["pwr_dac"], mem_addr) == [0, 0]
        mem_addr = 0x18 + (3 & 0x7)
        assert TLU.i2c.read(TLU.i2c.modules["pwr_dac"], mem_addr) == [0xCC, 0xCC]

    else:
        mem_addr = 0x18 + (0 & 0x7)
        assert TLU.i2c.read(TLU.i2c.modules["pwr_dac"], mem_addr) == 0
        mem_addr = 0x18 + (1 & 0x7)
        assert TLU.i2c.read(TLU.i2c.modules["pwr_dac"], mem_addr) == 0x31
        mem_addr = 0x18 + (2 & 0x7)
        assert TLU.i2c.read(TLU.i2c.modules["pwr_dac"], mem_addr) == 0x33
        mem_addr = 0x18 + (3 & 0x7)
        assert TLU.i2c.read(TLU.i2c.modules["pwr_dac"], mem_addr) == 0x35

    assert (
        TLU.io_controller._get_ioexpander_output(io_exp=2, exp_id=2, cmd_byte=3) == 0xB0
    )


if __name__ == "__main__":
    pytest.main()
