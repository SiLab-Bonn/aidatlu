#!/usr/bin/env python3
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
from constellation.core.datasender import DataSender

from aidatlu import logger
from aidatlu.hardware.i2c import I2CCore
from aidatlu.main.config_parser import toml_parser
from aidatlu.main.tlu import AidaTLU as TLU
from aidatlu.test.utils import MockI2C


class AidaTLU(DataSender):

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
        self.aidatlu.configure()
        return "Do launching complete"

    def do_landing(self, payload: Any) -> str:
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

        self.aidatlu.start_run_configuration()

        # Set Begin-of-run tags
        self.BOR["BoardID"] = self.aidatlu.get_device_id()

        # For EudaqNativeWriter compatibility
        self.BOR["eudaq_event"] = "TluRawDataEvent"
        self.BOR["frames_as_blocks"] = True

        return "Do starting complete"

    def do_run(self, run_identifier: str) -> str:
        t = threading.Thread(target=self.aidatlu.handle_status)
        t.start()
        while not self._state_thread_evt.is_set():
            evt = self.aidatlu.pull_fifo_event()
            if np.size(evt) == 6:
                timestamp = (np.uint64(evt[0]) & 0x0000FFFF << 32) + evt[1]
                # Collect metadata
                meta = {
                    "dtype": f"{evt.dtype}",
                    "flag_trigger": True,
                    "trigger": int(evt[3]),
                    "timestamp_begin": int(timestamp * 1000),
                    "timestamp_end": int((timestamp + 25) * 1000),
                }
                # Assemble payload in legacy format - first scalers then input bitmask
                payload = [
                    (evt[2] >> 24) & 0xFF,
                    (evt[2] >> 16) & 0xFF,
                    (evt[2] >> 8) & 0xFF,
                    evt[2] & 0xFF,
                    (evt[4] >> 24) & 0xFF,
                    (evt[4] >> 16) & 0xFF,
                    (evt[0] >> 16) & 0x3F,
                ]
                self.data_queue.put((payload, meta))
            elif np.size(evt) > 1:
                self.log.warning(
                    f"Wrong event data length, got {np.size(evt)}, expected 6"
                )

        t.do_run = False
        self.aidatlu.stop_run()
        return "Do running complete"

    def do_stopping(self) -> str:
        self.aidatlu.stop_run_configuration()
        return "Do stopping complete"

    def do_landing(self) -> str:
        self.aidatlu.reset_configuration()
        return "Do Stop"

    def _init_tlu(self, config: Configuration) -> None:
        "Parse configuration file to TLU and initialize, set loggers"
        self.config_file = toml_parser(config, constellation=True)
        self.clock_file = str(self.file_path) + "/../misc/aida_tlu_clk_config.txt"
        self.aidatlu = TLU(
            self.hw, self.config_file, self.clock_file, i2c=self.i2c_method
        )

        # Resets aidatlu loggers and replaces them with constellation loggers
        logger._reset_all_loggers()
        self.aidatlu.log = self.log
        self.aidatlu.io_controller.log = self.log
        self.aidatlu.dac_controller.log = self.log
        self.aidatlu.clock_controller.log = self.log
        self.aidatlu.trigger_logic.log = self.log
        self.aidatlu.dut_logic.log = self.log
        self.aidatlu.config_parser.log = self.log

    @schedule_metric("Hz", MetricsType.LAST_VALUE, 1)
    def pre_veto_rate_rate(self) -> Any:
        if self.fsm.current_state_value == SatelliteState.RUN and hasattr(
            self.aidatlu, "pre_veto_rate"
        ):
            return self.aidatlu.pre_veto_rate
        else:
            return None

    @schedule_metric("Hz", MetricsType.LAST_VALUE, 1)
    def post_veto_rate(self) -> Any:
        if self.fsm.current_state_value == SatelliteState.RUN and hasattr(
            self.aidatlu, "post_veto_rate"
        ):
            return self.aidatlu.post_veto_rate
        else:
            return None

    @schedule_metric("", MetricsType.LAST_VALUE, 1)
    def total_post_veto(self) -> Any:
        if self.fsm.current_state_value == SatelliteState.RUN and hasattr(
            self.aidatlu, "total_post_veto"
        ):
            return self.aidatlu.total_post_veto
        else:
            return None

    @schedule_metric("", MetricsType.LAST_VALUE, 1)
    def total_pre_veto(self) -> Any:
        if self.fsm.current_state_value == SatelliteState.RUN and hasattr(
            self.aidatlu, "total_pre_veto"
        ):
            return self.aidatlu.total_pre_veto
        else:
            return None

    @schedule_metric("", MetricsType.LAST_VALUE, 1)
    def sc0(self) -> Any:
        if self.fsm.current_state_value == SatelliteState.ORBIT:
            self.log.debug("sc0: %s" % self.aidatlu.get_scaler(0))
            return self.aidatlu.get_scaler(0)
        else:
            return None

    @schedule_metric("", MetricsType.LAST_VALUE, 1)
    def sc1(self) -> Any:
        if self.fsm.current_state_value == SatelliteState.ORBIT:
            return self.aidatlu.get_scaler(1)
        else:
            return None

    @schedule_metric("", MetricsType.LAST_VALUE, 1)
    def sc2(self) -> Any:
        if self.fsm.current_state_value == SatelliteState.ORBIT:
            return self.aidatlu.get_scaler(2)
        else:
            return None

    @schedule_metric("", MetricsType.LAST_VALUE, 1)
    def sc3(self) -> Any:
        if self.fsm.current_state_value == SatelliteState.ORBIT:
            return self.aidatlu.get_scaler(3)
        else:
            return None

    @schedule_metric("", MetricsType.LAST_VALUE, 1)
    def sc4(self) -> Any:
        if self.fsm.current_state_value == SatelliteState.ORBIT:
            return self.aidatlu.get_scaler(4)
        else:
            return None

    @schedule_metric("", MetricsType.LAST_VALUE, 1)
    def sc5(self) -> Any:
        if self.fsm.current_state_value == SatelliteState.ORBIT:
            return self.aidatlu.get_scaler(5)
        else:
            return None
