##########################################################
#  I2cBusProperties - simple encapsulation of all items
#                     required to control an I2C bus.
#
#  Carl Jeske, July 2010
#  Refactored by Robert Frazier, May 2011
##########################################################


class I2cBusProperties(object):
    """Encapsulates details of an I2C bus master in the form of a host device, a clock prescale value, and seven I2C master registers

    Provide the ChipsBus instance to the device hosting your I2C core, a 16-bit clock prescaling
    value for the Serial Clock Line (see I2C core docs for details), and the names of the seven
    registers that define/control the bus (assuming these names are not the defaults specified
    in the constructor below).  The seven registers consist of the two clock pre-scaling
    registers (PRElo, PREhi), and five bus master registers (CONTROL, TRANSMIT, RECEIVE,
    COMMAND and STATUS).

    Usage:  You'll need to create an instance of this class to give to a concrete I2C bus instance, such
            as OpenCoresI2cBus.  This I2cBusProperties class is simply a container to hold the properties
            that define the bus; a class such as OpenCoresI2cBus will make use of these properties.

            Access the items stored by this class via these (deliberately compact) variable names:

                chipsBus     -- the ChipsBus device hosting the I2C core
                preHiVal     -- the top byte of the clock prescale value
                preLoVal     -- the bottom byte of the clock prescale value
                preHiReg     -- the register the top byte of the clk prescale value (preHiVal) gets written to
                preLoReg     -- the register the bottom byte of the clk prescale value (preLoVal) gets written to
                ctrlReg      -- the I2C Control register
                txReg        -- the I2C Transmit register
                rxReg        -- the I2C Receive register
                cmdReg       -- the I2C Command register
                statusReg    -- the I2C Status register


    Compatibility Notes: The seven register names are the registers typically required to operate an
                         OpenCores or similar I2C Master (Lattice Semiconductor's I2C bus master works
                         the same way as the OpenCores one). This software is not compatible with your
                         I2C bus master if it doesn't use this register interface.
    """

    def __init__(self,
                 chipsBusDevice,
                 clkPrescaleU16,
                 clkPrescaleLoByteReg = "i2c_pre_lo",
                 clkPrescaleHiByteReg = "i2c_pre_hi",
                 controlReg           = "i2c_ctrl",
                 transmitReg          = "i2c_tx",
                 receiveReg           = "i2c_rx",
                 commandReg           = "i2c_cmd",
                 statusReg            = "i2c_status"):

        """Provide a host ChipsBus device that is controlling the I2C bus, and the names of five I2C control registers.

        chipsBusDevice:  Provide a ChipsBus instance to the device where the I2C bus is being
                controlled. The address table for this device must contain the five registers
                that control the bus, as declared next...

        clkPrescaleU16: A 16-bit value used to prescale the Serial Clock Line based on the host
                master-clock.  This value gets split into two 8-bit values and ultimately will
                get written to the two I2C clock-prescale registers as declared below.  See
                the OpenCores or Lattice Semiconductor I2C documentation for more details.

        clkPrescaleLoByteReg:  The register where the lower byte of the clock prescale value is set.  The default
                name for this register is "i2c_pre_lo".

        clkPrescaleHiByteReg:  The register where the higher byte of the clock prescale value is set.  The default
                name for this register is "i2c_pre_hi"

        controlReg:  The CONTROL register, used for enabling/disabling the I2C core, etc. This register is
                usually read and write accessible. The default name for this register is "i2c_ctrl".

        transmitReg:  The TRANSMIT register, used for holding the data to be transmitted via I2C, etc.  This
                typically shares the same address as the RECEIVE register, but has write-only access.  The default
                name for this register is "i2c_tx".

        receiveReg:  The RECEIVE register - allows access to the byte received over the I2C bus.  This
                typically shares the same address as the TRANSMIT register, but has read-only access.  The
                default name for this register is "i2c_rx".

        commandReg:  The COMMAND register - stores the command for the next I2C operation.  This typically
                shares the same address as the STATUS register, but has write-only access.  The default name for
                this register is "i2c_cmd".

        statusReg:  The STATUS register - allows monitoring of the I2C operations.  This typically shares
                the same address as the COMMAND register, but has read-only access.  The default name for this
                register is "i2c_status".
        """

        object.__init__(self)
        self.chipsBus = chipsBusDevice
        self.preHiVal = ((clkPrescaleU16 & 0xff00) >> 8)
        self.preLoVal = (clkPrescaleU16 & 0xff)
        
        # Check to see all the registers are in the address table
        registers = [clkPrescaleLoByteReg, clkPrescaleHiByteReg, controlReg, transmitReg, receiveReg, commandReg, statusReg]
        for reg in registers:
            if not self.chipsBus.addrTable.checkItem(reg):
                raise ChipsException("I2cBusProperties error: register '" + reg + "' is not present in the address table of the device hosting the I2C bus master!")

        # Check that the registers we'll need to write to are indeed writable
        writableRegisters = [clkPrescaleLoByteReg, clkPrescaleHiByteReg, controlReg, transmitReg, commandReg]
        for wReg in writableRegisters:
            if not self.chipsBus.addrTable.getItem(wReg).getWriteFlag():
                raise ChipsException("I2cBusProperties error: register '" + wReg + "' does not have the necessary write permission!")

        # Check that the registers we'll need to read from are indeed readable
        readableRegisters = [clkPrescaleLoByteReg, clkPrescaleHiByteReg, controlReg, receiveReg, statusReg]
        for rReg in readableRegisters:
            if not self.chipsBus.addrTable.getItem(rReg).getReadFlag():
                raise ChipsException("I2cBusProperties error: register '" + rReg + "' does not have the necessary read permission!")

        # Store the various register name strings
        self.preHiReg = clkPrescaleHiByteReg
        self.preLoReg = clkPrescaleLoByteReg
        self.ctrlReg = controlReg
        self.txReg = transmitReg
        self.rxReg = receiveReg
        self.cmdReg = commandReg
        self.statusReg = statusReg
