from hardware.i2c import I2CCore
from hardware.ioexpander_controller import IOControl
import logger

"""

Si5344 

"""

class ClockControl(object):
    def __init__(self, i2c: I2CCore, io_control: IOControl) -> None:
        self.log = logger.setup_derived_logger("Clock Controller")
        self.log.info("Initializing Clock Chip")
        self.i2c = i2c
        self.io_control = io_control

    def get_device_version(self) -> int:
        """Get Chip information.

        Returns:
            int: The Chip ID.
        """
        my_adress = 0x02
        chip_id = 0x0
        self._set_page(0)
        for i in range(2):
            nibble = self.i2c.read(self.i2c.modules["clk"], my_adress + i) 
            chip_id = ((nibble & 0xFF) << (i*8)) | chip_id
        return chip_id

    def check_design_id(self, hex_str: bool = False ) -> list:
        """Checks the Chip ID. If the chip is correctly configured the list corresponds 
           to the data in the clock configuration file between the addresses 0x026B and 0x0272.

        Args:
            hex_str (bool): Returns the design ID as a list of hex strings. Defaults to False. 

        Returns:
            list: List of the design ID contains 8 integers or hex strings.
        """
        reg_address = 0x026B
        numb_words = 8
        words = []
        for _ in range(numb_words):
            words.append(self.read_clock_register(reg_address)) 
            reg_address += 1
        if hex_str:
            words = [hex(words[i]) for i in range(numb_words)]
        return words

    def read_clock_register(self, address: int) -> int:
        """Reads register of the clock chip.

        Args:
            address (int): Address of the register.

        Returns:
            int: Integer from the register address.
        """
        address = address & 0xFFFF
        current_page = self._get_page()
        required_page = (address & 0XFF00) >> 8
        if (current_page != required_page):
            self._set_page(required_page)
        return self.i2c.read(self.i2c.modules["clk"], address)
        
    def write_clock_register(self, address: int, data: int) -> None:
        """Write data in specific Clock Chip register.

        Args:
            address (int): Destination register.
            data (int): Data to be written in address.
        """
        address = address & 0xFFFF
        current_page = self._get_page()
        required_page = (address & 0XFF00) >> 8
        if (current_page != required_page):
            self._set_page(required_page)
        
        self.i2c.write(self.i2c.modules["clk"], address, data)
        
    def parse_clock_conf(self, file_path: str) -> list:
        """reads the clock config file and returns a panda dataframe with two rows Adress and Data
           The configuration file is produced by Clockbuilder Pro (Silicon Labs). 
        Args:
            file_path (str): File path to the configuration file.
        
        Returns:
            list: 2-dim. list, consisting of the address and data values.
        """
        with open(file_path, newline='') as clk_conf:
            contents = clk_conf.read().splitlines()
            contents = [row.split(',') for row in contents[10:]]
        return contents

    def write_clock_conf(self, file_path: str) -> None:
        """Writes clock configuration consecutivly in register. This takes a few seconds.

        Args:
            file_path (str): File path to the clock configuration file.
        """
        clock_conf = self.parse_clock_conf(file_path)
        self.log.info("Writing clock configuration")
        self.io_control.all_on('r')
        for index,row in enumerate(clock_conf):
            self.write_clock_register(int(row[0], 16), int(row[1], 16))
            #This is just fancy, show progress of clock configuration with LEDs.
            if index % 10 == 0 and int((index/len(clock_conf)*10+1)) != 5:
                self.io_control.switch_led(int((index/len(clock_conf)*10+1)),'b')

        self.log.success("Done writing clock configuration ")
        self.io_control.all_off()

    def _set_page(self, page: int) -> None:
        """Configures chip to perform operations on specific address page.

        Args:
            page (int): Address page.
        """
        self.i2c.write(self.i2c.modules["clk"], 0x01, page)

    def _get_page(self) -> int:
        """Get the current address page.

        Returns:
            int: Current address page
        """
        return self.i2c.read(self.i2c.modules["clk"], 0x01)


    