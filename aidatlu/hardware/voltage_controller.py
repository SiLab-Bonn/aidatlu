from hardware.i2c import I2CCore
import logger

""" 

AD5665R

"""

class VoltageControl(object):
    def __init__(self, i2c: I2CCore, int_ref: bool = False) -> None:
        self.log = logger.setup_derived_logger("Voltage Controller")

        self.log.info("Initializing DAC Control")
        self.i2c = i2c

        self._set_dac_reference(int_ref, 0)
        self._set_dac_reference(int_ref, 1)
        self._set_dac_reference(int_ref, 2)


    def set_threshold(self, trigger_input: int, threshold_voltage: float, ref_v: float = 1.3) -> None:
        """Sets the Threshold voltage for the trigger input channel. Use channel = 7 to set threshold for all channels.

        Args:
            trigger_input (int): Trigger input channel. From 1 to 7, where 7 controlls all input channels.
            threshold_voltage (float): Threshold voltage in volt.
            ref_v (float): Reference voltage of the DAC. Defaults to the external reference voltage 1.3 V.
        """
        
        if threshold_voltage > ref_v:
            self.log.warn("Threshold larger than %s V is not supported, Threshold will default to %s V "%(ref_v,ref_v))
            threshold_voltage = ref_v
        if threshold_voltage < -ref_v:
            self.log.warn("Threshold smaller than %s V is not supported, Threshold will default to %s V "%(-ref_v,-ref_v))
            threshold_voltage = -ref_v
        if trigger_input != 7:
            if trigger_input < 1 or trigger_input > 6:
                raise ValueError("Invalid trigger input channel. Channel has to be between 1 and 6. Or use channel = 7 for all channels.")
            
        channel = trigger_input-1 #shift channel number by 1
        #calculates the DAC value for the threshold DAC 
        v_dac = (threshold_voltage + ref_v) / 2
        dac_value = int(0xFFFF * v_dac / ref_v)

        #Sets threshold for the different channels. The different handling of the channels come from the weird connections of the ADC.
        if channel == 6:
            self._set_dac_value(channel+1, dac_value, 1)
            self._set_dac_value(channel+1, dac_value, 2)
        #The DAC channels are connected in reverse order. The first two channels sit on DAC 1 in reverse order.   
        if channel < 2:
            self._set_dac_value(1-channel, dac_value, 1) 
        #The last 4 channels sit on DAC 2 in reverse order.
        if channel > 1 and channel < 7:
            self._set_dac_value(3-(channel-2), dac_value, 2) 
        self.log.info("Threshold of input %s set to %s V" %(trigger_input,threshold_voltage))

    def set_all_voltage(self, voltage: float) -> None:
        """Sets the same Voltage for all PMT DACs.

        Args:
            voltage (float): DAC voltage in volts.
        """
        for channel in range(4):
            self.set_voltage(channel+1, voltage)

    def set_voltage(self, pmt_channel: int, voltage: float) -> None:
        """Sets given PMT DAC to given output voltage.

        Args:
            pmt_channel (int): DAC channel for the PMT
            voltage (float): DAC output voltage
        """
        
        if pmt_channel < 1 or pmt_channel > 4:
            raise ValueError("PMT Channel has to be between 1 and 4")
        
        if voltage < 0:
            self.log.warn(
                "A Voltage value smaller than 0 is not supported, Voltage will default to 0"
                )
            voltage = 0
            
        if voltage > 1:
            self.log.warn(
                "A Voltage value higher than 1 is not supported, Voltage will default to 1"
                )
            voltage = 1

        #Channel - PMT map [channel 2 -> PMT 4, channel 0 -> PMT 3, channel 1 -> PMT 2, channel 3 -> PMT 1]
        if pmt_channel == 1:
            channel_map = 3
        if pmt_channel == 2:
            channel_map = 1
        if pmt_channel == 3:
            channel_map = 0
        if pmt_channel == 4:
            channel_map = 2 

        #0xFFFF is max DAC value
        self._set_dac_value(channel_map, int(voltage*0xFFFF))
        self.log.info('PMT channel %s set to %s V' %(pmt_channel, voltage))

    def _set_dac_reference(self, internal: bool = False, dac: int = 0) -> None:
        """Choose internal or external DAC reference

        Args:
            internal (bool, optional): Defaults to False.
            dac (int): 0 is the power dac, 1 and 2 are DAC 1 and DAC 2 for the thresholds. Defaults to 0. 
        """
        #There is a factor 2 in the output voltage between internal and external DAC reference. In general internal reference is a factor of 2 larger!!
        if internal:
            chr = [0x00, 0x01]

        else:
            chr = [0x00, 0x00]

        if dac == 0:
            self.i2c.write_array(self.i2c.modules["pwr_dac"], 0x38, chr)
        if dac == 1:
            self.i2c.write_array(self.i2c.modules["dac_1"], 0x38, chr)
        if dac == 2:
            self.i2c.write_array(self.i2c.modules["dac_2"], 0x38, chr)        
        #self.i2c.write_array(self.i2c.modules["pwr_dac"], 0x38, chr)
        self.log.info(
            "Set %s DAC reference" % ("internal" if internal else "external")
        )

    def _set_dac_value(self, channel: int, value: int, dac: int = 0) -> None:
        """Set the output value of the power DAC 

        Args:
            channel (int): DAC channel
            value (int): DAC output value
            dac (int): 0 is the power dac, 1 and 2 are DAC 1 and DAC 2 for the thresholds. Defaults to 0. 
        """
        if channel < 0 or channel > 7:
            raise ValueError("Channel has to be between 0 and 7")
        
        if value<0x0000:
            self.log.warn("DAC value < 0x0000 not supported, value will default to 0x0000")
            value = 0
            
        if value>0xFFFF:
            self.log.warn("DAC value > 0xFFFF not supported, value will default to 0xFFFF")
            value = 0xFFFF

        chr = [(value>>8) & 0xFF, value & 0xFF]
        mem_addr = 0x18 + (channel & 0x7)

        if dac == 0:
            self.i2c.write_array(self.i2c.modules["pwr_dac"], mem_addr, chr)
        if dac == 1:
            self.i2c.write_array(self.i2c.modules["dac_1"], mem_addr, chr)
        if dac == 2:
            self.i2c.write_array(self.i2c.modules["dac_2"], mem_addr, chr)