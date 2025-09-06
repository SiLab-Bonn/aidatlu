#!/usr/bin/env python3
from collections import deque
import os
import threading
import time
from pathlib import Path
from typing import Any

import numpy as np

from constellation.core.cmdp import MetricsType
from constellation.core.configuration import Configuration
from constellation.core.message.cscp1 import SatelliteState
from constellation.core.monitoring import schedule_metric
from constellation.core.transmitter_satellite import TransmitterSatellite

from aidatlu import logger
from aidatlu.hardware.i2c import I2CCore
from aidatlu.main.config_parser import Configure, toml_parser
from aidatlu.hardware.tlu_controller import TLUControl as TLU
from aidatlu.test.utils import MockI2C


class AidaTLU(TransmitterSatellite):

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.use_mock = os.environ.get("TLU_MOCK")

    def do_initializing(self, config: Configuration) -> str:
        self.log.info(
            "Received configuration with parameters: %s",
            ", ".join(config.get_keys()),
        )

        self.file_path = Path(__file__).parent

        if not self.use_mock:
            import uhal

            uhal.setLogLevelTo(uhal.LogLevel.NOTICE)
            manager = uhal.ConnectionManager(
                "file://" + str(self.file_path) + "/../misc/aida_tlu_connection.xml"
            )
            self.hw = uhal.HwInterface(manager.getDevice("aida_tlu.controlhub"))
            self.i2c_method = I2CCore
        else:
            self.i2c_method = MockI2C
            self.hw = None

        self._init_tlu(config)

        return "Initializing complete"

    def do_launching(self, payload: Any = None) -> str:
        self.config_parser.configure()
        self.conf_list = self.config_parser.get_configuration_table()
        self.aidatlu.get_event_fifo_fill_level()
        self.aidatlu.get_event_fifo_csr()
        self.aidatlu.get_scalers()
        return "Do launching complete"

    def do_landing(self) -> str:
        self.aidatlu.reset_configuration()
        return "Do landing complete"

    def do_reconfigure(self, config: Configuration) -> str:
        self._init_tlu(config)
        return "Do reconfigure complete"

    def do_starting(self, run_identifier: str = None) -> str:
        if self.use_mock:
            start_time = time.time()

            def _get_timestamp(self):
                # Helper function returns timestamp
                return (time.time() - start_time) / 25 * 1000000000

            def _pull_fifo_event(self):
                # Blank FIFO pull helper function
                return 0

            # Overwrite TLU methods needed for run loop
            func_type = type(self.aidatlu.get_timestamp)
            self.aidatlu.get_timestamp = func_type(_get_timestamp, self.aidatlu)
            func_type = type(self.aidatlu.pull_fifo_event)
            self.aidatlu.pull_fifo_event = func_type(_pull_fifo_event, self.aidatlu)

        self.aidatlu.start_run()
        self.aidatlu.get_fw_version()
        self.aidatlu.get_device_id()
        # reset starting parameter
        self.start_time = self.aidatlu.get_timestamp()
        self.last_time = 0
        self.last_post_veto_trigger = self.aidatlu.trigger_logic.get_post_veto_trigger()
        self.last_pre_veto_trigger = self.aidatlu.trigger_logic.get_pre_veto_trigger()

        # Set Begin-of-run tags
        self.bor["BoardID"] = self.aidatlu.get_device_id()

        # For EudaqNativeWriter compatibility
        self.bor["eudaq_event"] = "TluRawDataEvent"
        self.bor["frames_as_blocks"] = True

        return "Do starting complete"

    def do_run(self, run_identifier: str) -> str:
        t = threading.Thread(target=self.handle_status)
        t.start()

        # We ideally pull 6 uint32s, but we might pull more or less
        # Thus, add data to a queue and pop in blocks of 6 uint32s
        data_queue = deque()
        while not self._state_thread_evt.is_set():
            evt = self.aidatlu.pull_fifo_event()
            if np.size(evt) > 1:
                data_queue.extend(evt)
                while len(data_queue) >= 6:
                    self._handle_event([data_queue.popleft() for _ in range(6)])

        t.do_run = False
        self.aidatlu.stop_run()
        return "Do running complete"

    def do_stopping(self) -> str:
        self.aidatlu.pull_fifo_event()
        self.log.info("Run finished")
        return "Do stopping complete"

    def _init_tlu(self, config: Configuration) -> None:
        "Parse configuration file to TLU and initialize, set loggers"
        self.config_file = toml_parser(config, constellation=True)
        if self.config_file["clock_config"] in [None, "None", False]:
            self.log.info("No clock configuration provided, using default file")
            self.clock_file = str(self.file_path) + "/../misc/aida_tlu_clk_config.txt"
        else:
            self.clock_file = self.config_file["clock_config"]
        self.aidatlu = TLU(self.hw, i2c=self.i2c_method)
        self.config_parser = Configure(self.aidatlu, self.config_file)
        self.aidatlu.reset_configuration()
        # Resets aidatlu loggers and replaces them with constellation loggers
        logger._reset_all_loggers()
        self.aidatlu.log = self.log
        self.aidatlu.io_controller.log = self.log
        self.aidatlu.dac_controller.log = self.log
        self.aidatlu.clock_controller.log = self.log
        self.aidatlu.trigger_logic.log = self.log
        self.aidatlu.dut_logic.log = self.log
        self.config_parser.log = self.log

    def _handle_event(self, evt: list) -> None:
        # Calculate timestamp in nanoseconds from TLU 40MHz clock:
        timestamp = 25 * (((np.uint64(evt[0]) & 0x0000FFFF) << 32) + evt[1])
        # Collect metadata
        meta = {
            "flag_trigger": True,
            "trigger_number": int(evt[3]),
            "timestamp_begin": int(timestamp * 1000),
            "timestamp_end": int((timestamp + 25) * 1000),
        }
        # New data format: store 6 uint32 as bytes in little-endian
        payload = np.array(evt, dtype="<u4").tobytes()
        data_record = self.new_data_record()
        data_record.add_block(payload)
        self.send_data_record(data_record)

    def handle_status(self) -> None:
        """Status message handling in separate thread. Calculates run time and obtain trigger information and sent it out every second."""
        t = threading.current_thread()
        while getattr(t, "do_run", True):
            time.sleep(0.5)
            last_time = self.aidatlu.get_timestamp()
            current_time = (last_time - self.start_time) * 25 / 1000000000
            # Logs and poss. sends status every 1s.
            if current_time - self.last_time > 1:
                self.log_status(current_time)

    def log_status(self, time: int) -> None:
        """Logs the status of the TLU run with trigger number, runtime usw.
           Also calculates the mean trigger frequency between function calls.

        Args:
            time (int): current runtime of the TLU
        """
        self.post_veto_rate = (
            self.aidatlu.get_post_veto_trigger_number() - self.last_post_veto_trigger
        ) / (time - self.last_time)
        self.pre_veto_rate = (
            self.aidatlu.get_pre_veto_trigger_number() - self.last_pre_veto_trigger
        ) / (time - self.last_time)
        self.run_time = time
        self.total_post_veto = self.aidatlu.get_post_veto_trigger_number()
        self.total_pre_veto = self.aidatlu.get_pre_veto_trigger_number()
        s0, s1, s2, s3, s4, s5 = self.aidatlu.get_scalers()

        self.last_time = time
        self.last_post_veto_trigger = self.aidatlu.get_post_veto_trigger_number()
        self.last_pre_veto_trigger = self.aidatlu.get_pre_veto_trigger_number()

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
        if self.aidatlu.get_event_fifo_csr() == 0x10:
            self.log.warning("FIFO is full")

    @schedule_metric("Hz", MetricsType.LAST_VALUE, 1)
    def pre_veto_rate(self) -> Any:
        if self.fsm.current_state_value == SatelliteState.RUN and hasattr(
            self, "pre_veto_rate"
        ):
            return self.pre_veto_rate
        else:
            return None

    @schedule_metric("Hz", MetricsType.LAST_VALUE, 1)
    def post_veto_rate(self) -> Any:
        if self.fsm.current_state_value == SatelliteState.RUN and hasattr(
            self, "post_veto_rate"
        ):
            return self.post_veto_rate
        else:
            return None

    @schedule_metric("", MetricsType.LAST_VALUE, 1)
    def post_veto(self) -> Any:
        if self.fsm.current_state_value == SatelliteState.RUN:
            return self.aidatlu.get_post_veto_trigger_number()
        else:
            return None

    @schedule_metric("", MetricsType.LAST_VALUE, 1)
    def pre_veto(self) -> Any:
        if self.fsm.current_state_value == SatelliteState.RUN:
            return self.aidatlu.get_pre_veto_trigger_number()
        else:
            return None

    @schedule_metric("", MetricsType.LAST_VALUE, 1)
    def sc0(self) -> Any:
        if self.fsm.current_state_value in [SatelliteState.ORBIT, SatelliteState.RUN]:
            self.log.debug("sc0: %s" % self.aidatlu.get_scaler(0))
            return self.aidatlu.get_scaler(0)
        else:
            return None

    @schedule_metric("", MetricsType.LAST_VALUE, 1)
    def sc1(self) -> Any:
        if self.fsm.current_state_value in [SatelliteState.ORBIT, SatelliteState.RUN]:
            return self.aidatlu.get_scaler(1)
        else:
            return None

    @schedule_metric("", MetricsType.LAST_VALUE, 1)
    def sc2(self) -> Any:
        if self.fsm.current_state_value in [SatelliteState.ORBIT, SatelliteState.RUN]:
            return self.aidatlu.get_scaler(2)
        else:
            return None

    @schedule_metric("", MetricsType.LAST_VALUE, 1)
    def sc3(self) -> Any:
        if self.fsm.current_state_value in [SatelliteState.ORBIT, SatelliteState.RUN]:
            return self.aidatlu.get_scaler(3)
        else:
            return None

    @schedule_metric("", MetricsType.LAST_VALUE, 1)
    def sc4(self) -> Any:
        if self.fsm.current_state_value in [SatelliteState.ORBIT, SatelliteState.RUN]:
            return self.aidatlu.get_scaler(4)
        else:
            return None

    @schedule_metric("", MetricsType.LAST_VALUE, 1)
    def sc5(self) -> Any:
        if self.fsm.current_state_value in [SatelliteState.ORBIT, SatelliteState.RUN]:
            return self.aidatlu.get_scaler(5)
        else:
            return None
