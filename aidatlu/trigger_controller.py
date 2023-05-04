from i2c import I2CCore
import logger

class TriggerControl(object):
    def __init__(self, i2c: I2CCore) -> None:
        self.log = logger.setup_derived_logger("Trigger Controller")
        self.i2c = i2c

    def set_internal_trigger_frequency(self, frequency: int) -> None:
        """ Sets the internal trigger frequency.
        The maximum allowed Frequency is 160 MHz. #TODO What is the actual purpose of this function. It operates above the 

        Args:
            frequency (int): Frequency in Hz #TODO is this Hz?
        """
        self.log.info("Set internal trigger frequency to: %i Hz" %frequency)
        max_freq = 160000000
        if frequency < 0:
            raise ValueError("Frequency smaller than 0 does not work")
        if frequency > max_freq:
            raise ValueError("Frequency larger than 160MHz does not work")
        if frequency == 0:
            interval = frequency
        else:
            interval = int(160000000/frequency) #TODO here is prob. a rounding error I should use a round function this would prob. prevent the warning at ~10kHz.
        self._set_internal_trigger_interval(interval)
        #TODO check if this is really Hz
        new_freq = self.get_internal_trigger_frequency()
        if new_freq != frequency:
            self.log.warn("Frequency is set to different value. Internal Trigger frequency is %i Hz" %self.get_internal_trigger_frequency())

    def get_internal_trigger_frequency(self) -> int:
        """Reads the internal trigger frequency from the register.

        Returns:
            int: Frequency in Hz #TODO Hz?
        """
        interval = self.i2c.read_register("triggerLogic.InternalTriggerIntervalR")
        if interval == 0:
            freq = 0
        else:
            freq = int(160000000/interval) #TODO here is prob. a rounding error I should use a round function this would prob. prevent the warning at ~10kHz.
        return freq

    def _set_internal_trigger_interval(self, interval: int) -> None:
        """Number of internal clock cycles to be used as period for the internal trigger generator.
        #TODO In the documentation what is meant by smaller 5 and -2

        Args:
            interval (int): Number of internal clock cycles.
        """
        self.i2c.write_register("triggerLogic.InternalTriggerIntervalW", interval) 

    def set_trigger_veto(self, value: int) -> None:
        self.i2c.write_register("triggerLogic.TriggerVetoW", value)
        self.log.info("Trigger Veto set to: %s" %self.get_trigger_veto())

    def set_trigger_polarity(self, value: int) -> int:
        trigger_polarity = (0x3F & value)
        self.i2c.write_register("triggerInputs.InvertEdgeW", trigger_polarity)
        self.log.info("Trigger on %s edge" %("falling" if value == 1 else "rising")) #TODO NOT TESTED 

    def set_trigger_mask(self, value: int) -> None:
#    def set_trigger_mask(self, mask_high: int, mask_low: int) -> None:  #TODO EUDAQ uses both functions with same name      
        mask_high = (value >> 32) & 0xFF
        mask_low = value & 0xFF
        self.i2c.write_register("triggerLogic.TriggerPattern_lowW", mask_low)
        self.i2c.write_register("triggerLogic.TriggerPattern_highW", mask_high)
        self.log.info("Trigger mask: %s" %self.get_trigger_mask())

    def get_trigger_mask(self) -> int:
        mask_low = self.i2c.read_register("triggerLogic.TriggerPattern_lowR")
        mask_high = self.i2c.read_register("triggerLogic.TriggerPattern_highR")
        trigger_pattern = (mask_high << 32) | mask_low
        return trigger_pattern

    def get_trigger_veto(self) -> int:
        veto_state = self.i2c.read_register("triggerLogic.TriggerVetoR")
        return veto_state




