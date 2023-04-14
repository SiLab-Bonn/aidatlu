import time
from math import ceil

import logger

i2c_addr = {
    "core": 0x21,
    "clk": 0x68,  # Si5345
    "dac_1": 0x13,  # 1st AD5665R
    "dac_2": 0x1F,  # 2nd AD5665R
    "eeprom": 0x50,  # EEPROM
    "expander_1": 0x74,  # 1st expander PCA9539PW
    "expander_2": 0x75,  # 2nd expander PCA9539PW
    "pwr_id": 0x51,  # Address of EEPROM on powermodule, only available on new modules
    "pwr_dac": 0x1C,  # AD5665R (DAC) on powermodule
    "led_expander_1": 0x76,  # 1st expander PCA9539PW
    "led_expander_2": 0x77,  # 2nd expander PCA9539PW,
    "display": 0x3A,  # Display
}


class I2CCore(object):
    def __init__(self, hw_int):
        """hw_int: IPBus HwInterface instance"""
        self.log = logger.setup_derived_logger(__class__.__name__)
        self.i2c_hw = hw_int
        self.modules = {}

    def init(self):
        self.set_i2c_clock_prescale(0x30)
        self.set_i2c_control(0x80)

        self.write(i2c_addr["core"], 0x01, 0x7F)
        if self.read(i2c_addr["core"], 0x01) & 0x80 != 0:
            self.log.warn(
                "Enabling Enclustra I2C bus might have failed. This could prevent from talking to the I2C slaves on the TLU."
            )

        for addr in range(128):
            self.set_i2c_tx((addr << 1) | 0x0)
            self.set_i2c_command(0x90)
            if (self.get_i2c_status() >> 7 & 0x01) == 0:
                if addr in i2c_addr.values():
                    self.log.debug(
                        "Module %s found at address %s"
                        % (
                            list(i2c_addr.keys())[
                                list(i2c_addr.values()).index(addr)
                            ].upper(),
                            hex(addr),
                        )
                    )
                    self.modules[
                        list(i2c_addr.keys())[list(i2c_addr.values()).index(addr)]
                    ] = addr
                else:
                    self.log.debug(
                        "Unknown module found at address %s, not in address list"
                        % hex(addr)
                    )
        self.set_i2c_tx(0x0)
        self.set_i2c_command(0x50)

    def write_register(self, register: str, value: int) -> None:
        """
            register: str  Name of node in address file
            value:    int  Value to be written
        """
        if type(value) != int:
            raise TypeError("Value must be integer")
        try:
            self.i2c_hw.getNode(register).write(value)
            self.i2c_hw.dispatch()
        except Exception:
            raise

    def read_register(self, register: str) -> int:
        """
            register: str  Name of node in address file
        """
        try:
            ret = self.i2c_hw.getNode(register).read()
            self.i2c_hw.dispatch()
            if ret.valid():
                return ret.value()
            else:
                raise RuntimeError("Error reading register %s" % register)
        except Exception:
            raise

    def get_i2c_status(self):
        return self.read_register("i2c_master.i2c_cmdstatus")

    def set_i2c_control(self, value: int):
        self.write_register("i2c_master.i2c_ctrl", value & 0xFF)

    def set_i2c_command(self, value: int):
        self.write_register("i2c_master.i2c_cmdstatus", value & 0xFF)
        while self.is_done():
            time.sleep(1)

    def set_i2c_tx(self, value: int):
        self.write_register("i2c_master.i2c_rxtx", value & 0xFF)

    def is_done(self) -> bool:
        return bool((self.get_i2c_status() >> 1) & 0x1)

    def set_i2c_clock_prescale(self, value: int):
        self.write_register("i2c_master.i2c_pre_lo", value & 0xFF)
        self.write_register("i2c_master.i2c_pre_hi", (value >> 8) & 0xFF)

    def write(self, device_addr: int, mem_addr: int, value: int) -> None:
        self.set_i2c_tx((device_addr << 1) | 0x0)
        self.set_i2c_command(0x90)

        self.set_i2c_tx(mem_addr)
        self.set_i2c_command(0x10)

        if value > 0xFF:
            n_bytes_to_write = ceil(len(hex(value)[2:] / 2))
            for byte in range(
                8 * (n_bytes_to_write - 1), 0, -8
            ):  # funky magic to write byte by byte
                to_write = (value & (0xFF << byte)) >> byte
                self.set_i2c_tx(to_write)
                self.set_i2c_command(0x10)
        self.set_i2c_tx(value & 0xFF)
        self.set_i2c_command(0x50)

    def read(self, device_addr: int, mem_addr: int) -> int:
        self.set_i2c_tx((device_addr << 1) | 0x0)
        self.set_i2c_command(0x90)

        self.set_i2c_tx(mem_addr)
        self.set_i2c_command(0x10)

        self.set_i2c_tx((device_addr << 1) | 0x1)
        self.set_i2c_command(0x90)
        self.set_i2c_command(0x28)

        return self.read_register("i2c_master.i2c_rxtx")

