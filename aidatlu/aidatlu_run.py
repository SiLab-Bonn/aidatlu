import uhal
from main.tlu import AidaTLU
from main.config_parser import yaml_parser


class AIDATLU:
    def __init__(self, config_path, clock_path):
        print(r"----------------------------------------")
        print(r"    _   ___ ___   _     _____ _   _   _ ")
        print(r"   /_\ |_ _|   \ /_\   |_   _| | | | | |")
        print(r"  / _ \ | || |) / _ \ -- | | | |_| |_| |")
        print(r" /_/ \_\___|___/_/ \_\   |_| |____\___/ ")
        print(r"                                        ")
        print(r"----------------------------------------")
        print("tlu.help()\n")

        self.config_file = config_path
        self.clock_file = clock_path
        self.ready = False

    def run(self):
        if not self.ready:
            print("TLU not configured, Run aborted")
        else:
            self.aidatlu.run()

    def stop(self):
        self.aidatlu.stop_run()

    def configure(self):
        self.ready = True
        self.init()
        self.aidatlu.configure()

    def init(self):
        conf_dict = yaml_parser(self.config_file)
        self.aidatlu = AidaTLU(hw, conf_dict, self.clock_file)

    def help(self):
        print("tlu.configure()")
        print("start run: tlu.run()")
        print("stop  run: ctr+c")
        print("exit:      ctr+d/exit()\n")
        print("for access to the main tlu functions: tlu.aidatlu....")


if __name__ == "__main__":
    uhal.setLogLevelTo(uhal.LogLevel.NOTICE)
    manager = uhal.ConnectionManager("file://./misc/aida_tlu_connection.xml")
    hw = uhal.HwInterface(manager.getDevice("aida_tlu.controlhub"))

    config_path = "tlu_configuration.yaml"
    clock_path = "misc/aida_tlu_clk_config.txt"

    tlu = AIDATLU(config_path, clock_path)

    # Uncomment if you just want to use EUDET mode and just plug and play TLU.
    # tlu.configure
    # tlu.run
