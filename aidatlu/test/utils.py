import yaml
from aidatlu import logger
from aidatlu.hardware.i2c import I2CCore, i2c_addr


class MockI2C(I2CCore):
    """Class mocking the I2C interface and replacing the hardware with register dictionaries for testing."""

    def __init__(self, hw_int) -> None:  # noqa
        with open("register_table.yaml", "r") as yaml_file:
            self.reg_table = yaml.safe_load(yaml_file)
        self.i2c_device_table = {
            0x21: {},
            0x68: {},  # Si5345
            0x13: {},  # 1st AD5665R
            0x1F: {},  # 2nd AD5665R
            0x50: {},  # EEPROM
            0x74: {},  # 1st expander PCA9539PW
            0x75: {},  # 2nd expander PCA9539PW
            0x51: {},  # Address of EEPROM on powermodule, only available on new modules
            0x1C: {},  # AD5665R (DAC) on powermodule
            0x76: {},  # 1st expander PCA9539PW
            0x77: {},  # 2nd expander PCA9539PW,
            0x3A: {},  # Display
        }
        self.log = logger.setup_derived_logger("I2CCore")
        self.modules = i2c_addr  # Use I2C device name to address translation

    def init(self):
        self.set_i2c_clock_prescale(0x30)
        self.set_i2c_control(0x80)

        self.write(0x21, 0x01, 0x7F)
        if self.read(0x21, 0x01) & 0x80 != 0x80:
            self.log.warning(
                "Enabling Enclustra I2C bus might have failed. This could prevent from talking to the I2C slaves \
                 on the TLU."
            )
        # Omitted dynamic search for connected I2C modules here and just continue with `init`
        self.set_i2c_tx(0x0)
        self.set_i2c_command(0x50)

    def write(self, device_addr: int, mem_addr: int, value: int) -> None:
        """Mock I2C device memory write"""
        self.i2c_device_table[device_addr][mem_addr] = value

    def write_array(self, device_addr: int, mem_addr: int, values: list) -> None:
        """Mock I2C device memory array write"""
        self.i2c_device_table[device_addr][mem_addr] = values

    def read(self, device_addr: int, mem_addr: int) -> int:
        """Mock I2C memory read"""
        return self.i2c_device_table[device_addr][mem_addr]

    def write_register(self, register: str, value: int) -> None:
        """Mock IPbus register write"""
        reg_adressing = register.split(".")
        if len(reg_adressing) == 2:
            self.reg_table[reg_adressing[0]][reg_adressing[1]]["value"] = value
        elif len(reg_adressing) == 1:
            self.reg_table[register]["value"] = value
        else:
            raise ValueError("Invalid register addressing")

    def read_register(self, register: str) -> int:
        """Mock IPbus register read"""
        reg_adressing = register.split(".")
        if len(reg_adressing) == 2:
            return self.reg_table[reg_adressing[0]][reg_adressing[1]]["value"]
        if len(reg_adressing) == 2:
            return self.reg_table[reg_adressing[0]]["value"]
        raise ValueError("Invalid register addressing")
