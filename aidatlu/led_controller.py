import logger
from i2c import I2CCore
import time
from utils import _set_bit

class LEDControl(object):
    def __init__(self, i2c: I2CCore) -> None:
        self.log = logger.setup_derived_logger("LED Controller")
        self.i2c = i2c

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

    def test_leds(self,single=True) -> None:
        if single:
            for color in [[0,1,1],[1,0,1],[1,1,0],[1,0,0],[0,1,0],[0,0,1],[0,0,0]]:
                for i in range(11):
                    if i+1==5:
                        pass
                    else:
                        self._set_led(i+1,color)
                        time.sleep(0.1)
                        self.all_off()
                        time.sleep(0.05)
            for color in [[0,0,1],[0,1,1],[1,0,1]]:
                self._set_led(5,color)
                time.sleep(0.15)
                self.all_off()
                time.sleep(0.1)

        else:
            for color in ["w","r","g","b"]:
                self.log.info(
                "Testing LEDs color: %s" %color
                )
                        
                self.all_on(color)
                time.sleep(1)
                self.all_off()
                time.sleep(1)

    def all_on(self, color: str = "w") -> None:
        """Set all LEDs to same color

        Args:
            color (str, optional): Color code [white: "w", red: "r", green: "g", blue: "b"] Defaults to "w".
        """
        if color not in ["w","r","g","b"]:
            raise ValueError("%s color not supported" %color)

        if color == "w":
            self._set_ioexpander_output(exp=1, addr=2, value=0x0)
            self._set_ioexpander_output(exp=1, addr=3, value=0x0)
            self._set_ioexpander_output(exp=2, addr=2, value=0x0)
            self._set_ioexpander_output(exp=2, addr=3, value=0x0)

        if color == "r":
            self._set_ioexpander_output(exp=1, addr=2, value=0xb5)
            self._set_ioexpander_output(exp=1, addr=3, value=0x6d)
            self._set_ioexpander_output(exp=2, addr=2, value=0xdb)
            self._set_ioexpander_output(exp=2, addr=3, value=0xb6)

        if color == "g":
            self._set_ioexpander_output(exp=1, addr=2, value=0xda)
            self._set_ioexpander_output(exp=1, addr=3, value=0xb6)
            self._set_ioexpander_output(exp=2, addr=2, value=0x6d)
            self._set_ioexpander_output(exp=2, addr=3, value=0xdb)

        if color == "b":
            self._set_ioexpander_output(exp=1, addr=2, value=0x6f)
            self._set_ioexpander_output(exp=1, addr=3, value=0xdb)
            self._set_ioexpander_output(exp=2, addr=2, value=0xb6)
            self._set_ioexpander_output(exp=2, addr=3, value=0x6d)

    def all_off(self) -> None:
        """Turn off all LEDs
        """
        self._set_ioexpander_output(exp=1, addr=2, value=0xFF)
        self._set_ioexpander_output(exp=1, addr=3, value=0xFF)
        self._set_ioexpander_output(exp=2, addr=2, value=0xFF)
        self._set_ioexpander_output(exp=2, addr=3, value=0xFF)

    def switch_led(self, led_id: int, color: str = "off") -> None:
        """changes LED with led_id to specific color

        Args:
            led_id (int): ID for the 11 LEDs, led_ id has to be between 1 and 11
            color (str, optional): Color code [white: "w", red: "r", green: "g", blue: "b", off: "off"]
                                   for Clock LED only [red: "r", green: "g", off: "off"]. 
                                   Defaults to "off".
        """
        
        if led_id == 5 and color not in ["r","g","off"]:
            raise ValueError("%s color not supported for Clock LED" %color)
        
        elif color not in ["w", "r","g", "b","off"]:
            raise ValueError("%s color not supported for LED" %color)

        # Clock LED has only two LEDs
        if led_id == 5:
            if color == "r":
                rgb = [0,1,1]
            if color == "g":
                rgb = [1,0,1]
            if color == "off":
                rgb = [1,1,1]

        else:
            if color == "w":
                rgb = [0,0,0]
            if color == "r":
                rgb = [0,1,1]
            if color == "g":
                rgb = [1,0,1]
            if color == "b":
                rgb = [1,0,0]        
            if color == "off":
                rgb = [1,1,1]

        self._set_led(led_id,rgb)

    def _set_led(self,led_id: int, rgb: list) -> None:
            """sets led to a rgb value

            Args:
                led_id (int): Led id for the 11 LED, led_ id has to be between 1 and 11
                rgb (list): rgb value for the LED e.q. [0,0,0] #TODO which color has which code?

            """
            if led_id < 1 or led_id > 11:
                raise ValueError("LED ID has to be between 1 and 11")

            # indicator map for LED positions notice the -1 for the clock led #TODO should this be global??
            indicator = [[30, 29, 31], [27, 26, 28], [24, 23, 25], [21, 20, 22], [18, 17, -1], [15, 14, 16], [12, 11, 13], [9, 8, 10], [6, 5, 7], [3, 2, 4], [1, 0, 19]]


            now_status = [] #status of all ioexpander now
            next_status = [] #status of all ioexpander next
            now_status.append(0xFF & self._get_ioexpander_output(1,2))
            now_status.append(0xFF & self._get_ioexpander_output(1,3))
            now_status.append(0xFF & self._get_ioexpander_output(2,2))
            now_status.append(0xFF & self._get_ioexpander_output(2,3))  
            #print(now_status,"now_status of the ioexpander for debugging")

            word = 0x00000000
            word = word | now_status[0]
            word = word | (now_status[1] << 8)
            word = word | (now_status[2] << 16)
            word = word | (now_status[3] << 24)
            #print(word,"word for debugging")

            for index in range(3):
                if led_id == 5: #for clock led not all colors are allowed on clock [1,0,1] is green [0,1,1] is red the og eudaq indicator map produces here an error
                    #TODO some colors also switch on LED 11 
                    word = _set_bit(word,[18,17,19][index],rgb[index])
                else:
                    word = _set_bit(word,indicator[led_id-1][index],rgb[index])

            next_status.append(0xFF & word)
            next_status.append(0xFF & (word >> 8))
            next_status.append(0xFF & (word >> 16))
            next_status.append(0xFF & (word >> 24))
            #print(next_status,"next_status of the ioexpander for debugging")

            if now_status[0] != next_status[0]:
                self._set_ioexpander_output(1,2,next_status[0])

            if now_status[1] != next_status[1]:
                self._set_ioexpander_output(1,3,next_status[1])

            if now_status[2] != next_status[2]:
                self._set_ioexpander_output(2,2,next_status[2])

            if now_status[3] != next_status[3]:
                self._set_ioexpander_output(2,3,next_status[3])

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
        if exp not in [1, 2]:
            raise ValueError("Expander ID should be 1 or 2")

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
        if exp not in [1, 2]:
            raise ValueError("Expander ID should be 1 or 2")
        
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
            raise ValueError("Address should be 2 or 3")
        if exp not in [1, 2]:
            raise ValueError("Expander ID should be 1 or 2")
        self.i2c.write(self.i2c.modules["led_expander_%.1s" % exp], addr, value & 0xFF)

    def _get_ioexpander_output(self, exp: int, addr: int) -> int:
        """Get content of register 2 or 3

        Args:
            exp (int): _ID of LED Expander (1 or 2))
            addr (int): # TODO, what is this?!
        Returns:
            int: content of the ioexpander
        """
        if addr not in [2, 3]:
            raise ValueError("Address should be 2 or 3")
        if exp not in [1, 2]:
            raise ValueError("Expander ID should be 1 or 2")
        
        output = self.i2c.read(self.i2c.modules["led_expander_%.1s" % exp], addr)
        return output
