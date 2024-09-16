from aidatlu.hardware.i2c import I2CCore
from aidatlu.hardware.utils import _pack_bits
from aidatlu import logger


class TriggerLogic(object):
    def __init__(self, i2c: I2CCore) -> None:
        self.log = logger.setup_derived_logger("Trigger Controller")
        self.i2c = i2c

    """ Internal Trigger Generation """

    def set_internal_trigger_frequency(self, frequency: int) -> None:
        """Sets the internal trigger frequency.
        The maximum allowed Frequency is 160 MHz.

        Args:
            frequency (int): Frequency in Hz
        """
        self.log.info("Set internal trigger frequency to: %i Hz" % frequency)
        max_freq = 160000000

        if frequency < 0:
            raise ValueError("Frequency smaller 0 does not work")
        if frequency > max_freq:
            raise ValueError("Frequency larger %s Hz not supported" % max_freq)
        if frequency == 0:
            interval = frequency
        else:
            interval = int(
                max_freq / frequency
            )  # TODO here is a rounding error that comes from the interval calculations at ~10kHz.
        self._set_internal_trigger_interval(interval)
        new_freq = self.get_internal_trigger_frequency()
        if new_freq != frequency:
            self.log.warning(
                "Frequency set to different value. Internal Trigger frequency: %i Hz"
                % self.get_internal_trigger_frequency()
            )

    def get_internal_trigger_frequency(self) -> int:
        """Reads the internal trigger frequency from the register.

        Returns:
            int: Frequency in Hz
        """
        max_freq = 160000000
        interval = self.i2c.read_register("triggerLogic.InternalTriggerIntervalR")
        if interval == 0:
            freq = 0
        else:
            freq = int(
                max_freq / interval
            )  # TODO here is prob. a rounding error I should use a round function this would prob. prevent the warning at ~10kHz.
        return freq

    def _set_internal_trigger_interval(self, interval: int) -> None:
        """Number of internal clock cycles to be used as period for the internal trigger generator.
           The period for the internal trigger generator is reduced by 2 prob. in some hardware configuration.

        Args:
            interval (int): Number of internal clock cycles.
        """
        self.i2c.write_register("triggerLogic.InternalTriggerIntervalW", interval)

    """ Trigger Logic """

    def set_trigger_veto(self, veto: bool) -> None:
        """Enables or disables new trigger. This can be used to reset the procession of new triggers.
        Args:
            veto (bool): Sets a veto to the trigger logic of the tlu.
        """
        if type(veto) != bool:
            raise TypeError("Veto must be type bool")

        self.i2c.write_register("triggerLogic.TriggerVetoW", int(veto))
        self.log.info("Trigger Veto set to: %s" % self.get_trigger_veto())

    def set_trigger_polarity(self, value: int) -> int:
        """Sets if the TLU triggers on rising or falling edge.

        Args:
            value (int): 1 triggers on falling, 0 on rising. #TODO not tested

        """
        trigger_polarity = 0x3F & value
        self.i2c.write_register("triggerInputs.InvertEdgeW", trigger_polarity)
        self.log.info("Trigger on %s edge" % ("falling" if value == 1 else "rising"))

    def set_trigger_mask(self, mask_high: int, mask_low: int) -> None:
        """Sets the trigger logic. Each of the 64 possible combination is divided into two 32-bit words mask high and mask low.

        Args:
            mask_high (int): The most significant 32-bit word generated from the trigger configuration.
            mask_low (int): The least significant 32-bit word generated from the trigger configuration.
        """
        self.i2c.write_register("triggerLogic.TriggerPattern_lowW", mask_low)
        self.i2c.write_register("triggerLogic.TriggerPattern_highW", mask_high)
        self.log.info("Trigger mask: %s" % self.get_trigger_mask())

    def get_trigger_mask(self) -> int:
        """Retrieves the trigger logic words from the registers. The trigger pattern represents one of the 64 possible logic combinations."""
        mask_low = self.i2c.read_register("triggerLogic.TriggerPattern_lowR")
        mask_high = self.i2c.read_register("triggerLogic.TriggerPattern_highR")
        trigger_pattern = (mask_high << 32) | mask_low
        return trigger_pattern

    def get_trigger_veto(self) -> bool:
        """Reads the trigger veto from the register."""
        veto_state = self.i2c.read_register("triggerLogic.TriggerVetoR")
        return bool(veto_state)

    def get_post_veto_trigger(self) -> int:
        """Gets the number of triggers recorded in the TLU after the veto is applied"""
        return self.i2c.read_register("triggerLogic.PostVetoTriggersR")

    def get_pre_veto_trigger(self) -> int:
        """Number of triggers recorded in the TLU before the veto is applied."""
        return self.i2c.read_register("triggerLogic.PreVetoTriggersR")

    def set_trigger_mask_from_full_word(self, value: int) -> None:
        """Sets the trigger logic. Each of the 64 possible combination is divided into two 32-bit words mask high and mask low.

        Args:
            value (int): Sets trigger logic from trigger logic combination word.
        """
        mask_high = (value >> 32) & 0xFF
        mask_low = value & 0xFF
        self.i2c.write_register("triggerLogic.TriggerPattern_lowW", mask_low)
        self.i2c.write_register("triggerLogic.TriggerPattern_highW", mask_high)
        self.log.info("Trigger mask: %s" % self.get_trigger_mask())

    """ Trigger Pulse Length and Delay """

    def set_pulse_stretch_pack(self, vector: list) -> None:
        """Stretch word for trigger pulses. Each element of the input vector is stretched by N clock cycles.
            The input vector should have 6 elements for the different inputs.
            The vector is packed into a single word.

        Args:
            vector (list): A vector containing six integers. Each trigger input is stretched by the integer number of clock cycles.
        """
        packed = _pack_bits(vector)
        self._set_pulse_stretch(packed)
        self.log.info("Pulse stretch is set to %s" % self.get_pulse_stretch_pack())

    def set_pulse_delay_pack(self, vector: list) -> None:
        """Delay word for trigger pulses. Each element of the input vector is delayed by N clock cycles.
            The vector is packed into a single word.

        Args:
            vector (list): A vector containing six integers. Each trigger input is delayed by the integer number of clock cycles.
        """
        packed = _pack_bits(vector)
        self._set_pulse_delay(packed)
        self.log.info("Pulse Delay is set to %s" % self.get_pulse_delay_pack())

    def get_pulse_stretch_pack(self) -> int:
        """Get packed word describing the input pulse stretch."""
        return self.i2c.read_register("triggerLogic.PulseStretchR")

    def get_pulse_delay_pack(self) -> int:
        """Get packed word describing the input pulse stretch."""
        return self.i2c.read_register("triggerLogic.PulseDelayR")

    def _set_pulse_stretch(self, value: int) -> None:
        """Writes the packed word into the pulse stretch register.

        Args:
            value (int): The input vector packed to a single integer.
        """
        self.i2c.write_register("triggerLogic.PulseStretchW", value)

    def _set_pulse_delay(self, value: int) -> None:
        """Writes the packed word into the pulse delay register.

        Args:
            value (int): The input vector packed to a single integer.
        """
        self.i2c.write_register("triggerLogic.PulseDelayW", value)
