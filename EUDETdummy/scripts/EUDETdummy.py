# -*- coding: utf-8 -*-
import uhal;
import pprint;
#from FmcTluI2c import *
import time
from I2CuHal import I2CCore
from si5345 import si5345 # Library for clock chip
from AD5665R import AD5665R # Library for DAC
from PCA9539PW import PCA9539PW # Library for serial line expander

class EUDETdummy:
    """docstring for TLU"""
    def __init__(self, dev_name, man_file):
        self.dev_name = dev_name
        self.manager= uhal.ConnectionManager(man_file)
        self.hw = self.manager.getDevice(self.dev_name)
        self.nDUTs= 4 #Number of DUT connectors
        self.nChannels= 6 #Number of trigger inputs
        self.VrefInt= 2.5 #Internal DAC voltage reference
        self.VrefExt= 1.3 #External DAC voltage reference
        self.intRefOn= False #Internal reference is OFF by default

        self.fwVersion = self.hw.getNode("version").read()
        self.hw.dispatch()
        print "EUDUMMY FIRMWARE VERSION= " , hex(self.fwVersion)

        # Instantiate a I2C core to configure components
        self.TLU_I2C= I2CCore(self.hw, 10, 5, "i2c_master", None)
        #self.TLU_I2C.state()

        enableCore= True #Only need to run this once, after power-up
        self.enableCore()

        # Instantiate clock chip
        self.zeClock=si5345(self.TLU_I2C, 0x68)
        res= self.zeClock.getDeviceVersion()
        self.zeClock.checkDesignID()

        # Instantiate DACs and configure them to use reference based on TLU setting
        self.zeDAC1=AD5665R(self.TLU_I2C, 0x13)
        self.zeDAC2=AD5665R(self.TLU_I2C, 0x1F)
        self.zeDAC1.setIntRef(self.intRefOn)
        self.zeDAC2.setIntRef(self.intRefOn)

        # Instantiate the serial line expanders and configure them to default values
        self.IC6=PCA9539PW(self.TLU_I2C, 0x74)
        self.IC6.setInvertReg(0, 0x00)# 0= normal, 1= inverted
        self.IC6.setIOReg(0, 0x00)# 0= output, 1= input
        self.IC6.setOutputs(0, 0x88)# If output, set to XX

        self.IC6.setInvertReg(1, 0x00)# 0= normal, 1= inverted
        self.IC6.setIOReg(1, 0x00)# 0= output, 1= input
        self.IC6.setOutputs(1, 0x88)# If output, set to XX

        self.IC7=PCA9539PW(self.TLU_I2C, 0x75)
        self.IC7.setInvertReg(0, 0x00)# 0= normal, 1= inverted
        self.IC7.setIOReg(0, 0x00)# 0= output, 1= input
        self.IC7.setOutputs(0, 0x0F)# If output, set to XX

        self.IC7.setInvertReg(1, 0x00)# 0= normal, 1= inverted
        self.IC7.setIOReg(1, 0x00)# 0= output, 1= input
        self.IC7.setOutputs(1, 0x50)# If output, set to XX


##################################################################################################################################
##################################################################################################################################
    def DUTOutputs(self, dutN, enable=False, verbose=False):
        ## Set the status of the transceivers for a specific HDMI connector. When enable= False the transceivers are disabled and the
        ## connector cannot send signals from FPGA to the outside world. When enable= True then signals from the FPGA will be sent out to the HDMI.
        ## NOTE: the other direction is always enabled, i.e. signals from the DUTs are always sent to the FPGA.
        ## NOTE: CLK direction must be defined separately using DUTClkSrc

        if (dutN < 0) | (dutN> (self.nDUTs-1)):
            print "\tERROR: DUTOutputs. The DUT number must be comprised between 0 and ", self.nDUTs-1
            return -1
        bank= dutN//2 # DUT0 and DUT1 are on bank 0. DUT2 and DUT3 on bank 1
        nibble= dutN%2 # DUT0 and DUT2 are on nibble 0. DUT1 and DUT3 are on nibble 1
        print "  Setting DUT:", dutN, "to", enable
        if verbose:
            print "\tBank", bank, "Nibble", nibble
        res= self.IC6.getIOReg(bank)
        oldStatus= res[0]
        mask= 0xF << 4*nibble
        newStatus= oldStatus & (~mask)
        if (not enable): # we want to write 0 to activate the outputs so check opposite of "enable"
            newStatus |= mask
        if verbose:
            print "\tOldStatus= ", "{0:#0{1}x}".format(oldStatus,4), "Mask=" , hex(mask), "newStatus=", "{0:#0{1}x}".format(newStatus,4)
        self.IC6.setIOReg(bank, newStatus)
        return newStatus

    def DUTClkSrc(self, dutN, clkSrc=0, verbose= False):
        ## Allows to choose the source of the clock signal sent to the DUTs over HDMI
        ## clkSrc= 0: clock disabled
        ## clkSrc= 1: clock from Si5345
        ## clkSrc=2: clock from FPGA
        if (dutN < 0) | (dutN> (self.nDUTs-1)):
            print "\tERROR: DUTClkSrc. The DUT number must be comprised between 0 and ", self.nDUTs-1
            return -1
        if (clkSrc < 0) | (clkSrc> 2):
            print "\tERROR: DUTClkSrc. clkSrc can only be 0 (disabled), 1 (Si5345) or 2 (FPGA)"
            return -1
        bank=0
        maskLow= 1 << (1* dutN) #CLK FROM FPGA
        maskHigh= 1<< (1* dutN +4) #CLK FROM Si5345
        mask= maskLow | maskHigh
        res= self.IC7.getIOReg(bank)
        oldStatus= res[0]
        newStatus= oldStatus & ~mask #set both bits to zero
        outStat= ""
        if clkSrc==0:
            newStatus = newStatus | mask
            outStat= "disabled"
        elif clkSrc==1:
            newStatus = newStatus | maskLow
            outStat= "Si5435"
        elif clkSrc==2:
            newStatus= newStatus | maskHigh
            outStat= "FPGA"
        print "  Setting DUT:", dutN, "clock source to", outStat
        if verbose:
            print "\tOldStatus= ", "{0:#0{1}x}".format(oldStatus,4), "Mask=" , hex(mask), "newStatus=", "{0:#0{1}x}".format(newStatus,4)
        self.IC7.setIOReg(bank, newStatus)
        return newStatus

    def enableClkLEMO(self, enable= False, verbose= False):
        ## Enable or disable the output clock to the differential LEMO output
        bank=1
        mask= 0x10
        res= self.IC7.getIOReg(bank)
        oldStatus= res[0]
        newStatus= oldStatus & ~mask
        outStat= "enabled"
        if (not enable): #A 0 activates the output. A 1 disables it.
            newStatus= newStatus | mask
            outStat= "disabled"
        print "  Clk LEMO", outStat
        if verbose:
            print "\tOldStatus= ", "{0:#0{1}x}".format(oldStatus,4), "Mask=" , hex(mask), "newStatus=", "{0:#0{1}x}".format(newStatus,4)
        self.IC7.setIOReg(bank, newStatus)
        return newStatus

    def enableCore(self):
        ## At power up the Enclustra I2C lines are disabled (tristate buffer is off).
        ## This function enables the lines. It is only required once.
        mystop=True
        print "  Enabling I2C bus (expect 127):"
        myslave= 0x21
        mycmd= [0x01, 0x7F]
        nwords= 1
        self.TLU_I2C.write(myslave, mycmd, mystop)

        mystop=False
        mycmd= [0x01]
        self.TLU_I2C.write(myslave, mycmd, mystop)
        res= self.TLU_I2C.read( myslave, nwords)
        print "\tPost RegDir: ", res

    def getAllChannelsCounts(self):
        chCounts=[]
        for ch in range (0,self.nChannels):
            chCounts.append(int(self.getChCount(ch)))
        return chCounts

    def getChStatus(self):
        inputStatus= self.hw.getNode("triggerInputs.SerdesRstR").read()
        self.hw.dispatch()
        print "\tInput status= " , hex(inputStatus)
        return inputStatus

    def getChCount(self, channel):
        regString= "triggerInputs.ThrCount"+ str(channel)+"R"
        count = self.hw.getNode(regString).read()
        self.hw.dispatch()
        print "\tCh", channel, "Count:" , count
        return count

    def getClockStatus(self):
        clockStatus = self.hw.getNode("logic_clocks.LogicClocksCSR").read()
        self.hw.dispatch()
        print "  CLOCK STATUS [expected 1]"
        print "\t", hex(clockStatus)
        if ( clockStatus == 0 ):
            "ERROR: Clocks in EUDUMMY FPGA are not locked."
        return clockStatus

    def getDUTmask(self):
        DUTMaskR = self.hw.getNode("DUTInterfaces.DutMaskR").read()
        self.hw.dispatch()
        print "\tDUTMask read back as:" , hex(DUTMaskR)
        return DUTMaskR

    def getExternalVeto(self):
        extVeto= self.hw.getNode("triggerLogic.ExternalTriggerVetoR").read()
        self.hw.dispatch()
        print "\tEXTERNAL Veto read back as:", hex(extVeto)
        return extVeto

    def getFifoData(self, nWords):
    	#fifoData= self.hw.getNode("eventBuffer.EventFifoData").read()
    	fifoData= self.hw.getNode("eventBuffer.EventFifoData").readBlock (nWords);
    	self.hw.dispatch()
    	#print "\tFIFO Data:", hex(fifoData)
    	return fifoData

    def getFifoLevel(self):
        FifoFill= self.hw.getNode("eventBuffer.EventFifoFillLevel").read()
        self.hw.dispatch()
        print "\tFIFO level read back as:", hex(FifoFill)
        return FifoFill

    def getFifoCSR(self):
        FifoCSR= self.hw.getNode("eventBuffer.EventFifoCSR").read()
        self.hw.dispatch()
        print "\tFIFO CSR read back as:", hex(FifoCSR)
        return FifoCSR

    def getInternalTrg(self):
        trigIntervalR = self.hw.getNode("triggerLogic.InternalTriggerIntervalR").read()
        self.hw.dispatch()
        print "\tTrigger frequency read back as:", trigIntervalR, "Hz"
        return trigIntervalR

    def getMode(self):
        DUTInterfaceModeR = self.hw.getNode("DUTInterfaces.DUTInterfaceModeR").read()
        self.hw.dispatch()
        print "\tDUT mode read back as:" , hex(DUTInterfaceModeR)
        return DUTInterfaceModeR

    def getModeModifier(self):
        DUTInterfaceModeModifierR = self.hw.getNode("DUTInterfaces.DUTInterfaceModeModifierR").read()
        self.hw.dispatch()
        print "\tDUT mode modifier read back as:" , hex(DUTInterfaceModeModifierR)
        return DUTInterfaceModeModifierR

    def getSN(self):
        epromcontent=self.readEEPROM(0xfa, 6)
        print "  EUDET dummy serial number (EEPROM):"
        result="\t"
        for iaddr in epromcontent:
            result+="%02x "%(iaddr)
        print result
        return epromcontent

    def getPostVetoTrg(self):
        triggerN = self.hw.getNode("triggerLogic.PostVetoTriggersR").read()
        self.hw.dispatch()
        print "\tPOST VETO TRIGGER NUMBER:", (triggerN)
        return triggerN

    def getPulseDelay(self):
        pulseDelayR = self.hw.getNode("triggerLogic.PulseDelayR").read()
        self.hw.dispatch()
        print "\tPulse delay read back as:", hex(pulseDelayR)
        return pulseDelayR

    def getPulseStretch(self):
        pulseStretchR = self.hw.getNode("triggerLogic.PulseStretchR").read()
        self.hw.dispatch()
        print "\tPulse stretch read back as:", hex(pulseStretchR)
        return pulseStretchR

    def getRecordDataStatus(self):
        RecordStatus= self.hw.getNode("Event_Formatter.Enable_Record_Data").read()
        self.hw.dispatch()
        print "\tData recording:", RecordStatus
        return RecordStatus

    def getTriggerVetoStatus(self):
        trgVetoStatus= self.hw.getNode("triggerLogic.TriggerVetoR").read()
        self.hw.dispatch()
        print "\tTrigger veto status read back as:", trgVetoStatus
        return trgVetoStatus

    def getTrgPattern(self):
        triggerPattern_low = self.hw.getNode("triggerLogic.TriggerPattern_lowR").read()
        triggerPattern_high = self.hw.getNode("triggerLogic.TriggerPattern_highR").read()
        self.hw.dispatch()
        print "\tTrigger pattern read back as: 0x%08X 0x%08X" %(triggerPattern_high, triggerPattern_low)
        return triggerPattern_low, triggerPattern_high

    def getVetoDUT(self):
        IgnoreDUTBusyR = self.hw.getNode("DUTInterfaces.IgnoreDUTBusyR").read()
        self.hw.dispatch()
        print "\tIgnoreDUTBusy read back as:" , hex(IgnoreDUTBusyR)
        return IgnoreDUTBusyR

    def getVetoShutters(self):
        IgnoreShutterVeto = self.hw.getNode("DUTInterfaces.IgnoreShutterVetoR").read()
        self.hw.dispatch()
        print "\tIgnoreShutterVeto read back as:" , IgnoreShutterVeto
        return IgnoreShutterVeto

    def pulseT0(self):
        cmd = int("0x1",16)
        self.hw.getNode("Shutter.PulseT0").write(cmd)
        self.hw.dispatch()
        print "\tPulsing T0"

    def readEEPROM(self, startadd, bytes):
        mystop= 1
        time.sleep(0.1)
        myaddr= [startadd]#0xfa
        self.TLU_I2C.write( 0x50, [startadd], mystop)
        res= self.TLU_I2C.read( 0x50, bytes)
        return res

    def resetClock(self):
        # Set the RST pin from the PLL to 1
        print "  Clocks reset"
        cmd = int("0x1",16)
        self.hw.getNode("logic_clocks.LogicRst").write(cmd)
        self.hw.dispatch()

    def resetClocks(self):
        #Reset clock PLL
        self.resetClock()
        #Get clock status after reset
        self.getClockStatus()
        #Restore clock PLL
        self.restoreClock()
        #Get clock status after restore
        self.getClockStatus()
        #Get serdes status
        self.getChStatus()

    def resetCounters(self):
    	cmd = int("0x2", 16) #write 0x2 to reset
    	self.hw.getNode("triggerInputs.SerdesRstW").write(cmd)
    	restatus= self.hw.getNode("triggerInputs.SerdesRstR").read()
    	self.hw.dispatch()
    	cmd = int("0x0", 16) #write 0x2 to reset
    	self.hw.getNode("triggerInputs.SerdesRstW").write(cmd)
    	restatus= self.hw.getNode("triggerInputs.SerdesRstR").read()
    	self.hw.dispatch()
    	#print "Trigger Reset: 0x%X" % restatus
    	print "\tTrigger counters reset"

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

    def restoreClock(self):
        # Set the RST pin from the PLL to 0
        print "  Clocks restore"
        cmd = int("0x0",16)
        self.hw.getNode("logic_clocks.LogicRst").write(cmd)
        self.hw.dispatch()

    def setChStatus(self, cmd):
        self.hw.getNode("triggerInputs.SerdesRstW").write(cmd)
        inputStatus= self.hw.getNode("triggerInputs.SerdesRstR").read()
        self.hw.dispatch()
        print "  INPUT STATUS SET TO= " , hex(inputStatus)

    def setClockStatus(self, cmd):
        # Only use this for testing. The clock source is actually selected in the Si5345.
        self.hw.getNode("logic_clocks.LogicClocksCSR").write(cmd)
        self.hw.dispatch()

    def setDUTmask(self, DUTMask):
        print "  DUT MASK ENABLING: Mask= " , hex(DUTMask)
        self.hw.getNode("DUTInterfaces.DutMaskW").write(DUTMask)
        self.hw.dispatch()
        self.getDUTmask()

    def setFifoCSR(self, cmd):
        self.hw.getNode("eventBuffer.EventFifoCSR").write(cmd)
        self.hw.dispatch()
        self.getFifoCSR()

    def setInternalTrg(self, triggerInterval):
        print "  TRIGGERS INTERNAL:"
        if triggerInterval == 0:
            internalTriggerFreq = 0
            print "\tdisabled"
        else:
            internalTriggerFreq = 160000.0/triggerInterval
            print "\t  Setting:", internalTriggerFreq, "Hz"
        self.hw.getNode("triggerLogic.InternalTriggerIntervalW").write(int(internalTriggerFreq))
        self.hw.dispatch()
        self.getInternalTrg()

    def setMode(self, mode):
        print "  DUT MODE SET TO: ", hex(mode)
        self.hw.getNode("DUTInterfaces.DUTInterfaceModeW").write(mode)
        self.hw.dispatch()
        self.getMode()

    def setModeModifier(self, modifier):
        print "  DUT MODE MODIFIER:", hex(modifier)
        self.hw.getNode("DUTInterfaces.DUTInterfaceModeModifierW").write(modifier)
        self.hw.dispatch()
        self.getModeModifier()

    def setPulseDelay(self, pulseDelay):
        print "  TRIGGER DELAY SET TO", hex(pulseDelay), "[Units= 160MHz clock, 5-bit values (one per input) packed in to 32-bit word]"
        self.hw.getNode("triggerLogic.PulseDelayW").write(pulseDelay)
        self.hw.dispatch()
        self.getPulseDelay()

    def setPulseStretch(self, pulseStretch):
        print "  INPUT COINCIDENCE WINDOW SET TO", hex(pulseStretch) ,"[Units= 160MHz clock cycles, 5-bit values (one per input) packed in to 32-bit word]"
        self.hw.getNode("triggerLogic.PulseStretchW").write(pulseStretch)
        self.hw.dispatch()
        self.getPulseStretch()

    def setRecordDataStatus(self, status=False):
        print "  Data recording set:"
        self.hw.getNode("Event_Formatter.Enable_Record_Data").write(status)
        self.hw.dispatch()
        self.getRecordDataStatus()

    def setTriggerVetoStatus(self, status=False):
        self.hw.getNode("triggerLogic.TriggerVetoW").write(status)
        self.hw.dispatch()
        self.getTriggerVetoStatus()

    def setTrgPattern(self, triggerPatternH, triggerPatternL):
        triggerPatternL &= 0xffffffff
        triggerPatternH &= 0xffffffff
        print "  TRIGGER PATTERN (for external triggers) SET TO 0x%08X 0x%08X. Two 32-bit words." %(triggerPatternH, triggerPatternL)
        self.hw.getNode("triggerLogic.TriggerPattern_lowW").write(triggerPatternL)
        self.hw.getNode("triggerLogic.TriggerPattern_highW").write(triggerPatternH)
        self.hw.dispatch()
        self.getTrgPattern()

    def setVetoDUT(self, ignoreDUTBusy):
        print "  VETO IGNORE BY DUT BUSY MASK SET TO" , hex(ignoreDUTBusy)
        self.hw.getNode("DUTInterfaces.IgnoreDUTBusyW").write(ignoreDUTBusy)
        self.hw.dispatch()
        self.getVetoDUT()

    def setVetoShutters(self, newState):
        if newState:
            print "  IgnoreShutterVetoW SET TO LISTEN FOR VETO FROM SHUTTER"
            cmd= int("0x0",16)
        else:
            print "  IgnoreShutterVetoW SET TO IGNORE VETO FROM SHUTTER"
            cmd= int("0x1",16)
        self.hw.getNode("DUTInterfaces.IgnoreShutterVetoW").write(cmd)
        self.hw.dispatch()
        self.getVetoShutters()

    def writeThreshold(self, DACtarget, Vtarget, channel):
        #Writes the threshold. The DAC voltage differs from the threshold voltage because
        #the range is shifted to be symmetrical around 0V.

        #Check if the DACs are using the internal reference
        if (self.intRefOn):
            Vref= self.VrefInt
        else:
            Vref= self.VrefExt

        #Calculate offset voltage (because of the following shifter)
        Vdac= ( Vtarget + Vref ) / 2
        print"  THRESHOLD setting:"
        if channel==7:
            print "\tCH: ALL"
        else:
            print "\tCH:", channel
        print "\tTarget V:", Vtarget
        dacValue = 0xFFFF * (Vdac / Vref)
        DACtarget.writeDAC(int(dacValue), channel, True)

    def parseFifoData(self, fifoData, nEvents, verbose):
        #for index in range(0, len(fifoData)-1, 6):
        outList= []
        for index in range(0, (nEvents)*6, 6):
            word0= (fifoData[index] << 32) + fifoData[index + 1]
            word1= (fifoData[index + 2] << 32) + fifoData[index + 3]
            word2= (fifoData[index + 4] << 32) + fifoData[index + 5]
            evType= (fifoData[index] & 0xF0000000) >> 28
            inTrig= (fifoData[index] & 0x0FFF0000) >> 16
            tStamp= ((fifoData[index] & 0x0000FFFF) << 32) + fifoData[index + 1]
            fineTs= fifoData[index + 2]
            evNum= fifoData[index + 3]
            fineTsList=[-1]*12
            fineTsList[3]= (fineTs & 0x000000FF)
            fineTsList[2]= (fineTs & 0x0000FF00) >> 8
            fineTsList[1]= (fineTs & 0x00FF0000) >> 16
            fineTsList[0]= (fineTs & 0xFF000000) >> 24
            fineTsList[7]= (fifoData[index + 4] & 0x000000FF)
            fineTsList[6]= (fifoData[index + 4] & 0x0000FF00) >> 8
            fineTsList[5]= (fifoData[index + 4] & 0x00FF0000) >> 16
            fineTsList[4]= (fifoData[index + 4] & 0xFF000000) >> 24
            fineTsList[11]= (fifoData[index + 5] & 0x000000FF)
            fineTsList[10]= (fifoData[index + 5] & 0x0000FF00) >> 8
            fineTsList[9]= (fifoData[index + 5] & 0x00FF0000) >> 16
            fineTsList[8]= (fifoData[index + 5] & 0xFF000000) >> 24
            if verbose:
                print "====== EVENT", evNum, "================================================="
                print "[", hex(word0), "]", "\t TYPE", hex(evType), "\t TRIGGER", hex(inTrig), "\t TIMESTAMP", (tStamp)
                print "[",hex(word1), "]", "\tEV NUM", evNum, "\tFINETS[0,3]", hex(fineTs)
                print "[",hex(word2), "]", "\tFINETS[4,11]", hex(word2)
                print fineTsList
            fineTsList.insert(0, tStamp)
            fineTsList.insert(0, evNum)
            #print fineTsList
            outList.insert(len(outList), fineTsList)
        printdata= False
        if (printdata):
            print "=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-="
            print "EN#\tCOARSE_TS\tFINE_TS0...FINE_TS11"
            pprint.pprint(outList)
        return outList




##################################################################################################################################
##################################################################################################################################

    def initialize(self):
        print "\nEUDUMMY INITIALIZING..."

        # We need to pass it listenForTelescopeShutter , pulseDelay , pulseStretch , triggerPattern , DUTMask , ignoreDUTBusy , triggerInterval , thresholdVoltage

        #READ CONTENT OF EPROM VIA I2C
        self.getSN()


        #
        # #SET DACs
        targetV= -0.12
        DACchannel= 7
        self.writeThreshold(self.zeDAC1, targetV, DACchannel, )
        self.writeThreshold(self.zeDAC2, targetV, DACchannel, )

        #
        # #ENABLE/DISABLE HDMI OUTPUTS
        #self.DUTOutputs(0, True, False)
        #self.DUTOutputs(1, True, False)
        #self.DUTOutputs(2, True, False)
        #self.DUTOutputs(3, True, False)

        ## ENABLE/DISABLE LEMO CLOCK OUTPUT
        #self.enableClkLEMO(True, False)

        #
        # #Check clock status
        self.getClockStatus()

        resetClocks = 0
        resetSerdes = 0
        resetCounters= 0
        if resetClocks:
            self.resetClocks()
            self.getClockStatus()
        if resetSerdes:
            self.resetSerdes()
        if resetCounters:
	    self.resetCounters()



        print "EUDUMMY INITIALIZED"

##################################################################################################################################
##################################################################################################################################
    def start(self, logtimestamps=False):
        print "EUDUMMY STARTING..."

        print "  EUDUMMY RUNNING"

##################################################################################################################################
##################################################################################################################################
    def stop(self):
        print "EUDUMMY STOPPING..."

        print "  EUDUMMY STOPPED"
