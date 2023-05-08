from i2c import I2CCore
import logger

class TriggerLogic(object):
    def __init__(self, i2c: I2CCore) -> None:
        self.log = logger.setup_derived_logger("Trigger Controller")
        self.i2c = i2c

    """ 

    Internal Trigger Generation 

    """

    def set_internal_trigger_frequency(self, frequency: int) -> None:
        """ Sets the internal trigger frequency.
        The maximum allowed Frequency is 160 MHz. #TODO This should generate internal triggers with frequency > 0

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
           The period for the internal trigger generator is reduced by 2 prob. in some harware configuration. 
        #TODO In the documentation what is meant by smaller 5

        Args:
            interval (int): Number of internal clock cycles.
        """
        self.i2c.write_register("triggerLogic.InternalTriggerIntervalW", interval) 

    """ 
     
    Trigger Logic #TODO where are here the different DUT or trigger inpout channels and so on
    
    """

    def set_trigger_veto(self, value: int) -> None:
        """Enables or disables new trigger. This can be used to reset the procession of new triggers.

        Args:
            value (int): _description_ #TODO
        """
        self.i2c.write_register("triggerLogic.TriggerVetoW", value)
        self.log.info("Trigger Veto set to: %s" %self.get_trigger_veto())

    def set_trigger_polarity(self, value: int) -> int:
        """Sets if the TLU triggers on rising or falling edge.

        Args:
            value (int): 1 triggers on falling, 0 on rising. #TODO not tested

        """
        trigger_polarity = (0x3F & value)
        self.i2c.write_register("triggerInputs.InvertEdgeW", trigger_polarity)
        self.log.info("Trigger on %s edge" %("falling" if value == 1 else "rising")) #TODO NOT TESTED 

#    def set_trigger_mask(self, value: int) -> None:
    def set_trigger_mask(self, mask_high: int, mask_low: int) -> None:  #TODO EUDAQ uses both functions with same name      
        """Sets the trigger logic. Each of the 64 possible combination is divided into two 32-bit words mask high and mask low.
           #TODO To set a specific trigger logic one must find right two words in the TLU. doc p. 30 

        Args:
            mask_high (int): _description_ #TODO
            mask_low (int): _description_ #TODO
        """
        #mask_high = (value >> 32) & 0xFF
        #mask_low = value & 0xFF
        self.i2c.write_register("triggerLogic.TriggerPattern_lowW", mask_low)
        self.i2c.write_register("triggerLogic.TriggerPattern_highW", mask_high)
        self.log.info("Trigger mask: %s" %self.get_trigger_mask())

    def get_trigger_mask(self) -> int:
        """Retrieves the trigger logic words from the registers. The trigger pattern represents one of the 64 possible logic combinations.

        """
        mask_low = self.i2c.read_register("triggerLogic.TriggerPattern_lowR")
        mask_high = self.i2c.read_register("triggerLogic.TriggerPattern_highR")
        trigger_pattern = (mask_high << 32) | mask_low
        return trigger_pattern

    def get_trigger_veto(self) -> int:
        """Reads the trigger veto from the register.

        """
        veto_state = self.i2c.read_register("triggerLogic.TriggerVetoR")
        return veto_state

    def get_post_veto_trigger(self) -> int:
        """Gets the number of triggers recorded in the TLU after the veto is applied

        """
        return self.i2c.read_register("triggerLogic.PostVetoTriggersR")
    
    def get_pre_veto_trigger(self) -> int:
        """Number of triggers recorded in the TLU before the veto is applied. 
        
        """
        return self.i2c.read_register("triggerLogic.PreVetoTriggersR")

    """ 
    
    Trigger Pulse Length and Delay #TODO prob. to account for cable length and so on 
    
    """

    def set_pulse_stretch_pack(self, vector: list) -> None:
        """ Stretch word for trigger pulses. Each element of the input vector is stretched by N clock cycles.
            The input vector should have 6 elements for the different inputs.
            The vector is packed into a single word.
            
        Args:
            vector (list): _description_ #TODO
        """
        packed = self._pack_bits(vector)
        self._set_pulse_stretch(packed)
        self.log.info("Pulse stretch is set to %s" %self.get_pulse_stretch_pack())
    
    def set_pulse_delay_pack(self, vector: list) -> None:
        """ Delay word for trigger pulses. Each element of the input vector is delayed by N clock cycles.
            The vector is packed into a single word.
        
        Args:
            vector (list): _description_
        """
        packed = self._pack_bits(vector)
        self._set_pulse_delay(packed)
        self.log.info("Pulse Delay is set to %s" %self.get_pulse_delay_pack())
    
    def get_pulse_stretch_pack(self) -> int:
        """ Get packed word describing the input pulse stretch. #TODO a unpack function could be usefull.

        """
        return self.i2c.read_register("triggerLogic.PulseStretchR")
    
    def get_pulse_delay_pack(self) -> int:
        """Get packed word describing the input pulse stretch. #TODO a unpack function could be usefull.

        """
        return self.i2c.read_register("triggerLogic.PulseDelayR")
    
    def _set_pulse_stretch(self, value: int) -> None:
        """ Writes the packed word into the pulse stretch register.

        Args:
            value (int): _description_
        """
        self.i2c.write_register("triggerLogic.PulseStretchW", value)

    def _set_pulse_delay(self, value: int) -> None:
        """ Writes the packed word into the pulse delay register.

        Args:
            value (int): _description_
        """
        self.i2c.write_register("triggerLogic.PulseDelayW", value)

    def _pack_bits(self, vector: list) -> int:
        """Pack Vector of bits using 5-bits for each element. 

        Args:
            vector (list): Vector of bits with variable length.

        Returns:
            int: 32-bit word representation of the input vector. 
        """
        #TODO Numpy would prob. be more elegant for this.
        packed_bits = 0x0
        temp_int = 0x0
        for channel in range(len(vector)):
            temp_int = int(vector[channel]) << channel*5
            packed_bits = packed_bits | temp_int
        return packed_bits