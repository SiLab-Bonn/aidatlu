import logging
import uhal
import logger

from i2c import I2CCore, i2c_addr
from led_controller import LEDControl
from voltage_controller import VoltageControl
from clock_controller import ClockControl
from output_controller import OutputControl
from trigger_controller import TriggerLogic
from dut_controller import DUTLogic

class AidaTLU(object):
    def __init__(self, hw) -> None:
        self.log = logger.setup_main_logger(__class__.__name__, logging.DEBUG)

        self.i2c = I2CCore(hw)
        self.i2c_hw = hw
        self.i2c.init()
        if self.i2c.modules["eeprom"]:
            self.log.info("Found device with ID %s" % hex(self.get_device_id()))

        self.led_controller = LEDControl(self.i2c)
        self.voltage_controller = VoltageControl(self.i2c)
        self.clock_controller = ClockControl(self.i2c)
        self.output_controller = OutputControl(self.i2c, self.led_controller)
        self.trigger_logic = TriggerLogic(self.i2c)
        self.dut_logic = DUTLogic(self.i2c)

        #Disable all outputs
        self.output_controller.clock_lemo_output(False)
        for i in range(4): self.output_controller.configure_hdmi(i+1, False)

        #Resets all internal counters and raises the trigger veto.
        self.set_run_active(False)
        self.reset_status()
        self.reset_counters()
        self.trigger_logic.set_trigger_veto(True)
        self.reset_fifo()
        self.reset_timestamp()

        # if present, init display

    def get_device_id(self) -> int:
        """Read back board id. Consists of six blocks of hex data

        Returns:
            int: Board id as 48 bits integer
        """
        id = []
        for addr in range(6):
            id.append(self.i2c.read(self.i2c.modules["eeprom"], 0xFA + addr) & 0xFF)
        return int("0x" + "".join(["{:x}".format(i) for i in id]), 16) & 0xFFFFFFFFFFFF

    def get_fw_version(self) -> int:
        return self.i2c.read_register("version")

    def reset_board(self) -> None:
        #TODO THIS FUNCTION CRASHES THE TLU. This does not work at all...
        self.i2c.write_register("logic_clocks.LogicRst", 1)

    def reset_timestamp(self) -> None:
        """ Sets bit to  'ResetTimestampW' register to reset the time stamp. 
        """
        self.i2c.write_register("Event_Formatter.ResetTimestampW", 1)

    def reset_counters(self) -> None:
        """ Resets the trigger counters. 
        """
        self.write_status(0x2)
        self.write_status(0x0)

    def reset_status(self) -> None:
        """ Resets the complete status and all counters #TODO I think.
        """
        self.write_status(0x3)
        self.write_status(0x0)
        self.write_status(0x4)
        self.write_status(0x0)

    def reset_fifo(self) -> None:
        """ Sets 0 to 'EventFifoCSR' this resets the FIFO.
        """
        self.set_event_fifo_csr(0x0)

    def set_event_fifo_csr(self, value: int) -> None:
        """ Sets value to the EventFifoCSR register.

        Args:
            value (int): 0 resets the FIFO. #TODO can do other stuff that is not implemented

        """
        self.i2c.write_register("eventBuffer.EventFifoCSR", value)

    def write_status(self, value: int) -> None:
        """ Sets value to the 'SerdesRstW' register.

        Args:
            value (int): Bit 0 resets the status, bit 1 resets trigger counters and bit 2 calibrates IDELAY.
        """
        self.i2c.write_register("triggerInputs.SerdesRstW", value)

    def set_run_active(self, state: bool) -> None:
        """ Raises internal run active signal.

        Args:
            state (bool): True sets run active, False disables it.
        """
        if type(state) != bool:
            raise TypeError("State has to be bool")
        self.i2c.write_register("Shutter.RunActiveRW", int(state))
        self.log.info("Run active: %s" %self.get_run_active())

    def get_run_active(self) -> bool:
        """Reads register 'RunActiveRW'

        Returns:
            bool: Returns bool of the run active register.
        """
        return bool(self.i2c.read_register("Shutter.RunActiveRW"))

    def test_configuration(self) -> None:
        """ Configure DUT 1 to run in a default test configuration. 
            Runs in EUDET mode with internal generated triggers.
        """
        self.log.info("Configure DUT 1 in EUDET test mode")
        
        test_stretch = [1,1,1,1,1,1]
        test_delay = [0,0,0,0,0,0] 

        #self.set_run_active(False)
        #self.trigger_logic.set_trigger_veto(False)
        self.output_controller.configure_hdmi(1, '0111')
        self.output_controller.clock_hdmi_output(1, 'off')
        #self.trigger_logic.set_pulse_stretch_pack(test_stretch)
        #self.trigger_logic.set_pulse_delay_pack(test_delay)
        #self.trigger_logic.set_trigger_mask(mask_high=0x00000000, mask_low=0x00000002)
        #self.trigger_logic.set_trigger_polarity(1)
        self.dut_logic.set_dut_mask('0001')
        self.dut_logic.set_dut_mask_mode('00000000')
        # self.dut_logic.set_dut_mask_mode_modifier(0)
        # self.dut_logic.set_dut_ignore_busy(0)
        # self.dut_logic.set_dut_ignore_shutter(0x1)
        self.trigger_logic.set_internal_trigger_frequency(500)
 
        #self.set_enable_record_data(1)
        #self.get_event_fifo_csr()
        #self.get_event_fifo_fill_level()

    def start_run(self) -> None:
        """ Start run configurations
        """
        self.reset_counters()
        self.reset_fifo()
        self.set_run_active(True)
        self.trigger_logic.set_trigger_veto(False)

    def stop_run(self) -> None:
        """ Stop run configurations
        """
        self.trigger_logic.set_trigger_veto(True)
        self.set_run_active(False)

    def status(self) -> None:
        #TODO just bugfixing for now
        self.log.info("fifo csr: %s fifo fill level: %s" %(self.get_event_fifo_csr(),self.get_event_fifo_csr()))
        self.log.info("post: %s pre: %s" %(self.trigger_logic.get_post_veto_trigger(),self.trigger_logic.get_pre_veto_trigger()))
        self.log.info("time stamp: %s" %(self.get_timestamp()))

    def set_enable_record_data(self, value: int) -> None:
        """ #TODO not sure what this does. Looks like a seperate internal event buffer to the FIFO.

        Args:
            value (int): _description_
        """
        self.i2c.write_register("Event_Formatter.Enable_Record_Data", value)

    def get_event_fifo_csr(self) -> int:
        """ Reads value from 'EventFifoCSR'

        Returns:
            int: _description_#TODO
        """
        return self.i2c.read_register("eventBuffer.EventFifoCSR")

    def get_event_fifo_fill_level(self) -> int:
        """Reads value from 'EventFifoFillLevel'

        Returns:
            int: _description_ #TODO
        """
        return self.i2c.read_register("eventBuffer.EventFifoFillLevel")

    def reset_timestamp(self) -> None:
        """ Resets the internal timestamp by asserting a bit in 'ResetTimestampW'.
        """
        self.i2c.write_register("Event_Formatter.ResetTimestampW", 1)

    def get_timestamp(self) -> int:
        """ Get current time stamp.

        Returns:
            int: Time stamp is not formatted.
        """
        time = self.i2c.read_register("Event_Formatter.CurrentTimestampHR")
        time = time << 32
        time = time + self.i2c.read_register("Event_Formatter.CurrentTimestampLR")
        return time

    def pull_fifo_event(self) -> list:
        """ Pulls event from the FIFO. This is needed in the run loop to prevent the buffer to get stuck.
            if this register is full the fifo needs to be reset or new triggers are generated but not sent out.
            #TODO check here if the FIFO is full and reset it if needed would prob. make sense.

        Returns:
            list: _description_#TODO this is nonsense for now.
        """
        event_numb = self.get_event_fifo_fill_level()
        if event_numb:
            fifo_content = self.i2c_hw.getNode("eventBuffer.EventFifoData").readBlock(event_numb & 0xFF) #TODO check 0xFF
            self.i2c_hw.dispatch()
            return fifo_content
        pass            

    def run(self) -> None:
        """ Start run of the TLU. 
        """
        self.start_run()
        run_active = True
        last_time = self.get_timestamp()
        start_time = last_time
        while run_active:
            try:
                last_time = self.get_timestamp()
                current_time = (last_time-start_time)   #TODO these are nonsense numbers for now
                current_event = self.pull_fifo_event()  #TODO same here just an array of nonsense
            except:
                KeyboardInterrupt
                run_active = False
        self.stop_run()

if __name__ == "__main__":

    uhal.setLogLevelTo(uhal.LogLevel.NOTICE)
    manager = uhal.ConnectionManager("file://./misc/aida_tlu_connection.xml")
    hw = uhal.HwInterface(manager.getDevice("aida_tlu.controlhub"))

    tlu = AidaTLU(hw)