import logging
import uhal
import logger
import numpy as np
import tables as tb
from datetime import datetime
import zmq

from hardware.i2c import I2CCore

from hardware.clock_controller import ClockControl
from hardware.ioexpander_controller import IOControl
from hardware.dac_controller import DacControl
from hardware.trigger_controller import TriggerLogic
from hardware.dut_controller import DUTLogic
from main.config_parser import TLUConfigure

from main.data_parser import DataParser

class AidaTLU(object):
    def __init__(self, hw, config_path, clock_config_path) -> None:
        self.log = logger.setup_main_logger(__class__.__name__, logging.DEBUG)

        self.i2c = I2CCore(hw)
        self.i2c_hw = hw
        self.i2c.init()
        if self.i2c.modules["eeprom"]:
            self.log.info("Found device with ID %s" % hex(self.get_device_id()))

        #TODO some configuration also sends out ~70 triggers.
        self.io_controller = IOControl(self.i2c)
        self.clock_controller = ClockControl(self.i2c, self.io_controller)
        self.clock_controller.write_clock_conf(clock_config_path)
        self.dac_controller = DacControl(self.i2c)
        self.trigger_logic = TriggerLogic(self.i2c)
        self.dut_logic = DUTLogic(self.i2c)

        self.reset_configuration()
        self.config_parser = TLUConfigure(self, self.io_controller, config_path)
        self.data_parser = DataParser()

        self.log.success("TLU initialized")
        # if present, init display

    def configure(self) -> None:
        """loads the conf.yaml and configures the TLU accordingly.
        """
        self.config_parser.configure()

    def reset_configuration(self) -> None:
        """Switch off all outputs, reset all counters and set threshold to 1.2V
        """
        #Disable all outputs
        self.io_controller.clock_lemo_output(False)
        for i in range(4): self.io_controller.configure_hdmi(i+1, 0)
        self.dac_controller.set_all_voltage(0)
        self.io_controller.all_off()
        #sets all thresholds to 1.2 V
        for i in range(6): self.dac_controller.set_threshold(i+1, 1.2)
        #Resets all internal counters and raise the trigger veto.
        self.set_run_active(False)
        self.reset_status()
        self.reset_counters()
        self.trigger_logic.set_trigger_veto(True)
        self.reset_fifo()
        self.reset_timestamp()
        self.run_number = 0
        try:
            self.h5_file.close()
        except:
            pass

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

    # def reset_board(self) -> None:
    #     #THIS FUNCTION CRASHES THE TLU. TLU needs a power cycle afterwards. This does not work at all...
    #     self.i2c.write_register("logic_clocks.LogicRst", 1)

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
        """ Resets the complete status and all counters.
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
            This is just for testing and bugfixing.
        """
        self.log.info("Configure DUT 1 in EUDET test mode")
        
        test_stretch = [1,1,1,1,1,1]
        test_delay = [0,0,0,0,0,0] 

        self.io_controller.configure_hdmi(1, '0111')
        self.io_controller.clock_hdmi_output(1, 'off')
        self.trigger_logic.set_pulse_stretch_pack(test_stretch)
        self.trigger_logic.set_pulse_delay_pack(test_delay)
        self.trigger_logic.set_trigger_mask(mask_high=0x00000000, mask_low=0x00000002)
        self.trigger_logic.set_trigger_polarity(1)
        self.dut_logic.set_dut_mask('0001')
        self.dut_logic.set_dut_mask_mode('00000000')
        self.trigger_logic.set_internal_trigger_frequency(500)

    def default_configuration(self) -> None:
        """Default configuration. Configures DUT 1 to run in EUDET mode.
           This is just for testing and bugfixing.
        """
        test_stretch = [1, 1, 1, 1, 1, 1]
        test_delay = [0, 0, 0, 0, 0, 0] 

        self.io_controller.configure_hdmi(1, '0111')
        self.io_controller.configure_hdmi(2, '0111')
        self.io_controller.configure_hdmi(3, '0111')
        self.io_controller.configure_hdmi(4, '0111')
        self.io_controller.clock_hdmi_output(1, 'off')
        self.io_controller.clock_hdmi_output(2, 'off')
        self.io_controller.clock_hdmi_output(3, 'off')
        self.io_controller.clock_hdmi_output(4, 'off')
        self.io_controller.clock_lemo_output(False)
        self.dac_controller.set_threshold(1, -0.04)
        self.dac_controller.set_threshold(2, -0.04)
        self.dac_controller.set_threshold(3, -0.04)
        self.dac_controller.set_threshold(4, -0.04)
        self.dac_controller.set_threshold(5, -0.2)
        self.dac_controller.set_threshold(6, -0.2)
        self.trigger_logic.set_pulse_stretch_pack(test_stretch)
        self.trigger_logic.set_pulse_delay_pack(test_delay)
        self.trigger_logic.set_trigger_mask(mask_high=0, mask_low=2)
        self.trigger_logic.set_trigger_polarity(1)
        self.dut_logic.set_dut_mask('0001')
        self.dut_logic.set_dut_mask_mode('00000000')
        self.dut_logic.set_dut_mask_mode_modifier(0)
        self.dut_logic.set_dut_ignore_busy(0)
        self.dut_logic.set_dut_ignore_shutter(0x1)
        self.trigger_logic.set_internal_trigger_frequency(0)

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
        self.run_number += 1

    def set_enable_record_data(self, value: int) -> None:
        """ #TODO not sure what this does. Looks like a seperate internal event buffer to the FIFO.

        Args:
            value (int): #TODO I think this does not work
        """
        self.i2c.write_register("Event_Formatter.Enable_Record_Data", value)

    def get_event_fifo_csr(self) -> int:
        """ Reads value from 'EventFifoCSR'

        Returns:
            int: number of events
        """
        return self.i2c.read_register("eventBuffer.EventFifoCSR")

    def get_event_fifo_fill_level(self) -> int:
        """Reads value from 'EventFifoFillLevel'

        Returns:
            int: buffer level of the fifi
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
            list: 6 element long vector containing bitwords of the data.
        """
        event_numb = self.get_event_fifo_fill_level()
        if event_numb*6 == 0xFEA:
            self.log.warning('FIFO is full')
        if event_numb and event_numb % 6 == 0:
            fifo_content = self.i2c_hw.getNode("eventBuffer.EventFifoData").readBlock(event_numb)
            self.i2c_hw.dispatch()
            return np.array(fifo_content)
        pass            

    def init_raw_data_table(self):
        """ Initializes the raw data table, where the raw FIFO data is found.
        """
        self.data = np.dtype([('w0', 'u4'), ('w1', 'u4'), ('w2', 'u4'), ('w3', 'u4'), ('w4', 'u4'), ('w5', 'u4')])
        self.filter_data = tb.Filters(complib='blosc', complevel=5)
        self.h5_file = tb.open_file(self.raw_data_path, mode='w', title='TLU')
        self.data_table = self.h5_file.create_table(self.h5_file.root, name='raw_data', description=self.data , title='data', filters=self.filter_data)
        self.h5_file.create_group(self.h5_file.root , 'configuration', self.config_parser.conf)

    def log_sent_status(self, time: int) -> None:
        """Logs the status of the TLU run with trigger number, runtime usw.
           Also calculates the mean trigger frequency between function calls.

        Args:
            time (int): current runtime of the TLU
        """
        self.hit_rate = (self.trigger_logic.get_post_veto_trigger()-self.last_triggers_freq)/(time-self.last_time)
        self.run_time = time
        self.event_number = self.trigger_logic.get_post_veto_trigger()
        self.total_trigger_number = self.trigger_logic.get_pre_veto_trigger()

        if self.zmq_address not in [None, 'off']:
            self.socket.send_string(str([self.run_time, self.event_number, self.total_trigger_number,self.hit_rate]), flags=zmq.NOBLOCK)

        self.last_time = time
        self.last_triggers_freq = self.trigger_logic.get_post_veto_trigger()

        self.log.info("Run time: %.3f s, Event numb.: %s, Total trigger numb.: %s, Trigger freq.: %.f Hz" 
                      %(self.run_time, self.event_number, self.total_trigger_number,self.hit_rate))

        # self.log.warning('FIFO level: %s' %self.log.warning(self.get_event_fifo_fill_level()))
        # self.log.warning('FIFO level 2: %s' %self.log.warning(self.get_event_fifo_csr()))
        # self.log.info("fifo csr: %s fifo fill level: %s" %(self.get_event_fifo_csr(),self.get_event_fifo_csr()))
        # self.log.info("post: %s pre: %s" %(self.trigger_logic.get_post_veto_trigger(),self.trigger_logic.get_pre_veto_trigger()))
        # self.log.info("time stamp: %s" %(self.get_timestamp()))

    def log_trigger_inputs(self, event_vector: list) -> None:
        """Logs which inputs triggered the event corresponding to the event vector.

        Args:
            event_vector (list): 6 data long event vector from the FIFO.
        """
        w0 = event_vector[0]
        input_1 = (w0 >> 16) & 0x1
        input_2 = (w0 >> 17) & 0x1
        input_3 = (w0 >> 18) & 0x1
        input_4 = (w0 >> 19) & 0x1
        input_5 = (w0 >> 20) & 0x1
        input_6 = (w0 >> 21) & 0x1
        self.log.info('Event triggered:')
        self.log.info('Input 1: %s, Input 2: %s, Input 3: %s, Input 4: %s, Input 5: %s, Input 6: %s' %(input_1, input_2, input_3, input_4, input_5, input_6))

    def setup_zmq(self) -> None:
        self.context = zmq.Context()
        self.socket = self.context.socket(zmq.PUB)
        self.socket.bind(self.zmq_address)
        self.log.info('Connected ZMQ socket with address: %s' %self.zmq_address)

    def run(self) -> None:
        """ Start run of the TLU. 
        """
        self.start_run()
        run_active = True
        #reset starting parameter
        start_time = self.get_timestamp()
        self.last_time = 0
        self.last_triggers_freq = self.trigger_logic.get_post_veto_trigger()
        first_event = True
        #prepare data handling and zmq connection
        save_data, interpret_data = self.config_parser.get_data_handling()
        self.zmq_address = self.config_parser.get_zmq_connection()

        if save_data:
            self.raw_data_path = 'tlu_data/tlu_raw_run%s_%s.h5' %(self.run_number, datetime.now().strftime('%Y_%m_%d_%H_%M_%S'))
            self.interpreted_data_path = 'tlu_data/tlu_interpreted_run%s_%s.h5' %(self.run_number, datetime.now().strftime('%Y_%m_%d_%H_%M_%S'))
            self.init_raw_data_table()
        
        if self.zmq_address not in [None, 'off']:
            self.setup_zmq()

        while run_active:
            try:
                last_time = self.get_timestamp()
                current_time = (last_time-start_time)*25/1000000000
                current_event = self.pull_fifo_event()
                try: 
                    if np.size(current_event) > 1:
                        #This additional loop is needed because the event fifo can have multiple events in dependence of the trigger rate.
                        for event_vec in np.split(current_event,len(current_event)/6): 
                            if save_data:
                                self.data_table.append(event_vec)
                except:
                    if KeyboardInterrupt:
                        run_active = False
                    else:
                        #If this happens: poss. Hitrate to high for FIFO and or Data handling.
                        self.log.warning('Incomplete Event handling...')
            
                #Logs and poss. sends status every 1s.
                if current_time - self.last_time > 1:
                    self.log_sent_status(current_time)
                    # self.log_trigger_inputs(current_event)
                    # self.log.warning(str(current_event))

                #This loop sents which inputs produced the trigger signal for the first event.
                if (np.size(current_event)  > 1) and first_event: #TODO only first event?
                    self.log_trigger_inputs(current_event)
                    first_event = False

                #Stops the TLU after some time in seconds.
                # if current_time*25/1000000000 > 600:
                #     run_active = False
            except:
                KeyboardInterrupt
                run_active = False
        
        self.stop_run()
        #Cleanup of FIFO
        try:
            while np.size(current_event) > 1:      
                current_event = self.pull_fifo_event()
        except:
            KeyboardInterrupt 
            self.log.warning('Interupted FIFO cleanup')   
        
        if self.zmq_address not in [None, 'off']:
            self.socket.close()

        if save_data:
            self.h5_file.close()
        if interpret_data:
            try:
                self.data_parser.parse(self.raw_data_path, self.interpreted_data_path)
            except:
                self.log.warning("Cannot interpret data.")
        self.log.success('Run finished')

if __name__ == "__main__":

    uhal.setLogLevelTo(uhal.LogLevel.NOTICE)
    manager = uhal.ConnectionManager("file://./misc/aida_tlu_connection.xml")
    hw = uhal.HwInterface(manager.getDevice("aida_tlu.controlhub"))

    clock_path = 'misc/aida_tlu_clk_config.txt'
    config_path = 'conf.yaml'

    tlu = AidaTLU(hw, config_path, clock_path)

    tlu.configure()
    
    tlu.run()