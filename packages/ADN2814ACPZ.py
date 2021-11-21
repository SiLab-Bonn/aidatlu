# -*- coding: utf-8 -*-
import uhal
from I2CuHal import I2CCore
import StringIO
import math

class ADN2814ACPZ:
    #Class to configure the ADN2814 clock and data recovery chip (CDR)
    # The I2C address can either be 0x40 or 0x60

    def __init__(self, i2c, slaveaddr=0x40):
        self.i2c = i2c
        self.slaveaddr = slaveaddr
        self.regDictionary= {'freq0': 0x0, 'freq1': 0x1, 'freq2': 0x2, 'rate': 0x3, 'misc': 0x4, 'ctrla': 0x8, 'ctrlb': 0x9, 'ctrlc': 0x11}

    def writeReg(self, regN, regContent, verbose=False):
        #Basic functionality to write to register.
        regContent= regContent & 0xFF
        mystop=True
        cmd= [regN, regContent]
        self.i2c.write( self.slaveaddr, cmd, mystop)


    def readReg(self, regN, nwords, verbose=False):
        #Basic functionality to read from register.
        mystop=False
        self.i2c.write( self.slaveaddr, [regN], mystop)
        res= self.i2c.read( self.slaveaddr, nwords)
        return res

    def readf0(self, verbose=False):
        res= self.readReg(self.regDictionary['freq0'], 1, False)
        if verbose:
            print "\tfreq0 is", res[0]
        return res[0]

    def readf1(self, verbose=False):
        res= self.readReg(self.regDictionary['freq1'], 1, False)
        if verbose:
            print "\tfreq1 is", res[0]
        return res[0]

    def readf2(self, verbose=False):
        res= self.readReg(self.regDictionary['freq2'], 1, False)
        if verbose:
            print "\tfreq2 is", res[0]
        return res[0]

    def readFrequency(self, verbose=False):
        # write 1 to CTRLA[1]
        # reset MISC[2] by writing a 1 followed by a 0 to CTRLB[3]
        # read back MISC[2], if 0 the measurement is not complete (typ 80 ms). If 1 the data rate can be read by reading FREQ[22:0]
        # read FREQ2, FREQ1, FREQ0
        # rate= (FREQ[22:0]xFrefclk)/2^(14+SEL_RATE)

        return

    def readLOLstatus(self, verbose=False):
        # return the status of the LOL bit MISC[3] and the STATIC LOL MISC[4]
        # the STATIC LOL is asserted if a LOL condition occurred and remains asserted
        # until cleared by writing 1 followed by 0 to the CTRLB[6] bit
        misc= self.readReg(self.regDictionary['misc'], 1, False)[0]
        staticLOL= (misc & 0x10000) >> 4
        LOL= (misc & 0x1000) >> 3
        if verbose:
            print "MISC=", misc, "LOL=", LOL, "StaticLOL=", staticLOL
        return [LOL, staticLOL]

    def readRate(self, verbose=False):
        rate_msb= self.readReg(self.regDictionary['rate'], 1, False)[0]
        rate_lsb= self.readReg(self.regDictionary['misc'], 1, False)[0]
        rate_lsb= 0x1 & rate_lsb
        rate= (rate_msb << 1) | rate_lsb
        if verbose:
            print "\tcoarse rate is", rate
        return rate

    def _writeCTRLA(self, fRef, dataRatio, measureDataRate, lockToRef, verbose=False):
        #write content to register CTRLA:
        # fRef: reference frequency in MHz; range is [10 : 160]
        # dataRatio: integer in range [0 : 8] equal to Data Rate/Div_FREF Ratio
        # measureDataRate: set to 1 to measure data rate
        # lockToRef= 0 > lock to input data; 1 > lock to reference clock
        regContent= 0x0
        if fRef < 10:
            print "fRef must be comprised between 10 and 160. Coherced to 10"
            fRef = 10
        if fRef > 160:
            print "fRef must be comprised between 10 and 160. Coherced to 160"
            fRef = 160
        fRefRange={
           10<= fRef <20 : 0x00,
           20<= fRef <40 : 0x01,
           40<= fRef <80 : 0x02,
           80<= fRef <=160 : 0x03,
           }[1]
        fRefRange= fRefRange << 6
        regContent= regContent | fRefRange

        if ((1 <= dataRatio <= 256) & (isinstance(dataRatio, (int, long) )) ):
            ratioValue= math.log(dataRatio, 2)
            ratioValue= int(ratioValue)
        else:
            print "  dataRatio should be an integer in the form 2^n with 0<= n <= 8. Coherced to 0"
            ratioValue= 0
        if verbose:
            print "\tratioValue=", ratioValue
        ratioValue = ratioValue << 2
        regContent= regContent | ratioValue

        measureDataRate= (measureDataRate & 0x1) << 1
        lockToRef= lockToRef & 0x1
        regContent= regContent | measureDataRate | lockToRef

        self.writeReg( self.regDictionary['ctrla'], regContent, verbose=False)
        return

    def _writeCTRLB(self, confLOL, rstMisc4, systemReset, rstMisc2, verbose=False):
        #write content to register CTRLB:
        # confLOL=0 > LOL pin normal operation; 1 > LOL pin is static LOL
        # rstMisc4= Write a 1 followed by 0 to reset MISC[4] (staticLOL)
        # systemReset= Write 1 followed by 0 to reset ADN2814
        # rsttMisc2= Write a 1 followed by 0 to reset MISC[2] (data read measure complete)
        regContent= 0x0
        confLOL= (confLOL & 0x1) << 7
        rstMisc4= (rstMisc4 & 0x1) << 6
        systemReset= (systemReset & 0x1) << 5
        rstMisc2= (rstMisc2 & 0x1) << 3
        regContent= regContent | confLOL | rstMisc4 | systemReset | rstMisc2
        self.writeReg( self.regDictionary['ctrlb'], regContent, verbose=False)
        return

    def _writeCTRLC(self, confLOS, squelch, outBoost, verbose=False):
        #write content to register CTRLC:
        # confLOS= 0 > active high LOS; 1 > active low LOS
        # squelch= 0 > squelch CLK and DATA; 1 > squelch CLK or DATA
        # outBoost= 0 > default swing; boost output swing
        regContent= 0x0
        confLOS= (confLOS & 0x1) << 2
        squelch= (squelch & 0x1) << 1
        outBoost= (outBoost & 0x1)
        regContent= regContent | confLOS | squelch | outBoost
        self.writeReg( self.regDictionary['ctrlc'], regContent, verbose=False)
        return
