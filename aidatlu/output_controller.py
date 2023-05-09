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

        self._set_ioexpander_polarity_out(exp=1, cmd_byte=4, polarity=False)
        self._set_ioexpander_direction_out(exp=1, cmd_byte=6, direction="output")
        self._set_ioexpander_output_out(exp=1, cmd_byte=2, value=0xFF)

        self._set_ioexpander_polarity_out(exp=1, cmd_byte=5, polarity=False)
        self._set_ioexpander_direction_out(exp=1, cmd_byte=7, direction="output")
        self._set_ioexpander_output_out(exp=1, cmd_byte=3, value=0xFF)

        self._set_ioexpander_polarity_out(exp=2, cmd_byte=4, polarity=False)
        self._set_ioexpander_direction_out(exp=2, cmd_byte=6, direction="output")
        self._set_ioexpander_output_out(exp=2, cmd_byte=2, value=0x00)

        self._set_ioexpander_polarity_out(exp=2, cmd_byte=5, polarity=False)
        self._set_ioexpander_direction_out(exp=2, cmd_byte=7, direction="output")
        self._set_ioexpander_output_out(exp=2, cmd_byte=3, value=0xB0)

    def configure_hdmi(self, hdmi_channel: int, enable: int | str) -> None:
        """ This enables the pins of one HDMI channel as input (0) or output (1).
            Enable is a 4-bit WORD for each pin as integer or binary string. With CONT = bit 0, SPARE = bit 1, TRIG = bit 2 and BUSY = bit 3. 
            E.q. 0b0111 or '0111' sets CONT, SPARE and TRIGGER as outputs and BUSY as input. '1100' sets CONT and SPARE as input and BUSY and TRIG as output. 
            The clock runs with the seperate function: clock_hdmi_output.
        
        Args:
            hdmi_num (int): HDMI channels from 1 to 4
            enable (int | str, optional): 4-bit WORD to enable the 4 pins on the HDMI output. Can be an integer or binary string.

        """
        #TODO use DUT Interface or HDMI channel?
        if hdmi_channel < 1 or hdmi_channel > 4:
            raise ValueError("HDMI channel should be between 1 and 4")

        if type(enable) == str:
            enable = int(enable, 2)

        if enable > 0b1111:
            raise ValueError("Enable has to be smaller than 16 ('10000').")
        if enable < 0b0000:
            raise ValueError("Enable has to be positive.")

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
        if enable: #TODO move these LEDS to DUT mode blue AIDA and green EUDET or so?
            self.led_controller.switch_led(hdmi_channel+1, "g")
        else:
            self.led_controller.switch_led(hdmi_channel+1, "off")
        self.log.info("HDMI Channel %i %s" %(hdmi_channel+1, ("enabled" if enable else "disabled")))

    def clock_hdmi_output(self, hdmi_channel: int, clock_source: str) -> None:
        """Enables the Clock output for one HDMI channel. 
           Valid Clock sources are Si5453 clock chip 'chip' and FPGA 'fpga'.
           #TODO does FPGA work?   
           
        Args:
            hdmi_channel (int): HDMI channels from 1 to 4
            clock_source (str): Clock source valid options are 'off', 'chip' and 'fpga'.
        """
        if clock_source not in ["off", "chip", "fpga"]:
            raise ValueError("Clock source has to be 'off', 'chip' or 'fpga'")
        if hdmi_channel < 1 or hdmi_channel > 4:
            raise ValueError("HDMI channel should be between 1 and 4")
        
        cmd_byte = 2
        expander = 2 

        hdmi_channel = hdmi_channel -1 #shift channel
        mask_low = 1 << (hdmi_channel)
        mask_high = 1 << (hdmi_channel + 4)
        mask = mask_low | mask_high
        old_status = self._get_ioexpander_output_out(expander, cmd_byte)

        if clock_source == 'off':
            new_status = old_status & ~mask
        elif clock_source == 'chip': #TODO Signal looks unstable
            new_status = (old_status | mask_high) & ~mask_low
        elif clock_source == 'fpga': #TODO nothing measurable here for now
            new_status = (old_status | mask_high) & ~mask_high
        else:
            new_status = old_status
        self._set_ioexpander_output_out(expander, cmd_byte, new_status)
        self.log.info("Clock source of HDMI Channel %i set to %s." %(hdmi_channel+1,clock_source))


    def clock_lemo_output(self, enable: bool = True) -> None:
        """Enables the clock LEMO output. #TODO only with ~40MHz default clock

        Args:
            enable (bool, optional): Enable clock LEMO output. Defaults to True.
        """
        
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
            
    def _set_ioexpander_output_out(self, exp: int, cmd_byte: int, value: int) -> None:
        """Set content of register 2 or 3 which determine signal if direction is output
            A command byte of 2 or 3 reflects the outgoing logic levels of the output pins on the two different banks of the chip.
        Args:
            exp (int): ID of LED Expander (1 or 2))
            cmd_byte (int): The Command byte is used as a pointer to a specific register see datasheet PC9539.
            value (int): 8 bit value for the output
        """
        if cmd_byte not in [2, 3]:
            raise ValueError("Command byte should be 2 or 3")
        if exp not in [1, 2]:
            raise ValueError("Expander ID should be 1 or 2")
        self.i2c.write(self.i2c.modules["expander_%.1s" % exp], cmd_byte, value & 0xFF)

    def _get_ioexpander_output_out(self, exp: int, cmd_byte: int) -> int:
        """Get content of register 2 or 3
            A command byte of 2 or 3 reflects the outgoing logic levels of the output pins on the two different banks of the chip.
        Args:
            exp (int): _ID of LED Expander (1 or 2))
            cmd_byte (int): The Command byte is used as a pointer to a specific register see datasheet PC9539.
        Returns:
            int: content of the ioexpander
        """
        if cmd_byte not in [2, 3]:
            raise ValueError("Command byte should be 2 or 3")
        if exp not in [1, 2]:
            raise ValueError("Expander ID should be 1 or 2")
        
        output = self.i2c.read(self.i2c.modules["expander_%.1s" % exp], cmd_byte)
        return output
    
    def _set_ioexpander_polarity_out(
        self, exp: int, cmd_byte: int, polarity: bool = False
        ) -> None:
        """Set content of register 4 or 5 which determine polarity of ports.
            A command byte of 4 or 5 determines the polarity of ports on the two different banks of the chip.

        Args:
            exp (int): ID of LED Expander (1 or 2))
            cmd_byte (int): The Command byte is used as a pointer to a specific register see datasheet PC9539.
            polarity (bool, optional): False (0) = normal, True (1) = inverted. Defaults to False.
        """
        if cmd_byte not in [4, 5]:
            raise ValueError("Command byte should be 4 or 5")
        if exp not in [1, 2]:
            raise ValueError("Expander ID should be 1 or 2")

        self.i2c.write(self.i2c.modules["expander_%.1s" % exp], cmd_byte, polarity)

    def _set_ioexpander_direction_out(
        self, exp: int, cmd_byte: int, direction: str = "input"
    ) -> None:
        """Set content of register 6 or 7 which determine direction of signal
        A command byte of 6 or 7 determines the direction of signal on the two different banks of the chip.
        
        Args:
            exp (int): ID of LED Expander (1 or 2))
            cmd_byte (int): The Command byte is used as a pointer to a specific register see datasheet PC9539.
            direction (str, optional): "input or "output" direction of port. Defaults to "input".
        """
        if cmd_byte not in [6, 7]:
            raise ValueError("Command byte should be 6 or 7")
        if direction not in ["input", "output"]:
            raise ValueError('Direction parameter must be "input" or "output"')
        if exp not in [1, 2]:
            raise ValueError("Expander ID should be 1 or 2")
        
        self.i2c.write(
            self.i2c.modules["expander_%.1s" % exp],
            cmd_byte,
            1 if direction == "input" else 0,
        )

