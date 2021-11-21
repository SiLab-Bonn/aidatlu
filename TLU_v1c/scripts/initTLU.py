#
# Function to initialize TLU
#
# David Cussans, October 2015
#
# Nasty hack - use both PyChips and uHAL ( for block read ... )

from PyChipsUser import *
from FmcTluI2c import *

import uhal

import sys
import time

def startTLU( uhalDevice , pychipsBoard , writeTimestamps):

    print "RESETTING FIFO"
    pychipsBoard.write("EventFifoCSR",0x2)
    eventFifoFillLevel = pychipsBoard.read("EventFifoFillLevel")
    print "FIFO FILL LEVEL AFTER RESET= " , eventFifoFillLevel


    if writeTimestamps:
        print "ENABLING DATA RECORDING"
        pychipsBoard.write("Enable_Record_Data",1)
    else:
        print "Disabling data recording"
        pychipsBoard.write("Enable_Record_Data",0)

    print "Pulsing T0"
    pychipsBoard.write("PulseT0",1)

    print "Turning off software trigger veto"
    pychipsBoard.write("TriggerVetoW",0)

    print "TLU is running"


def stopTLU( uhalDevice , pychipsBoard ):

    print "Turning on software trigger veto"
    pychipsBoard.write("TriggerVetoW",1)

    print "TLU triggers are stopped"

def initTLU( uhalDevice , pychipsBoard , listenForTelescopeShutter , pulseDelay , pulseStretch , triggerPattern , DUTMask , ignoreDUTBusy , triggerInterval , thresholdVoltage ):

    print "SETTING UP AIDA TLU"

    fwVersion = uhalDevice.getNode("version").read()
    uhalDevice.dispatch()
    print "\tVersion (uHAL)= " , hex(fwVersion)

    print "\tTurning on software trigger veto"
    pychipsBoard.write("TriggerVetoW",1)

    # Check the bus for I2C devices
    pychipsBoardi2c = FmcTluI2c(pychipsBoard)

    print "\tScanning I2C bus:"
    scanResults = pychipsBoardi2c.i2c_scan()
    #print scanResults
    print '\t', ', '.join(scanResults), '\n'

    boardId = pychipsBoardi2c.get_serial_number()
    print "\tFMC-TLU serial number= " , boardId

    resetClocks = 0
    resetSerdes = 0

# set DACs to -200mV
    print "\tSETTING ALL DAC THRESHOLDS TO" , thresholdVoltage , "V"
    pychipsBoardi2c.set_threshold_voltage(7, thresholdVoltage)

    clockStatus = pychipsBoard.read("LogicClocksCSR")
    print "\tCLOCK STATUS (should be 3 if all clocks locked)= " , hex(clockStatus)
    assert ( clockStatus == 3 ) , "Clocks in TLU FPGA are not locked. No point in continuing. Re-prgramme or power cycle board"

    if resetClocks:
        print "Resetting clocks"
        pychipsBoard.write("LogicRst", 1 )

        clockStatus = pychipsBoard.read("LogicClocksCSR")
        print "Clock status after reset = " , hex(clockStatus)

        inputStatus = pychipsBoard.read("SerdesRstR")
        print "Input status = " , hex(inputStatus)

    if resetSerdes:
        pychipsBoard.write("SerdesRstW", 0x00000003 )
        inputStatus = pychipsBoard.read("SerdesRstR")
        print "Input status during reset = " , hex(inputStatus)

        pychipsBoard.write("SerdesRstW", 0x00000000 )
        inputStatus = pychipsBoard.read("SerdesRstR")
        print "Input status after reset = " , hex(inputStatus)

        pychipsBoard.write("SerdesRstW", 0x00000004 )
        inputStatus = pychipsBoard.read("SerdesRstR")
        print "Input status during calibration = " , hex(inputStatus)

        pychipsBoard.write("SerdesRstW", 0x00000000 )
        inputStatus = pychipsBoard.read("SerdesRstR")
        print "Input status after calibration = " , hex(inputStatus)


    inputStatus = pychipsBoard.read("SerdesRstR")
    print "\tINPUT STATUS= " , hex(inputStatus)

    count0 = pychipsBoard.read("ThrCount0R")
    print "\t  Count 0= " , count0

    count1 = pychipsBoard.read("ThrCount1R")
    print "\t  Count 1= " , count1

    count2 = pychipsBoard.read("ThrCount2R")
    print "\t  Count 2= " , count2

    count3 = pychipsBoard.read("ThrCount3R")
    print "\t  Count 3= " , count3

# Stop internal triggers until setup complete
    pychipsBoard.write("InternalTriggerIntervalW",0)

    print "\tSETTING INPUT COINCIDENCE WINDOW TO",pulseStretch,"[Units= 160MHz clock cycles, Four 5-bit values (one per input) packed in to 32-bit word]"
    pychipsBoard.write("PulseStretchW",int(pulseStretch))
    pulseStretchR = pychipsBoard.read("PulseStretchR")
    print "\t  Pulse stretch read back as:", hex(pulseStretchR)
 #   assert (int(pulseStretch) == pulseStretchR) , "Pulse stretch read-back doesn't equal written value"

    print "\tSETTING INPUT TRIGGER DELAY TO",pulseDelay , "[Units= 160MHz clock cycles, Four 5-bit values (one per input) packed in to 32-bit word]"
    pychipsBoard.write("PulseDelayW",int(pulseDelay))
    pulseDelayR = pychipsBoard.read("PulseDelayR")
    print "\t  Pulse delay read back as:", hex(pulseDelayR)

    print "\tSETTING TRIGGER PATTERN (for external triggers) TO 0x%08X. Two 16-bit patterns packed into 32 bit word  " %(triggerPattern)
    pychipsBoard.write("TriggerPatternW",int(triggerPattern))
    triggerPatternR = pychipsBoard.read("TriggerPatternR")
    print "\t  Trigger pattern read back as: 0x%08X " % (triggerPatternR)

    print "\tENABLING DUT(s): Mask= " , hex(DUTMask)
    pychipsBoard.write("DUTMaskW",int(DUTMask))
    DUTMaskR = pychipsBoard.read("DUTMaskR")
    print "\t  DUTMask read back as:" , hex(DUTMaskR)

    print "\tSETTING ALL DUTs IN AIDA MODE"
    pychipsBoard.write("DUTInterfaceModeW", 0xFF)
    DUTInterfaceModeR = pychipsBoard.read("DUTInterfaceModeR")
    print "\t  DUT mode read back as:" , DUTInterfaceModeR

    print "\tSET DUT MODE MODIFIER"
    pychipsBoard.write("DUTInterfaceModeModifierW", 0xFF)
    DUTInterfaceModeModifierR = pychipsBoard.read("DUTInterfaceModeModifierR")
    print "\t  DUT mode modifier read back as:" , DUTInterfaceModeModifierR

    if listenForTelescopeShutter:
        print "\tSET IgnoreShutterVetoW TO LISTEN FOR VETO FROM SHUTTER"
        pychipsBoard.write("IgnoreShutterVetoW",0)
    else:
        print "\tSET IgnoreShutterVetoW TO IGNORE VETO FROM SHUTTER"
        pychipsBoard.write("IgnoreShutterVetoW",1)
    IgnoreShutterVeto = pychipsBoard.read("IgnoreShutterVetoR")
    print "\t  IgnoreShutterVeto read back as:" , IgnoreShutterVeto

    print "\tSETTING IGNORE VETO BY DUT BUSY MASK TO" , hex(ignoreDUTBusy)
    pychipsBoard.write("IgnoreDUTBusyW",int(ignoreDUTBusy))
    IgnoreDUTBusy = pychipsBoard.read("IgnoreDUTBusyR")
    print "\t  IgnoreDUTBusy read back as:" , hex(IgnoreDUTBusy)

#print "Enabling handshake: No-handshake"
#board.write("HandshakeTypeW",1)


    print "\tSETTING INTERNAL TRIGGER INTERVAL TO" , triggerInterval , "(zero= no internal triggers)"
    if triggerInterval == 0:
        internalTriggerFreq = 0
    else:
        internalTriggerFreq = 160000.0/triggerInterval
    print "\tINTERNAL TRIGGER FREQUENCY= " , internalTriggerFreq , " kHz"
    pychipsBoard.write("InternalTriggerIntervalW",triggerInterval)  #0->Internal pulse generator disabled. Any other value will generate pulses with a frequency of n*6.25ns
    trigIntervalR = pychipsBoard.read("InternalTriggerIntervalR")
    print "\t  Trigger interval read back as:", trigIntervalR
    print "AIDA TLU SETUP COMPLETED"
