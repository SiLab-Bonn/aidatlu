# -*- coding: utf-8 -*-
import uhal;
# import pprint;
# import ConfigParser
#from FmcTluI2c import *
# from ROOT import TFile, TTree, gROOT, AddressOf
# from ROOT import *
import time

from packages.I2CuHal import I2CCore
from packages.si5345 import si5345 # Library for clock chip
from packages.AD5665R import AD5665R # Library for DAC
from packages.PCA9539PW import PCA9539PW # Library for serial line expander
from packages.I2CDISP import LCD_ada # Library for Adafruit display
from packages.I2CDISP import LCD09052 # Library for SparkFun display
from packages.TLU_powermodule import PWRLED
from packages.ATSHA204A import ATSHA204A


class TLU:
    """docstring for TLU"""
    def __init__(self, dev_name, man_file, parsed_cfg):

        uhal.setLogLevelTo(uhal.LogLevel.NOTICE) ## Get rid of initial flood of IPBUS messages
        self.isRunning= False

        section_name= "Producer.fmctlu"
        self.dev_name = dev_name

        #man_file= parsed_cfg.get(section_name, "ConnectionFile")
        self.manager= uhal.ConnectionManager(man_file)
        self.hw = self.manager.getDevice(self.dev_name)

        # #Get Verbose setting
        self.verbose= parsed_cfg.getint(section_name, "verbose")

        #self.nDUTs= 4 #Number of DUT connectors
        self.nDUTs= parsed_cfg.getint(section_name, "nDUTs")

        #self.nChannels= 6 #Number of trigger inputs
        self.nChannels= parsed_cfg.getint(section_name, "nTrgIn")

        #self.VrefInt= 2.5 #Internal DAC voltage reference
        self.VrefInt= parsed_cfg.getfloat(section_name, "VRefInt")

        #self.VrefExt= 1.3 #External DAC voltage reference
        self.VrefExt= parsed_cfg.getfloat(section_name, "VRefExt")

        #self.intRefOn= False #Internal reference is OFF by default
        self.intRefOn= int(parsed_cfg.get(section_name, "intRefOn"))

        self.fwVersion = self.hw.getNode("version").read()
        self.hw.dispatch()
        print("TLU V1E FIRMWARE VERSION= " , hex(self.fwVersion))

        # Instantiate a I2C core to configure components
        self.TLU_I2C= I2CCore(self.hw, 10, 5, "i2c_master", None)
        #self.TLU_I2C.state()

        enableCore= True #Only need to run this once, after power-up
        self.enableCore()
        ####### EEPROM AX3 testing
        doAtmel= False
        if doAtmel:
            self.ax3eeprom= ATSHA204A(self.TLU_I2C, 0x64)
            print("shiftR\tdatBit\tcrcBit\tcrcReg \n", self.ax3eeprom._CalculateCrc([255, 12, 54, 28, 134, 89], 3))
            self.ax3eeprom._wake(True, True)
            print(self.ax3eeprom._GetCommandPacketSize(8))
            #self.eepromAX3read()
        ####### EEPROM AX3 testing end

        # Instantiate clock chip and configure it (if necessary)
        #self.zeClock=si5345(self.TLU_I2C, 0x68)
        clk_addr= int(parsed_cfg.get(section_name, "I2C_CLK_Addr"), 16)
        self.zeClock=si5345(self.TLU_I2C, clk_addr)
        res= self.zeClock.getDeviceVersion()
        if (int(parsed_cfg.get(section_name, "CONFCLOCK"), 16)):
            #clkRegList= self.zeClock.parse_clk("./../../bitFiles/TLU_CLK_Config_v1e.txt")
            clkRegList= self.zeClock.parse_clk(parsed_cfg.get(section_name, "CLOCK_CFG_FILE"))
            self.zeClock.writeConfiguration(clkRegList, self.verbose)######

        self.zeClock.checkDesignID()

        # Instantiate DACs and configure them to use reference based on TLU setting
        #self.zeDAC1=AD5665R(self.TLU_I2C, 0x13)
        #self.zeDAC2=AD5665R(self.TLU_I2C, 0x1F)
        dac_addr1= int(parsed_cfg.get(section_name, "I2C_DAC1_Addr"), 16)
        self.zeDAC1=AD5665R(self.TLU_I2C, dac_addr1)
        dac_addr2= int(parsed_cfg.get(section_name, "I2C_DAC2_Addr"), 16)
        self.zeDAC2=AD5665R(self.TLU_I2C, dac_addr2)
        self.zeDAC1.setIntRef(self.intRefOn, self.verbose)
        self.zeDAC2.setIntRef(self.intRefOn, self.verbose)

        # Instantiate the serial line expanders and configure them to default values
        #self.IC6=PCA9539PW(self.TLU_I2C, 0x74)
        exp1_addr= int(parsed_cfg.get(section_name, "I2C_EXP1_Addr"), 16)
        self.IC6=PCA9539PW(self.TLU_I2C, exp1_addr)
        self.IC6.setInvertReg(0, 0x00)# 0= normal, 1= inverted
        self.IC6.setIOReg(0, 0x00)# 0= output, 1= input
        self.IC6.setOutputs(0, 0xFF)# If output, set to XX

        self.IC6.setInvertReg(1, 0x00)# 0= normal, 1= inverted
        self.IC6.setIOReg(1, 0x00)# 0= output, 1= input
        self.IC6.setOutputs(1, 0xFF)# If output, set to XX

        #self.IC7=PCA9539PW(self.TLU_I2C, 0x75)
        exp2_addr= int(parsed_cfg.get(section_name, "I2C_EXP2_Addr"), 16)
        self.IC7=PCA9539PW(self.TLU_I2C, exp2_addr)
        self.IC7.setInvertReg(0, 0x00)# 0= normal, 1= inverted
        self.IC7.setIOReg(0, 0x00)# 0= output, 1= input
        self.IC7.setOutputs(0, 0x00)# If output, set to XX

        self.IC7.setInvertReg(1, 0x00)# 0= normal, 1= inverted
        self.IC7.setIOReg(1, 0x00)# 0= output, 1= input
        self.IC7.setOutputs(1, 0xB0)# If output, set to XX

        #Attempt to instantiate Display
        self.displayPresent= True
        i2ccmd= [7, 150]
        mystop= True
        print("  Attempting to detect TLU display")
        # res= self.TLU_I2C.write( 0x3A, i2ccmd, mystop)
        res= self.TLU_I2C.write( 0x20, i2ccmd, mystop)
        if (res== -1): # if this fails, likely no display installed
            self.displayPresent= False
            print("\tNo TLU display detected")
        if self.displayPresent:
            self.DISP = LCD_ada(self.TLU_I2C, 0x20)
            self.DISP.test()
            # self.DISP=LCD09052(self.TLU_I2C, 0x3A) #0x3A for Sparkfun, 0x20 for Adafruit
            # self.DISP.test2("192.168.200.30", "AIDA TLU")
        #self.DISP=CFA632(self.TLU_I2C, 0x2A) #

        #Instantiate Power/Led Module
        dac_addr_module= int(parsed_cfg.get(section_name, "I2C_DACModule_Addr"), 16)
        exp1_addr= int(parsed_cfg.get(section_name, "I2C_EXP1Module_Addr"), 16)
        exp2_addr= int(parsed_cfg.get(section_name, "I2C_EXP2Module_Addr"), 16)
        pmtCtrVMax= parsed_cfg.getfloat(section_name, "PMT_vCtrlMax")

        self.pwdled= PWRLED(self.TLU_I2C, dac_addr_module, pmtCtrVMax, exp1_addr, exp2_addr)

        self.pwdled.allGreen()
        time.sleep(0.1)
        self.pwdled.allBlue()
        time.sleep(0.1)
        self.pwdled.allBlack()
        time.sleep(0.1)
        self.pwdled.kitt()
        time.sleep(0.1)
        self.pwdled.allWhite()
        #self.pwdled.test()
        


##################################################################################################################################
##################################################################################################################################
    def DUTOutputs_old(self, dutN, enable=False, verbose=False):
        ## Set the status of the transceivers for a specific HDMI connector. When enable= False the transceivers are disabled and the
        ## connector cannot send signals from FPGA to the outside world. When enable= True then signals from the FPGA will be sent out to the HDMI.
        ## NOTE: the other direction is always enabled, i.e. signals from the DUTs are always sent to the FPGA.
        ## NOTE: CLK direction must be defined separately using DUTClkSrc
        ## NOTE: This version changes all the pins together. Use DUTOutputs to control individual pins.

        if (dutN < 0) | (dutN> (self.nDUTs-1)):
            print("\tERROR: DUTOutputs. The DUT number must be comprised between 0 and ", self.nDUTs-1)
            return -1
        bank= dutN//2 # DUT0 and DUT1 are on bank 0. DUT2 and DUT3 on bank 1
        nibble= dutN%2 # DUT0 and DUT2 are on nibble 0. DUT1 and DUT3 are on nibble 1
        print("  Setting DUT:", dutN, "to", enable)
        if (verbose > 1):
            print("\tBank", bank, "Nibble", nibble)
        res= self.IC6.getOutputs(bank)
        oldStatus= res[0]
        mask= 0xF << 4*nibble
        newStatus= oldStatus & (~mask)
        if (not enable): # we want to write 0 to activate the outputs so check opposite of "enable"
            newStatus |= mask
        self.IC6.setOutputs(bank, newStatus)

        if verbose:
            print("\tOldStatus= ", "{0:#0{1}x}".format(oldStatus,4), "Mask=" , hex(mask), "newStatus=", "{0:#0{1}x}".format(newStatus,4))
        return newStatus

    def DUTOutputs(self, dutN, enable=0x7, verbose=False):
        ## Set the status of the transceivers for a specific HDMI connector. When enable= False the transceivers are disabled and the
        ## connector cannot send signals from FPGA to the outside world. When enable= True then signals from the FPGA will be sent out to the HDMI.
        ## NOTE: the other direction is always enabled, i.e. signals from the DUTs are always sent to the FPGA.
        ## NOTE: CLK direction must be defined separately using DUTClkSrc

        if (dutN < 0) | (dutN> (self.nDUTs-1)):
            print("\tERROR: DUTOutputs. The DUT number must be comprised between 0 and ", self.nDUTs-1)
            return -1
        bank= dutN//2 # DUT0 and DUT1 are on bank 0. DUT2 and DUT3 on bank 1
        nibble= dutN%2 # DUT0 and DUT2 are on nibble 0. DUT1 and DUT3 are on nibble 1
        print("  Setting DUT:", dutN, "pins status to", hex(enable))
        if (verbose > 1):
            print("\tBank", bank, "Nibble", nibble)
        res= self.IC6.getOutputs(bank)
        oldStatus= res[0]
        mask= 0xF << 4*nibble
        newnibble= (enable & 0xF) << 4*nibble # bits we want to change are marked with 1
        newStatus= (oldStatus & (~mask)) | (newnibble & mask)

        self.IC6.setOutputs(bank, newStatus)

        if (verbose > 0):
            self.getDUTOutpus(dutN, verbose)
        if (verbose > 1):
            print("\tOldStatus= ", "{0:#0{1}x}".format(oldStatus,4), "Mask=" , hex(mask), "newStatus=", "{0:#0{1}x}".format(newStatus,4))

        return newStatus

    def DUTClkSrc(self, dutN, clkSrc=0, verbose= False):
        ## Allows to choose the source of the clock signal sent to the DUTs over HDMI
        ## clkSrc= 0: clock disabled
        ## clkSrc= 1: clock from Si5345
        ## clkSrc=2: clock from FPGA
        if (dutN < 0) | (dutN> (self.nDUTs-1)):
            print("\tERROR: DUTClkSrc. The DUT number must be comprised between 0 and ", self.nDUTs-1)
            return -1
        if (clkSrc < 0) | (clkSrc> 2):
            print("\tERROR: DUTClkSrc. clkSrc can only be 0 (disabled), 1 (Si5345) or 2 (FPGA)")
            return -1
        bank=0
        maskLow= 1 << (1* dutN) #CLK FROM FPGA
        maskHigh= 1<< (1* dutN +4) #CLK FROM Si5345
        mask= maskLow | maskHigh
        res= self.IC7.getOutputs(bank)
        oldStatus= res[0]
        newStatus= oldStatus & ~mask #set both bits to zero
        outStat= ""
        if clkSrc==0:
            newStatus = newStatus
            outStat= "disabled"
        elif clkSrc==1:
            newStatus = newStatus | maskLow
            outStat= "Si5435"
        elif clkSrc==2:
            newStatus= newStatus | maskHigh
            outStat= "FPGA"
        print("  Setting DUT:", dutN, "clock source to", outStat)
        if (verbose > 1):
            print("\tOldStatus= ", "{0:#0{1}x}".format(oldStatus,4), "Mask=" , hex(mask), "newStatus=", "{0:#0{1}x}".format(newStatus,4))
        self.IC7.setOutputs(bank, newStatus)
        return newStatus

    def eepromAX3read(self):
        mystop=True
        print("  Reading AX3 eeprom (not working 100% yet):")
        myslave= 0x64
        self.TLU_I2C.write(myslave, [0x02, 0x00])
        nwords= 5
        res= self.TLU_I2C.read( myslave, nwords)
        print("\tAX3 awake: ", res)
        mystop=True
        nwords= 7
        #mycmd= [0x03, 0x07, 0x02, 0x00, 0x00, 0x00, 0x1e, 0x2d]#conf 0?
        mycmd= [0x03, 0x07, 0x02, 0x00, 0x01, 0x00, 0x17, 0xad]#conf 1 <<< seems to reply with correct error code (0)
        #mycmd= [0x03, 0x07, 0x02, 0x02, 0x00, 0x00, 0x1d, 0xa8]#data 0?
        self.TLU_I2C.write(myslave, mycmd, mystop)
        res= self.TLU_I2C.read( myslave, nwords)
        print("\tAX3 EEPROM: ", res)

    def enableClkLEMO(self, enable= False, verbose= False):
        ## Enable or disable the output clock to the differential LEMO output
        bank=1
        mask= 0x10
        res= self.IC7.getOutputs(bank)
        oldStatus= res[0]
        newStatus= oldStatus & ~mask
        outStat= "enabled"
        if (not enable): #A 0 activates the output. A 1 disables it.
            newStatus= newStatus | mask
            outStat= "disabled"
        print("  Clk LEMO", outStat)
        if verbose:
            print("\tOldStatus= ", "{0:#0{1}x}".format(oldStatus,4), "Mask=" , hex(mask), "newStatus=", "{0:#0{1}x}".format(newStatus,4))
        self.IC7.setOutputs(bank, newStatus)
        return newStatus

    def enableCore(self):
        ## At power up the Enclustra I2C lines are disabled (tristate buffer is off).
        ## This function enables the lines. It is only required once.
        mystop=True
        print("  Enabling I2C bus (expect 127):")
        myslave= 0x21
        mycmd= [0x01, 0x7F]
        nwords= 1
        self.TLU_I2C.write(myslave, mycmd, mystop)

        mystop=False
        mycmd= [0x01]
        self.TLU_I2C.write(myslave, mycmd, mystop)
        res= self.TLU_I2C.read( myslave, nwords)
        print("\tPost RegDir: ", res)

    def getDUTOutpus(self, dutN, verbose=0):
        if (dutN < 0) | (dutN> (self.nDUTs-1)):
            print("\tERROR: DUTOutputs. The DUT number must be comprised between 0 and ", self.nDUTs-1)
            return -1
        bank= dutN//2 # DUT0 and DUT1 are on bank 0. DUT2 and DUT3 on bank 1
        nibble= dutN%2 # DUT0 and DUT2 are on nibble 0. DUT1 and DUT3 are on nibble 1
        res= self.IC6.getOutputs(bank)
        dut_status= res[0]
        dut_lines= ["CONT", "SPARE", "TRIG", "BUSY"]
        dut_status= 0x0F & (dut_status >> (4*nibble))

        if verbose > 0:
            for idx, iLine in enumerate(dut_lines):
                this_bit= 0x1 & (dut_status  >> idx)
                if this_bit:
                    this_status= "ENABLED"
                else:
                    this_status= "DISABLED"
                print("\t", iLine, "output is", this_status)

        if verbose > 1:
            print("\tDUT CURRENT:", hex(dut_status), "Nibble:", nibble, "Bank:", bank)

        return dut_status

    def getAllChannelsCounts(self):
        chCounts=[]
        for ch in range (0,self.nChannels):
            chCounts.append(int(self.getChCount(ch)))
        return chCounts

    def getChStatus(self):
        inputStatus= self.hw.getNode("triggerInputs.SerdesRstR").read()
        self.hw.dispatch()
        print("\tTRIGGER COUNTERS status= " , hex(inputStatus))
        return inputStatus

    def getChCount(self, channel):
        regString= "triggerInputs.ThrCount"+ str(channel)+"R"
        count = self.hw.getNode(regString).read()
        self.hw.dispatch()
        print("\tCh", channel, "Count:" , count)
        return count

    def getClockStatus(self):
        clockStatus = self.hw.getNode("logic_clocks.LogicClocksCSR").read()
        self.hw.dispatch()
        print("  CLOCK STATUS [expected 1]")
        print("\t", hex(clockStatus))
        if ( clockStatus == 0 ):
            "ERROR: Clocks in TLU FPGA are not locked."
        return clockStatus

    def getDUTmask(self):
        DUTMaskR = self.hw.getNode("DUTInterfaces.DUTMaskR").read()
        self.hw.dispatch()
        print("\tDUTMask read back as:" , hex(DUTMaskR))
        return DUTMaskR

    def getExternalVeto(self):
        extVeto= self.hw.getNode("triggerLogic.ExternalTriggerVetoR").read()
        self.hw.dispatch()
        print("\tEXTERNAL Veto read back as:", hex(extVeto))
        return extVeto

    def getFifoData(self, nWords):
    	#fifoData= self.hw.getNode("eventBuffer.EventFifoData").read()
    	fifoData= self.hw.getNode("eventBuffer.EventFifoData").readBlock(nWords)
    	self.hw.dispatch()
    	#print "\tFIFO Data:", hex(fifoData)
    	return fifoData

    def getFifoLevel(self, verbose= 0):
        FifoFill= self.hw.getNode("eventBuffer.EventFifoFillLevel").read()
        self.hw.dispatch()
        if (verbose > 0):
            print("\tFIFO level read back as:", hex(FifoFill))
        return FifoFill

    def getFifoCSR(self):
        FifoCSR= self.hw.getNode("eventBuffer.EventFifoCSR").read()
        self.hw.dispatch()
        print("\tFIFO CSR read back as:", hex(FifoCSR))
        return FifoCSR

    def getFifoFlags(self):
        # Useless?
        FifoFLAG= self.hw.getNode("eventBuffer.EventFifoFillLevelFlags").read()
        self.hw.dispatch()
        print("\tFIFO FLAGS read back as:", hex(FifoFLAG))
        return FifoFLAG

    def getInternalTrg(self):
        trigIntervalR = self.hw.getNode("triggerLogic.InternalTriggerIntervalR").read()
        self.hw.dispatch()
        print("\tInternal interval read back as:", trigIntervalR)
        return trigIntervalR

    def getMode(self):
        DUTInterfaceModeR = self.hw.getNode("DUTInterfaces.DUTInterfaceModeR").read()
        self.hw.dispatch()
        print("\tDUT mode read back as:" , hex(DUTInterfaceModeR))
        return DUTInterfaceModeR

    def getModeModifier(self):
        DUTInterfaceModeModifierR = self.hw.getNode("DUTInterfaces.DUTInterfaceModeModifierR").read()
        self.hw.dispatch()
        print("\tDUT mode modifier read back as:" , hex(DUTInterfaceModeModifierR))
        return DUTInterfaceModeModifierR

    def getSN(self):
        epromcontent=self.readEEPROM(0xfa, 6)
        print("  FMC-TLU serial number (EEPROM):")
        result="\t"
        for iaddr in epromcontent:
            result+="%02x "%(iaddr)
        print(result)
        return epromcontent

    def getPostVetoTrg(self):
        triggerN = self.hw.getNode("triggerLogic.PostVetoTriggersR").read()
        self.hw.dispatch()
        print("\tPOST VETO TRIGGER NUMBER:", (triggerN))
        return triggerN

    def getPulseDelay(self):
        pulseDelayR = self.hw.getNode("triggerLogic.PulseDelayR").read()
        self.hw.dispatch()
        print("\tPulse delay read back as:", hex(pulseDelayR))
        return pulseDelayR

    def getPulseStretch(self):
        pulseStretchR = self.hw.getNode("triggerLogic.PulseStretchR").read()
        self.hw.dispatch()
        print("\tPulse stretch read back as:", hex(pulseStretchR))
        return pulseStretchR

    def getRecordDataStatus(self):
        RecordStatus= self.hw.getNode("Event_Formatter.Enable_Record_Data").read()
        self.hw.dispatch()
        print("\tData recording:", RecordStatus)
        return RecordStatus

    def getTriggerVetoStatus(self):
        trgVetoStatus= self.hw.getNode("triggerLogic.TriggerVetoR").read()
        self.hw.dispatch()
        print("\tTrigger veto status read back as:", trgVetoStatus)
        return trgVetoStatus

    def getTrgPattern(self):
        triggerPattern_low = self.hw.getNode("triggerLogic.TriggerPattern_lowR").read()
        triggerPattern_high = self.hw.getNode("triggerLogic.TriggerPattern_highR").read()
        self.hw.dispatch()
        print("\tTrigger pattern read back as: 0x%08X 0x%08X" %(triggerPattern_high, triggerPattern_low))
        return triggerPattern_low, triggerPattern_high

    def getVetoDUT(self):
        IgnoreDUTBusyR = self.hw.getNode("DUTInterfaces.IgnoreDUTBusyR").read()
        self.hw.dispatch()
        print("\tIgnoreDUTBusy read back as:" , hex(IgnoreDUTBusyR))
        return IgnoreDUTBusyR

    def getVetoShutters(self):
        IgnoreShutterVeto = self.hw.getNode("DUTInterfaces.IgnoreShutterVetoR").read()
        self.hw.dispatch()
        print("\tIgnoreShutterVeto read back as:" , IgnoreShutterVeto)
        return IgnoreShutterVeto

#    def pulseT0(self):
#        cmd = int("0x1",16)
#        self.hw.getNode("Shutter.PulseT0").write(cmd)
#        self.hw.dispatch()
#        print "\tPulsing T0"


    def setRunActive(self):
        cmd = int("0x1",16)
        self.hw.getNode("Shutter.RunActiveRW").write(cmd)
        self.hw.dispatch()
        print("\tSet run active (pulses T0)")

    def setRunInactive(self):
        cmd = int("0x0",16)
        self.hw.getNode("Shutter.RunActiveRW").write(cmd)
        self.hw.dispatch()
        print("\tSet run inactive")

    def readEEPROM(self, startadd, bytes):
        mystop= 1
        time.sleep(0.1)
        myaddr= [startadd]#0xfa
        self.TLU_I2C.write( 0x50, [startadd], mystop)
        res= self.TLU_I2C.read( 0x50, bytes)
        return res

    def resetClock(self):
        # Set the RST pin from the PLL to 1
        print("  Clocks reset")
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
    	print("\tTrigger counters reset")

    def resetSerdes(self):
        cmd = int("0x3",16)
        self.setChStatus(cmd)
        inputStatus= self.getChStatus()
        print("\t  Input status during reset = " , hex(inputStatus))

        cmd = int("0x0",16)
        self.setChStatus(cmd)
        inputStatus= self.getChStatus()
        print("\t  Input status after reset = " , hex(inputStatus))

        cmd = int("0x4",16)
        self.setChStatus(cmd)
        inputStatus= self.getChStatus()
        print("\t  Input status during calibration = " , hex(inputStatus))

        cmd = int("0x0",16)
        self.setChStatus(cmd)
        inputStatus= self.getChStatus()
        print("\t  Input status after calibration = " , hex(inputStatus))

    def restoreClock(self):
        # Set the RST pin from the PLL to 0
        print("  Clocks restore")
        cmd = int("0x0",16)
        self.hw.getNode("logic_clocks.LogicRst").write(cmd)
        self.hw.dispatch()

    def setChStatus(self, cmd):
        self.hw.getNode("triggerInputs.SerdesRstW").write(cmd)
        inputStatus= self.hw.getNode("triggerInputs.SerdesRstR").read()
        self.hw.dispatch()
        print("  INPUT STATUS SET TO= " , hex(inputStatus))

    def setClockStatus(self, cmd):
        # Only use this for testing. The clock source is actually selected in the Si5345.
        self.hw.getNode("logic_clocks.LogicClocksCSR").write(cmd)
        self.hw.dispatch()

    def setDUTmask(self, DUTMask):
        print("  DUT MASK ENABLING: Mask= " , hex(DUTMask))
        self.hw.getNode("DUTInterfaces.DUTMaskW").write(DUTMask)
        self.hw.dispatch()
        self.getDUTmask()

    def setFifoCSR(self, cmd):
        self.hw.getNode("eventBuffer.EventFifoCSR").write(cmd)
        self.hw.dispatch()
        self.getFifoCSR()

    def setInternalTrg(self, triggerInterval):
        print("  TRIGGERS INTERNAL:")
        if triggerInterval == 0:
            internalTriggerFreq = 0
            print("\tdisabled")
        else:
            internalTriggerFreq = 160000000.0/triggerInterval
            print("\tRequired internal trigger frequency:", triggerInterval, "Hz")
            print("\tSetting internal interval to:", internalTriggerFreq)
        self.hw.getNode("triggerLogic.InternalTriggerIntervalW").write(int(internalTriggerFreq))
        self.hw.dispatch()
        self.getInternalTrg()

    def setMode(self, mode):
        print("  DUT MODE SET TO: ", hex(mode))
        self.hw.getNode("DUTInterfaces.DUTInterfaceModeW").write(mode)
        self.hw.dispatch()
        self.getMode()

    def setModeModifier(self, modifier):
        print("  DUT MODE MODIFIER:", hex(modifier))
        self.hw.getNode("DUTInterfaces.DUTInterfaceModeModifierW").write(modifier)
        self.hw.dispatch()
        self.getModeModifier()

    def setPulseDelay(self, inArray):
        print("  TRIGGER DELAY SET TO", inArray, "[Units= 160MHz clock, 5-bit values (one per input) packed in to 32-bit word]")
        pulseDelay= self.packBits(inArray)
        self.hw.getNode("triggerLogic.PulseDelayW").write(pulseDelay)
        self.hw.dispatch()
        self.getPulseDelay()

    def setPulseStretch(self, inArray):
        print("  INPUT COINCIDENCE WINDOW SET TO", inArray ,"[Units= 160MHz clock cycles, 5-bit values (one per input) packed in to 32-bit word]")
        pulseStretch= self.packBits(inArray)
        self.hw.getNode("triggerLogic.PulseStretchW").write(pulseStretch)
        self.hw.dispatch()
        self.getPulseStretch()

    def setRecordDataStatus(self, status=False):
        print("  Data recording set:")
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
        print("  TRIGGER PATTERN (for external triggers) SET TO 0x%08X 0x%08X. Two 32-bit words." %(triggerPatternH, triggerPatternL))
        self.hw.getNode("triggerLogic.TriggerPattern_lowW").write(triggerPatternL)
        self.hw.getNode("triggerLogic.TriggerPattern_highW").write(triggerPatternH)
        self.hw.dispatch()
        self.getTrgPattern()

    def setVetoDUT(self, ignoreDUTBusy):
        print("  VETO IGNORE BY DUT BUSY MASK SET TO" , hex(ignoreDUTBusy))
        self.hw.getNode("DUTInterfaces.IgnoreDUTBusyW").write(ignoreDUTBusy)
        self.hw.dispatch()
        self.getVetoDUT()

    def setVetoShutters(self, newState):
        if newState:
            print("  IgnoreShutterVetoW SET TO LISTEN FOR VETO FROM SHUTTER")
            cmd= int("0x0",16)
        else:
            print("  IgnoreShutterVetoW SET TO IGNORE VETO FROM SHUTTER")
            cmd= int("0x1",16)
        self.hw.getNode("DUTInterfaces.IgnoreShutterVetoW").write(cmd)
        self.hw.dispatch()
        self.getVetoShutters()

    def writeThreshold(self, DACtarget, Vtarget, channel, verbose=False):
        #Writes the threshold. The DAC voltage differs from the threshold voltage because
        #the range is shifted to be symmetrical around 0V.

        #Check if the DACs are using the internal reference
        if (self.intRefOn):
            Vref= self.VrefInt
        else:
            Vref= self.VrefExt

        #Calculate offset voltage (because of the following shifter)
        Vdac= ( Vtarget + Vref ) / 2
        print("  THRESHOLD setting:")
        if channel==7:
            print("\tCH: ALL")
        else:
            print("\tCH:", channel)
        print("\tTarget V:", Vtarget)
        dacValue = 0xFFFF * (Vdac / Vref)
        DACtarget.writeDAC(int(dacValue), channel, verbose)

    def packBits(self, raw_values):
        packed_bits= 0
        if (len(raw_values) != self.nChannels):
            print("Error (packBits): wrong number of elements in array")
        else:
            for idx, iCh in enumerate(raw_values):
                tmpint= iCh << idx*5
                packed_bits= packed_bits | tmpint
        print("\tPacked =", hex(packed_bits))
        return packed_bits

    def parseFifoData(self, fifoData, nEvents, mystruct, root_tree, verbose):
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
                print("====== EVENT", evNum, "=================================================")
                print("[", hex(word0), "]", "\t TYPE", hex(evType), "\t TRIGGER", hex(inTrig), "\t TIMESTAMP", (tStamp))
                print("[",hex(word1), "]", "\tEV NUM", evNum, "\tFINETS[0,3]", hex(fineTs))
                print("[",hex(word2), "]", "\tFINETS[4,11]", hex(word2))
                print(fineTsList)
            fineTsList.insert(0, tStamp)
            fineTsList.insert(0, evNum)
            if (root_tree != None):
                highWord= word0
                lowWord= word1
                extWord= word2
                timeStamp= tStamp
                bufPos= 0
                evtNumber= evNum
                evtType= evType
                trigsFired= inTrig
                mystruct.raw0= fifoData[index]
                mystruct.raw1= fifoData[index+1]
                mystruct.raw2= fifoData[index+2]
                mystruct.raw3= fifoData[index+3]
                mystruct.raw4= fifoData[index+4]
                mystruct.raw5= fifoData[index+5]
                mystruct.evtNumber= evNum
                mystruct.tluTimeStamp= tStamp
                mystruct.tluEvtType= evType
                mystruct.tluTrigFired= inTrig
                root_tree.Fill()

            outList.insert(len(outList), fineTsList)
        #print "=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-="
        #print "EN#\tCOARSE_TS\tFINE_TS0...FINE_TS11"
        #pprint.pprint(outList)
        return outList

    def plotFifoData(self, outList):
        import matplotlib.pyplot as plt
        import numpy as np
        import matplotlib.mlab as mlab

        coarseColumn= [row[1] for row in outList]
        fineColumn= [row[2] for row in outList]
        timeStamp= [sum(x) for x in zip(coarseColumn, fineColumn)]
        correctTs= [-1]*len(coarseColumn)
        coarseVal= 0.000000025 #coarse time value (40 Mhz, 25 ns)
        fineVal=   0.00000000078125 #fine time value (1280 MHz, 0.78125 ns)
        for iTs in range(0, len(coarseColumn)):
            correctTs[iTs]= coarseColumn[iTs]*coarseVal + fineColumn[iTs]*fineVal
            #if iTs:
                #print correctTs[iTs]-correctTs[iTs-1], "\t ", correctTs[iTs], "\t", coarseColumn[iTs], "\t", fineColumn[iTs]

        xdiff = np.diff(correctTs)
        np.all(xdiff[0] == xdiff)
        P= 1000000000 #display in ns
        nsDeltas = [x * P for x in xdiff]
        #centerRange= np.mean(nsDeltas)
        centerRange= 476
        windowsns= 30
        minRange= centerRange-windowsns
        maxRange= centerRange+windowsns
        plt.hist(nsDeltas, 60, range=[minRange, maxRange], facecolor='blue', align='mid', alpha= 0.75)
        #plt.hist(nsDeltas, 100, normed=True, facecolor='blue', align='mid', alpha=0.75)
        #plt.xlim((min(nsDeltas), max(nsDeltas)))
        plt.xlabel('Time (ns)')
        plt.ylabel('Entries')
        plt.title('Histogram DeltaTime')
        plt.grid(True)

        #Superimpose Gauss
        mean = np.mean(nsDeltas)
        variance = np.var(nsDeltas)
        sigma = np.sqrt(variance)
        x = np.linspace(min(nsDeltas), max(nsDeltas), 100)
        plt.plot(x, mlab.normpdf(x, mean, sigma))

        #Display plot
        plt.show()

    def saveFifoData(self, outList):
        import csv
        with open("output.csv", "wb") as f:
            writer = csv.writer(f)
            writer.writerows(outList)

##################################################################################################################################
##################################################################################################################################
    def acquire(self, mystruct, root_tree= None):
        print("STARTING ACQUIRE LOOP")
        print("Run#" , self.runN, "\n")
        self.isRunning= True
        index=0
        while (self.isRunning == True):
            eventFifoFillLevel= self.getFifoLevel(0)
            nFifoWords= int(eventFifoFillLevel)
            if (nFifoWords > 0):
                fifoData= self.getFifoData(nFifoWords)
                outList= self.parseFifoData(fifoData, nFifoWords/6, mystruct, root_tree, False)

            time.sleep(0.1)
            index= index + nFifoWords/6
        print("STOPPING ACQUIRE LOOP:", index, "events collected")
        return index

    def configure(self, parsed_cfg):
        print("\nTLU INITIALIZING...")
        section_name= "Producer.fmctlu"

        #READ CONTENT OF EPROM VIA I2C
        self.getSN()

        print("  Turning on software trigger veto")
        cmd = int("0x1",16)
        self.setTriggerVetoStatus(cmd)

        # #Get Verbose setting
        self.verbose= parsed_cfg.getint(section_name, "verbose")


        # #SET DACs
        self.writeThreshold(self.zeDAC1, parsed_cfg.getfloat(section_name, "DACThreshold0"), 1, self.verbose)
        self.writeThreshold(self.zeDAC1, parsed_cfg.getfloat(section_name, "DACThreshold1"), 0, self.verbose)
        self.writeThreshold(self.zeDAC2, parsed_cfg.getfloat(section_name, "DACThreshold2"), 3, self.verbose)
        self.writeThreshold(self.zeDAC2, parsed_cfg.getfloat(section_name, "DACThreshold3"), 2, self.verbose)
        self.writeThreshold(self.zeDAC2, parsed_cfg.getfloat(section_name, "DACThreshold4"), 1, self.verbose)
        self.writeThreshold(self.zeDAC2, parsed_cfg.getfloat(section_name, "DACThreshold5"), 0, self.verbose)

        #
        # #ENABLE/DISABLE HDMI OUTPUTS
        self.DUTOutputs(0, int(parsed_cfg.get(section_name, "HDMI1_set"), 16) , self.verbose)
        self.DUTOutputs(1, int(parsed_cfg.get(section_name, "HDMI2_set"), 16) , self.verbose)
        self.DUTOutputs(2, int(parsed_cfg.get(section_name, "HDMI3_set"), 16) , self.verbose)
        self.DUTOutputs(3, int(parsed_cfg.get(section_name, "HDMI4_set"), 16) , self.verbose)

        # #SELECT CLOCK SOURCE TO HDMI
        self.DUTClkSrc(0, int(parsed_cfg.get(section_name, "HDMI1_clk"), 16) , self.verbose)
        self.DUTClkSrc(1, int(parsed_cfg.get(section_name, "HDMI2_clk"), 16) , self.verbose)
        self.DUTClkSrc(2, int(parsed_cfg.get(section_name, "HDMI3_clk"), 16) , self.verbose)
        self.DUTClkSrc(3, int(parsed_cfg.get(section_name, "HDMI4_clk"), 16) , self.verbose)

        # #ENABLE/DISABLE LEMO CLOCK OUTPUT
        self.enableClkLEMO(parsed_cfg.getint(section_name, "LEMOclk"), False)

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

        # # Get inputs status and counters
        self.getChStatus()
        self.getAllChannelsCounts()

        # # Stop internal triggers until setup complete
        cmd = int("0x0",16)
        self.setInternalTrg(cmd)

        # # Set the control voltages for the PMTs
        PMT1_V= parsed_cfg.getfloat(section_name, "PMT1_V")
        PMT2_V= parsed_cfg.getfloat(section_name, "PMT2_V")
        PMT3_V= parsed_cfg.getfloat(section_name, "PMT3_V")
        PMT4_V= parsed_cfg.getfloat(section_name, "PMT4_V")
        self.pwdled.setVch(0, PMT1_V, True)
        self.pwdled.setVch(1, PMT2_V, True)
        self.pwdled.setVch(2, PMT3_V, True)
        self.pwdled.setVch(3, PMT4_V, True)

        # # Set pulse stretches
        str0= parsed_cfg.getint(section_name, "in0_STR")
        str1= parsed_cfg.getint(section_name, "in1_STR")
        str2= parsed_cfg.getint(section_name, "in2_STR")
        str3= parsed_cfg.getint(section_name, "in3_STR")
        str4= parsed_cfg.getint(section_name, "in4_STR")
        str5= parsed_cfg.getint(section_name, "in5_STR")
        self.setPulseStretch([str0, str1, str2, str3, str4, str5])

        # # Set pulse delays
        del0= parsed_cfg.getint(section_name, "in0_DEL")
        del1= parsed_cfg.getint(section_name, "in1_DEL")
        del2= parsed_cfg.getint(section_name, "in2_DEL")
        del3= parsed_cfg.getint(section_name, "in3_DEL")
        del4= parsed_cfg.getint(section_name, "in4_DEL")
        del5= parsed_cfg.getint(section_name, "in5_DEL")
        self.setPulseDelay([del0, del1, del2, del3, del4, del5])

        # # Set trigger pattern
        triggerPattern_low= int(parsed_cfg.get(section_name, "trigMaskLo"), 16)
        triggerPattern_high= int(parsed_cfg.get(section_name, "trigMaskHi"), 16)
        self.setTrgPattern(triggerPattern_high, triggerPattern_low)

        # # Set active DUTs
        DUTMask= int(parsed_cfg.get(section_name, "DUTMask"), 16)
        self.setDUTmask(DUTMask)

        # # Set mode (AIDA, EUDET)
        DUTMode= int(parsed_cfg.get(section_name, "DUTMaskMode"), 16)
        self.setMode(DUTMode)

        # # Set modifier
        modifier = int(parsed_cfg.get(section_name, "DUTMaskModeModifier"), 16)
        self.setModeModifier(modifier)

        # # Set veto shutter
        setVetoShutters = int(parsed_cfg.get(section_name, "DUTIgnoreShutterVeto"), 16)
        self.setVetoShutters(setVetoShutters)

        # # Set veto by DUT
        ignoreDUTBusy = int(parsed_cfg.get(section_name, "DUTIgnoreBusy"), 16)
        self.setVetoDUT(ignoreDUTBusy)

        print("  Check external veto:")
        self.getExternalVeto()

        # # Set trigger interval (use 0 to disable internal triggers)
        triggerInterval= parsed_cfg.getint(section_name, "InternalTriggerFreq")
        self.setInternalTrg(triggerInterval)

        print("TLU INITIALIZED")

##################################################################################################################################
##################################################################################################################################
    def start(self, logtimestamps=False, runN=0, mystruct= None, root_tree= None):
        print("TLU STARTING...")
        self.runN= runN

        print("  FIFO RESET:")
        FIFOcmd= 0x2
        self.setFifoCSR(FIFOcmd)
        eventFifoFillLevel= self.getFifoLevel()
        #cmd = int("0x000",16)
        #self.setInternalTrg(cmd)

        if logtimestamps:
            self.setRecordDataStatus(True)
        else:
            self.setRecordDataStatus(False)

        # Pulse T0
        #self.pulseT0()
        # Set run active
        self.setRunActive()

        print("  Turning off software trigger veto")
        self.setTriggerVetoStatus( int("0x0",16) )

        print("TLU STARTED")

        # nEvents= self.acquire(mystruct, root_tree)
        return


##################################################################################################################################
##################################################################################################################################
    def stop(self, saveD= False, plotD= False):
        print("TLU STOPPING...")

        self.getPostVetoTrg()
        eventFifoFillLevel= self.getFifoLevel()
        self.getFifoFlags()
        self.getFifoCSR()
        print("  Turning on software trigger veto")
        self.setTriggerVetoStatus( int("0x1",16) )

        print("Turning off shutter (setting run inactive)")
        self.setRunInactive()

        nFifoWords= int(eventFifoFillLevel)
        fifoData= self.getFifoData(nFifoWords)

        #outList= self.parseFifoData(fifoData, nFifoWords/6, None, None, True)
        #if saveD:
        #    self.saveFifoData(outList)
        #if plotD:
        #    self.plotFifoData(outList)
        #outFile = open('./test.txt', 'w')
        #for iData in range (0, 30):
    	#    outFile.write("%s\n" % fifoData[iData])
        #    print hex(fifoData[iData])
        print("TLU STOPPED")
        return
