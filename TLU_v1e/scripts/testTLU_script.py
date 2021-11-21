# miniTLU test script

from FmcTluI2c import *
import uhal
import sys
import time
from I2CuHal import I2CCore
from miniTLU import MiniTLU
from datetime import datetime

if __name__ == "__main__":
    print "\tTEST TLU SCRIPT"
    miniTLU= MiniTLU("minitlu", "file://./connection.xml")
    #(self, target, wclk, i2cclk, name="i2c", delay=None)
    TLU_I2C= I2CCore(miniTLU.hw, 10, 5, "i2c_master", None)
    TLU_I2C.state()


    #READ CONTENT OF EEPROM ON 24AA02E48 (0xFA - 0XFF)
    mystop= 1
    time.sleep(0.1)
    myaddr= [0xfa]
    TLU_I2C.write( 0x50, myaddr, mystop)
    res=TLU_I2C.read( 0x50, 6)
    print "Checkin EEPROM:"
    result="\t"
    for iaddr in res:
        result+="%02x "%(iaddr)
    print result

    #SCAN I2C ADDRESSES
    #WRITE PROM
    #WRITE DAC


    #Convert required threshold voltage to DAC code
    #def convert_voltage_to_dac(self, desiredVoltage, Vref=1.300):
    print("Writing DAC setting:")
    Vref= 1.300
    desiredVoltage= 3.3
    channel= 0
    i2cSlaveAddrDac = 0x1F
    vrefOn= 0
    Vdaq = ( desiredVoltage + Vref ) / 2
    dacCode = 0xFFFF * Vdaq / Vref
    dacCode= 0x391d
    print "\tVreq:", desiredVoltage
    print "\tDAC code:"  , dacCode
    print "\tCH:", channel
    print "\tIntRef:", vrefOn

    #Set DAC value
    #def set_dac(self,channel,value , vrefOn = 0 , i2cSlaveAddrDac = 0x1F):
    if channel<0 or channel>7:
        print "set_dac ERROR: channel",channel,"not in range 0-7 (bit mask)"
        ##return -1
    if dacCode<0 or dacCode>0xFFFF:
        print "set_dac ERROR: value",dacCode ,"not in range 0-0xFFFF"
        ##return -1
    # AD5665R chip with A0,A1 tied to ground
    #i2cSlaveAddrDac = 0x1F   # seven bit address, binary 00011111

    # print "I2C address of DAC = " , hex(i2cSlaveAddrDac)
    # dac = RawI2cAccess(self.i2cBusProps, i2cSlaveAddrDac)
    # # if we want to enable internal voltage reference:

    if vrefOn:
        # enter vref-on mode:
        print "\tTurning internal reference ON"
        #dac.write([0x38,0x00,0x01])
        TLU_I2C.write( i2cSlaveAddrDac, [0x38,0x00,0x01], 0)
    else:
        print "\tTurning internal reference OFF"
        #dac.write([0x38,0x00,0x00])
        TLU_I2C.write( i2cSlaveAddrDac, [0x38,0x00,0x00], 0)
    # Now set the actual value
    sequence=[( 0x18 + ( channel &0x7 ) ) , int(dacCode/256)&0xff , int(dacCode)&0xff]
    print "\tWriting byte sequence:", sequence
    TLU_I2C.write( i2cSlaveAddrDac, sequence, 0)
