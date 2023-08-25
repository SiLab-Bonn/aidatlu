
from main.tlu import AidaTLU
import uhal

class AIDATLU():
    def __init__(self, config_path, clock_path):
        print(' ---------------------------------------')
        print("    _   ___ ___   _     _____ _   _   _ ")
        print("   /_\ |_ _|   \ /_\   |_   _| | | | | |")
        print("  / _ \ | || |) / _ \    | | | |_| |_| |")
        print(" /_/ \_\___|___/_/ \_\   |_| |____\___/ \n")
        print(' ---------------------------------------')
        print('tlu.help\n')

        self.cfile = config_path
        self.clock = clock_path

    @property
    def run(self):
        self.aidatlu.run()

    @property
    def stop(self):
        self.aidatlu.stop_run()

    @property
    def configure(self):
        self.init
        self.aidatlu.configure()

    @property
    def init(self):
        self.aidatlu = AidaTLU(hw, self.cfile , self.clock)

    @property
    def help(self):
        print('tlu.configure')
        print('start run: tlu.run')
        print('stop  run: ctr+c')
        print('exit:      ctr+d/exit()')

if __name__ == '__main__':
    uhal.setLogLevelTo(uhal.LogLevel.NOTICE)
    manager = uhal.ConnectionManager("file://./misc/aida_tlu_connection.xml")
    hw = uhal.HwInterface(manager.getDevice("aida_tlu.controlhub"))

    clock_path = 'misc/aida_tlu_clk_config.txt'
    config_path = 'conf.yaml'

    tlu = AIDATLU(config_path, clock_path)
    