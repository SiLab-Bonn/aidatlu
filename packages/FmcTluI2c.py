import time
#from PyChipsUser import *
from I2cBusProperties import *
from RawI2cAccess import *


class FmcTluI2c:


    ############################
    ### configure i2c connection
    ############################
    def __init__(self,board):
        self.board = board
        i2cClockPrescale = 0x30
        self.i2cBusProps = I2cBusProperties(self.board, i2cClockPrescale)
        return


    ##########################
    ### scan all i2c addresses
    ##########################
    def i2c_scan(self):
        list=[]
        for islave in range(128):
            i2cscan = RawI2cAccess(self.i2cBusProps, islave)
            try:
                i2cscan.write([0x00])
                device="slave address "+hex(islave)+" "
                if islave==0x1f:
                    device+="(DAC)"
                elif islave==0x50:
                    device+="(serial number PROM)"
                elif islave>=0x54 and islave<=0x57:
                    device+="(sp601 onboard EEPROM)"
                else:
                    device+="(???)"
                    pass
                list.append(device)
                pass
            except:
                pass
            pass
        return list


    ###################
    ### write to EEPROM
    ###################
    def eeprom_write(self,address,value):
        if address<0 or address>127:
            print "eeprom_write ERROR: address",address,"not in range 0-127"
            return
        if value<0 or value>255:
            print "eeprom_write ERROR: value",value,"not in range 0-255"
            return
        i2cSlaveAddr = 0x50   # seven bit address, binary 1010000
        prom = RawI2cAccess(self.i2cBusProps, i2cSlaveAddr)
        prom.write([address,value])
        time.sleep(0.01) # write cycle time is 5ms. let's wait 10 to make sure.
        return


    ####################
    ### read from EEPROM
    ####################
    def eeprom_read(self,address):
        if address<0 or address>255:
            print "eeprom_write ERROR: address",address,"not in range 0-127"
            return
        i2cSlaveAddr = 0x50   # seven bit address, binary 1010000
        prom = RawI2cAccess(self.i2cBusProps, i2cSlaveAddr)
        prom.write([address])
        return prom.read(1)[0]


    ######################
    ### read serial number
    ######################
    def get_serial_number(self):
        result=""
        for iaddr in [0xfa, 0xfb, 0xfc, 0xfd, 0xfe, 0xff]:
            result+="%02x "%(self.eeprom_read(iaddr))
            pass
        return result


    #################
    ### set DAC value
    #################
    def set_dac(self,channel,value , vrefOn = 0 , i2cSlaveAddrDac = 0x1F):
        if channel<0 or channel>7:
            print "set_dac ERROR: channel",channel,"not in range 0-7 (bit mask)"
            return -1
        if value<0 or value>0xFFFF:
            print "set_dac ERROR: value",value,"not in range 0-0xFFFF"
            return -1
        # AD5665R chip with A0,A1 tied to ground
        #i2cSlaveAddrDac = 0x1F   # seven bit address, binary 00011111
        print "I2C address of DAC = " , hex(i2cSlaveAddrDac)
        dac = RawI2cAccess(self.i2cBusProps, i2cSlaveAddrDac)
        # if we want to enable internal voltage reference:
        if vrefOn:
            # enter vref-on mode:
	    print "Turning internal reference ON"
            dac.write([0x38,0x00,0x01])
        else:
	    print "Turning internal reference OFF"
            dac.write([0x38,0x00,0x00])
        # now set the actual value
        sequence=[( 0x18 + ( channel &0x7 ) ) , (value/256)&0xff , value&0xff]
        print sequence
        dac.write(sequence)



    ##################################################
    ### convert required threshold voltage to DAC code
    ##################################################
    def convert_voltage_to_dac(self, desiredVoltage, Vref=1.300):
        Vdaq = ( desiredVoltage + Vref ) / 2
        dacCode = 0xFFFF * Vdaq / Vref
        return int(dacCode)


    ##################################################
    ### calculate the DAC code required and set DAC
    ##################################################
    def set_threshold_voltage(self, channel , voltage ):
        dacCode = self.convert_voltage_to_dac(voltage)
        print " requested voltage, calculated DAC code = " , voltage , dacCode
        self.set_dac(channel , dacCode)
