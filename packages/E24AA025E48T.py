# -*- coding: utf-8 -*-
import uhal
from I2CuHal import I2CCore
import StringIO

class E24AA025E48T:
    #Class to configure the EEPROM

    def __init__(self, i2c, slaveaddr=0x50):
        self.i2c = i2c
        self.slaveaddr = slaveaddr


    def readEEPROM(self, startadd, nBytes):
        #Read EEPROM memory locations
        mystop= False
        myaddr= [startadd]#0xfa
        self.i2c.write( self.slaveaddr, [startadd], mystop)
        res= self.i2c.read( self.slaveaddr, nBytes)
        return res
