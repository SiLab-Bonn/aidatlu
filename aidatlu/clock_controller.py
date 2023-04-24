from i2c import I2CCore
import logger

class ClockControl(object):
    def __init__(self, i2c: I2CCore) -> None:
        self.log = logger.setup_derived_logger("Clock Controller")
        self.i2c = i2c
        
        self.parse_clock_conf()
        self.write_clock_conf()

    def get_device_version():
        pass 

    def read_clock_register():
        pass

    def write_clock_register():
        pass

    def check_design_id():
        pass

    def parse_clock_conf():
        pass

    def write_clock_conf():
        pass

    def _set_page():
        pass

    def _get_page():
        pass


    