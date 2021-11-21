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
enableCore= True #Only need to run this once, after power-up
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
# #######################################
#
# time.sleep(0.1)
# #Read the EPROM
# mystop=False
# nwords=6
# myslave= 0x53 #DUNE EPROM 0x53 (Possibly)
# myaddr= [0xfa]#0xfa
# master_I2C.write( myslave, myaddr, mystop)
# #res= master_I2C.read( 0x50, 6)
# res= master_I2C.read( myslave, nwords)
# print "  PCB EPROM: "
# result="\t  "
# for iaddr in res:
#    result+="%02x "%(iaddr)
# print result
# #######################################


#Second I2C core
#print ("Instantiating SFP I2C core:")
#clock_I2C= I2CCore(hw, 10, 5, "i2c_sfp", None)
#clock_I2C.state()

# #Third I2C core
# print ("Instantiating clock I2C core:")
# clock_I2C= I2CCore(hw, 10, 5, "i2c_clk", None)
# clock_I2C.state()


# #time.sleep(0.01)
# #Read the EPROM
# mystop=False
# nwords=2
# myslave= 0x68 #DUNE CLOCK CHIP 0x68
# myaddr= [0x02 ]#0xfa
# clock_I2C.write( myslave, myaddr, mystop)
# #time.sleep(0.1)
# res= clock_I2C.read( myslave, nwords)
# print "  CLOCK EPROM: "
# result="\t  "
# for iaddr in res:
#     result+="%02x "%(iaddr)
# print result

#

#CLOCK CONFIGURATION BEGIN
zeClock=si5345(master_I2C, 0x68)
res= zeClock.getDeviceVersion()
zeClock.checkDesignID()
#zeClock.setPage(0, True)
#zeClock.getPage(True)
clkRegList= zeClock.parse_clk("./../../bitFiles/TLU_CLK_Config.txt")
zeClock.writeConfiguration(clkRegList)######
zeClock.writeRegister(0x0536, [0x0B]) #Configures manual switch of inputs
zeClock.writeRegister(0x0949, [0x0F]) #Enable all inputs
zeClock.writeRegister(0x052A, [0x05]) #Configures source of input
iopower= zeClock.readRegister(0x0949, 1)
print "  Clock IO power: 0x%X" % iopower[0]
lol= zeClock.readRegister(0x000E, 1)
print "  Clock LOL: 0x%X" % lol[0]
los= zeClock.readRegister(0x000D, 1)
print "  Clock LOS: 0x%X" % los[0]
#CLOCK CONFIGURATION END

#DAC CONFIGURATION BEGIN
zeDAC1=AD5665R(master_I2C, 0x13)
zeDAC1.setIntRef(intRef= False, verbose= True)
zeDAC1.writeDAC(0x0, 7, verbose= True)#7626

zeDAC2=AD5665R(master_I2C, 0x1F)
zeDAC2.setIntRef(intRef= False, verbose= True)
zeDAC2.writeDAC(0x2fff, 3, verbose= True)
#DAC CONFIGURATION END

#EEPROM BEGIN
zeEEPROM= E24AA025E48T(master_I2C, 0x50)
res=zeEEPROM.readEEPROM(0xfa, 6)
result="  EEPROM ID:\n\t"
for iaddr in res:
    result+="%02x "%(iaddr)
print result
#EEPROM END

# #I2C EXPANDER CONFIGURATION BEGIN
IC6=PCA9539PW(master_I2C, 0x74)
#BANK 0
IC6.setInvertReg(0, 0x00)# 0= normal
IC6.setIOReg(0, 0xFF)# 0= output <<<<<<<<<<<<<<<<<<<
IC6.setOutputs(0, 0xFF)
res= IC6.getInputs(0)
print "IC6 read back bank 0: 0x%X" % res[0]
#
#BANK 1
IC6.setInvertReg(1, 0x00)# 0= normal
IC6.setIOReg(1, 0xFF)# 0= output <<<<<<<<<<<<<<<<<<<
IC6.setOutputs(1, 0xFF)
res= IC6.getInputs(1)
print "IC6 read back bank 1: 0x%X" % res[0]

# # #
IC7=PCA9539PW(master_I2C, 0x75)
#BANK 0
IC7.setInvertReg(0, 0xFF)# 0= normal
IC7.setIOReg(0, 0xFA)# 0= output <<<<<<<<<<<<<<<<<<<
IC7.setOutputs(0, 0xFF)
res= IC7.getInputs(0)
print "IC7 read back bank 0: 0x%X" % res[0]
#
#BANK 1
IC7.setInvertReg(1, 0x00)# 0= normal
IC7.setIOReg(1, 0x0F)# 0= output <<<<<<<<<<<<<<<<<<<
IC7.setOutputs(1, 0xFF)
res= IC7.getInputs(1)
print "IC7 read back bank 1: 0x%X" % res[0]
# #I2C EXPANDER CONFIGURATION END


# #Reset counters
#cmd = int("0x0", 16) #write 0x2 to reset
#hw.getNode("triggerInputs.SerdesRstW").write(cmd)
#restatus= hw.getNode("triggerInputs.SerdesRstR").read()
#hw.dispatch()
#print "Trigger Reset: 0x%X" % restatus
## #Read trigger inputs
#myreg= [-1, -1, -1, -1, -1, -1]
#for inputN in range(0, 6):
#  regString= "triggerInputs.ThrCount%dR" % inputN
#  myreg[inputN]= hw.getNode(regString).read()
#  hw.dispatch()
#  print regString, myreg[inputN]

## Read ev formatter
#cmd = int("0x0", 16) #
##hw.getNode("Event_Formatter.Enable_Record_Data").write(cmd)
#efstatus= hw.getNode("Event_Formatter.CurrentTimestampLR").read()
#hw.dispatch()
#print "Event Formatter Record: 0x%X" % efstatus
