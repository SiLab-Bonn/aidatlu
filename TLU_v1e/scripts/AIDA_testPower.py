# -*- coding: utf-8 -*-
import uhal
from I2CuHal import I2CCore
import time
#import miniTLU
from si5345 import si5345
from AD5665R import AD5665R
from PCA9539PW import PCA9539PW
from E24AA025E48T import E24AA025E48T

manager = uhal.ConnectionManager("file://./TLUconnection.xml")
hw = manager.getDevice("tlu")

# hw.getNode("A").write(255)
reg = hw.getNode("version").read()
hw.dispatch()
print "CHECK REG= ", hex(reg)


# #First I2C core
print ("Instantiating master I2C core:")
master_I2C= I2CCore(hw, 10, 5, "i2c_master", None)
master_I2C.state()




#
# #######################################
enableCore= False #Only need to run this once, after power-up
if (enableCore):
   mystop=True
   print "  Write RegDir to set I/O[7] to output:"
   myslave= 0x21
   mycmd= [0x01, 0x7F]
   nwords= 1
   master_I2C.write(myslave, mycmd, mystop)

   mystop=False
   mycmd= [0x01]
   master_I2C.write(myslave, mycmd, mystop)
   res= master_I2C.read( myslave, nwords)
   print "\tPost RegDir: ", res


#DAC CONFIGURATION BEGIN
if (False):
   zeDAC1=AD5665R(master_I2C, 0x1C)
   zeDAC1.setIntRef(intRef= False, verbose= True)
   zeDAC1.writeDAC(0x0, 7, verbose= True)#7626

if (True):
   # #I2C EXPANDER CONFIGURATION BEGIN
   IC6=PCA9539PW(master_I2C, 0x76)
   #BANK 0
   IC6.setInvertReg(0, 0x00)# 0= normal
   IC6.setIOReg(0, 0x00)# 0= output <<<<<<<<<<<<<<<<<<<
   IC6.setOutputs(0, 0x00)
   res= IC6.getInputs(0)
   print "IC6 read back bank 0: 0x%X" % res[0]
   #
   #BANK 1
   IC6.setInvertReg(1, 0x00)# 0= normal
   IC6.setIOReg(1, 0x00)# 0= output <<<<<<<<<<<<<<<<<<<
   IC6.setOutputs(1, 0x00)
   res= IC6.getInputs(1)
   print "IC6 read back bank 1: 0x%X" % res[0]

   # # #
   IC7=PCA9539PW(master_I2C, 0x77)
   #BANK 0
   IC7.setInvertReg(0, 0x00)# 0= normal
   IC7.setIOReg(0, 0x00)# 0= output <<<<<<<<<<<<<<<<<<<
   IC7.setOutputs(0, 0x00)
   res= IC7.getInputs(0)
   print "IC7 read back bank 0: 0x%X" % res[0]
   #
   #BANK 1
   IC7.setInvertReg(1, 0x00)# 0= normal
   IC7.setIOReg(1, 0x00)# 0= output <<<<<<<<<<<<<<<<<<<
   IC7.setOutputs(1, 0x00)
   res= IC7.getInputs(1)
   print "IC7 read back bank 1: 0x%X" % res[0]
   # #I2C EXPANDER CONFIGURATION END

