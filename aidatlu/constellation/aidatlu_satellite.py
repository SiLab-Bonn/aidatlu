from collections import deque
from enum import StrEnum
import os
import threading
import time
from pathlib import Path
from typing import Any

import numpy as np

from constellation.core.configuration import Configuration
from constellation.core.message.cscp1 import SatelliteState
from constellation.core.monitoring import schedule_metric
from constellation.core.transmitter_satellite import TransmitterSatellite

from aidatlu.hardware.i2c import I2CCore
from aidatlu.main.config_parser import toml_parser
from aidatlu.hardware.tlu_controller import TLUControl, TLUConfigure
from aidatlu.test.utils import MockI2C
import aidatlu.logger as logger


class DUTInterfaceType(StrEnum):
    EUDET = "eudet"
    AIDA = "aida"
    AIDATRIG = "aidatrig"
    OFF = "off"


class TriggerPolarity(StrEnum):
    RISING = "rising"
    FALLING = "falling"


class AidaTLU(TransmitterSatellite):

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.use_mock = os.environ.get("TLU_MOCK")
        self.file_path = Path(__file__).parent

    def do_initializing(self, config: Configuration) -> str:

        configuration = self._read_config(config)

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

        self._init_tlu(configuration)

        return "Initializing complete"

    def do_launching(self, payload: Any = None) -> str:
        self.tlu_controller.reset_counters()
        self.tlu_controller.reset_fifo()
        self.tlu_controller.reset_timestamp()
        self.tlu_configure.configure()
        self.conf_list = self.tlu_configure.get_configuration_table()
        self.tlu_controller.get_event_fifo_fill_level()
        self.tlu_controller.get_event_fifo_csr()
        self.tlu_controller.reset_counters()
        self.tlu_controller.get_scalers()
        return "Do launching complete"

    def do_landing(self) -> str:
        self.tlu_controller.reset_configuration()
        return "Do landing complete"

    def do_reconfigure(self, config: Configuration) -> str:
        configuration = self._read_config(config)
        self._init_tlu(configuration)
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
            func_type = type(self.tlu_controller.get_timestamp)
            self.tlu_controller.get_timestamp = func_type(
                _get_timestamp, self.tlu_controller
            )
            func_type = type(self.tlu_controller.pull_fifo_event)
            self.tlu_controller.pull_fifo_event = func_type(
                _pull_fifo_event, self.tlu_controller
            )

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
        self._pre_veto_rate = 0.0
        self._post_veto_rate = 0.0

        # Set Begin-of-run tags
        self.bor["BoardID"] = self.tlu_controller.get_device_id()

        # For EudaqNativeWriter compatibility
        self.bor["eudaq_event"] = "TluRawDataEvent"
        self.bor["write_as_blocks"] = True

        return "Do starting complete"

    def do_run(self, run_identifier: str) -> str:
        t = threading.Thread(target=self.handle_status)
        t.start()

        # We ideally pull 6 uint32s, but we might pull more or less
        # Thus, add data to a queue and pop in blocks of 6 uint32s
        data_queue = deque()
        while not self._state_thread_evt.is_set():
            evt = self.tlu_controller.pull_fifo_event()
            if np.size(evt) > 1:
                data_queue.extend(evt)
                while len(data_queue) >= 6:
                    self._handle_event([data_queue.popleft() for _ in range(6)])

        t.do_run = False
        return "Do running complete"

    def do_stopping(self) -> str:
        self.tlu_controller.stop_run()
        self.tlu_controller.pull_fifo_event()
        return "Do running complete"

    def _read_config(self, config: Configuration):
        "Reads and checks Constellation configuration"
        config.set_default(
            key="clock_config",
            value=str(
                (self.file_path / ".." / "misc" / "aida_tlu_clk_config.txt").resolve()
            ),
        )
        config.set_default(key="ignore_busy", value=[False, False, False, False])
        config.set_default(key="internal_trigger_rate", value=0)
        config.set_default(key="enable_clock_lemo_output", value=False)
        config.set_default(key="status_interval", value=1.0)
        config.set_default(key="trigger_polarity", value=["falling", "falling", "falling", "falling", "falling", "falling"])

        configuration = {
            "internal_trigger_rate": config.get_int(key="internal_trigger_rate"),
            "dut_interfaces": config.get_array(
                key="dut_interfaces",
                element_type=lambda x: DUTInterfaceType[str(x).upper()].value,
            ),
            "trigger_threshold": config.get_array(
                key="trigger_threshold", element_type=float
            ),
            "trigger_inputs_logic": config.get(key="trigger_inputs_logic"),
            "trigger_polarity": config.get_array(key="trigger_polarity", element_type=str),
            "trigger_signal_stretch": config.get_array(
                key="trigger_signal_stretch", element_type=int
            ),
            "trigger_signal_delay": config.get_array(
                key="trigger_signal_delay", element_type=int
            ),
            "enable_clock_lemo_output": config.get(key="enable_clock_lemo_output"),
            "pmt_power": config.get_array(key="pmt_power", element_type=float),
            "clock_config": config.get_path(key="clock_config", check_exists=True),
            "ignore_busy": config.get_array(key="ignore_busy", element_type=bool),
        }

        self.status_interval = config.get_float("status_interval")
        self.log.debug("Calculating status every %.3f s" % self.status_interval)

        return configuration

    def _init_tlu(self, config: Configuration) -> None:
        "Parse configuration file to TLU and initialize, set loggers"
        self.tlu_config = toml_parser(config, constellation=True)
        self.clock_file = config["clock_config"]
        self.tlu_controller = TLUControl(self.hw, i2c=self.i2c_method)
        self.tlu_controller.write_clock_config(self.clock_file)

        self.tlu_configure = TLUConfigure(self.tlu_controller, self.tlu_config)
        self.tlu_controller.reset_configuration()

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
        data_record = self.new_data_record(meta)
        data_record.add_block(payload)
        self.send_data_record(data_record)

    def handle_status(self) -> None:
        """Status message handling in separate thread. Calculates run time and obtain trigger information and sent it out every second."""
        t = threading.current_thread()
        while getattr(t, "do_run", True):
            time.sleep(0.5)
            last_time = self.tlu_controller.get_timestamp()
            current_time = (last_time - self.start_time) * 25 / 1000000000
            # Calculate and poss. sends status every self.status_interval seconds.
            if current_time - self.last_time > self.status_interval:
                self.check_status(current_time)
                self.log.debug(
                    "Run time: %.1f s, Pre veto: %s, Post veto: %s, Pre veto rate: %.f Hz, Post veto rate.: %.f Hz"
                    % (
                        self.run_time,
                        self.total_pre_veto,
                        self.total_post_veto,
                        self._pre_veto_rate,
                        self._post_veto_rate,
                    )
                )

    def check_status(self, time: int) -> None:
        """Calculates operation status of the TLU run with runtime, pre- and post-veto numbers/rates.
           Also calculates the mean trigger frequency between function calls.

        Args:
            time (int): current runtime of the TLU
        """
        self._post_veto_rate = (
            self.tlu_controller.get_post_veto_trigger_number()
            - self.last_post_veto_trigger
        ) / (time - self.last_time)
        self._pre_veto_rate = (
            self.tlu_controller.get_pre_veto_trigger_number()
            - self.last_pre_veto_trigger
        ) / (time - self.last_time)
        self.run_time = time
        self.total_post_veto = self.tlu_controller.get_post_veto_trigger_number()
        self.total_pre_veto = self.tlu_controller.get_pre_veto_trigger_number()
        s0, s1, s2, s3, s4, s5 = self.tlu_controller.get_scalers()

        self.last_time = time
        self.last_post_veto_trigger = self.tlu_controller.get_post_veto_trigger_number()
        self.last_pre_veto_trigger = self.tlu_controller.get_pre_veto_trigger_number()

        if self.tlu_controller.get_event_fifo_csr() == 0x10:
            self.log.warning("FIFO is full")

    @schedule_metric("Hz", 1)
    def pre_veto_rate(self) -> float | None:
        if self.fsm.state == SatelliteState.RUN:
            return self._pre_veto_rate
        return None

    @schedule_metric("Hz", 1)
    def post_veto_rate(self) -> float | None:
        if self.fsm.state == SatelliteState.RUN:
            return self._post_veto_rate
        return None

    @schedule_metric("", 1)
    def post_veto(self) -> int | None:
        if self.fsm.state == SatelliteState.RUN:
            return self.tlu_controller.get_post_veto_trigger_number()
        return None

    @schedule_metric("", 1)
    def pre_veto(self) -> int | None:
        if self.fsm.state == SatelliteState.RUN:
            return self.tlu_controller.get_pre_veto_trigger_number()
        return None

    @schedule_metric("", 1)
    def sc1(self) -> int | None:
        if self.fsm.state in [SatelliteState.ORBIT, SatelliteState.RUN]:
            return self.tlu_controller.get_scaler(0)
        return None

    @schedule_metric("", 1)
    def sc2(self) -> int | None:
        if self.fsm.state in [SatelliteState.ORBIT, SatelliteState.RUN]:
            return self.tlu_controller.get_scaler(1)
        return None

    @schedule_metric("", 1)
    def sc3(self) -> int | None:
        if self.fsm.state in [SatelliteState.ORBIT, SatelliteState.RUN]:
            return self.tlu_controller.get_scaler(2)
        return None

    @schedule_metric("", 1)
    def sc4(self) -> int | None:
        if self.fsm.state in [SatelliteState.ORBIT, SatelliteState.RUN]:
            return self.tlu_controller.get_scaler(3)
        return None

    @schedule_metric("", 1)
    def sc5(self) -> int | None:
        if self.fsm.state in [SatelliteState.ORBIT, SatelliteState.RUN]:
            return self.tlu_controller.get_scaler(4)
        return None

    @schedule_metric("", 1)
    def sc6(self) -> int | None:
        if self.fsm.state in [SatelliteState.ORBIT, SatelliteState.RUN]:
            return self.tlu_controller.get_scaler(5)
        return None
