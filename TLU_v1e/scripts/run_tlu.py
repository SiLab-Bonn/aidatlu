import time

from config_parser import ConfigParser
from TLU_v1e import TLU

conf = ConfigParser(filename="/home/silab/git/aida-tlu/TLU_v1e/scripts/localIni.ini")
configure_conf = ConfigParser(filename="/home/silab/git/aida-tlu/TLU_v1e/scripts/localConf.conf")
t = TLU(dev_name='tlu', man_file='file:///home/silab/git/aida-tlu/TLU_v1e/scripts/TLUconnection.xml', parsed_cfg=conf)
t.configure(configure_conf)
t.start()
t.isRunning = True
try:
    while (t.isRunning == True):
        eventFifoFillLevel= t.getFifoLevel(0)
        nFifoWords= int(eventFifoFillLevel)
        if (nFifoWords > 0):
            fifoData= t.getFifoData(nFifoWords)
            print(fifoData)
        time.sleep(1)
except KeyboardInterrupt:
    t.isRunning = False
t.stop()
