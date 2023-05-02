from i2c import I2CCore
import logger

class TriggerControll(object):
    def __init__(self, i2c: I2CCore) -> None:
        self.log = logger.setup_derived_logger("Trigger Controller")
        self.i2c = i2c

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




