import logger
from i2c import I2CCore, i2c_addr


class LEDControl(object):
    def __init__(self, i2c: I2CCore, int_ref: bool = False) -> None:
        self.log = logger.setup_derived_logger("LED Controller")
        self.i2c = i2c
        self._set_dac_reference(int_ref)
        # TODO: WHY?!
        self._set_ioexpander_polarity(exp=1, addr=4, polarity=False)
        self._set_ioexpander_direction(exp=1, addr=6, direction="output")
        self._set_ioexpander_output(exp=1, addr=2, value=0xFF)
        self._set_ioexpander_polarity(exp=1, addr=5, polarity=False)
        self._set_ioexpander_direction(exp=1, addr=7, direction="output")
        self._set_ioexpander_output(exp=1, addr=3, value=0xFF)
        self._set_ioexpander_polarity(exp=2, addr=4, polarity=False)
        self._set_ioexpander_direction(exp=2, addr=6, direction="output")
        self._set_ioexpander_output(exp=2, addr=2, value=0xFF)
        self._set_ioexpander_polarity(exp=2, addr=5, polarity=False)
        self._set_ioexpander_direction(exp=2, addr=7, direction="output")
        self._set_ioexpander_output(exp=2, addr=3, value=0xFF)

    def test_leds(self) -> None:
        pass

    def all_on(self, color: str = "w") -> None:
        """Set all LEDs to same color

        Args:
            color (str, optional): Color code, currently only white (w) supported. Defaults to "w".
        """
        self._set_ioexpander_output(exp=1, addr=2, value=0x0)
        self._set_ioexpander_output(exp=1, addr=3, value=0x0)
        self._set_ioexpander_output(exp=2, addr=2, value=0x0)
        self._set_ioexpander_output(exp=2, addr=3, value=0x0)

    def all_off(self) -> None:
        """Turn off all LEDs
        """
        self._set_ioexpander_output(exp=1, addr=2, value=0xFF)
        self._set_ioexpander_output(exp=1, addr=3, value=0xFF)
        self._set_ioexpander_output(exp=2, addr=2, value=0xFF)
        self._set_ioexpander_output(exp=2, addr=3, value=0xFF)

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

    def _set_ioexpander_polarity(
        self, exp: int, addr: int, polarity: bool = False
    ) -> None:
        """Set content of register 4 or 5 which determine polarity of ports

        Args:
            exp (int): ID of LED Expander (1 or 2))
            addr (int):  # TODO, what is this?!
            polarity (bool, optional): False (0) = normal, True (1) = inverted. Defaults to False.
        """
        if addr not in [4, 5]:
            raise ValueError("Address should be 4 or 5")
        self.i2c.write(self.i2c.modules["led_expander_%.1s" % exp], addr, polarity)

    def _set_ioexpander_direction(
        self, exp: int, addr: int, direction: str = "input"
    ) -> None:
        """Set content of register 6 or 7 which determine direction of signal

        Args:
            exp (int): ID of LED Expander (1 or 2))
            addr (int): # TODO, what is this?!
            direction (str, optional): "input or "output" direction of port. Defaults to "input".
        """
        if addr not in [6, 7]:
            raise ValueError("Address should be 6 or 7")
        if direction not in ["input", "output"]:
            raise ValueError('Direction parameter must be "input" or "output"')
        self.i2c.write(
            self.i2c.modules["led_expander_%.1s" % exp],
            addr,
            1 if direction == "input" else 0,
        )

    def _set_ioexpander_output(self, exp: int, addr: int, value: int) -> None:
        """Set content of register 2 or 3 which determine signal if direction is output

        Args:
            exp (int): ID of LED Expander (1 or 2))
            addr (int): # TODO, what is this?!
            value (int): 8 bit value for the output
        """
        if addr not in [2, 3]:
            raise ValueError("Address should be 6 or 7")
        self.i2c.write(self.i2c.modules["led_expander_%.1s" % exp], addr, value & 0xFF)
