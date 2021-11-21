# -*- coding: utf-8 -*-
import uhal
from packages.I2CuHal2 import I2CCore
import time

import math
import numpy as np

#######################################################################################
class CFA632:
    #Class to configure the CFA632 display

    def __init__(self, i2c, slaveaddr=0x2A):
        self.i2c = i2c
        self.slaveaddr = slaveaddr

    def test(self):
        print("Testing the display")
        return

    def writeSomething(self, i2ccmd):
        mystop= True
        print("Write to CFA632")
        print("\t", i2ccmd)
        #myaddr= [int(i2ccmd)]
        self.i2c.write( self.slaveaddr, i2ccmd, mystop)
        return

#######################################################################################
class LCD_ada:
    def __init__(self, i2c, slaveaddr=0x20):
        self.i2c = i2c
        self.slaveaddr = slaveaddr
        self.nRows= 2
        self.nCols= 16

    def test(self):
        mystop= True
        i2ccmd= []
        print("Write to LCD_ada")
        print("\t", i2ccmd)
        #myaddr= [int(i2ccmd)]
        self.getIOdir()
        self.setIOdir(0x7F)
        self.getIOdir()
        self.setGPIO(0x80)
        self.i2c.write( self.slaveaddr, i2ccmd, mystop)

    def getGPIO(self):
        # Read port (if configured as inputs)
        mystop=False
        regN= 0x09
        nwords= 1
        self.i2c.write( self.slaveaddr, [regN], mystop)
        res= self.i2c.read( self.slaveaddr, nwords)
        print("MCP23008 IOdir", res)
        return res

    def setGPIO(self, gpio):
        # Sets the output latch
        mystop= True
        i2ccmd= [9, gpio]
        print("Write GPIO to MCP23008")
        self.i2c.write( self.slaveaddr, i2ccmd, mystop)

    def getIOdir(self):
        mystop=False
        regN= 0x00
        nwords= 1
        self.i2c.write( self.slaveaddr, [regN], mystop)
        res= self.i2c.read( self.slaveaddr, nwords)
        print("MCP23008 IOdir", res)
        return res

    def setIOdir(self, iodir):
        # 1 indicates the port is an input
        # 0 indicates the port is an output
        mystop= True
        i2ccmd= [0, iodir]
        print("Write IODIR to MCP23008")
        self.i2c.write( self.slaveaddr, i2ccmd, mystop)

#######################################################################################
class LCD09052:
    #Class to configure the LCD09052 display

    def __init__(self, i2c, slaveaddr=0x3A):
        self.i2c = i2c
        self.slaveaddr = slaveaddr
        self.nRows= 2
        self.nCols= 16
        self.setLCDtype(self.nRows, self.nCols)

    def test(self):
        print("\tTesting display (LCD09052)")
        self.clear()
        self.setBrightness(0)
        time.sleep(0.2)
        self.setBrightness(250)
        time.sleep(0.2)
        self.setBrightness(0)
        time.sleep(0.2)
        self.setBrightness(250)
        for ipos in range(1, 17):
            self.writeChar(33)
            self.posCursor(1, ipos-1)
            time.sleep(0.1)
            self.writeChar(254)
        self.posCursor(2, 1)
        for ipos in range(1, 17):
            self.writeChar(33)
            self.posCursor(2, ipos-1)
            time.sleep(0.1)
            self.writeChar(254)
        self.clear
        self.clearLine(1)
        self.writeChar(33)
        time.sleep(0.1)
        self.writeChar(33)
        time.sleep(0.1)
        self.writeChar(33)
        time.sleep(0.1)
        self.writeChar(33)
        time.sleep(0.1)
        self.writeChar(33)
        time.sleep(0.1)
        self.clearLine(1)
        self.writeString([80, 81, 80, 81, 82])
        return

    def test2(self, myString1= "", myString2= ""):
        #myString= [80, 81, 80, 81, 82]
        self.clear()
        self.dispString(myString1)
        self.posCursor(2, 1)
        self.dispString(myString2)
        self.pulseLCD(1)
        time.sleep(0.3)
        myChar= [0, 17, 0, 0, 17, 14, 0, 0]
        #self.writeChar(1)
        #time.sleep(1)
        #self.createChar(1, [31, 31, 31, 0, 17, 14, 0, 0])
        #self.createChar(2, [0, 0, 17, 0, 0, 17, 14, 0])
        #time.sleep(1)
        #self.writeChar(1)
        return

    def dispString(self, myString):
    ### Writes the string on the display
        myInts=[]
        for iChar in list(myString):
            myInts.append(ord(iChar))
        self.writeString(myInts)
        return

    def writeString(self, myChars):
    ### Writes a list of chars from the current position of the cursor
    ##  NOTE: myChars is a list of integers corresponding to the ASCII code of each
    ##  character to be printed. Use "dispString" to input an actual string.
        #i2ccmd= [1, myChars]
        myChars.insert(0, 1)
        mystop= True
        self.i2c.write( self.slaveaddr, myChars, mystop)

    def posCursor(self, line, pos):
    ### Position the cursor on a specific location
    ##  line can be 1 (top) or 2 (bottom)
    ##  pos can be [1, 16}
        if ( ((line==1) or (line==2)) and (1 <= pos <= self.nCols)):
            i2ccmd= [2, line, pos]
            mystop= True
            self.i2c.write( self.slaveaddr, i2ccmd, mystop)
        else:
            print("Cursor line can only be 1 or 2, position must be in range [1,", self.nCols, "]")

    def clearLine(self, iLine):
    ### Clear line. Place cursor at beginning of line.
        if ((iLine==1) or (iLine==2)):
            i2ccmd= [3, iLine]
            mystop= True
            self.i2c.write( self.slaveaddr, i2ccmd, mystop)

    def clear(self):
    ### Clears the display and locates the curson on position (1,1), i.e. top left
        i2ccmd= [4]
        mystop= True
        self.i2c.write( self.slaveaddr, i2ccmd, mystop)

    def setLCDtype(self, nLines, nColumns):
    ### Specifies the number of lines and columns in the display.
    ##  This does not seem to do much but we use it anyway.
    ##  NOTE: no check is performed on the nLines and nColumns parameters so be
    ##  carefuls in using this function.
        i2ccmd= [5, nLines, nColumns]
        mystop= True
        self.i2c.write( self.slaveaddr, i2ccmd, mystop)

    def setBrightness(self, value= 250):
    ### Sets the brightness level of the backlight.
    ##  Value is an integer in range [0, 250]. 0= no light, 250= maximum light.
        if value < 0:
            print("setBrightness: minimum value= 0. Coherced to 0")
            value = 0
        if value > 250:
            print("setBrightness: maximum value= 250. Coherced to 250")
            value = 250
        i2ccmd= [7, value]
        mystop= True
        self.i2c.write( self.slaveaddr, i2ccmd, mystop)

    def writeChar(self, value):
    ### Writes a char in the current cursor position
    ##  The cursor is then shifted right one position
    ##  value must be an integer corresponding to the ascii code of the character
        i2ccmd= [10, value]
        mystop= True
        self.i2c.write( self.slaveaddr, i2ccmd, mystop)
        return

    def createChar(self, pos=1, myChar=[]):
    ### Define a personalized character and stores it in position "pos"
    ##  NOTE: This is not working yet.
        mystop= True
        myChar= [0, 17, 0, 0, 17, 14, 0, 0]
        myChar.insert(0, 64)
        self.i2c.write( self.slaveaddr, myChar, mystop)
        return

    def writeSomething(self, i2ccmd):
        mystop= True
        print("Write to LCD09052")
        print("\t", i2ccmd)
        #myaddr= [int(i2ccmd)]
        self.i2c.write( self.slaveaddr, i2ccmd, mystop)
        return

    def pulseLCD(self, nCycles):
    ### Sets the backlight to pulse for N cycles.
    ##  Each cycle lasts approximately 1.5 s and start/stop on full brightness
    ##  The light varies according to a sinusoidal wave
        startP= 0
        endP= nCycles*(math.pi)
        nPoints= 15*nCycles
        myList= np.linspace(startP, endP, nPoints).tolist()
        for iPt in myList:
            iBright= int(250*abs(math.cos(iPt)))
            self.setBrightness(iBright)
            time.sleep(0.1)
