from i2c import I2CCore
import logger



class VoltageControl(object,):
    def __init__(self, i2c: I2CCore, int_ref: bool = False) -> None:
        self.log = logger.setup_derived_logger("Voltage Controller")
        self.i2c = i2c
        self._set_dac_reference(int_ref)


    def set_voltage(self, channel: int, voltage: float) -> None:
        # Does float voltage work here? 
        pass


    def _set_dac_reference(self, internal: bool = False) -> None:
        """Choose internal or external DAC reference

        Args:
            internal (bool, optional): Defaults to False.
        """
        if internal:
            self.i2c.write(self.i2c.modules["pwr_dac"], 0x38, 0x0001)
        else:
            self.i2c.write(self.i2c.modules["pwr_dac"], 0x38, 0x0001)
        self.log.info(
            "Set %s DAC reference for LEDs" % ("internal" if internal else "external")
        )

    def _set_dac_value(self, channel: int, value: int) -> None:
        
        if channel < 0 or channel > 7:
            raise ValueError("Channel hast to be between 0 and 7")
        
        if value<0:
            self.log.info(
                "value < 0 not supported, value will default to 0"
                )
            value = 0
            
        if value>0xFFFF:
            self.log.info(
                "value > 0xFFFF not supported, value will default to 0xFFFF"
                )
            value = 0xFFFF

        pass
