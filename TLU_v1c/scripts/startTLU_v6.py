#
# Script to setup AIDA TLU for TPix3 telescope <--> TORCH synchronization
#
# David Cussans, December 2012
#
# Nasty hack - use both PyChips and uHAL ( for block read ... )

from PyChipsUser import *
from FmcTluI2c import *

import uhal

import sys

import time

from datetime import datetime

from optparse import OptionParser

# For single character non-blocking input:
import select
import tty
import termios

from initTLU import *

def isData():
    return select.select([sys.stdin], [], [], 0) == ([sys.stdin], [], [])

now = datetime.now().strftime('%Y-%m-%dT%H_%M_%S')
default_filename = 'tluData_' + now + '.root'
parser = OptionParser()

parser.add_option('-r','--rootFname',dest='rootFname',
                       default=default_filename,help='Path of output file')
parser.add_option('-o','--writeTimestamps',dest='writeTimestamps',
                       default="True",help='Set True to write timestamps to ROOT file')
parser.add_option('-p','--printTimestamps',dest='printTimestamps',
                       default="True",help='Set True to print timestamps to screen (nothing printed unless also output to file) ')
parser.add_option('-s','--listenForTelescopeShutter',dest='listenForTelescopeShutter',
                       default=False,help='Set True to veto triggers when shutter goes high')
parser.add_option('-d','--pulseDelay',dest='pulseDelay', type=int,
                       default=0x00,help='Delay added to input triggers. Four 5-bit numbers packed into 32-bt word, Units of 6.125ns')
parser.add_option('-w','--pulseStretch',dest='pulseStretch',type=int,
                       default=0x00,help='Width added to input triggers. Four 5-bit numbers packed into 32-bt word. Units of 6.125ns')
parser.add_option('-t','--triggerPattern',dest='triggerPattern',type=int,
                       default=0xFFFEFFFE,help='Pattern match to generate trigger. Two 16-bit words packed into 32-bit word.')
parser.add_option('-m','--DUTMask',dest='DUTMask',type=int,
                       default=0x01,help='Three-bit mask selecting which DUTs are active.')
parser.add_option('-y','--ignoreDUTBusy',dest='ignoreDUTBusy',type=int,
                       default=0x0F,help='Three-bit mask selecting which DUTs can veto triggers by setting BUSY high. Low = can veto, high = ignore busy.')
parser.add_option('-i','--triggerInterval',dest='triggerInterval',type=int,
                       default=0,help='Interval between internal trigers ( in units of 6.125ns ). Set to zero to turn off internal triggers')
parser.add_option('-v','--thresholdVoltage',dest='thresholdVoltage',type=float,
                       default=-0.2,help='Threshold voltage for TLU inputs ( units of volts)')

(options, args) = parser.parse_args(sys.argv[1:])

from ROOT import TFile, TTree
from ROOT import gROOT

print "SETTING UP AIDA TLU TO SUPPLY CLOCK AND TRIGGER TO TORCH READOUT\n"

# Point to board in uHAL
manager = uhal.ConnectionManager("file://./connection.xml")
hw = manager.getDevice("minitlu")
device_id = hw.id()

# Point to TLU in Pychips
bAddrTab = AddressTable("./aida_mini_tlu_addr_map.txt")

# Assume DIP-switch controlled address. Switches at 2
board = ChipsBusUdp(bAddrTab,"192.168.200.32",50001)

# Open Root file
print "OPENING ROOT FILE:", options.rootFname
f = TFile( options.rootFname, 'RECREATE' )

# Create a root "tree"
tree = TTree( 'T', 'TLU Data' )
highWord =0
lowWord =0
evtNumber=0
timeStamp=0
evtType=0
trigsFired=0
bufPos = 0

# Create a branch for each piece of data
tree.Branch( 'tluHighWord'  , highWord  , "HighWord/l")
tree.Branch( 'tluLowWord'   , lowWord   , "LowWord/l")
tree.Branch( 'tluTimeStamp' , timeStamp , "TimeStamp/l")
tree.Branch( 'tluBufPos'    , bufPos    , "Bufpos/s")
tree.Branch( 'tluEvtNumber' , evtNumber , "EvtNumber/i")
tree.Branch( 'tluEvtType'   , evtType   , "EvtType/b")
tree.Branch( 'tluTrigFired' , trigsFired, "TrigsFired/b")

# Initialize TLU registers
initTLU( uhalDevice = hw, pychipsBoard = board, listenForTelescopeShutter = options.listenForTelescopeShutter, pulseDelay = options.pulseDelay, pulseStretch = options.pulseStretch, triggerPattern = options.triggerPattern , DUTMask = options.DUTMask, ignoreDUTBusy = options.ignoreDUTBusy , triggerInterval = options.triggerInterval, thresholdVoltage = options.thresholdVoltage )

loopWait = 0.1
oldEvtNumber = 0

oldPreVetotriggerCount = board.read("PreVetoTriggersR")
oldPostVetotriggerCount = board.read("PostVetoTriggersR")

oldThresholdCounter0 =0
oldThresholdCounter1 =0
oldThresholdCounter2 =0
oldThresholdCounter3 =0

print "STARTING POLLING LOOP"

eventFifoFillLevel = 0
loopRunning = True
runStarted = False

oldTime = time.time()

# Save old terminal settings
oldTermSettings = termios.tcgetattr(sys.stdin)
tty.setcbreak(sys.stdin.fileno())

while loopRunning:

    if isData():
        c = sys.stdin.read(1)
        print "\tGOT INPUT:", c
        if c == 't':
            loopRunning = False
            print "\tTERMINATING LOOP"
        elif c == 'c':
            runStarted = True
            print "\tSTARTING RUN"
            startTLU( uhalDevice = hw, pychipsBoard = board,  writeTimestamps = ( options.writeTimestamps == "True" ) )
        elif c == 'f':
            # runStarted = True
            print "\tSTOPPING TRIGGERS"
            stopTLU( uhalDevice = hw, pychipsBoard = board )


    if runStarted:

        eventFifoFillLevel = hw.getNode("eventBuffer.EventFifoFillLevel").read()

        preVetotriggerCount = hw.getNode("triggerLogic.PreVetoTriggersR").read()
        postVetotriggerCount = hw.getNode("triggerLogic.PostVetoTriggersR").read()

        timestampHigh = hw.getNode("Event_Formatter.CurrentTimestampHR").read()
        timestampLow  = hw.getNode("Event_Formatter.CurrentTimestampLR").read()

        thresholdCounter0 = hw.getNode("triggerInputs.ThrCount0R").read()
        thresholdCounter1 = hw.getNode("triggerInputs.ThrCount1R").read()
        thresholdCounter2 = hw.getNode("triggerInputs.ThrCount2R").read()
        thresholdCounter3 = hw.getNode("triggerInputs.ThrCount3R").read()

        hw.dispatch()

        newTime = time.time()
        timeDelta = newTime - oldTime
        oldTime = newTime
        #print "time delta = " , timeDelta
        preVetoFreq = (preVetotriggerCount-oldPreVetotriggerCount)/timeDelta
        postVetoFreq = (postVetotriggerCount-oldPostVetotriggerCount)/timeDelta
        oldPreVetotriggerCount = preVetotriggerCount
        oldPostVetotriggerCount = postVetotriggerCount

        deltaCounts0 = thresholdCounter0 - oldThresholdCounter0
        oldThresholdCounter0 = thresholdCounter0
        deltaCounts1 = thresholdCounter1 - oldThresholdCounter1
        oldThresholdCounter1 = thresholdCounter1
        deltaCounts2 = thresholdCounter2 - oldThresholdCounter2
        oldThresholdCounter2 = thresholdCounter2
        deltaCounts3 = thresholdCounter3 - oldThresholdCounter3
        oldThresholdCounter3 = thresholdCounter3

        print "pre , post  veto triggers , pre , post frequency = " , preVetotriggerCount , postVetotriggerCount , preVetoFreq , postVetoFreq

        print "CURRENT TIMESTAMP HIGH, LOW (hex) = " , hex(timestampHigh) , hex(timestampLow)

        print "Input counts 0,1,2,3 = "      , thresholdCounter0 , thresholdCounter1 , thresholdCounter2 , thresholdCounter3
        print "Input freq (Hz) 0,1,2,3 = " , deltaCounts0/timeDelta , deltaCounts1/timeDelta , deltaCounts2/timeDelta , deltaCounts3/timeDelta

        nEvents = int(eventFifoFillLevel)//4  # only read out whole events ( 4 x 32-bit words )
        wordsToRead =  nEvents*4

        print "FIFO FILL LEVEL= " , eventFifoFillLevel

        print "# EVENTS IN FIFO = ",nEvents
        print "WORDS TO READ FROM FIFO  = ",wordsToRead

        # get timestamp data and fifo fill in same outgoing packet.
        timestampData = hw.getNode("eventBuffer.EventFifoData").readBlock(wordsToRead)

        hw.dispatch()

    #    print timestampData
        for bufPos in range (0, nEvents ):
            lowWord  = timestampData[bufPos*4 + 1] + 0x100000000* timestampData[ (bufPos*4) + 0] # timestamp

            highWord = timestampData[bufPos*4 + 3] + 0x100000000* timestampData[ (bufPos*4) + 2] # evt number
            evtNumber = timestampData[bufPos*4 + 3]

            if evtNumber != ( oldEvtNumber + 1 ):
                print "***WARNING *** Non sqeuential event numbers *** , evt,oldEvt = ",  evtNumber , oldEvtNumber

            oldEvtNumber = evtNumber

            timeStamp = lowWord & 0xFFFFFFFFFFFF

            evtType = timestampData[ (bufPos*4) + 0] >> 28

            trigsFired = (timestampData[ (bufPos*4) + 0] >> 16) & 0xFFF

            if (options.printTimestamps == "True" ):
                print "bufferPos, highWord , lowWord , event-number , timestamp , evtType = %x %016x %016x %08x %012x %01x %03x" % ( bufPos , highWord , lowWord, evtNumber , timeStamp , evtType , trigsFired)

            # Fill root branch - see example in http://wlav.web.cern.ch/wlav/pyroot/tpytree.html : write raw data and decoded data for now.
            tree.Fill()

    time.sleep( loopWait)

# Fixme - at the moment infinite loop.
preVetotriggerCount = board.read("PreVetoTriggersR")
postVetotriggerCount = board.read("PostVetoTriggersR")
print "EXIT POLLING LOOP"
print "\nTRIGGER COUNT AT THE END OF RUN [pre, post]:" , preVetotriggerCount , postVetotriggerCount

termios.tcsetattr(sys.stdin, termios.TCSADRAIN, oldTermSettings)
f.Write()
f.Close()
