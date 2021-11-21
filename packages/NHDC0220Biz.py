# -*- coding: utf-8 -*-
import uhal
from I2CuHal import I2CCore
import StringIO

class NHDC0220Biz:
    #Class to configure the EEPROM

    def __init__(self, i2c, slaveaddr=0x3c):
        self.i2c = i2c
        self.slaveaddr = 0x2a#slaveaddr

    def test(self):
	print "Testing the display"
	return
    
    def writeSomething(self):
	mystop= True
	print "Write random stuff"
	myaddr= [0x08, 0x38]
	self.i2c.write( self.slaveaddr, myaddr, mystop)
	
	return
