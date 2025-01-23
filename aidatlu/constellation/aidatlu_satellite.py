#!/usr/bin/env python3
from typing import Any, Tuple
from pathlib import Path
import uhal
import threading

from constellation.core.satellite import Satellite, SatelliteArgumentParser
from constellation.core.configuration import ConfigError, Configuration
from constellation.core.fsm import SatelliteState
from aidatlu.main.tlu import AidaTLU
from constellation.core.commandmanager import cscp_requestable
from constellation.core.cscp import CSCPMessage
from constellation.core.base import setup_cli_logging


class AidaTLuSatellite(Satellite):

    def do_initializing(self, config: Configuration) -> str:
        self.log.info(
            "Received configuration with parameters: %s",
            ", ".join(config.get_keys()),
        )

        file_path = Path(__file__).parent

        uhal.setLogLevelTo(uhal.LogLevel.NOTICE)
        manager = uhal.ConnectionManager(
            "file://" + str(file_path) + "/../misc/aida_tlu_connection.xml"
        )
        hw = uhal.HwInterface(manager.getDevice("aida_tlu.controlhub"))

        clock_path = str(file_path) + "/../misc/aida_tlu_clk_config.txt"
        config_path = str(file_path) + "/../tlu_configuration.yaml"

        self.config_file = config_path
        self.clock_file = clock_path
        self.ready = False
        self.aidatlu = AidaTLU(hw, self.config_file, self.clock_file)

    def do_launching(self, payload: Any = None) -> str:
        self.aidatlu.configure()
        return "Do launching complete"

    def do_landing(self, payload: Any) -> str:
        self.aidatlu.reset_configuration()
        return "Do landing complete"

    def do_reconfigure(self, config: Configuration) -> str:
        file_path = Path(__file__).parent

        uhal.setLogLevelTo(uhal.LogLevel.NOTICE)
        manager = uhal.ConnectionManager(
            "file://" + str(file_path) + "/../misc/aida_tlu_connection.xml"
        )
        hw = uhal.HwInterface(manager.getDevice("aida_tlu.controlhub"))

        self.aidatlu = AidaTLU(hw, self.config_file, self.clock_file)
        self.aidatlu.configure()
        return "Do reconfigure complete"

    def do_starting(self, run_identifier: str = None) -> str:
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
        self.aidatlu.stopping()
        return "Do stopping complete"

    def do_landing(self) -> str:
        return "Do Stop"


def main(args=None):

    parser = SatelliteArgumentParser(
        description=main.__doc__,
        epilog="This is a 3rd-party component of Constellation.",
    )
    parser.set_defaults(name="aidatlu")
    args = vars(parser.parse_args(args))

    setup_cli_logging(args["name"], args.pop("log_level"))

    s = AidaTLuSatellite(**args)
    s.run_satellite()
