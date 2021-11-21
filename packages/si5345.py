import time
import uhal
from packages.I2CuHal import I2CCore
import io
import csv
import sys

class si5345:
    #Class to configure the Si5344 clock generator

    def __init__(self, i2c, slaveaddr=0x68):
        self.i2c = i2c
        self.slaveaddr = slaveaddr
        #self.configList=

    #def writeReg(self, address, data):

    def readRegister(self, myaddr, nwords, verbose= False):
        ### Read a specific register on the Si5344 chip. There is not check on the validity of the address but
        ### the code sets the correct page before reading.

        #First make sure we are on the correct page
        currentPg= self.getPage()
        requirePg= (myaddr & 0xFF00) >> 8
        if verbose:
            print("REG", hex(myaddr), "CURR PG" , hex(currentPg[0]), "REQ PG", hex(requirePg))
        if currentPg[0] != requirePg:
            self.setPage(requirePg)
        #Now read from register.
        addr=[]
        addr.append(myaddr)
        mystop=False
        self.i2c.write( self.slaveaddr, addr, mystop)
        # time.sleep(0.1)
        res= self.i2c.read( self.slaveaddr, nwords)
        return res

    def writeRegister(self, myaddr, data, verbose=False):
        ### Write a specific register on the Si5344 chip. There is not check on the validity of the address but
        ### the code sets the correct page before reading.
        ### myaddr is an int
        ### data is a list of ints

        #First make sure we are on the correct page
        myaddr= myaddr & 0xFFFF
        currentPg= self.getPage()
        requirePg= (myaddr & 0xFF00) >> 8
        #print "REG", hex(myaddr), "CURR PG" , currentPg, "REQ PG", hex(requirePg)
        if currentPg[0] != requirePg:
            self.setPage(requirePg)
        #Now write to register.
        data.insert(0, myaddr)
        if verbose:
            print("  Writing: ")
            result="\t  "
            for iaddr in data:
                result+="%#02x "%(iaddr)
            print(result)
        self.i2c.write( self.slaveaddr, data)
        #time.sleep(0.01)

    def setPage(self, page, verbose=False):
        #Configure the chip to perform operations on the specified address page.
        mystop=True
        myaddr= [0x01, page]
        self.i2c.write( self.slaveaddr, myaddr, mystop)
        #time.sleep(0.01)
        if verbose:
            print("  Si5345 Set Reg Page:", page)

    def getPage(self, verbose=False):
        #Read the current address page
        mystop=False
        myaddr= [0x01]
        self.i2c.write( self.slaveaddr, myaddr, mystop)
        rPage= self.i2c.read( self.slaveaddr, 1)
        #time.sleep(0.1)
        if verbose:
            print("\tPage read:", rPage)
        return rPage

    def getDeviceVersion(self):
        #Read registers containing chip information
        mystop=False
        nwords=2
        myaddr= [0x02 ]#0xfa
        self.setPage(0)
        self.i2c.write( self.slaveaddr, myaddr, mystop)
        #time.sleep(0.1)
        res= self.i2c.read( self.slaveaddr, nwords)
        print("  Si5345 EEPROM: ")
        result="\t"
        for iaddr in reversed(res):
            result+="%#02x "%(iaddr)
        print(result)
        return res

    def parse_clk(self, filename, verbose= False):
        #Parse the configuration file produced by Clockbuilder Pro (Silicon Labs)
        deletedcomments=""""""
        if verbose:
               print("\tParsing file", filename)
        with open(filename, 'r') as configfile:
            for i, line in enumerate(configfile):
                if not line[0] == '#' :
                    if not line[0:3] == 'Add':
                        deletedcomments+=line
        csvfile = io.StringIO(deletedcomments)
        cvr= csv.reader(csvfile, delimiter=',', quotechar='|')
        #print "\tN elements  parser:", sum(1 for row in cvr)
        #return [addr_list,data_list]
        # for item in cvr:
        #     print "rere"
        #     regAddr= int(item[0], 16)
        #     regData[0]= int(item[1], 16)
        #     print "\t  ", hex(regAddr), hex(regData[0])
        #self.configList= cvr
        regSettingList= list(cvr)
        if verbose:
            print("\t  ", len(regSettingList), "elements")
        return regSettingList

    def writeConfiguration(self, regSettingList, verbose= 0):
        print("  Si5345 Writing configuration:")
        toolbar_width = 38
        if (verbose==1):
            sys.stdout.write("  [%s]" % (" " * toolbar_width))
            sys.stdout.flush()
            sys.stdout.write("\b" * (toolbar_width+1)) # return to start of line, after '['
        #regSettingList= list(regSettingCsv)
        counter=0
        for item in regSettingList:
            regAddr= int(item[0], 16)
            regData=[0]
            regData[0]= int(item[1], 16)
            if (verbose > 1):
                print("\t", counter, "Reg:", hex(regAddr), "Data:", regData)
            counter += 1
            self.writeRegister(regAddr, regData, False)
            if (not(counter % 10) and (verbose==1)):
                sys.stdout.write("-")
                sys.stdout.flush()
        sys.stdout.write("\n")
        print("\tSi5345 configuration done")

    def checkDesignID(self):
        regAddr= 0x026B
        res= self.readRegister(regAddr, 8)
        result= "  Si5345 design Id:\n\t"
        for iaddr in res:
            result+=chr(iaddr)
        print(result)
