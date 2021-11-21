#
# Script to exercise AIDA mini-TLU
#
# David Cussans, December 2012
# 
# Nasty hack - use both PyChips and uHAL ( for block read ... )

from PyChipsUser import *
from FmcTluI2c import *

import sys
import time


# Point to TLU in Pychips
bAddrTab = AddressTable("./aida_mini_tlu_addr_map.txt")
# Assume DIP-switch controlled address. Switches at 2 
board = ChipsBusUdp(bAddrTab,"192.168.200.32",50001)

# Check the bus for I2C devices
boardi2c = FmcTluI2c(board)

firmwareID=board.read("FirmwareId")

print "Firmware (from PyChips) = " , hex(firmwareID)

print "Scanning I2C bus:"
scanResults = boardi2c.i2c_scan()
print scanResults

boardId = boardi2c.get_serial_number()
print "FMC-TLU serial number = " , boardId

resetClocks = 0
 


clockStatus = board.read("LogicClocksCSR")
print "Clock status = " , hex(clockStatus)

if resetClocks:
    print "Resetting clocks"
    board.write("LogicRst", 1 )

    clockStatus = board.read("LogicClocksCSR")
    print "Clock status after reset = " , hex(clockStatus)


board.write("InternalTriggerIntervalW",0)

print "Enabling DUT 0 and 1"
board.write("DUTMaskW",3)
DUTMask = board.read("DUTMaskR")
print "DUTMaskR = " , DUTMask

print "Ignore veto on DUT 0 and 1"
board.write("IgnoreDUTBusyW",3)
IgnoreDUTBusy = board.read("IgnoreDUTBusyR")
print "IgnoreDUTBusyR = " , IgnoreDUTBusy

print "Turning off software trigger veto"
board.write("TriggerVetoW",0)

print "Reseting FIFO"
board.write("EventFifoCSR",0x2)
eventFifoFillLevel = board.read("EventFifoFillLevel")
print "FIFO fill level after resetting FIFO = " , eventFifoFillLevel

print "Enabling data recording"
board.write("Enable_Record_Data",1)

#print "Enabling handshake: No-handshake"
#board.write("HandshakeTypeW",1)

#TriggerInterval = 400000
TriggerInterval = 0
print "Setting internal trigger interval to " , TriggerInterval
board.write("InternalTriggerIntervalW",TriggerInterval)  #0->Internal pulse generator disabled. Any other value will generate pulses with a frequency of n*6.25ns
trigInterval = board.read("InternalTriggerIntervalR")
print "Trigger interval read back as ", trigInterval

print "Setting TPix_maskexternal to ignore external shutter and T0"
board.write("TPix_maskexternal",0x0003)

numLoops = 500000
oldEvtNumber = 0

for iLoop in range(0,numLoops):

    board.write("TPix_T0", 0x0001)

#   time.sleep( 1.0)
