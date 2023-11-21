import logger
from hardware.i2c import I2CCore
import time
from hardware.utils import _set_bit

""" 

PCA9539PW

"""


class IOControl(object):
    def __init__(self, i2c: I2CCore) -> None:
        self.log = logger.setup_derived_logger("IO Expander")

        self.log.info("Initializing IO expander")
        self.i2c = i2c

        self.init_led_expander()
        self.init_output_expander()

    def init_led_expander(self) -> None:
        """Initialize LED expanders"""
        self._set_ioexpander_polarity(1, exp_id=1, cmd_byte=4, polarity=False)
        self._set_ioexpander_direction(1, exp_id=1, cmd_byte=6, direction="output")
        self._set_ioexpander_output(1, exp_id=1, cmd_byte=2, value=0xFF)

        self._set_ioexpander_polarity(1, exp_id=1, cmd_byte=5, polarity=False)
        self._set_ioexpander_direction(1, exp_id=1, cmd_byte=7, direction="output")
        self._set_ioexpander_output(1, exp_id=1, cmd_byte=3, value=0xFF)

        self._set_ioexpander_polarity(1, exp_id=2, cmd_byte=4, polarity=False)
        self._set_ioexpander_direction(1, exp_id=2, cmd_byte=6, direction="output")
        self._set_ioexpander_output(1, exp_id=2, cmd_byte=2, value=0xFF)

        self._set_ioexpander_polarity(1, exp_id=2, cmd_byte=5, polarity=False)
        self._set_ioexpander_direction(1, exp_id=2, cmd_byte=7, direction="output")
        self._set_ioexpander_output(1, exp_id=2, cmd_byte=3, value=0xFF)

    def init_output_expander(self) -> None:
        """Initialize output expanders"""
        self._set_ioexpander_polarity(2, exp_id=1, cmd_byte=4, polarity=False)
        self._set_ioexpander_direction(2, exp_id=1, cmd_byte=6, direction="output")
        self._set_ioexpander_output(2, exp_id=1, cmd_byte=2, value=0xFF)

        self._set_ioexpander_polarity(2, exp_id=1, cmd_byte=5, polarity=False)
        self._set_ioexpander_direction(2, exp_id=1, cmd_byte=7, direction="output")
        self._set_ioexpander_output(2, exp_id=1, cmd_byte=3, value=0xFF)

        self._set_ioexpander_polarity(2, exp_id=2, cmd_byte=4, polarity=False)
        self._set_ioexpander_direction(2, exp_id=2, cmd_byte=6, direction="output")
        self._set_ioexpander_output(2, exp_id=2, cmd_byte=2, value=0x00)

        self._set_ioexpander_polarity(2, exp_id=2, cmd_byte=5, polarity=False)
        self._set_ioexpander_direction(2, exp_id=2, cmd_byte=7, direction="output")
        self._set_ioexpander_output(2, exp_id=2, cmd_byte=3, value=0xB0)

    """ 

    LED Control

    """

    def test_leds(self, single=True) -> None:
        """Test the 11 LEDs

        Args:
            single (bool, optional): Test all possible RGB combinations for all LEDs. Defaults to True.
        """
        self.log.info("Testing LEDs colors")
        if single:
            for color in [
                [0, 1, 1],
                [1, 0, 1],
                [1, 1, 0],
                [1, 0, 0],
                [0, 1, 0],
                [0, 0, 1],
                [0, 0, 0],
            ]:
                for i in range(11):
                    if i + 1 == 5:
                        pass
                    else:
                        self._set_led(i + 1, color)
                        time.sleep(0.1)
                        self.all_off()
                        time.sleep(0.05)
            for color in [[0, 0, 1], [0, 1, 1], [1, 0, 1]]:
                self._set_led(5, color)
                time.sleep(0.15)
                self.all_off()
                time.sleep(0.1)

        else:
            for color in ["w", "r", "g", "b"]:
                self.log.info("Testing LEDs color: %s" % color)

                self.all_on(color)
                time.sleep(1)
                self.all_off()
                time.sleep(1)

    def all_on(self, color: str = "w") -> None:
        """Set all LEDs to same color

        Args:
            color (str, optional): Color code [white: "w", red: "r", green: "g", blue: "b"] Defaults to "w".
        """
        if color not in ["w", "r", "g", "b"]:
            raise ValueError("%s color not supported" % color)

        if color == "w":
            self._set_ioexpander_output(io_exp=1, exp_id=1, cmd_byte=2, value=0x0)
            self._set_ioexpander_output(io_exp=1, exp_id=1, cmd_byte=3, value=0x0)
            self._set_ioexpander_output(io_exp=1, exp_id=2, cmd_byte=2, value=0x0)
            self._set_ioexpander_output(io_exp=1, exp_id=2, cmd_byte=3, value=0x0)

        if color == "r":
            self._set_ioexpander_output(io_exp=1, exp_id=1, cmd_byte=2, value=0xB5)
            self._set_ioexpander_output(io_exp=1, exp_id=1, cmd_byte=3, value=0x6D)
            self._set_ioexpander_output(io_exp=1, exp_id=2, cmd_byte=2, value=0xDB)
            self._set_ioexpander_output(io_exp=1, exp_id=2, cmd_byte=3, value=0xB6)

        if color == "g":
            self._set_ioexpander_output(io_exp=1, exp_id=1, cmd_byte=2, value=0xDA)
            self._set_ioexpander_output(io_exp=1, exp_id=1, cmd_byte=3, value=0xB6)
            self._set_ioexpander_output(io_exp=1, exp_id=2, cmd_byte=2, value=0x6D)
            self._set_ioexpander_output(io_exp=1, exp_id=2, cmd_byte=3, value=0xDB)

        if color == "b":
            self._set_ioexpander_output(io_exp=1, exp_id=1, cmd_byte=2, value=0x6F)
            self._set_ioexpander_output(io_exp=1, exp_id=1, cmd_byte=3, value=0xDB)
            self._set_ioexpander_output(io_exp=1, exp_id=2, cmd_byte=2, value=0xB6)
            self._set_ioexpander_output(io_exp=1, exp_id=2, cmd_byte=3, value=0x6D)

    def all_off(self) -> None:
        """Turn off all LEDs"""
        self._set_ioexpander_output(io_exp=1, exp_id=1, cmd_byte=2, value=0xFF)
        self._set_ioexpander_output(io_exp=1, exp_id=1, cmd_byte=3, value=0xFF)
        self._set_ioexpander_output(io_exp=1, exp_id=2, cmd_byte=2, value=0xFF)
        self._set_ioexpander_output(io_exp=1, exp_id=2, cmd_byte=3, value=0xFF)

    def switch_led(self, led_id: int, color: str = "off") -> None:
        """changes LED with led_id to specific color

        Args:
            led_id (int): ID for the 11 LEDs, led_id has to be between 1 and 11
            color (str, optional): Color code [white: "w", red: "r", green: "g", blue: "b", off: "off"]
                                   for Clock LED only [red: "r", green: "g", off: "off"].
                                   Defaults to "off".
        """

        if led_id == 5 and color not in ["r", "g", "off"]:
            raise ValueError("%s color not supported for Clock LED" % color)

        elif color not in ["w", "r", "g", "b", "off"]:
            raise ValueError("%s color not supported for LED" % color)

        # Clock LED has only two LEDs
        if led_id == 5:
            if color == "r":
                rgb = [0, 1, 1]
            if color == "g":
                rgb = [1, 0, 1]
            if color == "off":
                rgb = [1, 1, 1]

        else:
            if color == "w":
                rgb = [0, 0, 0]
            if color == "r":
                rgb = [0, 1, 1]
            if color == "g":
                rgb = [1, 0, 1]
            if color == "b":
                rgb = [1, 0, 0]
            if color == "off":
                rgb = [1, 1, 1]

        self._set_led(led_id, rgb)

    def _set_led(self, led_id: int, rgb: list) -> None:
        """sets led to a rgb value

        Args:
            led_id (int): Led id for the 11 LED, led_ id has to be between 1 and 11
            rgb (list): rgb value for the LED e.q. [0,0,0]

        """
        if led_id < 1 or led_id > 11:
            raise ValueError("LED ID has to be between 1 and 11")

        # indicator map for LED positions notice the -1 for the clock led #TODO should this be global??
        indicator = [
            [30, 29, 31],
            [27, 26, 28],
            [24, 23, 25],
            [21, 20, 22],
            [18, 17, -1],
            [15, 14, 16],
            [12, 11, 13],
            [9, 8, 10],
            [6, 5, 7],
            [3, 2, 4],
            [1, 0, 19],
        ]

        now_status = []  # status of all ioexpander now
        next_status = []  # status of all ioexpander next
        now_status.append(0xFF & self._get_ioexpander_output(1, 1, 2))
        now_status.append(0xFF & self._get_ioexpander_output(1, 1, 3))
        now_status.append(0xFF & self._get_ioexpander_output(1, 2, 2))
        now_status.append(0xFF & self._get_ioexpander_output(1, 2, 3))

        word = 0x00000000
        word = word | now_status[0]
        word = word | (now_status[1] << 8)
        word = word | (now_status[2] << 16)
        word = word | (now_status[3] << 24)
        # print(word,"word for debugging")

        for index in range(3):
            if (
                led_id == 5
            ):  # for clock led not all colors are allowed on clock [1,0,1] is green [0,1,1] is red the og eudaq indicator map produces here an error
                # TODO some colors also switch on LED 11
                word = _set_bit(word, [18, 17, 19][index], rgb[index])
            else:
                word = _set_bit(word, indicator[led_id - 1][index], rgb[index])

        next_status.append(0xFF & word)
        next_status.append(0xFF & (word >> 8))
        next_status.append(0xFF & (word >> 16))
        next_status.append(0xFF & (word >> 24))
        # print(next_status,"next_status of the ioexpander for debugging")

        if now_status[0] != next_status[0]:
            self._set_ioexpander_output(1, 1, 2, next_status[0])

        if now_status[1] != next_status[1]:
            self._set_ioexpander_output(1, 1, 3, next_status[1])

        if now_status[2] != next_status[2]:
            self._set_ioexpander_output(1, 2, 2, next_status[2])

        if now_status[3] != next_status[3]:
            self._set_ioexpander_output(1, 2, 3, next_status[3])

    """ 

    Output Control

    """

    def configure_hdmi(self, hdmi_channel: int, enable: int | str) -> None:
        """This enables the pins of one HDMI channel as input (0) or output (1).
            Enable is a 4-bit WORD for each pin as integer or binary string. With CONT = bit 0, SPARE = bit 1, TRIG = bit 2 and BUSY = bit 3.
            E.q. 0b0111 or '0111' sets CONT, SPARE and TRIGGER as outputs and BUSY as input. '1100' sets CONT and SPARE as input and BUSY and TRIG as output.
            The clock runs with the seperate function: clock_hdmi_output.

        Args:
            hdmi_num (int): HDMI channels from 1 to 4
            enable (int | str, optional): 4-bit WORD to enable the 4 pins on the HDMI output. Can be an integer or binary string.

        """
        # TODO use DUT Interface or HDMI channel?
        if hdmi_channel < 1 or hdmi_channel > 4:
            raise ValueError("HDMI channel should be between 1 and 4")

        if type(enable) == str:
            enable = int(enable, 2)

        if enable > 0b1111 or enable < 0b0000:
            raise ValueError("Enable has to be between 0 and 16 ('10000').")

        expander_id = 1

        # TODO what is the difference between nibble and bank and address?
        hdmi_channel = hdmi_channel - 1  # shift channel
        bank = (
            int(hdmi_channel / 2) + 2
        )  # DUT0 and DUT1 are on bank0. DUT2 and DUT 3 are on bank 1. Shift of +2 due to the command bytes.
        nibble = (
            hdmi_channel % 2
        )  # DUT0 and DUT2 are on nibble 0. DUT1 and DUT3 are on nibble 1.

        # TODO what is happening here
        old_status = self._get_ioexpander_output(2, expander_id, bank)
        new_nibble = (enable & 0xF) << 4 * nibble
        mask = 0xF << 4 * nibble
        new_status = (old_status & (~mask)) | (new_nibble & mask)

        self._set_ioexpander_output(2, expander_id, bank, new_status)
        self.log.info("HDMI Channel %i set to %s" % (hdmi_channel + 1, str(enable)))

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
        expander_id = 2

        hdmi_channel = hdmi_channel - 1  # shift channel
        mask_low = 1 << (hdmi_channel)
        mask_high = 1 << (hdmi_channel + 4)
        mask = mask_low | mask_high
        old_status = self._get_ioexpander_output(2, expander_id, cmd_byte)

        if clock_source == "off":
            new_status = old_status & ~mask
        elif clock_source == "chip":
            new_status = (old_status | mask_high) & ~mask_low
        elif clock_source == "fpga":  # TODO nothing measurable here for now
            new_status = (old_status | mask_low) & ~mask_high
        else:
            new_status = old_status
        self._set_ioexpander_output(2, expander_id, cmd_byte, new_status)
        self.log.info(
            "Clock source of HDMI Channel %i set to %s."
            % (hdmi_channel + 1, clock_source)
        )

    def clock_lemo_output(self, enable: bool = True) -> None:
        """Enables the clock LEMO output. #TODO only with ~40MHz default clock

        Args:
            enable (bool, optional): Enable clock LEMO output. Defaults to True.
        """

        cmd_byte = 3  # this is bank+2 in EUDAQ
        mask = 0x10
        expander_id = 2

        old_status = self._get_ioexpander_output(2, expander_id, cmd_byte) & 0xFF
        new_status = old_status & (~mask) & 0xFF
        if enable:
            new_status = new_status | mask & 0xFF

        self._set_ioexpander_output(2, expander_id, cmd_byte, new_status)
        if enable:
            self.switch_led(5, "g")
        else:
            self.switch_led(5, "off")
        self.log.info("Clock LEMO output %s" % ("enabled" if enable else "disabled"))

    """ 

    General Expander Control

    """

    def _set_ioexpander_polarity(
        self, io_exp: int, exp_id: int, cmd_byte: int, polarity: bool = False
    ) -> None:
        """Set content of register 4 or 5 which determine polarity of ports.
            A command byte of 4 or 5 determines the polarity of ports on the two different banks of the chip.
            io_exp and exp_id control the 2 expander for the LEDs and 2 for the output control.

        Args:
            io_exp (int): Expander (1 or 2). The LED expander on 1 the output expander on 2.
            exp_id (int): ID of the Expander (1 or 2))
            cmd_byte (int): The Command byte is used as a pointer to a specific register see datasheet PC9539.
            polarity (bool, optional): False (0) = normal, True (1) = inverted. Defaults to False.
        """
        if io_exp not in [1, 2]:
            raise ValueError("Expander should be 1 or 2")
        if cmd_byte not in [4, 5]:
            raise ValueError("Command byte should be 4 or 5")
        if exp_id not in [1, 2]:
            raise ValueError("Expander ID should be 1 or 2")

        if io_exp == 1:
            exp = "led_expander"
        else:
            exp = "expander"

        self.i2c.write(self.i2c.modules["%s_%.1s" % (exp, exp_id)], cmd_byte, polarity)

    def _set_ioexpander_direction(
        self, io_exp: int, exp_id: int, cmd_byte: int, direction: str = "input"
    ) -> None:
        """Set content of register 6 or 7 which determine direction of signal.
            A command byte of 6 or 7 determines the direction of signal on the two different banks of the chip.
            io_exp and exp_id control the 2 expander for the LEDs and 2 for the output control.

        Args:
            io_exp (int): Expander (1 or 2). The LED expander on 1 the output expander on 2.
            exp (int): ID of Expander (1 or 2))
            cmd_byte (int): The Command byte is used as a pointer to a specific register see datasheet PC9539.
            direction (str, optional): "input or "output" direction of port. Defaults to "input".
        """
        if io_exp not in [1, 2]:
            raise ValueError("Expander should be 1 or 2")
        if cmd_byte not in [6, 7]:
            raise ValueError("Command byte should be 6 or 7")
        if direction not in ["input", "output"]:
            raise ValueError('Direction parameter must be "input" or "output"')
        if exp_id not in [1, 2]:
            raise ValueError("Expander ID should be 1 or 2")

        if io_exp == 1:
            exp = "led_expander"
        else:
            exp = "expander"

        self.i2c.write(
            self.i2c.modules["%s_%.1s" % (exp, exp_id)],
            cmd_byte,
            1 if direction == "input" else 0,
        )

    def _set_ioexpander_output(
        self, io_exp: int, exp_id: int, cmd_byte: int, value: int
    ) -> None:
        """Set content of register 2 or 3 which determine signal if direction is output
            A command byte of 2 or 3 reflects the outgoing logic levels of the output pins on the two different banks of the chip.
            io_exp and exp_id control the 2 expander for the LEDs and 2 for the output control.

        Args:
            io_exp (int): Expander (1 or 2). The LED expander on 1 the output expander on 2.
            exp (int): ID of Expander (1 or 2))
            cmd_byte (int): The Command byte is used as a pointer to a specific register see datasheet PC9539.
            value (int): 8 bit value for the output
        """
        if io_exp not in [1, 2]:
            raise ValueError("Expander should be 1 or 2")
        if cmd_byte not in [2, 3]:
            raise ValueError("Command byte should be 2 or 3")
        if exp_id not in [1, 2]:
            raise ValueError("Expander ID should be 1 or 2")

        if io_exp == 1:
            exp = "led_expander"
        else:
            exp = "expander"

        self.i2c.write(
            self.i2c.modules["%s_%.1s" % (exp, exp_id)], cmd_byte, value & 0xFF
        )

    def _get_ioexpander_output(self, io_exp: int, exp_id: int, cmd_byte: int) -> int:
        """Get content of register 2 or 3
            A command byte of 2 or 3 reflects the outgoing logic levels of the output pins on the two different banks of the chip.
            io_exp and exp_id control the 2 expander for the LEDs and 2 for the output control.

        Args:
            io_exp (int): Expander (1 or 2). The LED expander on 1 the output expander on 2.
            exp_id (int): ID of Expander (1 or 2).
            cmd_byte (int): The Command byte is used as a pointer to a specific register see datasheet PC9539.
        Returns:
            int: content of the ioexpander
        """
        if io_exp not in [1, 2]:
            raise ValueError("Expander should be 1 or 2")
        if cmd_byte not in [2, 3]:
            raise ValueError("Command byte should be 2 or 3")
        if exp_id not in [1, 2]:
            raise ValueError("Expander ID should be 1 or 2")

        if io_exp == 1:
            exp = "led_expander"
        else:
            exp = "expander"

        output = self.i2c.read(self.i2c.modules["%s_%.1s" % (exp, exp_id)], cmd_byte)
        return output
