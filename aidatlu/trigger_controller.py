


#TODO these functions do not work.


def get_internal_trigger_frequency(self) -> int:
    interval = self.i2c.read_register("triggerLogic.InternalTriggerIntervalR")
    if interval == 0:
        freq = 0
    else:
        freq = int(160000000/interval)
    return freq

def set_internal_trigger_frequency(self, frequency: int) -> None:
    max_freq = 160000000
    if frequency < 0:
        raise ValueError("Frequency smaller 0 does not work")
    if frequency > max_freq:
        raise ValueError("Frequency larger 160MHz does not work")
    if frequency == 0:
        interval = frequency
    else:
        interval = int(160000000/frequency)
    self.set_internal_trigger_interval(interval)
    self.log.info("Internal frequency: %i" %self.get_internal_trigger_frequency())

    #self.compare_write_read()

def set_internal_trigger_interval(self, interval) -> None:
    self.i2c.write_register("triggerLogic.InternalTriggerIntervalW", interval) 
