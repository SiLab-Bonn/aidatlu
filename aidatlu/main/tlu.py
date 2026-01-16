import threading
import time
from datetime import datetime
from pathlib import Path

import numpy as np
import tables as tb
import zmq

from aidatlu import logger
from aidatlu.hardware.tlu_controller import TLUControl, TLUConfigure
from aidatlu.hardware.i2c import I2CCore
from aidatlu.main.config_parser import yaml_parser
from aidatlu.main.data_parser import interpret_data


class AidaTLU:
    def __init__(self, hw, config_dict, clock_config_path, i2c=I2CCore) -> None:
        self.log = logger.setup_main_logger(__class__.__name__)

        self.tlu_controller = TLUControl(hw=hw, i2c=i2c)
        self.tlu_controller.write_clock_config(clock_config_path)

        self.reset_configuration()
        self.tlu_configure = TLUConfigure(self.tlu_controller, config_dict)

        self.log.success("TLU initialized")

    def configure(self) -> None:
        """loads the conf.yaml and configures the TLU accordingly."""
        self.tlu_configure.configure()
        self.conf_list = self.tlu_configure.get_configuration_table()
        self.tlu_controller.get_event_fifo_fill_level()
        self.tlu_controller.get_event_fifo_csr()
        self.tlu_controller.get_scalers()

    def reset_configuration(self) -> None:
        self.tlu_controller.reset_configuration()
        self.run_number = 0
        try:
            self.h5_file.close()
        except:
            pass

    def stop_run(self) -> None:
        self.tlu_controller.stop_run()
        self.run_number += 1

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
            last_time = self.tlu_controller.get_timestamp()
            current_time = (last_time - self.start_time) * 25 / 1000000000
            # Logs and poss. sends status every 1s.
            if current_time - self.last_time > 1:
                self.log_sent_status(current_time)
            # Stops the TLU after some time in seconds.
            if self.timeout != None:
                if current_time > self.timeout:
                    self.stop_condition = True
            if self.max_trigger != None:
                if (
                    self.tlu_controller.trigger_logic.get_post_veto_trigger()
                    > self.max_trigger
                ):
                    self.stop_condition = True

    def log_sent_status(self, time: int) -> None:
        """Logs the status of the TLU run with trigger number, runtime usw.
           Also calculates the mean trigger frequency between function calls.

        Args:
            time (int): current runtime of the TLU
        """
        self.post_veto_rate = (
            self.tlu_controller.trigger_logic.get_post_veto_trigger()
            - self.last_post_veto_trigger
        ) / (time - self.last_time)
        self.pre_veto_rate = (
            self.tlu_controller.trigger_logic.get_pre_veto_trigger()
            - self.last_pre_veto_trigger
        ) / (time - self.last_time)
        self.run_time = time
        self.total_post_veto = self.tlu_controller.trigger_logic.get_post_veto_trigger()
        self.total_pre_veto = self.tlu_controller.trigger_logic.get_pre_veto_trigger()

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
        self.last_post_veto_trigger = (
            self.tlu_controller.trigger_logic.get_post_veto_trigger()
        )
        self.last_pre_veto_trigger = (
            self.tlu_controller.trigger_logic.get_pre_veto_trigger()
        )

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

        if self.tlu_controller.get_event_fifo_csr() == 0x10:
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
        self.tlu_controller.start_run()
        self.tlu_controller.get_fw_version()
        self.tlu_controller.get_device_id()
        # reset starting parameter
        self.start_time = self.tlu_controller.get_timestamp()
        self.last_time = 0
        self.last_post_veto_trigger = (
            self.tlu_controller.trigger_logic.get_post_veto_trigger()
        )
        self.last_pre_veto_trigger = (
            self.tlu_controller.trigger_logic.get_pre_veto_trigger()
        )
        self.stop_condition = False
        # prepare data handling and zmq connection
        self.save_data = self.tlu_configure.get_data_handling()
        self.zmq_address = self.tlu_configure.get_zmq_connection()
        self.max_trigger, self.timeout = self.tlu_configure.get_stop_condition()

        if self.save_data:
            self.path = self.tlu_configure.get_output_data_path()
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
            current_event = self.tlu_controller.pull_fifo_event()
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
        self.tlu_controller.pull_fifo_event()

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
