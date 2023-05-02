import logger
from i2c import I2CCore
from led_controller import LEDControl

""" 

PCA9539PW

"""

#TODO should this be merged with LEDControll to I/OExpanderControll

class OutputControl(object):
    def __init__(self, i2c: I2CCore, led: LEDControl):
        self.log = logger.setup_derived_logger("Output Controller")

        self.i2c = i2c
        self.led_controller = led

    def configure_hdmi(self, hdmi_channel: int, enable: bool = True) -> None:
        """This enables the HDMI output of one specific HDMI channel. #TODO not tested

        Args:
            hdmi_num (int): _description_
            enable (bool, optional): _description_. Defaults to True.
        """
    
        if hdmi_channel < 1 and hdmi_channel > 4:
            raise ValueError("HDMI channel should be between 1 and 4")

        expander = 1

        #TODO what is the difference between nibble and bank and address?
        hdmi_channel = hdmi_channel -1 #shift channel
        bank = int(hdmi_channel/2) + 2 # DUT0 and DUT1 are on bank0. DUT2 and DUT 3 are on bank 1. Shift of +2 due to the command bytes.
        nibble = hdmi_channel % 2  #DUT0 and DUT2 are on nibble 0. DUT1 and DUT3 are on nibble 1.

        #TODO what is happening here
        old_status = self._get_ioexpander_output_out(expander, bank)
        new_nibble = (enable & 0xF) << 4*nibble
        mask = 0xF << 4*nibble
        new_status = (old_status & (~mask)) | (new_nibble & mask)

        self._set_ioexpander_output_out(expander, bank, new_status)
        if enable:
            self.led_controller.switch_led(hdmi_channel+1, "g")
        else:
            self.led_controller.switch_led(hdmi_channel+1, "off")

    def clock_lemo_output(self, enable: bool = True) -> None:
        """Enables the clock LEMO output. #TODO not tested

        Args:
            enable (bool, optional): Enable clock LEMO output. Defaults to True.
        """
        #TODO this does not work I checked with all combinations of expander[1,2] and bank[1,2,3]
        cmd_byte = 3 #this is bank+2 in EUDAQ
        mask = 0x10
        expander = 2

        old_status = self._get_ioexpander_output_out(expander, cmd_byte) & 0xFF
        new_status = old_status & (~mask) & 0xFF
        if enable:
            new_status = new_status | mask & 0xFF

        self._set_ioexpander_output_out(expander, cmd_byte, new_status)
        if enable:
            self.led_controller.switch_led(5, "g")  
        else:
            self.led_controller.switch_led(5, "off")
        self.log.info("Clock LEMO output %s" %("enabled" if enable else "disabled"))
            
    def _set_ioexpander_output_out(self, exp: int, addr: int, value: int) -> None:
        """Set content of register 2 or 3 which determine signal if direction is output
            A command byte of 2 or 3 reflects the outgoing logic levels of the output pins on the two different banks of the chip.
        Args:
            exp (int): ID of LED Expander (1 or 2))
            addr (int): The Command byte is used as a pointer to a specific register see datasheet PC9539.
            value (int): 8 bit value for the output
        """
        if addr not in [2, 3]:
            raise ValueError("Address should be 2 or 3")
        if exp not in [1, 2]:
            raise ValueError("Expander ID should be 1 or 2")
        self.i2c.write(self.i2c.modules["expander_%.1s" % exp], addr, value & 0xFF)

    def _get_ioexpander_output_out(self, exp: int, addr: int) -> int:
        """Get content of register 2 or 3
            A command byte of 2 or 3 reflects the outgoing logic levels of the output pins on the two different banks of the chip.
        Args:
            exp (int): _ID of LED Expander (1 or 2))
            addr (int): The Command byte is used as a pointer to a specific register see datasheet PC9539.
        Returns:
            int: content of the ioexpander
        """
        if addr not in [2, 3]:
            raise ValueError("Address should be 2 or 3")
        if exp not in [1, 2]:
            raise ValueError("Expander ID should be 1 or 2")
        
        output = self.i2c.read(self.i2c.modules["expander_%.1s" % exp], addr)
        return output
