# -*- coding: utf-8 -*-
import uhal
from packages.I2CuHal import I2CCore


class PCA9539PW:
    #Class to configure the expander modules

    def __init__(self, i2c, slaveaddr=0x74):
        self.i2c = i2c
        self.slaveaddr = slaveaddr


    def writeReg(self, regN, regContent, verbose=False):
        #Basic functionality to write to register.
        if (regN < 0) | (regN > 7):
            print("PCA9539PW - ERROR: register number should be in range [0:7]")
            return
        regContent= regContent & 0xFF
        mystop=True
        cmd= [regN, regContent]
        self.i2c.write( self.slaveaddr, cmd, mystop)


    def readReg(self, regN, nwords, verbose=False):
        #Basic functionality to read from register.
        if (regN < 0) | (regN > 7):
            print("PCA9539PW - ERROR: register number should be in range [0:7]")
            return
        mystop=False
        self.i2c.write( self.slaveaddr, [regN], mystop)
        res= self.i2c.read( self.slaveaddr, nwords)
        return res


    def setInvertReg(self, regN, polarity= 0x00):
        #Set the content of register 4 or 5 which determine the polarity of the
        #ports (0= normal, 1= inverted).
        if (regN < 0) | (regN > 1):
            print("PCA9539PW - ERROR: regN should be 0 or 1")
            return
        polarity = polarity & 0xFF
        self.writeReg(regN+4, polarity)

    def getInvertReg(self, regN):
        #Read the content of register 4 or 5 which determine the polarity of the
        #ports (0= normal, 1= inverted).
        if (regN < 0) | (regN > 1):
            print("PCA9539PW - ERROR: regN should be 0 or 1")
            return
        res= self.readReg(regN+4, 1)
        return res

    def setIOReg(self, regN, direction= 0xFF):
        #Set the content of register 6 or 7 which determine the direction of the
        #ports (0= output, 1= input).
        if (regN < 0) | (regN > 1):
            print("PCA9539PW - ERROR: regN should be 0 or 1")
            return
        direction = direction & 0xFF
        self.writeReg(regN+6, direction)

    def getIOReg(self, regN):
        #Read the content of register 6 or 7 which determine the polarity of the
        #ports (0= normal, 1= inverted).
        if (regN < 0) | (regN > 1):
            print("PCA9539PW - ERROR: regN should be 0 or 1")
            return
        res= self.readReg(regN+6, 1)
        return res

    def getInputs(self, bank):
        #Read the incoming values of the pins for one of the two 8-bit banks.
        if (bank < 0) | (bank > 1):
            print("PCA9539PW - ERROR: bank should be 0 or 1")
            return
        res= self.readReg(bank, 1)
        return res

    def setOutputs(self, bank, values= 0x00):
        #Set the content of the output flip-flops.
        if (bank < 0) | (bank > 1):
            print("PCA9539PW - ERROR: bank should be 0 or 1")
            return
        values = values & 0xFF
        self.writeReg(bank+2, values)

    def getOutputs(self, bank):
        #Read the state of the outputs (i.e. what value is being written to them)
        if (bank < 0) | (bank > 1):
            print("PCA9539PW - ERROR: bank should be 0 or 1")
            return
        res= self.readReg(bank+2, 1)
        return res
