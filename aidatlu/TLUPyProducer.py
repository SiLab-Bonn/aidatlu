#! /usr/bin/env python3
# load binary lib/pyeudaq.so
import time

import pyeudaq
import uhal
from main.tlu import AidaTLU
from pyeudaq import EUDAQ_ERROR, EUDAQ_INFO

"""
Example Producer from EUDAQ
This is not well tested. But something like this should work.
Prob. one needs to work a bit on the run loop.

"""


def exception_handler(method):
    def inner(*args, **kwargs):
        try:
            return method(*args, **kwargs)
        except Exception as e:
            EUDAQ_ERROR(str(e))
            raise e

    return inner


class TLUPyProducer(pyeudaq.Producer):
    def __init__(self, name, runctrl):
        pyeudaq.Producer.__init__(self, name, runctrl)

        self.is_running = 0
        EUDAQ_INFO("New instance of TLUPyProducer")

    @exception_handler
    def DoInitialise(self):
        EUDAQ_INFO("DoInitialise")
        uhal.setLogLevelTo(uhal.LogLevel.NOTICE)
        manager = uhal.ConnectionManager("file://./misc/aida_tlu_connection.xml")
        hw = uhal.HwInterface(manager.getDevice("aida_tlu.controlhub"))

        self.tlu = AidaTLU(hw)
        # print 'key_a(init) = ', self.GetInitItem("key_a")

    @exception_handler
    def DoConfigure(self):
        EUDAQ_INFO("DoConfigure")
        self.tlu.configure()
        # print 'key_b(conf) = ', self.GetConfigItem("key_b")

    @exception_handler
    def DoStartRun(self):
        EUDAQ_INFO("DoStartRun")
        self.tlu.run()
        self.is_running = 1

    @exception_handler
    def DoStopRun(self):
        EUDAQ_INFO("DoStopRun")
        self.tlu.stop_run()
        self.is_running = 0

    @exception_handler
    def DoReset(self):
        EUDAQ_INFO("DoReset")
        self.tlu.reset_configuration()
        self.is_running = 0

    @exception_handler
    def RunLoop(self):
        EUDAQ_INFO("Start of RunLoop in TLUPyProducer")
        trigger_n = 0
        # TODO here the Run loop from the tlu is probably needed
        while self.is_running:
            ev = pyeudaq.Event("RawEvent", "sub_name")
            ev.SetTriggerN(trigger_n)
            # block = bytes(r'raw_data_string')
            # ev.AddBlock(0, block)
            # print ev
            # Mengqing:
            datastr = "raw_data_string"
            block = bytes(datastr, "utf-8")
            ev.AddBlock(0, block)
            # print(ev)

            self.SendEvent(ev)
            trigger_n += 1
            time.sleep(1)
        EUDAQ_INFO("End of RunLoop in TLUPyProducer")


if __name__ == "__main__":
    myproducer = TLUPyProducer("AIDA_TLU", "tcp://localhost:44000")
    print(
        "connecting to runcontrol in localhost:44000",
    )
    myproducer.Connect()
    time.sleep(2)
    while myproducer.IsConnected():
        time.sleep(1)
