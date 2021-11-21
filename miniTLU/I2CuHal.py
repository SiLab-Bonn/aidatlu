"""
solidfpa.py provides functionality to control the front end boards currently
being prototyped.

For the ADC:
    One or more LTM9007 ADCs can be controlled via the IPbus SPI block.
    Each chip is really two four channel ADCs, with each controlled with a
    separate chip select line. Bank A is channels 1, 4, 5, 8.
    Bank B is 2, 3, 6, 7.

    Control is via a simple SPI interface where 16 bits are transferred.
    b0 is read/!write
    b7:1 are the register address
    b15:b8 are the data sent to/from the ADC

    If the ADC.cehckwrite flag is True then all write commands will immediately
    be confirmed by a read command to the same address.
"""

import time

import uhal

verbose = True
"""
class SoLidFPGA:

    def __init__(self, board, nadc=4, verbose=False, minversion=None):
        cm = uhal.ConnectionManager("file://solidfpga.xml")
        self.target = cm.getDevice(board)
        #self.config()
        self.offsets = TimingOffsets(self.target)
        self.trigger = Trigger(self.target)
        self.databuffer = OutputBuffer(self.target)
        self.spi = SPICore(self.target, 31.25e6, 100e3)
        self.clock_i2c = I2CCore(self.target, 31.25e6, 40e3, "io.clock_i2c")
        self.analog_i2c = I2CCore(self.target, 31.25e6, 40e3, "io.analog_i2c")
        self.clockchip = Si5326(self.clock_i2c)
        self.adcs = []
        for i in range(1):
            self.adcs.append(ADCLTM9007(self.spi, 2 * i, 2 * i + 1))
        # For board Wim sent to Bristol for testing the MCP4725 address seems
        # to be 0b1100001, whereas for the first test board the address was
        # 0b1100111.
        self.gdac = DACMCP4725(self.analog_i2c, 0b1100001, 4.45)
        self.trimdacs = [
                DACMCP4728(self.analog_i2c, 0b1100011, 4.45),
                DACMCP4728(self.analog_i2c, 0b1100101, 4.45)
        ]
        self.temp = TempMCP9808(self.analog_i2c)
        self.firmwareversion = None
        self.minversion = minversion
        self.config(7, 16)

    def config(self, slip, tap):
        # check ID
        boardid = self.target.getNode("ctrl_reg.id").read()
        stat = self.target.getNode("ctrl_reg.stat").read()
        self.target.dispatch()
        if verbose:
            print "ID = 0x%x, stat = 0x%x" % (boardid, stat)
        self.id = (boardid & 0xffff0000) >> 16
        self.firmwareversion = boardid & 0x0000ffff
        if self.minversion is not None:
            msg = "Old version of firmware (v%d) running, require >= v%d." % (
                    self.firmwareversion, self.minversion)
            assert self.firmwareversion >= self.minversion, msg
        self.spi.config()
        self.clock_i2c.config()
        self.analog_i2c.config()
        # Check for 40 MHz clock lock
        lock = self.target.getNode("ctrl_reg.stat.mmcm_locked").read()
        self.target.dispatch()
        #assert lock == 1, "No 40 MHz clock clock, code not yet moved to frontend.py"
        if lock != 1:
            # Config clock chip
            self.clockchip.config("siclock/si5326.txt")
            time.sleep(1.0)
        lock = self.target.getNode("ctrl_reg.stat.mmcm_locked").read()
        self.target.dispatch()
        assert lock == 1, "No 40 MHz clock clock, Si53266 configuration must have failed."
        # Reset clock
        timing_rst = self.target.getNode("timing.csr.ctrl.rst")
        timing_rst.write(0x1)
        self.target.dispatch()
        timing_rst.write(0x0)
        self.target.dispatch()
        lock = False
        while not lock:
            lock = self.target.getNode("ctrl_reg.stat.mmcm_locked").read()
            self.target.dispatch()
        clkcount = self.target.getNode("io.freq_ctr.freq.count").read()
        self.target.dispatch()
        freq = int(clkcount) / 8388.608 # not sure why, from Lukas
        if verbose:
            print "Frequency = %g MHz" % freq
        assert freq > 39 and freq < 41
        # Configure trigger block
        self.trigger.config()
        # Set timing offset on inputs from ADC
        self.offsets.setoffset(slip, tap)
        for adc in self.adcs:
            adc.config()
        print "Analog board temperature = %g C." % self.temp.temp()

    def reset(self, slip=7, tap=16):
        if verbose:
            print "Resetting board."
        # Soft reset
        soft_rst = self.target.getNode("ctrl_reg.ctrl.soft_rst")
        soft_rst.write(1)
        soft_rst.write(0)
        self.target.dispatch()
        time.sleep(1.0)
        if verbose:
            print "Reset complete."
        self.config(slip, tap)

    def readvoltages(self):
        bias = self.gdac.readbias()
        print "Global bias = %g V" %  bias
        trims = "Channel trims:\n"
        ichan = 0
        for dac in self.trimdacs:
            voltages = dac.readvoltages()
            for v in voltages:
                trims += "    Chan %d, v = %g V\n" % (ichan, v)
                ichan += 1
        print trims

    def bias(self, bias):
        self.gdac.setbias(bias)

    def trim(self, trim):
        for i in range(4):
            for trimdac in self.trimdacs:
                trimdac.setvoltage(i, trim)

    def trims(self, trims):
        for chan in trims:
            trim = trims[chan]
            ndac = chan / 4
            nchan = chan % 4
            self.trimdacs[ndac].setvoltage(nchan, trim)

# IPbus blocks
class TimingOffsets:
    #Timing offsets for the ADC data deserialisation.

    def __init__(self, target):
        self.target = target

    def setoffset(self, slip=7, tap=16):
        if verbose:
            print "Setting timing offset with channel slip = %d and %d taps." % (slip, tap)
        chan_slip = self.target.getNode("timing.csr.ctrl.chan_slip")
        for i in range(slip):
            chan_slip.write(1)
            self.target.dispatch()
        chan_slip.write(0)
        self.target.dispatch()
        chan_inc = self.target.getNode("timing.csr.ctrl.chan_inc")
        for i in range(tap):
            chan_inc.write(1)
            self.target.dispatch()
        chan_inc.write(0)
        self.target.dispatch()

class Trigger:

    def __init__(self, target, nsamples=0x800):
        self.target = target
        self.nsamples = nsamples
        self.capture = target.getNode("timing.csr.ctrl.chan_cap")
        self.chanselect = target.getNode("ctrl_reg.ctrl.chan")
        self.fifo = target.getNode("chan.fifo")

    def config(self):
        # Set up channels
        for i in range(8):
            self.target.getNode("ctrl_reg.ctrl.chan").write(i)
            self.target.getNode("chan.csr.ctrl.en_sync").write(1)
        self.target.dispatch()

    def trigger(self):
        data = []
        self.capture.write(1)
        self.capture.write(0)
        self.target.dispatch()
        for i in range(8):
            self.chanselect.write(i)
            wf = self.fifo.readBlock(self.nsamples)
            self.target.dispatch()
            data.append(wf)
        return data

class OutputBuffer:
    #Output data block.

    def __init__(self, target):
        self.target = target
"""


################################################################################
# /*
#        I2C CORE
# */
################################################################################



"""
I2C core XML:

<node description="I2C master controller" fwinfo="endpoint;width=3">
    <node id="ps_lo" address="0x0" description="Prescale low byte"/>
    <node id="ps_hi" address="0x1" description="Prescale low byte"/>
    <node id="ctrl" address="0x2" description="Control"/>
    <node id="data" address="0x3" description="Data"/>
    <node id="cmd_stat" address="0x4" description="Command / status"/>
</node>

"""
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
        self.prescale_low = self.target.getNode("%s.i2c_pre_lo" % name)
        self.prescale_high = self.target.getNode("%s.i2c_pre_hi" % name)
        self.ctrl = self.target.getNode("%s.i2c_ctrl" % name)
        self.data = self.target.getNode("%s.i2c_rxtx" % name)
        self.cmd_stat = self.target.getNode("%s.i2c_cmdstatus" % name)
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
                print "reg %s = %d, 0x%x, %s" % (reg, val, val, bval)

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
        prescale = 0x30 #FOR NOW HARDWIRED, TO BE MODIFIED
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
            self.cmd_stat.write(I2CCore.readcmd)
            self.target.dispatch()
            ack = self.delayorcheckack()
            val = self.data.read()
            self.target.dispatch()
            data.append(val & 0xff)
        self.cmd_stat.write(I2CCore.stopcmd)
        self.target.dispatch()
        return data

################################################################################
# /*
#        I2C WRITE-READ
# */
################################################################################



    def writeread(self, addr, data, n):
        """Write data to device, then read n bytes back from it."""
        nwritten = self.write(addr, data, stop=False)
        readdata = []
        if nwritten == len(data):
            readdata = self.read(addr, n)
        return nwritten, readdata

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
            print "Configuring SPI core, divider = 0x%x" % self.divider_val
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
            print "SPI control val = 0x%x = %s" % (self.control_val, bin(self.control_val))
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
"""
        print "Data to send: 0x%x = %s" % (checkdata, bin(int(checkdata)))
        ss = 0x1 << chip
        nss = ss ^ 0xffff
        print "chip = %d, nSS = 0x%x = %s" % (chip, nss, bin(nss))
        ctrl = self.control.read()
        self.target.dispatch()
        busy = (ctrl & SPICore.go_busy) > 0
        while busy:
            ctrl = self.control.read()
            self.target.dispatch()
            busy = (ctrl & SPICore.go_busy) > 0
        self.slaveselect.write(nss)
        self.target.dispatch()
        self.control.write(self.control_val)
        self.target.dispatch()
        self.control.write(self.control_val | SPICore.go_busy)
        self.target.dispatch()
        time.sleep(0.1)
        ncheck = 0
        finished = False
        while not finished:
            ctrl = self.control.read()
            self.target.dispatch()
            # Check if transfer is complete by reading the GO_BSY bit of CTRL
            finished = (ctrl & SPICore.go_busy) == 0
            ncheck += 1
        #    assert ncheck < 10, "ctrl = 0x%x, %s finished = %s" % (ctrl, bin(int(ctrl)), str(finished))
        #    time.sleep(0.1)
        print "%d checks before busy not asserted." % ncheck
        self.slaveselect.write(0xffff)
        self.target.dispatch()
        ss = self.slaveselect.read()
        data = self.data.read()
        self.target.dispatch()
        print "After transmit, ss = 0x%x" % ss
        print "Received 0x%x = %s" % (data, bin(int(data)))
        time.sleep(0.1)
        return data
"""

# External chips

class Si5326:

    def __init__(self, i2c, slaveaddr=0b1101000):
        self.i2c = i2c
        self.slaveaddr = slaveaddr

    def config(self, fn):
        if verbose:
            print "Loading Si5326 configuration from %s" % fn
        inp = open(fn, "r")
        inmap = False
        regvals = {}
        for line in inp:
            if inmap:
                if "END_REGISTER_MAP" in line:
                    inmap = False
                    continue
                line = line.split(",")
                reg = int(line[0])
                val = line[1].strip().replace("h", "")
                val = int(val, 16)
                regvals[reg] = val
            if "#REGISTER_MAP" in line:
                inmap = True
        inp.close()
        if verbose:
            print "Register map: %s" % str(regvals)
        for reg in regvals:
            n = self.i2c.write(self.slaveaddr, [reg, regvals[reg]])
            assert n == 2, "Only wrote %d of 2 bytes over I2C." % n
        if verbose:
            print "Clock configured"

lvdscurrents = {
        3.5: 0b000,
        4.0: 0b001,
        4.5: 0b010,
        3.0: 0b100,
        2.5: 0b101,
        2.1: 0b110,
        1.75: 0b111
}

napchannels = {
        1: 0b0001,
        2: 0b0001,
        3: 0b0010,
        4: 0b0010,
        5: 0b0100,
        6: 0b0100,
        7: 0b1000,
        8: 0b1000
}

class ADCLTM9007:

    def __init__(self, spicore, csA, csB, checkwrite=False):
        self.checkwrite = checkwrite
        self.spicore = spicore
        self.csA = csA
        self.csB = csB

    def config(self):
        self.reset()
        self.testpattern(False)
        self.setoutputmode(3.5, False, True, 1, 14)
        self.setformat(False, False)

    def writereg(self, bank, addr, data):
        value = 0x0
        value |= 0x0 << 15 # write bit
        value |= (addr & 0x7f) << 8
        value |= data & 0xff
        #print "writereg sending 0x%x = %s" % (value, bin(value))
        assert bank in ["A", "B"]
        if bank == "A":
            reply = self.spicore.transmit(self.csA, value)
        else:
            reply = self.spicore.transmit(self.csB, value)
        if self.checkwrite:
            readdata = self.readreg(bank, addr)
            msg = "Incorrect data from bank %s register 0x%x: " (bank, addr)
            msg += " after writing 0x%x, read 0x%x.\n" % (data, readdata)
            assert readdata == data, msg


    def writerega(self, addr, data):
        self.writereg("A", addr, data)

    def writeregb(self, addr, data):
        self.writereg("B", addr, data)

    def readreg(self, bank, addr):
        value = 0x0
        value |= 0x1 << 15
        value |= (addr & 0x7f) << 8
        #print "readreg sending 0x%x = %s" % (value, bin(value))
        assert bank in ["A", "B"]
        if bank == "A":
            reply = self.spicore.transmit(self.csA, value)
        else:
            reply = self.spicore.transmit(self.csB, value)
        reply16 = 0xff & reply
        #print "Reply = 0x%x -> 0x%x" % (reply, reply16)
        return reply16

    def readrega(self, addr):
        return self.readreg("A", addr)

    def readregb(self, addr):
        return self.readreg("B", addr)

    def reset(self, bank=None):
        """Reset ADC bank(s)."""
        if verbose:
            print "Resetting ADC."
        rstcmd  = 0x1 << 7
        if bank == "A" or bank is None:
            if verbose:
                print "Reset A"
            self.writerega(0x0, rstcmd)
            time.sleep(0.5)
        if bank == "B" or bank is None:
            if verbose:
                print "Reset B"
            self.writeregb(0x0, rstcmd)
            time.sleep(0.5)

    def testpattern(self, on, pattern=0x0, bank=None):
        """Set bank(s)'s test pattern and en/disable it."""
        pattern = int(pattern) & 0x3fff
        if verbose:
            if on:
                print "Setting ADC test pattern = 0x%x = %s." % (pattern, bin(pattern))
            else:
                print "Setting ADC test pattern off."
        msb = 0x0
        if on:
            msb = 0x1 << 7
        msb |= ((pattern & 0x3f00) >> 8)
        lsb = pattern & 0xff
        if verbose:
            print "msb = 0x%x = %s, lsb = 0x%x = %s" % (msb, bin(msb), lsb, bin(lsb))
        if bank is None or bank == "A":
            self.writerega(0x4, lsb)
            self.writerega(0x3, msb)
        if bank is None or bank == "B":
            self.writeregb(0x4, lsb)
            self.writeregb(0x3, msb)

    def gettestpattern(self):
        valA = self.readrega(0x3) << 8
        valA |= self.readrega(0x4)
        print "Test pattern on bank A: 0x%x, %s" % (valA, bin(valA))
        valB = self.readregb(0x3) << 8
        valB |= self.readregb(0x4)
        print "Test pattern on bank B: 0x%x, %s" % (valB, bin(valB))

    def getstatus(self):
        print "Bank A:"
        for reg in range(5):
            val = self.readrega(reg)
            print "    reg%d = 0x%x = %s" % (reg, val, bin(val))
        print "Bank B:"
        for reg in range(5):
            val = self.readregb(reg)
            print "    reg%d = 0x%x = %s" % (reg, val, bin(val))

    def setoutputmode(self, lvdscurrent, lvdstermination, outenable, lanes, bits, bank=None):
        """Configure bank(s)'s output mode."""
        if verbose:
            print "Setting ADC output mode."
        mode = 0x0
        assert lanes in [1, 2] and bits in [12, 14, 16]
        if lanes == 1:
            if bits == 12:
                mode |= 0b110
            elif bits == 14:
                mode |= 0b101
            else: # bits = 16
                mode |= 0b111
        else:   # lanes = 2
            if bits == 12:
                mode |= 0b010
            elif bits == 14:
                mode |= 001
            else: # bits = 16
                mode |= 0b111
        if not outenable:
            mode |= 0b1000
        if lvdstermination:
            mode |= (0x1 << 4)
        mode |= (lvdscurrents[lvdscurrent] << 5)
        if bank is None or bank == "A":
            self.writerega(0x2, mode)
        if bank is None or bank == "B":
            self.writeregb(0x2, mode)

    def setformat(self, randomiser, twoscomp, stabiliser=True, bank=None):
        """Configure bank(s)'s output format."""
        if verbose:
            print "Setting ADC format."
        if bank is None or bank == "A":
            data = self.readrega(0x1)
            if twoscomp:
                data |= (0x1 << 5)
            else:
                data &= 0xff ^ (0x1 << 5)
            if randomiser:
                data |= (0x1 << 6)
            else:
                data &= 0xff ^ (0x1 << 6)
            if not stabiliser:
                data |= (0x1 << 7)
            else:
                data &= 0xff ^ (0x1 << 7)
            self.writerega(0x1, data)
        if bank is None or bank == "B":
            data = self.readregb(0x1)
            if twoscomp:
                data |= (0x1 << 5)
            else:
                data &= 0xff ^ (0x1 << 5)
            if randomiser:
                data |= (0x1 << 6)
            else:
                data &= 0xff ^ (0x1 << 6)
            if not stabiliser:
                data |= (0x1 << 7)
            else:
                data &= 0xff ^ (0x1 << 7)
            self.writeregb(0x1, data)

    def setsleep(self, sleep, bank=None):
        """Put ADC bank(s) to sleep."""
        if verbose:
            print "Setting ADC sleep mode"
        if bank is None or bank == "A":
            data = self.readrega(0x1)
            if sleep:
                data |= (0x1 << 4)
            else:
                data &= 0xff ^ (0x1 << 4)
            self.writerega(0x1, data)
        if bank is None or bank == "B":
            data = self.readregb(0x1)
            if sleep:
                data |= (0x1 << 4)
            else:
                data &= 0xff ^ (0x1 << 4)
            self.writeregb(0x1, data)

    def nap(self, channels):
        """Provide a list of channels to put down for a nap, all others will be not napping."""
        if verbose:
            print "Setting ADC channel nap."
        dataa = self.readrega(0x1)
        dataa &= 0xf0
        datab = self.readregb(0x1)
        datab &= 0xf0
        for chan in channels:
            assert chan < 9 and chan > 0
            if chan in [1, 4, 5, 8]:
                dataa |= napchannels[chan]
            else:
                datab |= napchannels[chan]
        self.writerega(0x1, dataa)
        self.writeregb(0x1, datab)

class MCP472XPowerMode:

    on = 0b00
    off1k = 0b01
    off100k = 0b10
    off500k = 0b11

class DACMCP4725:
    """Global trim DAC"""

    # Write modes
    fast = 0b00
    writeDAC = 0b10
    writeDACEEPROM = 0b11

    def __init__(self, i2ccore, addr=0b1100111, vdd=5.0):
        self.i2ccore = i2ccore
        self.slaveaddr = addr & 0x7f
        self.vdd = float(vdd)

    def setbias(self, bias):
        # DAC voltage goes through potential divider to HV chip, where it is scaled up
        r1 = 1.0
        r2 = 2.4
        divider = r2 / (r1 + r2)
        voltage = bias / 30.0 / divider
        self.setvoltage(voltage)

    def setvoltage(self, voltage, powerdown=MCP472XPowerMode.on):
        if voltage > self.vdd:
            print "Overriding MCP4725 voltage: %g -> %g V (max of range)" % (voltage, self.vdd)
            voltage = self.vdd
        value = int(voltage / float(self.vdd) * 4096)
        #print "%g -> %d" % (voltage, value)
        self.setvalue(value, powerdown, self.writeDACEEPROM)

    def setvalue(self, value, powerdown, mode):
        value = int(value)
        value &= 0xfff
        if mode == self.fast:
            data = []
            data.append((powerdown << 4) | ((value & 0xf00) >> 8))
            data.append(value & 0x0ff)
            self.i2ccore.write(self.slaveaddr, data)
        else:
            data = []
            data.append((mode << 5) | (powerdown << 1))
            data.append((value & 0xff0) >> 4)
            data.append((value & 0x00f) << 4)
            #print "Writing %s" % str(data)
            self.i2ccore.write(self.slaveaddr, data)

    def status(self):
        data = self.i2ccore.read(self.slaveaddr, 5)
        assert len(data) == 5, "Only recieved %d of 5 expected bytes from MCP4725." % len(data)
        dx = "0x"
        db = ""
        for val in data:
            dx += "%02x" % val
            db += "%s " % bin(val)
        #print dx, db
        ready = (data[0] & (0x1 << 7)) > 0
        por = (data[0] & (0x1 << 6)) > 0 # power on reset?
        powerdown = (data[0] & 0b110) >> 1
        dacvalue = data[1] << 4
        dacvalue |= (data[2] & 0xf0) >> 4
        voltage = self.vdd * dacvalue / 2**12
        #print dacvalue, voltage
        return dacvalue, voltage, ready, por, powerdown

    def readvoltage(self):
        vals = self.status()
        return vals[1]

    def readbias(self):
        v = self.readvoltage()
        r1 = 1.0
        r2 = 2.4
        divider = r2 / (r1 + r2)
        bias = v * 30.0 * divider
        return bias

# class MCP4728ChanStatus:
#
#     def __init__(self, data):
#         assert len(data) == 3
#         s = "0x"
#         for val in data:
#             s += "%02x" % val
#         #print data, s
#         self.ready = (data[0] & (0x1 << 7)) > 0
#         self.por = (data[0] & (0x1 << 6)) > 0
#         self.chan = (data[0] & (0b11 << 4)) >> 4
#         self.addr = data[0] & 0x0f
#         self.vref = (data[1] & (0b1 << 7)) > 0
#         self.powerdown = (data[1] & (0b11 << 5)) >> 5
#         self.gain = (data[1] & (0b1 << 4)) > 0
#         self.value = (data[1] & 0x0f) << 8
#         self.value |= data[2]
#
#     def __repr__(self):
#         return "chan %d: vref = %s, powerdown = %d, value = %d" % (self.chan, str(self.vref), self.powerdown, self.value)

# class MCP4728Channel:
#
#     def __init__(self, data):
#         assert len(data) == 6
#         self.output = MCP4728ChanStatus(data[:3])
#         self.EEPROM = MCP4728ChanStatus(data[3:])
#         self.chan = self.EEPROM.chan
#         #print self.output

# class DACMCP4728:
#     """Channel trim DAC"""
#
#     # Commands
#     writeDACEEPROM = 0b010
#
#     # write functions
#     multiwrite = 0b00
#     sequentialwrite = 0b10
#     singlewrite = 0b11
#
#     # stuff
#     vref = 0b0 << 7 # Uses external reference, ie Vdd
#
#     def __init__(self, i2ccore, addr, vdd=5.0):
#         self.i2ccore = i2ccore
#         self.slaveaddr = addr & 0x7f
#         self.vdd = float(vdd)
#
#     def setvoltage(self, channel, voltage, powerdown=MCP472XPowerMode.on):
#         value = int(voltage / self.vdd * 2**12)
#         #print "%g V -> %d" % (voltage, value)
#         self.setvalue(channel, value, powerdown)
#
#     def setvalue(self, channel, value, powerdown=MCP472XPowerMode.on):
#         value = int(value) & 0xfff
#         data = [] # data is an empty array that gets filled as below
#         cmd = DACMCP4728.writeDACEEPROM << 5
#         cmd |= DACMCP4728.singlewrite << 3
#         cmd |= (channel & 0b11) << 1
#         data.append(cmd) data gets appende the cmd string
#         val = DACMCP4728.vref | ((powerdown & 0b11) << 5)
#         val |= (value & 0xf00) >> 8
#         data.append(val)
#         data.append(value & 0xff)
#         sx = "0x"
#         sb = ""
#         for val in data:
#             sx += "%02x" % val
#             sb += "%s " % bin(val)
#         #print "Writing data to %s value: " % bin(self.slaveaddr), data, sx, sb
#         nwritten = self.i2ccore.write(self.slaveaddr, data)
#         assert nwritten == len(data), "Only wrote %d of %d bytes setting MCP4728." % (nwritten, len(data))
#         time.sleep(0.2)
#
#     def status(self):
#         data = self.i2ccore.read(self.slaveaddr, 24)
#         assert len(data) == 24, "Only read %d of 24 bytes getting MCP4728 status." % len(data)
#         #print data
#         chans = []
#         for chan in range(4):
#             i = chan * 6
#             chans.append(MCP4728Channel(data[i:i+6]))
#         return chans
#
#     def readvoltages(self):
#         chans = self.status()
#         voltages = []
#         for chan in chans:
#             value = float(chan.output.value)
#             voltage = self.vdd * value / 2**12
#             voltages.append(voltage)
#         return voltages

class TempMCP9808:
    """Temperture chip on analog board."""

    regTemp = 0x5

    def __init__(self, i2ccore, addr=0b0011000):
        self.i2ccore = i2ccore
        self.slaveaddr = addr & 0x7f
# Here the chip needs a specific register written as a command before it knows
# where to write to, which is the regaddr byte that is passed upself.

    def readreg(self, regaddr):
        n, data = self.i2ccore.writeread(self.slaveaddr, [regaddr], 2)
        assert n == 1 # this is the one byte address for the registry
        assert len(data) == 2 # this is teh length of the data read from the chip
        val = data[0] << 8
        val |= data[1]
        return val

    def temp(self):
        val = self.readreg(TempMCP9808.regTemp)
        return self.u16todeg(val)

    def u16todeg(self, val):
        val &= 0x1fff
        neg = val & 0x1000 > 0
        val &= 0x0fff
        if neg:
            return -float(0xfff - val) / 16.0
        return float(val) / 16.0
