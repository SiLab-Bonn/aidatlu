#!/usr/bin/env python3
from typing import Any
from pathlib import Path
import time
import threading

from constellation.core.satellite import Satellite, SatelliteArgumentParser
from constellation.core.configuration import ConfigError, Configuration
from constellation.core.fsm import SatelliteState
from aidatlu.main.tlu import AidaTLU as TLU
from aidatlu.test.utils import MockI2C
from aidatlu.hardware.i2c import I2CCore
from aidatlu import logger
from aidatlu.main.config_parser import toml_parser
from constellation.core.commandmanager import cscp_requestable
from constellation.core.cscp import CSCPMessage
from constellation.core.logging import setup_cli_logging
from constellation.core.monitoring import schedule_metric
from constellation.core.cmdp import MetricsType
from constellation.core.fsm import SatelliteState

TEST = True


class AidaTLU(Satellite):

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

    def do_initializing(self, config: Configuration) -> str:
        self.log.info(
            "Received configuration with parameters: %s",
            ", ".join(config.get_keys()),
        )

        file_path = Path(__file__).parent

        if not TEST:
            import uhal

            uhal.setLogLevelTo(uhal.LogLevel.NOTICE)
            manager = uhal.ConnectionManager(
                "file://" + str(file_path) + "/../misc/aida_tlu_connection.xml"
            )
            hw = uhal.HwInterface(manager.getDevice("aida_tlu.controlhub"))
            I2CMETHOD = I2CCore
        else:
            I2CMETHOD = MockI2C
            hw = None

        clock_path = str(file_path) + "/../misc/aida_tlu_clk_config.txt"

        self.config_file = toml_parser(config, open_toml=False)
        self.clock_file = clock_path
        self.aidatlu = TLU(hw, self.config_file, self.clock_file, i2c=I2CMETHOD)

        # this is stupid is there a better way
        logger._reset_all_loggers()
        self.aidatlu.log = self.log
        self.aidatlu.io_controller.log = self.log
        self.aidatlu.dac_controller.log = self.log
        self.aidatlu.clock_controller.log = self.log
        self.aidatlu.trigger_logic.log = self.log
        self.aidatlu.dut_logic.log = self.log
        return "Initializing complete"

    def do_launching(self, payload: Any = None) -> str:
        self.aidatlu.configure()
        return "Do launching complete"

    def do_landing(self, payload: Any) -> str:
        self.aidatlu.reset_configuration()
        return "Do landing complete"

    def do_reconfigure(self, config: Configuration) -> str:
        file_path = Path(__file__).parent

        if not TEST:
            uhal.setLogLevelTo(uhal.LogLevel.NOTICE)
            manager = uhal.ConnectionManager(
                "file://" + str(file_path) + "/../misc/aida_tlu_connection.xml"
            )
            hw = uhal.HwInterface(manager.getDevice("aida_tlu.controlhub"))
            I2CMETHOD = I2CCore
        else:
            I2CMETHOD = MockI2C
            hw = None

        self.aidatlu = TLU(hw, self.config_file, self.clock_file, i2c=I2CMETHOD)
        logger._reset_all_loggers()
        self.aidatlu.log = self.log
        self.aidatlu.io_controller.log = self.log
        self.aidatlu.dac_controller.log = self.log
        self.aidatlu.clock_controller.log = self.log
        self.aidatlu.trigger_logic.log = self.log
        self.aidatlu.dut_logic.log = self.log
        self.aidatlu.configure()
        return "Do reconfigure complete"

    def do_starting(self, run_identifier: str = None) -> str:
        if TEST:
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

        return "Do starting complete"

    def do_run(self, run_identifier: str) -> str:
        t = threading.Thread(target=self.aidatlu.handle_status)
        t.start()
        while not self._state_thread_evt.is_set():
            self.aidatlu.run_loop()
        t.do_run = False
        self.aidatlu.stop_run()
        return "Do running complete"

    def do_stopping(self) -> str:
        return "Do stopping complete"

    def do_landing(self) -> str:
        return "Do Stop"

    @schedule_metric("Hz", MetricsType.LAST_VALUE, 1)
    def trigger_in_rate(self) -> Any:
        if self.fsm.current_state_value == SatelliteState.RUN and hasattr(
            self.aidatlu, "particle_rate"
        ):
            return self.aidatlu.particle_rate
        else:
            return None

    @schedule_metric("Hz", MetricsType.LAST_VALUE, 1)
    def trigger_out_rate(self) -> Any:
        if self.fsm.current_state_value == SatelliteState.RUN and hasattr(
            self.aidatlu, "hit_rate"
        ):
            return self.aidatlu.hit_rate
        else:
            return None

    @schedule_metric("", MetricsType.LAST_VALUE, 1)
    def trigger_total_trigger_nr(self) -> Any:
        if self.fsm.current_state_value == SatelliteState.RUN and hasattr(
            self.aidatlu, "total_trigger_number"
        ):
            return self.aidatlu.total_trigger_number
        else:
            return None

    @schedule_metric("", MetricsType.LAST_VALUE, 1)
    def sc0(self) -> Any:
        if self.fsm.current_state_value == SatelliteState.ORBIT:
            self.log.debug("sc0: %s" % self.aidatlu.get_scalar(0))
            return self.aidatlu.get_scalar(0)
        else:
            return None

    @schedule_metric("", MetricsType.LAST_VALUE, 1)
    def sc1(self) -> Any:
        if self.fsm.current_state_value == SatelliteState.ORBIT:
            return self.aidatlu.get_scalar(1)
        else:
            return None

    @schedule_metric("", MetricsType.LAST_VALUE, 1)
    def sc2(self) -> Any:
        if self.fsm.current_state_value == SatelliteState.ORBIT:
            return self.aidatlu.get_scalar(2)
        else:
            return None

    @schedule_metric("", MetricsType.LAST_VALUE, 1)
    def sc3(self) -> Any:
        if self.fsm.current_state_value == SatelliteState.ORBIT:
            return self.aidatlu.get_scalar(3)
        else:
            return None

    @schedule_metric("", MetricsType.LAST_VALUE, 1)
    def sc4(self) -> Any:
        if self.fsm.current_state_value == SatelliteState.ORBIT:
            return self.aidatlu.get_scalar(4)
        else:
            return None

    @schedule_metric("", MetricsType.LAST_VALUE, 1)
    def sc5(self) -> Any:
        if self.fsm.current_state_value == SatelliteState.ORBIT:
            return self.aidatlu.get_scalar(5)
        else:
            return None
