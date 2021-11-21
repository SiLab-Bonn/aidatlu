import uhal;
from FmcTluI2c import *
from I2CuHal import I2CCore

class MiniTLU:
    """docstring for miniTLU"""
    def __init__(self, dev_name, man_file):
        self.dev_name = dev_name
        self.manager= uhal.ConnectionManager(man_file)
        self.hw = self.manager.getDevice(self.dev_name)
        self.nChannels= 4
        self.VrefInt= 2.5 #Internal DAC voltage reference
        self.VrefExt= 1.3 #External DAC voltage reference
        self.intRefOn= False #Internal reference is OFF by default

        self.fwVersion = self.hw.getNode("version").read()
        self.hw.dispatch()
        print "uHAL VERSION= " , hex(self.fwVersion)

        # Instantiate a I2C core to configure the DACs
        self.TLU_I2C= I2CCore(self.hw, 10, 5, "i2c_master", None)
        self.TLU_I2C.state()


    def initialize(self):
        print "miniTLU INITIALIZING..."
        # We need to pass it listenForTelescopeShutter , pulseDelay , pulseStretch , triggerPattern , DUTMask , ignoreDUTBusy , triggerInterval , thresholdVoltage

        print "\tTurning on software trigger veto"
        cmd = int("0x1",16)
        self.setTriggerVetoStatus(cmd)

        #READ CONTENT OF EPROM VIA I2C
        self.getSN()

        #SET DACs
        targetV= 1.1
        intRef= False
        self.setDACintRef(intRef)
        DACchannel= 7
        self.writeThreshold(targetV, DACchannel)

        #Check clock status
        self.checkClkStatus()

        resetClocks = 0
        resetSerdes = 0
        if resetClocks:
            self.resetClocks()
        if resetSerdes:
            self.resetSerdes()

        # Get inputs status and counters
        self.getChStatus()
        self.getAllChannelsCounts()

        # Stop internal triggers until setup complete
        cmd = int("0x0",16)
        self.setInternalTrg(cmd)

        # Set pulse stretch
        pulseStretch= 0x000FFFFF
        self.setPulseStretch(pulseStretch)

        # Set pulse delay
        pulseDelay= 0x0
        #self.setPulseDelay(pulseDelay) #NEED TO FIX ADDRESS TABLE

        # Set trigger pattern
        triggerPattern= 0x0
        self.setTrgPattern(triggerPattern)

        # Set DUTs
        DUTMask= 0x1
        self.setDUTmask(DUTMask)

        # # Set mode
        DUTMode= 0x0
        self.setMode(DUTMode)

        # # Set modifier
        modifier = int("0xFF",16) 
        self.setModeModifier(modifier)

        # Set veto shutter
        setVetoShutters=0
        self.setVetoShutters(setVetoShutters)

        # Set veto by DUT
        ignoreDUTBusy=0x0
        self.setVetoDUT(ignoreDUTBusy)

        # Set trigger interval (use 0 to disable internal triggers)
        triggerInterval=0
        self.setInternalTrg(triggerInterval)

        print "miniTLU INITIALIZED"

    def setModeModifier(self, modifier):
        print "\tDUT MODE MODIFIER:",modifier
        self.hw.getNode("DUTInterfaces.DUTInterfaceModeModifierW").write(modifier)
        self.hw.dispatch()
        self.getModeModifier()

    def getModeModifier(self):
        DUTInterfaceModeModifierR = self.hw.getNode("DUTInterfaces.DUTInterfaceModeModifierR").read()
        self.hw.dispatch()
        print "\t  DUT mode modifier read back as:" , hex(DUTInterfaceModeModifierR)
        return DUTInterfaceModeModifierR

    def resetClock(self):
        print "\tClocks reset"
        cmd = int("0x1",16)
        self.hw.getNode("logic_clocks.LogicRst").write(cmd)
        self.hw.dispatch()

    def getClockStatus(self):
        clockStatus = self.hw.getNode("logic_clocks.LogicClocksCSR").read()
        self.hw.dispatch()
        print "\t  Clock status=" , hex(clockStatus)
        return clockStatus

    def readEEPROM(self, startadd, bytes):
        mystop= 1
        time.sleep(0.1)
        myaddr= [startadd]#0xfa
        self.TLU_I2C.write( 0x50, [startadd], mystop)
        res= self.TLU_I2C.read( 0x50, bytes)
        return res

    def getSN(self):
        epromcontent=self.readEEPROM(0xfa, 6)
        print "\tFMC-TLU serial number (EEPROM):"
        result="\t  "
        for iaddr in epromcontent:
            result+="%02x "%(iaddr)
        print result
        return epromcontent

    def writeThreshold(self, Vtarget, channel):
        #Writes the threshold. The DAC voltage differs from the threshold voltage because
        #the range is shifted to be symmetrical around 0V.

        #Check if the DACs are using the internal reference
        if (self.intRefOn):
            Vref= self.VrefInt
        else:
            Vref= self.VrefExt

        #Calculate offset voltage (because of the following shifter)
        Vdac= ( Vtarget + Vref ) / 2
        print"\tTHRESHOLD setting:"
        if channel==7:
            print "\t  CH: ALL"
        else:
            print "\t  CH:", channel
        print "\t  Target V:", Vtarget
        dacValue = 0xFFFF * Vtarget / Vref
        self.writeDAC(int(dacValue), channel)

    def writeDAC(self, dacCode, channel):
        #Vtarget is the required voltage, channel is the DAC channel to target
        #intRef indicates whether to use the external voltage reference (True)
        #or the internal one (False).

        i2cSlaveAddrDac = 0x1F

        print "\t  DAC value:"  , dacCode
        if channel<0 or channel>7:
            print "writeDAC ERROR: channel",channel,"not in range 0-7 (bit mask)"
            ##return -1
        if dacCode<0:
            print "writeDAC ERROR: value",dacCode,"<0. Default to 0"
            dacCode=0
        elif dacCode>0xFFFF :
            print "writeDAC ERROR: value",dacCode,">0xFFFF. Default to 0xFFFF"
            dacCode=0xFFFF

        sequence=[( 0x18 + ( channel &0x7 ) ) , int(dacCode/256)&0xff , int(dacCode)&0xff]
        print "\t  Writing DAC string:", sequence
        self.TLU_I2C.write( i2cSlaveAddrDac, sequence, 0)

    # def readDAC(self, channel):
    #     #TO BE DONE
    #     i2cSlaveAddrDac = 0x1F
    #     bytes= 3
    #     if channel<0 or channel>7:
    #         print "writeDAC ERROR: channel",channel,"not in range 0-7 (bit mask)"
    #         ##return -1
    #     cmdDAC=[( 0x18 + ( channel &0x7 ) ) ]
    #     self.TLU_I2C.write( i2cSlaveAddrDac, cmdDAC, 0)
    #     res= self.TLU_I2C.read( i2cSlaveAddrDac, bytes)
    #     print res

    def setDACintRef(self, intRef=False):
        i2cSlaveAddrDac = 0x1F
        self.intRefOn= intRef
        if intRef:
            print "\tDAC internal reference ON"
            cmdDAC= [0x38,0x00,0x01]
        else:
            print "\tDAC internal reference OFF"
            cmdDAC= [0x38,0x00,0x00]
        self.TLU_I2C.write( i2cSlaveAddrDac, cmdDAC, 0)

    # def getDACintRef(self):
    #     #TO BE FIXED!
    #     bytes= 3
    #     i2cSlaveAddrDac = 0x1F
    #     cmdDAC= [0x78]
    #     self.TLU_I2C.write( i2cSlaveAddrDac, cmdDAC, 0)
    #     res= self.TLU_I2C.read( i2cSlaveAddrDac, bytes)
    #     print res

    def setTrgPattern(self, triggerPattern):
        triggerPattern &= 0xffffffff
        print "\tTRIGGER PATTERN (for external triggers) SET TO 0x%08X. Two 16-bit patterns packed into 32 bit word  " %(triggerPattern)
        self.hw.getNode("triggerLogic.TriggerPatternW").write(triggerPattern)
        self.hw.dispatch()
        self.getTrgPattern()

    def getTrgPattern(self):
        triggerPatternR = self.hw.getNode("triggerLogic.TriggerPatternR").read()
        self.hw.dispatch()
        print "\t  Trigger pattern read back as: 0x%08X " % (triggerPatternR)
        return triggerPatternR

    def setDUTmask(self, DUTMask):
        print "\tDUT MASK ENABLING: Mask= " , hex(DUTMask)
        self.hw.getNode("DUTInterfaces.DutMaskW").write(DUTMask)
        self.hw.dispatch()
        self.getDUTmask()

    def getDUTmask(self):
        DUTMaskR = self.hw.getNode("DUTInterfaces.DutMaskR").read()
        self.hw.dispatch()
        print "\t  DUTMask read back as:" , hex(DUTMaskR)
        return DUTMaskR

    def setVetoShutters(self, newState):
        if newState:
            print "\tIgnoreShutterVetoW SET TO LISTEN FOR VETO FROM SHUTTER"
            cmd= int("0x0",16)
        else:
            print "\tIgnoreShutterVetoW SET TO IGNORE VETO FROM SHUTTER"
            cmd= int("0x1",16)
        self.hw.getNode("DUTInterfaces.IgnoreShutterVetoW").write(cmd)
        self.hw.dispatch()
        self.getVetoShutters()

    def getVetoShutters(self):
        IgnoreShutterVeto = self.hw.getNode("DUTInterfaces.IgnoreShutterVetoR").read()
        self.hw.dispatch()
        print "\t  IgnoreShutterVeto read back as:" , IgnoreShutterVeto
        return IgnoreShutterVeto

    def setVetoDUT(self, ignoreDUTBusy):
        print "\tVETO IGNORE BY DUT BUSY MASK SET TO" , hex(ignoreDUTBusy)
        self.hw.getNode("DUTInterfaces.IgnoreDUTBusyW").write(ignoreDUTBusy)
        self.hw.dispatch()
        self.getVetoDUT()

    def getVetoDUT(self):
        IgnoreDUTBusyR = self.hw.getNode("DUTInterfaces.IgnoreDUTBusyR").read()
        self.hw.dispatch()
        print "\t  IgnoreDUTBusy read back as:" , hex(IgnoreDUTBusyR)
        return IgnoreDUTBusyR

    def setInternalTrg(self, triggerInterval):
        print "\tTRIGGERS INTERNAL:"
        if triggerInterval == 0:
            internalTriggerFreq = 0
            print "\t  disabled"
        else:
            internalTriggerFreq = 160000.0/triggerInterval
            print "\t  Setting:", internalTriggerFreq, "Hz"
        self.hw.getNode("triggerLogic.InternalTriggerIntervalW").write(int(internalTriggerFreq))
        self.hw.dispatch()
        self.getInternalTrg()

    def getInternalTrg(self):
        trigIntervalR = self.hw.getNode("triggerLogic.InternalTriggerIntervalR").read()
        self.hw.dispatch()
        print "\t  Trigger frequency read back as:", trigIntervalR, "Hz"
        return trigIntervalR

    def checkClkStatus(self):
        clockStatus = self.hw.getNode("logic_clocks.LogicClocksCSR").read()
        self.hw.dispatch()
        print "\tCLOCK STATUS [expected 3]"
        print "\t ", hex(clockStatus)
        assert ( clockStatus == 3 ) , "Clocks in TLU FPGA are not locked. No point in continuing. Re-prgramme or power cycle board"
        return clockStatus

    def setPulseStretch(self, pulseStretch):
        print "\tINPUT COINCIDENCE WINDOW SET TO", hex(pulseStretch) ,"[Units= 160MHz clock cycles, Four 5-bit values (one per input) packed in to 32-bit word]"
        self.hw.getNode("triggerLogic.InternalTriggerIntervalW").write(pulseStretch)
        self.hw.dispatch()
        self.getPulseStretch()

    def getPulseStretch(self):
        pulseStretchR = self.hw.getNode("triggerLogic.InternalTriggerIntervalR").read()
        self.hw.dispatch()
        print "\t  Pulse stretch read back as:", hex(pulseStretchR)
        return pulseStretchR

    def getChCount(self, channel):
        regString= "triggerInputs.ThrCount"+ str(channel)+"R"
        count = self.hw.getNode(regString).read()
        self.hw.dispatch()
        print "\t  Ch", channel, "Count:" , count
        return count

    def getChStatus(self):
        inputStatus= self.hw.getNode("triggerInputs.SerdesRstR").read()
        self.hw.dispatch()
        print "\t  Input status= " , hex(inputStatus)
        return inputStatus

    def setChStatus(self, cmd):
        self.hw.getNode("triggerInputs.SerdesRstW").write(cmd)
        inputStatus= self.hw.getNode("triggerInputs.SerdesRstR").read()
        self.hw.dispatch()
        print "\tINPUT STATUS SET TO= " , hex(inputStatus)

    def resetSerdes(self):
        cmd = int("0x3",16)
        self.setChStatus(cmd)
        inputStatus= self.getChStatus()
        print "\t  Input status during reset = " , hex(inputStatus)

        cmd = int("0x0",16)
        self.setChStatus(cmd)
        inputStatus= self.getChStatus()
        print "\t  Input status after reset = " , hex(inputStatus)

        cmd = int("0x4",16)
        self.setChStatus(cmd)
        inputStatus= self.getChStatus()
        print "\t  Input status during calibration = " , hex(inputStatus)

        cmd = int("0x0",16)
        self.setChStatus(cmd)
        inputStatus= self.getChStatus()
        print "\t  Input status after calibration = " , hex(inputStatus)

    def resetClocks(self):
        #Reset clocks
        self.resetClock()
        #Get clock status after reset
        self.getClockStatus()
        #Get serdes status
        self.getChStatus()

    def getAllChannelsCounts(self):
        chCounts=[]
        for ch in range (0,self.nChannels):
            chCounts.append(int(self.getChCount(ch)))
        return chCounts

    def setPulseDelay(self, pulseDelay):
        print "\tTRIGGER DELAY SET TO", pulseDelay, "[Units= 160MHz clock, Four 5-bit values (one per input) packed in to 32-bit word]"
        self.hw.getNode("triggerLogic.PulseDelayW").write(pulseDelay)
        self.hw.dispatch()
        self.getPulseDelay()

    def getPulseDelay(self):
        pulseDelayR = self.hw.getNode("triggerLogic.PulseDelayR").read()
        self.hw.dispatch()
        print "\t  Pulse delay read back as:", hex(pulseDelayR)
        return pulseDelayR

    def setMode(self, mode):
        print "\tDUT MODE SET TO: ", mode
        self.hw.getNode("DUTInterfaces.DUTInterfaceModeW").write(mode)
        self.hw.dispatch()
        self.getMode()

    def getMode(self):
        DUTInterfaceModeR = self.hw.getNode("DUTInterfaces.DUTInterfaceModeR").read()
        self.hw.dispatch()
        print "\t  DUT mode read back as:" , DUTInterfaceModeR
        return DUTInterfaceModeR

    def setFifoCSR(self, cmd):
        self.hw.getNode("eventBuffer.EventFifoCSR").write(cmd)
        self.hw.dispatch()
        self.getFifoCSR()

    def getFifoCSR(self):
        FifoCSR= self.hw.getNode("eventBuffer.EventFifoCSR").read()
        self.hw.dispatch()
        print "\t  FIFO CSR read back as:", hex(FifoCSR)
        return FifoCSR

    def getFifoLevel(self):
        FifoFill= self.hw.getNode("eventBuffer.EventFifoFillLevel").read()
        self.hw.dispatch()
        print "\t  FIFO level read back as:", hex(FifoFill)
        return FifoFill

    def setRecordDataStatus(self, status=False):
        self.hw.getNode("Event_Formatter.Enable_Record_Data").write(status)
        self.hw.dispatch()
        self.getRecordDataStatus()

    def getRecordDataStatus(self):
        RecordStatus= self.hw.getNode("Event_Formatter.Enable_Record_Data").read()
        self.hw.dispatch()
        print "\t  Data recording:", RecordStatus
        return RecordStatus

    def pulseT0(self):
        cmd = int("0x1",16)
        self.hw.getNode("Shutter.PulseT0").write(cmd)
        self.hw.dispatch()
        print "\tPulsing T0"

    def setTriggerVetoStatus(self, status=False):
        self.hw.getNode("triggerLogic.TriggerVetoW").write(status)
        self.hw.dispatch()
        self.getTriggerVetoStatus()

    def getTriggerVetoStatus(self):
        trgVetoStatus= self.hw.getNode("triggerLogic.TriggerVetoR").read()
        self.hw.dispatch()
        print "\t  Trigger veto status read back as:", trgVetoStatus
        return trgVetoStatus

    def start(self, logtimestamps=False):
        print "miniTLU STARTING..."

        print "\tFIFO RESET:"
        FIFOcmd= 0x2
        self.setFifoCSR(FIFOcmd)

        eventFifoFillLevel= self.getFifoLevel()

        if logtimestamps:
            print "\tData recording set: ON"
            self.setRecordDataStatus(True)
        else:
            print "\tData recording set: OFF"
            self.setRecordDataStatus(False)

        # Pulse T0
        self.pulseT0()

        print "\tTurning off software trigger veto"
        cmd = int("0x0",16)
        self.setTriggerVetoStatus(cmd)

        print "miniTLU RUNNING"

    def stop(self):
        print "miniTLU STOPPING..."

        print "\tTurning on software trigger veto"
        cmd = int("0x1",16)
        self.setTriggerVetoStatus(cmd)

        print "miniTLU STOPPED"
