# -*- coding: utf-8 -*-
import uhal
from packages.I2CuHal import I2CCore


class AD5665R:
    #Class to configure the DAC modules

    def __init__(self, i2c, slaveaddr=0x1F):
        self.i2c = i2c
        self.slaveaddr = slaveaddr


    def setIntRef(self, intRef=False, verbose=False):
        mystop=True
        if intRef:
            cmdDAC= [0x38,0x00,0x01]
        else:
            cmdDAC= [0x38,0x00,0x00]
        self.i2c.write( self.slaveaddr, cmdDAC, mystop)
        if verbose:
            print("  AD5665R")
            print("\tDAC int ref:", intRef)


    def writeDAC(self, dacCode, channel, verbose=False):
        #Vtarget is the required voltage, channel is the DAC channel to target
        #intRef indicates whether to use the external voltage reference (True)
        #or the internal one (False).

        print("\tDAC value:"  , hex(dacCode))
        if channel<0 or channel>7:
            print("writeDAC ERROR: channel",channel,"not in range 0-7 (bit mask)")
            return -1
        if dacCode<0:
            print("writeDAC ERROR: value",dacCode,"<0. Default to 0")
            dacCode=0
        elif dacCode>0xFFFF :
            print("writeDAC ERROR: value",dacCode,">0xFFFF. Default to 0xFFFF")
            dacCode=0xFFFF

        sequence=[( 0x18 + ( channel &0x7 ) ) , int(dacCode/256)&0xff , int(dacCode)&0xff]
        print("\tWriting DAC string:", sequence)
        mystop= False
        self.i2c.write( self.slaveaddr, sequence, mystop)
