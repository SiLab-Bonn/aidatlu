from i2c import I2CCore
import logger
import pandas as pd

"""

Si5344 

"""

class ClockControl(object):
    def __init__(self, i2c: I2CCore) -> None:
        self.log = logger.setup_derived_logger("Clock Controller")
        self.log.info("Initializing Clock Chip")
        self.i2c = i2c
        
        self.write_clock_conf("misc/aida_tlu_clk_config.txt")

    def get_device_version(self) -> int:
        """Get Chip informations.

        Returns:
            int: The Chip ID. #TODO what is this chip id what format should this be??
        """
        my_adress = 0x02
        chip_id = 0x00000
        self._set_page(0)
        for i in range(2):
            nibble = self.i2c.read(self.i2c.modules["clk"], my_adress) 
            chip_id = ((nibble & 0xFF) << (i*8)) | chip_id
        return chip_id

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
        
    def check_design_id(self) -> list:
        """Checks the Chip ID

        Returns:
            list: List of the Design ID should contain 8 integers. #TODO what is this now? What format should this be??
        """
        reg_address = 0x026B
        numb_words = 8
        words = []
        for _ in range(numb_words):
            words.append(self.read_clock_register(reg_address)) 
            reg_address += 1
        return words

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
        
    def parse_clock_conf(self, file_path: str) -> pd.core.frame.DataFrame:
        """reads the clock config file and returns a panda dataframe with two rows Adress and Data
           The configuration file is produced by Clockbuilder Pro (Silicon Labs).
           This function uses pandas. 
        Args:
            file_path (str): File path to the configuration file.
        
        Returns:
            panda Dataframe: 2-dim. dataframe, consisting of the address and data values.
        """
        return pd.read_csv(file_path,sep=",", skiprows = 9)

    def write_clock_conf(self, file_path: str) -> None:
        """Writes clock configuration consecutivly in register. This takes a few seconds.

        Args:
            file_path (str): File path to the clock configuration file.
        """
        clock_conf = self.parse_clock_conf(file_path)
        self.log.info("Writing Clock Configuration")
        for index,row in clock_conf.iterrows():
            self.write_clock_register(int(row["Address"],0), int(row["Data"],0))
        self.log.info("DONE")

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
        return self.i2c.read(self.i2c.modules["clk"],0x01)


    