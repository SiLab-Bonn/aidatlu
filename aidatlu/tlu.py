import logging

import logger
from i2c import I2CCore, i2c_addr
from led_controller import LEDControl


class AidaTLU(object):
    def __init__(self, hw) -> None:
        self.log = logger.setup_main_logger(__class__.__name__, logging.DEBUG)

        self.i2c = I2CCore(hw)
        self.i2c.init()
        if self.i2c.modules["eeprom"]:
            self.log.info("Found device with ID %s" % hex(self.get_device_id()))
        self.led_controller = LEDControl(self.i2c)

        # init pwrled

        # if present, init display

    def get_device_id(self) -> int:
        """Read back board id. Consists of six blocks of hex data

        Returns:
            int: Board id as 48 bits integer
        """
        id = []
        for addr in range(6):
            id.append(self.i2c.read(self.i2c.modules["eeprom"], 0xFA + addr) & 0xFF)

        return int("0x" + "".join(["{:x}".format(i) for i in id]), 16) & 0xFFFFFFFFFFFF

    def get_fw_version(self) -> int:
        return self.i2c.read_register("version")

    def init_power_leds(self) -> None:
        raise NotImplementedError("TODO")
