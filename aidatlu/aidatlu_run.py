import os
import time
import argparse
from pathlib import Path

import uhal
from aidatlu.main.tlu import AidaTLU
from aidatlu.main.config_parser import yaml_parser
import aidatlu.logger as logger
from aidatlu.test.utils import MockI2C
from aidatlu.hardware.i2c import I2CCore


FILEPATH = Path(__file__).parent


class AIDATLU:
    def __init__(self, config_path, clock_path):
        print(r"----------------------------------------")
        print(r"    _   ___ ___   _     _____ _   _   _ ")
        print(r"   /_\ |_ _|   \ /_\   |_   _| | | | | |")
        print(r"  / _ \ | || |) / _ \ -- | | | |_| |_| |")
        print(r" /_/ \_\___|___/_/ \_\   |_| |____\___/ ")
        print(r"                                        ")
        print(r"----------------------------------------")

        self.config_file = config_path
        self.clock_file = clock_path
        self.ready = False

    def run(self):
        if not self.ready:
            print("TLU not configured, Run aborted")
        else:
            if self.MOCK:
                start_time = time.time()

                def _get_timestamp(self):
                    # Helper function returns timestamp
                    return (time.time() - start_time) / 25 * 1000000000

                def _pull_fifo_event(self):
                    # Blank FIFO pull helper function
                    return 0

                # Overwrite TLU methods needed for run loop
                func_type = type(self.aidatlu.tlu_controller.get_timestamp)
                self.aidatlu.tlu_controller.get_timestamp = func_type(
                    _get_timestamp, self.aidatlu.tlu_controller
                )
                func_type = type(self.aidatlu.tlu_controller.pull_fifo_event)
                self.aidatlu.tlu_controller.pull_fifo_event = func_type(
                    _pull_fifo_event, self.aidatlu.tlu_controller
                )
            self.aidatlu.run()

    def stop(self):
        self.aidatlu.stop_run()

    def configure(self):
        self.ready = True
        self.init()
        self.aidatlu.configure()

    def init(self):
        conf_dict = yaml_parser(self.config_file)
        try:
            self.MOCK = os.environ["TEST"] == "True"
            I2CMETHOD = MockI2C
            hw = None
        except KeyError:
            self.MOCK = False
            I2CMETHOD = I2CCore
            uhal.setLogLevelTo(uhal.LogLevel.NOTICE)
            manager = uhal.ConnectionManager(
                "file://" + str(FILEPATH) + "/misc/aida_tlu_connection.xml"
            )
            hw = uhal.HwInterface(manager.getDevice("aida_tlu.controlhub"))

        self.aidatlu = AidaTLU(hw, conf_dict, self.clock_file, i2c=I2CMETHOD)

    def help(self):
        print("tlu.configure()")
        print("start run: tlu.run()")
        print("stop  run: ctr+c")
        print("exit:      ctr+d/exit()\n")
        print("for access to the main tlu functions: tlu.aidatlu....")


def start():
    parser = argparse.ArgumentParser(
        prog="aidatlu",
        description="Control the 2020-Aida-TLU using a Python based interface.",
    )
    parser.add_argument(
        "-c", "--config", type=str, help="Path to configuration yaml", nargs="*"
    )
    args = vars(parser.parse_args())

    config_path = args["config"][0]
    clock_path = str(FILEPATH) + "/misc/aida_tlu_clk_config.txt"

    logger.setup_main_logger(name="AIDA-TLU", level="INFO")
    tlu = AIDATLU(config_path, clock_path)
    tlu.configure()
    tlu.run()


if __name__ == "__main__":
    config_path = "tlu_configuration.yaml"
    clock_path = "misc/aida_tlu_clk_config.txt"

    logger.setup_main_logger(name="AIDA-TLU", level="INFO")
    tlu = AIDATLU(config_path, clock_path)

    print("tlu.help()")
