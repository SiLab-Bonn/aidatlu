import threading
import time
from datetime import datetime
from pathlib import Path

import numpy as np
import tables as tb
import zmq

from aidatlu import logger
from aidatlu.hardware.clock_controller import ClockControl
from aidatlu.hardware.dac_controller import DacControl
from aidatlu.hardware.dut_controller import DUTLogic
from aidatlu.hardware.i2c import I2CCore
from aidatlu.hardware.ioexpander_controller import IOControl
from aidatlu.hardware.trigger_controller import TriggerLogic
from aidatlu.main.config_parser import Configure, yaml_parser
from aidatlu.main.data_parser import interpret_data


class AidaTLU:
    def __init__(self, hw, config_dict, clock_config_path, i2c=I2CCore) -> None:
        self.log = logger.setup_main_logger(__class__.__name__)

        self.i2c = i2c(hw)
        self.i2c_hw = hw
        self.log.info("Initializing IPbus interface")
        self.i2c.init()

        if self.i2c.modules["eeprom"]:
            self.log.info("Found device with ID %s" % hex(self.get_device_id()))

        # TODO some configuration also sends out ~70 triggers.
        self.io_controller = IOControl(self.i2c)
        self.dac_controller = DacControl(self.i2c)
        self.clock_controller = ClockControl(self.i2c, self.io_controller)
        self.clock_controller.write_clock_conf(clock_config_path)
        self.trigger_logic = TriggerLogic(self.i2c)
        self.dut_logic = DUTLogic(self.i2c)

        self.reset_configuration()
        self.config_parser = Configure(self, config_dict)

        self.log.success("TLU initialized")

    def configure(self) -> None:
        """loads the conf.yaml and configures the TLU accordingly."""
        self.config_parser.configure()
        self.conf_list = self.config_parser.get_configuration_table()
        self.get_event_fifo_fill_level()
        self.get_event_fifo_csr()
        self.get_scalers()

    def reset_configuration(self) -> None:
        """Switch off all outputs, reset all counters and set threshold to 1.2V"""
        # Disable all outputs
        self.io_controller.clock_lemo_output(False)
        for i in range(4):
            self.io_controller.configure_hdmi(i + 1, 1)
        self.dac_controller.set_voltage(5, 0)
        self.io_controller.all_off()
        # sets all thresholds to 1.2 V
        for i in range(6):
            self.dac_controller.set_threshold(i + 1, 0)
        # Resets all internal counters and raise the trigger veto.
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

    def reset_timestamp(self) -> None:
        """Sets bit to  'ResetTimestampW' register to reset the time stamp."""
        self.i2c.write_register("Event_Formatter.ResetTimestampW", 1)

    def reset_counters(self) -> None:
        """Resets the trigger counters."""
        self.write_status(0x2)
        self.write_status(0x0)

    def reset_status(self) -> None:
        """Resets the complete status and all counters."""
        self.write_status(0x3)
        self.write_status(0x0)
        self.write_status(0x4)
        self.write_status(0x0)

    def reset_fifo(self) -> None:
        """Sets 0 to 'EventFifoCSR' this resets the FIFO."""
        self.set_event_fifo_csr(0x0)

    def set_event_fifo_csr(self, value: int) -> None:
        """Sets value to the EventFifoCSR register.

        Args:
            value (int): 0 resets the FIFO. #TODO can do other stuff that is not implemented

        """
        self.i2c.write_register("eventBuffer.EventFifoCSR", value)

    def write_status(self, value: int) -> None:
        """Sets value to the 'SerdesRstW' register.

        Args:
            value (int): Bit 0 resets the status, bit 1 resets trigger counters and bit 2 calibrates IDELAY.
        """
        self.i2c.write_register("triggerInputs.SerdesRstW", value)

    def set_run_active(self, state: bool) -> None:
        """Raises internal run active signal.

        Args:
            state (bool): True sets run active, False disables it.
        """
        if type(state) != bool:
            raise TypeError("State has to be bool")
        self.i2c.write_register("Shutter.RunActiveRW", int(state))
        self.log.info("Run active: %s" % self.get_run_active())

    def get_run_active(self) -> bool:
        """Reads register 'RunActiveRW'

        Returns:
            bool: Returns bool of the run active register.
        """
        return bool(self.i2c.read_register("Shutter.RunActiveRW"))

    def start_run(self) -> None:
        """Start run configurations"""
        self.reset_counters()
        self.reset_fifo()
        self.reset_timestamp()
        self.set_run_active(True)
        self.trigger_logic.set_trigger_veto(False)

    def stop_run(self) -> None:
        """Stop run configurations"""
        self.trigger_logic.set_trigger_veto(True)
        self.set_run_active(False)
        self.run_number += 1

    def set_enable_record_data(self, value: int) -> None:
        """#TODO not sure what this does. Looks like a separate internal event buffer to the FIFO.

        Args:
            value (int): #TODO I think this does not work
        """
        self.i2c.write_register("Event_Formatter.Enable_Record_Data", value)

    def get_event_fifo_csr(self) -> int:
        """Reads value from 'EventFifoCSR', corresponds to status flags of the FIFO.

        Returns:
            int: number of events
        """
        return self.i2c.read_register("eventBuffer.EventFifoCSR")

    def get_event_fifo_fill_level(self) -> int:
        """Reads value from 'EventFifoFillLevel'
           Returns the number of words written in
           the FIFO. The lowest 14-bits are the actual data.

        Returns:
            int: buffer level of the fifi
        """
        return self.i2c.read_register("eventBuffer.EventFifoFillLevel")

    def get_timestamp(self) -> int:
        """Get current time stamp.

        Returns:
            int: Time stamp is not formatted.
        """
        time = self.i2c.read_register("Event_Formatter.CurrentTimestampHR")
        time = time << 32
        time = time + self.i2c.read_register("Event_Formatter.CurrentTimestampLR")
        return time

    def pull_fifo_event(self) -> list:
        """Pulls event from the FIFO. This is needed in the run loop to prevent the buffer to get stuck.
            if this register is full the fifo needs to be reset or new triggers are generated but not sent out.
            #TODO check here if the FIFO is full and reset it if needed would prob. make sense.

        Returns:
            list: 6 element long vector containing bitwords of the data.
        """
        event_numb = self.get_event_fifo_fill_level()
        if event_numb:
            fifo_content = self.i2c_hw.getNode("eventBuffer.EventFifoData").readBlock(
                event_numb
            )
            self.i2c_hw.dispatch()
            return np.array(fifo_content)
        pass

    def get_scaler(self, channel: int) -> int:
        """reads current scaler value from register"""
        if channel < 0 or channel > 5:
            raise ValueError("Only channels 0 to 5 are valid")
        return self.i2c.read_register(f"triggerInputs.ThrCount{channel:d}R")

    def get_scalers(self) -> list:
        """reads current sc values from registers

        Returns:
            list: all 6 trigger sc values
        """
        return [self.get_scaler(n) for n in range(6)]

    def init_raw_data_table(self) -> None:
        """Initializes the raw data table, where the raw FIFO data is found."""
        data_dtype = np.dtype([("raw", "u4")])
        config_dtype = np.dtype([("attribute", "S32"), ("value", "S32")])

        Path(self.path).mkdir(parents=True, exist_ok=True)
        hdf5_filter = tb.Filters(complib="blosc", complevel=5)
        self.h5_file = tb.open_file(self.raw_data_path, mode="w", title="TLU")
        self.data_table = self.h5_file.create_table(
            self.h5_file.root,
            name="raw_data",
            description=data_dtype,
            title="Raw data",
            filters=hdf5_filter,
        )
        config_table = self.h5_file.create_table(
            self.h5_file.root,
            name="conf",
            description=config_dtype,
            title="Configuration",
            filters=hdf5_filter,
        )
        self.buffer = []
        config_table.append(self.conf_list)

    def handle_status(self) -> None:
        """Status message handling in separate thread. Calculates run time and obtain trigger information and sent it out every second."""
        t = threading.current_thread()
        while getattr(t, "do_run", True):
            time.sleep(0.5)
            last_time = self.get_timestamp()
            current_time = (last_time - self.start_time) * 25 / 1000000000
            # Logs and poss. sends status every 1s.
            if current_time - self.last_time > 1:
                self.log_sent_status(current_time)
            # Stops the TLU after some time in seconds.
            if self.timeout != None:
                if current_time > self.timeout:
                    self.stop_condition = True
            if self.max_trigger != None:
                if self.trigger_logic.get_post_veto_trigger() > self.max_trigger:
                    self.stop_condition = True

    def log_sent_status(self, time: int) -> None:
        """Logs the status of the TLU run with trigger number, runtime usw.
           Also calculates the mean trigger frequency between function calls.

        Args:
            time (int): current runtime of the TLU
        """
        self.post_veto_rate = (
            self.trigger_logic.get_post_veto_trigger() - self.last_post_veto_trigger
        ) / (time - self.last_time)
        self.pre_veto_rate = (
            self.trigger_logic.get_pre_veto_trigger() - self.last_pre_veto_trigger
        ) / (time - self.last_time)
        self.run_time = time
        self.total_post_veto = self.trigger_logic.get_post_veto_trigger()
        self.total_pre_veto = self.trigger_logic.get_pre_veto_trigger()

        if self.zmq_address:
            self.socket.send_string(
                str(
                    [
                        self.run_time,
                        self.total_post_veto,
                        self.total_pre_veto,
                        self.pre_veto_rate,
                        self.post_veto_rate,
                    ]
                ),
                flags=zmq.NOBLOCK,
            )

        self.last_time = time
        self.last_post_veto_trigger = self.trigger_logic.get_post_veto_trigger()
        self.last_pre_veto_trigger = self.trigger_logic.get_pre_veto_trigger()

        self.log.info(
            "Run time: %.1f s, Pre veto: %s, Post veto: %s, Pre veto rate: %.f Hz, Post veto rate.: %.f Hz"
            % (
                self.run_time,
                self.total_pre_veto,
                self.total_post_veto,
                self.pre_veto_rate,
                self.post_veto_rate,
            )
        )

        if self.get_event_fifo_csr() == 0x10:
            self.log.warning("FIFO is full")

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
        self.log.debug(
            "Input 1: %s, Input 2: %s, Input 3: %s, Input 4: %s, Input 5: %s, Input 6: %s"
            % (input_1, input_2, input_3, input_4, input_5, input_6)
        )

    def setup_zmq(self) -> None:
        """Setup the zmq connection, this connection receives status messages."""
        self.context = zmq.Context()
        self.socket = self.context.socket(zmq.PUB)
        self.socket.bind(self.zmq_address)
        self.log.info("Connected ZMQ socket with address: %s" % self.zmq_address)

    def run(self) -> None:
        """Start run of the TLU."""
        self.start_run_configuration()
        self.run_active = True
        t = threading.Thread(target=self.handle_status)
        t.start()
        while self.run_active:
            try:
                self.run_loop()
                if self.stop_condition is True:
                    raise KeyboardInterrupt
            except:
                if KeyboardInterrupt:
                    self.run_active = False
                else:
                    # If this happens: poss. Hitrate to high for FIFO and or data handling.
                    self.log.warning("Incomplete event handling...")

        self.stop_run()
        t.do_run = False
        self.stop_run_configuration()

    def start_run_configuration(self) -> None:
        """Start of the run configurations, consists of timestamp resets, data preparations and zmq connections initialization."""
        self.start_run()
        self.get_fw_version()
        self.get_device_id()
        # reset starting parameter
        self.start_time = self.get_timestamp()
        self.last_time = 0
        self.last_post_veto_trigger = self.trigger_logic.get_post_veto_trigger()
        self.last_pre_veto_trigger = self.trigger_logic.get_pre_veto_trigger()
        self.stop_condition = False
        # prepare data handling and zmq connection
        self.save_data = self.config_parser.get_data_handling()
        self.zmq_address = self.config_parser.get_zmq_connection()
        self.max_trigger, self.timeout = self.config_parser.get_stop_condition()

        if self.save_data:
            self.path = self.config_parser.get_output_data_path()
            if self.path == None:
                self.path = Path(__file__).parent.parent / "tlu_data/"
            self.raw_data_path = str(self.path) + "/tlu_raw_run%s_%s.h5" % (
                self.run_number,
                datetime.now().strftime("%Y_%m_%d_%H_%M_%S"),
            )
            self.interpreted_data_path = str(
                self.path
            ) + "/tlu_interpreted_run%s_%s.h5" % (
                self.run_number,
                datetime.now().strftime("%Y_%m_%d_%H_%M_%S"),
            )
            self.init_raw_data_table()

        if self.zmq_address:
            self.setup_zmq()

    def run_loop(self) -> None:
        """A single instance of the run loop. In a TLU run this function needs to be called repeatedly.

        Raises:
            KeyboardInterrupt: The run loop can be interrupted when raising a KeyboardInterrupt.
        """
        try:
            current_event = self.pull_fifo_event()
            try:
                if self.save_data and np.size(current_event) > 1:
                    self.data_table.append(current_event)
                if self.stop_condition is True:
                    raise KeyboardInterrupt
            except:
                if KeyboardInterrupt:
                    self.run_active = False
                else:
                    # If this happens: poss. Hitrate to high for FIFO and or Data handling.
                    self.log.warning("Incomplete Event handling...")

        except KeyboardInterrupt:
            self.run_active = False

    def stop_run_configuration(self) -> None:
        """Cleans remaining FIFO data and closes data files and zmq connections after a run."""
        # Cleanup of FIFO
        self.pull_fifo_event()

        if self.zmq_address:
            self.socket.close()

        if self.save_data:
            self.h5_file.close()
            interpret_data(self.raw_data_path, self.interpreted_data_path)

        self.log.info("Run finished")


if __name__ == "__main__":
    import uhal

    uhal.setLogLevelTo(uhal.LogLevel.NOTICE)
    manager = uhal.ConnectionManager("file://../misc/aida_tlu_connection.xml")
    hw = uhal.HwInterface(manager.getDevice("aida_tlu.controlhub"))

    clock_path = "../misc/aida_tlu_clk_config.txt"
    config_path = "../tlu_configuration.yaml"

    conf_dict = yaml_parser(config_path)
    tlu = AidaTLU(hw, config_path, clock_path)

    tlu.configure()
    tlu.run()
