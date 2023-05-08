import logger
from i2c import I2CCore

class DUTLogic(object):
    def __init__(self, i2c: I2CCore):
        self.log = logger.setup_derived_logger("DUT Logic")

        self.i2c = i2c

    def set_dut_mask(self, value: int) -> None:
        """Enables HDMI Outputs the value is here an 4-bit number to enable eache HDMI channel.
           e.q. 0b0001 enables HDMI 1 and so on. #TODO see TLU doc p. 62.

        Args:
            value (int): _description_
        """
        self.i2c.write_register("DUTInterfaces.DUTMaskW", value)
        self.log.info("DUT mask is set to %s" %self.get_dut_mask())

    def set_dut_mask_mode(self, value: int) -> None:
        """Sets the DUT interface mode. value consits of 4 2-bit numbers. 
        Each 2-bit number corresponds to one HDMI output and its Mode.
        E.q. 0b00000011 sets HDMI channel 1 to AIDA mode. #TODO See TLU doc. p. 49 and p. 62. 

        Args:
            value (int): _description_
        """
        self.i2c.write_register("DUTInterfaces.DUTInterfaceModeW", value)
        self.log.info("DUT mask mode is set to %s" %self.get_dut_mask_mode())

    def set_dut_mask_mode_modifier(self, value: int) -> None:
        self.i2c.write_register("DUTInterfaces.DUTInterfaceModeModifierW", value)
        self.log.info("DUT mask mode modifier is set to %s" %self.get_dut_mask_mode_modifier())

    def set_dut_ignore_busy(self, value: int) -> None:
        self.i2c.write_register("DUTInterfaces.IgnoreDUTBusyW", value)
        self.log.info("DUT ignore busy is set to %s" %self.get_dut_ignore_busy())

    def get_dut_mask(self) -> int:
        return self.i2c.read_register("DUTInterfaces.DUTMaskR")

    def get_dut_mask_mode(self)  -> int:
        return self.i2c.read_register("DUTInterfaces.DUTInterfaceModeR")

    def get_dut_mask_mode_modifier(self)  -> int:
        return self.i2c.read_register("DUTInterfaces.DUTInterfaceModeModifierR")

    def get_dut_ignore_busy(self) -> int:
        return self.i2c.read_register("DUTInterfaces.IgnoreDUTBusyR")

