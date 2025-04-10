from pathlib import Path
import time
import os
import pytest
from aidatlu.main.tlu import AidaTLU
from aidatlu.hardware.i2c import I2CCore
from aidatlu.test.utils import MockI2C

FILEPATH = Path(__file__).parent
CONFIG_FILE = FILEPATH / "fixtures" / "tlu_test_configuration.yaml"

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

TLU = AidaTLU(
    HW,
    CONFIG_FILE,
    FILEPATH / "../misc/aida_tlu_clk_config.txt",
    i2c=I2CMETHOD,
)


def test_check_ups():
    """Test read write TLU configurations"""

    if MOCK:
        TLU.set_event_fifo_csr(0)
        assert TLU.get_event_fifo_csr() == 0
        assert TLU.get_device_id() == 0xFFFFFFFFFFFF
        assert TLU.get_fw_version() == -1
        assert TLU.get_run_active() == 0
        assert TLU.get_event_fifo_fill_level() == -1
        assert TLU.get_timestamp() == -0x100000001
        assert TLU.get_scalars() == [-1, -1, -1, -1, -1, -1]
        with pytest.raises(ValueError):
            TLU.get_scalar(6)
    else:
        TLU.set_event_fifo_csr(0)
        assert TLU.get_event_fifo_csr() == 3
        assert TLU.get_run_active() == 0
        assert TLU.get_event_fifo_fill_level() == 0


def test_configuration():
    """Full test TLU configuration using test configuration file"""

    TLU.configure()


def test_run():
    """Full test TLU run using test configuration file"""

    if MOCK:
        start_time = time.time()

        def _get_timestamp(self):
            # Helper function returns timestamp
            return (time.time() - start_time) / 25 * 1000000000

        def _pull_fifo_event(self):
            # Blank FIFO pull helper function
            return 0

        # Overwrite TLU methods needed for run loop
        func_type = type(TLU.get_timestamp)
        TLU.get_timestamp = func_type(_get_timestamp, TLU)
        func_type = type(TLU.pull_fifo_event)
        TLU.pull_fifo_event = func_type(_pull_fifo_event, TLU)

        TLU.configure()
        TLU.run()

    else:
        TLU.configure()
        TLU.run()


if __name__ == "__main__":
    pytest.main()
