from i2c import I2CCore
import logger

class VoltageControl(object):
    def __init__(self, i2c: I2CCore, int_ref: bool = False) -> None:
        self.log = logger.setup_derived_logger("Voltage Controller")
        self.i2c = i2c
        self._set_dac_reference(int_ref)

    def set_voltage(self, channel: int, voltage: float) -> None:
        """Sets given DAC to given output voltage.

        Args:
            channel (int): DAC channel
            voltage (float): DAC output voltage
        """
        #TODO why here between 0 and 3 and for dac value between 0 and 7??
        if channel < 0 or channel > 3:
            raise ValueError("Channel has to be between 0 and 3")
        
        if voltage < 0:
            self.log.warn(
                "A Voltage value smaller than 0 is not supported, Voltage will default to 0"
                )
            voltage = 0
            
        if voltage > 1:
            self.log.warn(
                "A Voltage value bigger than 1 is not supported, Voltage will default to 1"
                )
            voltage = 1

            #0xFFFF is max DAC value
            self._set_dac_value(channel,int(voltage*0xFFFF))

    def _set_dac_reference(self, internal: bool = False) -> None:
        """Choose internal or external DAC reference

        Args:
            internal (bool, optional): Defaults to False.
        """
        if internal:
            #TODO does this work? eudaq uses here an array write function. That function uses a loop to write the single chars from the array in.
            self.i2c.write(self.i2c.modules["pwr_dac"], 0x38, 0x0001)
        else:
            #TODO does this work? eudaq uses here an array write function. That function uses a loop to write the single chars from the array in.
            self.i2c.write(self.i2c.modules["pwr_dac"], 0x38, 0x0000)
        self.log.info(
            "Set %s DAC reference for LEDs" % ("internal" if internal else "external")
        )

    def _set_dac_value(self, channel: int, value: int) -> None:
        """Set the output value of a DAC

        Args:
            channel (int): DAC channel
            value (int): DAC output value
        """
        if channel < 0 or channel > 7:
            raise ValueError("Channel has to be between 0 and 7")
        
        if value<0x0000:
            self.log.warn(
                "DAC value < 0x0000 not supported, value will default to 0x0000"
                )
            value = 0
            
        if value>0xFFFF:
            self.log.warn(
                "DAC value > 0xFFFF not supported, value will default to 0xFFFF"
                )
            value = 0xFFFF
        
        first_value = value & 0xFF
        second_value = (value>>8) & 0xFF

        #TODO does this work? eudaq uses here an array write function. This uses a loop to write the single chars from the array in.
        # There could be a bug here due to the consecutive writing of the the register with non zero values. poss. there is a need for this write array function here
        mem_addr = 0x18 + (channel & 0x7)
        self.i2c.write(self.i2c.modules["pwr_dac"], mem_addr, first_value)
        self.i2c.write(self.i2c.modules["pwr_dac"], mem_addr, second_value)

