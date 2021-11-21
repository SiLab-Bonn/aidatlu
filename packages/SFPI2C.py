# -*- coding: utf-8 -*-
import uhal
from I2CuHal import I2CCore
import StringIO

class SFPI2C:
    #Class to configure the EEPROM

    def __init__(self, i2c, slaveaddr=0x50):
        self.i2c = i2c
        self.slaveaddr = slaveaddr

    """def readEEPROM(self, startadd, nBytes):
        #Read EEPROM memory locations
        mystop= False
        myaddr= [startadd]#0xfa
        self.i2c.write( self.slaveaddr, [startadd], mystop)
        res= self.i2c.read( self.slaveaddr, nBytes)
        return res"""
        
    def _listToString(self, mylist):
        mystring= ""
        for iChar in mylist:
          mystring= mystring + str(unichr(iChar))
        return mystring

    def writeReg(self, regN, regContent, verbose=False):
        #Basic functionality to write to register.
        if (regN < 0) | (regN > 7):
            print "PCA9539PW - ERROR: register number should be in range [0:7]"
            return
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
        
    def getConnector(self):
        """Code for connector type (table 3.4)"""
        conntype= self.readReg(2, 1, False)[0]
        print "Connector type:", hex(conntype)
        return conntype
        
    def getDiagnosticsType(self):
        """Types of diagnostics available (table 3.9)"""
        diaType= self.readReg(92, 1, False)[0]
        print "Available Diagnostics:", hex(diaType)
        return diaType
        
    def getEncoding(self):
        encoding= self.readReg(11, 1, False)[0]
        print "Encoding", encoding
        return encoding
        
    def getEnhancedOpt(self):
        enOpt= self.readReg(93, 1, False)[0]
        print "Enhanced Options:", enOpt
        return enOpt
        
    def getTransceiver(self):
        res= self.readReg(3, 8, False)
        return res

    def getVendorId(self):
        """ Returns the OUI vendor id"""
        vendID= self.readReg(37, 3, False)
        return vendID
        
    def getVendorName(self):
        res= self.readReg( 20 , 16, False)
        mystring= self._listToString(res)
        return mystring
    
    def getVendorPN(self):
        """ Returns the part number defined by the vendor"""
        pn=[]
        mystring= ""
        res= self.readReg( 40 , 16, False)
        mystring= self._listToString(res)
        return mystring

    def scanI2C(self):
        mystop=True
        for iAddr in range (0, 128):
            self.i2c.write( iAddr, [], mystop)
