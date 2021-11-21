# -*- coding: utf-8 -*-
"""

"""

import time

import uhal

verbose = True



################################################################################
# /*
#        I2C CORE
# */
################################################################################

### Same as the class defined in I2CuHal.py but the register names are changed to
### comply with D. Newbold's notation. To be used in the Dune SFP Fanout (pc059a)

class I2CCore:
    """I2C communication block."""

    # Define bits in cmd_stat register
    startcmd = 0x1 << 7
    stopcmd = 0x1 << 6
    readcmd = 0x1 << 5
    writecmd = 0x1 << 4
    ack = 0x1 << 3
    intack = 0x1

    recvdack = 0x1 << 7
    busy = 0x1 << 6
    arblost = 0x1 << 5
    inprogress = 0x1 << 1
    interrupt = 0x1

    def __init__(self, target, wclk, i2cclk, name="i2c", delay=None):
        self.target = target
        self.name = name
        self.delay = delay
        self.prescale_low = self.target.getNode("%s.ps_lo" % name)
        self.prescale_high = self.target.getNode("%s.ps_hi" % name)
        self.ctrl = self.target.getNode("%s.ctrl" % name)
        self.data = self.target.getNode("%s.data" % name)
        self.cmd_stat = self.target.getNode("%s.cmd_stat" % name)
        self.wishboneclock = wclk
        self.i2cclock = i2cclk
        self.config()

    def state(self):
        status = {}
        status["ps_low"] = self.prescale_low.read()
        status["ps_hi"] = self.prescale_high.read()
        status["ctrl"] = self.ctrl.read()
        status["data"] = self.data.read()
        status["cmd_stat"] = self.cmd_stat.read()
        self.target.dispatch()
        status["prescale"] = status["ps_hi"] << 8
        status["prescale"] |= status["ps_low"]
        for reg in status:
            val = status[reg]
            bval = bin(int(val))
            if verbose:
                print("\treg %s = %d, 0x%x, %s" % (reg, val, val, bval))

    def clearint(self):
        self.ctrl.write(0x1)
        self.target.dispatch()

    def config(self):
        #INITIALIZATION OF THE I2S MASTER CORE
        #Disable core
        self.ctrl.write(0x0 << 7)
        self.target.dispatch()
        #Write pre-scale register
        #prescale = int(self.wishboneclock / (5.0 * self.i2cclock)) - 1
        #prescale = int(self.wishboneclock / (5.0 * self.i2cclock))
        prescale = 0x0100 #FOR NOW HARDWIRED, TO BE MODIFIED
        self.prescale_low.write(prescale & 0xff)
        self.prescale_high.write((prescale & 0xff00) >> 8)
        #Enable core
        self.ctrl.write(0x1 << 7)
        self.target.dispatch()

    def checkack(self):
        inprogress = True
        ack = False
        while inprogress:
            cmd_stat = self.cmd_stat.read()
            self.target.dispatch()
            inprogress = (cmd_stat & I2CCore.inprogress) > 0
            ack = (cmd_stat & I2CCore.recvdack) == 0
        return ack

    def delayorcheckack(self):
        ack = True
        if self.delay is None:
            ack = self.checkack()
        else:
            time.sleep(self.delay)
            ack = self.checkack()#Remove this?
        return ack

################################################################################
# /*
#        I2C WRITE
# */
################################################################################



    def write(self, addr, data, stop=True):
        """Write data to the device with the given address."""
        # Start transfer with 7 bit address and write bit (0)
        nwritten = -1
        addr &= 0x7f
        addr = addr << 1
        startcmd = 0x1 << 7
        stopcmd = 0x1 << 6
        writecmd = 0x1 << 4
        #Set transmit register (write operation, LSB=0)
        self.data.write(addr)
        #Set Command Register to 0x90 (write, start)
        self.cmd_stat.write(I2CCore.startcmd | I2CCore.writecmd)
        self.target.dispatch()
        ack = self.delayorcheckack()
        if not ack:
            self.cmd_stat.write(I2CCore.stopcmd)
            self.target.dispatch()
            print("no ack from I2C address", hex(addr>>1))
            return nwritten
        nwritten += 1
        for val in data:
            val &= 0xff
            #Write slave memory address
            self.data.write(val)
            #Set Command Register to 0x10 (write)
            self.cmd_stat.write(I2CCore.writecmd)
            self.target.dispatch()
            ack = self.delayorcheckack()
            if not ack:
                self.cmd_stat.write(I2CCore.stopcmd)
                self.target.dispatch()
                return nwritten
            nwritten += 1
        if stop:
            self.cmd_stat.write(I2CCore.stopcmd)
            self.target.dispatch()
        return nwritten

################################################################################
# /*
#        I2C READ
# */
################################################################################
    def read(self, addr, n):
        """Read n bytes of data from the device with the given address."""
        # Start transfer with 7 bit address and read bit (1)
        data = []
        addr &= 0x7f
        addr = addr << 1
        addr |= 0x1 # read bit
        self.data.write(addr)
        self.cmd_stat.write(I2CCore.startcmd | I2CCore.writecmd)
        self.target.dispatch()
        ack = self.delayorcheckack()
        if not ack:
            self.cmd_stat.write(I2CCore.stopcmd)
            self.target.dispatch()
            return data
        for i in range(n):
            if i < (n-1):
                self.cmd_stat.write(I2CCore.readcmd) # <---
            else:
                self.cmd_stat.write(I2CCore.readcmd | I2CCore.ack | I2CCore.stopcmd) # <--- This tells the slave that it is the last word
            self.target.dispatch()
            ack = self.delayorcheckack()
            val = self.data.read()
            self.target.dispatch()
            data.append(val & 0xff)
        #self.cmd_stat.write(I2CCore.stopcmd)
        #self.target.dispatch()
        return data

################################################################################
# /*
#        I2C WRITE-READ
# */
################################################################################



    # def writeread(self, addr, data, n):
    #     """Write data to device, then read n bytes back from it."""
    #     nwritten = self.write(addr, data, stop=False)
    #     readdata = []
    #     if nwritten == len(data):
    #         readdata = self.read(addr, n)
    #     return nwritten, readdata

"""
SPI core XML:

<node description="SPI master controller" fwinfo="endpoint;width=3">
    <node id="d0" address="0x0" description="Data reg 0"/>
    <node id="d1" address="0x1" description="Data reg 1"/>
    <node id="d2" address="0x2" description="Data reg 2"/>
    <node id="d3" address="0x3" description="Data reg 3"/>
    <node id="ctrl" address="0x4" description="Control reg"/>
    <node id="divider" address="0x5" description="Clock divider reg"/>
    <node id="ss" address="0x6" description="Slave select reg"/>
</node>
"""
class SPICore:

    go_busy = 0x1 << 8
    rising = 1
    falling = 0


    def __init__(self, target, wclk, spiclk, basename="io.spi"):
        self.target = target
        # Only a single data register is required since all transfers are
        # 16 bit long
        self.data = target.getNode("%s.d0" % basename)
        self.control = target.getNode("%s.ctrl" % basename)
        self.control_val = 0b0
        self.divider = target.getNode("%s.divider" % basename)
        self.slaveselect = target.getNode("%s.ss" % basename)
        self.divider_val = int(wclk / spiclk / 2.0 - 1.0)
        self.divider_val = 0x7f
        self.configured = False

    def config(self):
        "Configure SPI interace for communicating with ADCs."
        self.divider_val = int(self.divider_val) % 0xffff
        if verbose:
            print("Configuring SPI core, divider = 0x%x" % self.divider_val)
        self.divider.write(self.divider_val)
        self.target.dispatch()
        self.control_val = 0x0
        self.control_val |= 0x0 << 13 # Automatic slave select
        self.control_val |= 0x0 << 12 # No interrupt
        self.control_val |= 0x0 << 11 # MSB first
        # ADC samples data on rising edge of SCK
        self.control_val |= 0x1 << 10 # change ouput on falling edge of SCK
        # ADC changes output shortly after falling edge of SCK
        self.control_val |= 0x0 << 9 # read input on rising edge
        self.control_val |= 0x10 # 16 bit transfers
        if verbose:
            print("SPI control val = 0x%x = %s" % (self.control_val, bin(self.control_val)))
        self.configured = True

    def transmit(self, chip, value):
        if not self.configured:
            self.config()
        assert chip >= 0 and chip < 8
        value &= 0xffff
        self.data.write(value)
        checkdata = self.data.read()
        self.target.dispatch()
        assert checkdata == value
        self.control.write(self.control_val)
        self.slaveselect.write(0xff ^ (0x1 << chip))
        self.target.dispatch()
        self.control.write(self.control_val | SPICore.go_busy)
        self.target.dispatch()
        busy = True
        while busy:
            status = self.control.read()
            self.target.dispatch()
            busy = status & SPICore.go_busy > 0
        self.slaveselect.write(0xff)
        data = self.data.read()
        ss = self.slaveselect.read()
        status = self.control.read()
        self.target.dispatch()
        #print "Received data: 0x%x, status = 0x%x, ss = 0x%x" % (data, status, ss)
        return data
