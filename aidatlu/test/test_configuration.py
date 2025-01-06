from pathlib import Path

import yaml
import pytest
from aidatlu.main.config_parser import TLUConfigure
from aidatlu.hardware.ioexpander_controller import IOControl
from aidatlu.main.tlu import AidaTLU
from aidatlu.hardware.i2c import I2CCore
from aidatlu.test.utils import MockI2C

FILEPATH = Path(__file__).parent

with open(FILEPATH / "tlu_test_configuration.yaml") as yaml_file:
    test_config = yaml.safe_load(yaml_file)
MOCK = test_config["MOCK"]

if MOCK:
    I2CMETHOD = MockI2C
    HW = None
    I2C = I2CMETHOD(HW)
elif not MOCK:
    import uhal

    uhal.setLogLevelTo(uhal.LogLevel.NOTICE)
    manager = uhal.ConnectionManager(
        "file://" + str(FILEPATH / "../misc/aida_tlu_connection.xml")
    )
    HW = uhal.HwInterface(manager.getDevice("aida_tlu.controlhub"))
    I2CMETHOD = I2CCore
    I2C = I2CMETHOD(HW)

I2C.init()
IOCONTROLLER = IOControl(I2C)


TLU = AidaTLU(
    HW,
    FILEPATH / "tlu_test_configuration.yaml",
    FILEPATH / "../misc/aida_tlu_clk_config.txt",
    i2c=I2CMETHOD,
)


def test_config_parser():
    """Test parsing the configuration file"""

    config_parser = TLUConfigure(
        TLU=TLU,
        io_control=IOCONTROLLER,
        config_path=FILEPATH / "tlu_test_configuration.yaml",
    )
    with open(FILEPATH / "tlu_test_configuration.yaml") as yaml_file:
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
        io_control=IOCONTROLLER,
        config_path=FILEPATH / "tlu_test_configuration.yaml",
    )
    config_parser.conf_dut()
    if MOCK:
        # Read register does not have the same value as the write register for the mock
        TLU.i2c.write_register(
            "DUTInterfaces.DUTMaskR", TLU.i2c.read_register("DUTInterfaces.DUTMaskW")
        )
        TLU.i2c.write_register(
            "DUTInterfaces.DUTInterfaceModeR",
            TLU.i2c.read_register("DUTInterfaces.DUTInterfaceModeW"),
        )
        TLU.i2c.write_register(
            "DUTInterfaces.DUTInterfaceModeModifierR",
            TLU.i2c.read_register("DUTInterfaces.DUTInterfaceModeModifierW"),
        )
        TLU.i2c.write_register(
            "DUTInterfaces.IgnoreDUTBusyR",
            TLU.i2c.read_register("DUTInterfaces.IgnoreDUTBusyW"),
        )
        TLU.i2c.write_register(
            "DUTInterfaces.IgnoreShutterVetoR",
            TLU.i2c.read_register("DUTInterfaces.IgnoreShutterVetoW"),
        )

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
    config_parser = TLUConfigure(
        TLU=TLU,
        io_control=IOCONTROLLER,
        config_path=FILEPATH / "tlu_test_configuration.yaml",
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

    elif not MOCK:
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
    config_parser = TLUConfigure(
        TLU=TLU,
        io_control=IOCONTROLLER,
        config_path=FILEPATH / "tlu_test_configuration.yaml",
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

        # Read register does not have the same value as the write register for the mock
        TLU.i2c.write_register(
            "triggerLogic.TriggerPattern_lowR",
            TLU.i2c.read_register("triggerLogic.TriggerPattern_lowW"),
        )
        TLU.i2c.write_register(
            "triggerLogic.TriggerPattern_highR",
            TLU.i2c.read_register("triggerLogic.TriggerPattern_highW"),
        )

    elif not MOCK:
        mem_addr = 0x18 + (0 & 0x7)
        assert TLU.i2c.read(TLU.i2c.modules["dac_1"], mem_addr) == 0xD8
        assert TLU.i2c.read(TLU.i2c.modules["dac_2"], mem_addr) == 0x89
        mem_addr = 0x18 + (1 & 0x7)
        assert TLU.i2c.read(TLU.i2c.modules["dac_1"], mem_addr) == 0x31
        assert TLU.i2c.read(TLU.i2c.modules["dac_2"], mem_addr) == 0x31

    assert TLU.i2c.read_register("triggerLogic.TriggerPattern_lowR") == 0xF8F8F8F8
    assert TLU.i2c.read_register("triggerLogic.TriggerPattern_highR") == 0xF8F8F8F8


def test_conf_utils():
    """Test PMT power and LEMO clock I/O"""
    config_parser = TLUConfigure(
        TLU=TLU,
        io_control=IOCONTROLLER,
        config_path=FILEPATH / "tlu_test_configuration.yaml",
    )
    config_parser.conf_utils()

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

    elif not MOCK:
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
