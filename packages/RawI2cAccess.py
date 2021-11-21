# Created on Sep 10, 2012
# @author: Kristian Harder, based on code by Carl Jeske

from I2cBusProperties import I2cBusProperties
from ChipsBus import ChipsBus
from ChipsLog import chipsLog
from ChipsException import ChipsException


class RawI2cAccess:

    def __init__(self, i2cBusProps, slaveAddr):

        # For performing read/writes over an OpenCores-compatible I2C bus master
        #
        # An instance of this class is required to communicate with each
        # I2C slave on the I2C bus.
        #
        # i2cBusProps: an instance of the class I2cBusProperties that contains
        #    the relevant ChipsBus host and the I2C bus-master registers (if
        #    they differ from the defaults specified by the I2cBusProperties
        #    class).
        #
        #slaveAddr: The address of the I2C slave you wish to communicate with.
        #

        self._i2cProps = i2cBusProps   # The I2C Bus Properties
        self._slaveAddr = 0x7f & slaveAddr  # 7-bit slave address


    def resetI2cBus(self):

        # Resets the I2C bus
        #
        # This function does the following:
        #        1) Disables the I2C core
        #        2) Sets the clock prescale registers
        #        3) Enables the I2C core
        #        4) Sets all writable bus-master registers to default values

        try:
            self._chipsBus().queueWrite(self._i2cProps.ctrlReg, 0x00)
            #self._chipsBus().getNode(self._i2cProps.ctrlReg).write(0)
            self._chipsBus().queueWrite(self._i2cProps.preHiReg,
                                        self._i2cProps.preHiVal)
            self._chipsBus().queueWrite(self._i2cProps.preLoReg,
                                        self._i2cProps.preLoVal)
            self._chipsBus().queueWrite(self._i2cProps.ctrlReg, 0x80)
            self._chipsBus().queueWrite(self._i2cProps.txReg, 0x00)
            self._chipsBus().queueWrite(self._i2cProps.cmdReg, 0x00)
            self._chipsBus().queueRun()
        except ChipsException, err:
            raise ChipsException("I2C reset error:\n\t" + str(err))


    def read(self, numBytes):

        # Performs an I2C read. Returns the 8-bit read result(s).
        #
        # numBytes: number of bytes expected as response
        #

        try:
            result = self._privateRead(numBytes)
        except ChipsException, err:
            raise ChipsException("I2C read error:\n\t" + str(err))
        return result


    def write(self, listDataU8):

        # Performs an 8-bit I2C write.
        #
        # listDataU8:  The 8-bit data values to be written.
        #

        try:
            self._privateWrite(listDataU8)
        except ChipsException, err:
            raise ChipsException("I2C write error:\n\t" + str(err))
        return


    def _chipsBus(self):

        # Returns the instance of the ChipsBus device that's hosting
        # the I2C bus master

        return self._i2cProps.chipsBus


    def _privateRead(self, numBytes):

        # I2C read implementation.
        #
        #  Fast I2C read implementation,
        # i.e. done with the fewest packets possible.


        # transmit reg definitions
        # bits 7-1: 7-bit slave address during address transfer
        #           or first 7 bits of byte during data transfer
        # bit 0: RW flag during address transfer or LSB during data transfer.
        #        '1' = reading from slave
        #        '0' = writing to slave

        # command reg definitions
        # bit 7:   Generate start condition
        # bit 6:   Generate stop condition
        # bit 5:   Read from slave
        # bit 4:   Write to slave
        # bit 3:   0 when acknowledgement is received
        # bit 2:1: Reserved
        # bit 0:   Interrupt acknowledge. When set, clears a pending interrupt

        # Reset bus before beginning
        self.resetI2cBus()

        # Set slave address in bits 7:1, and set bit 0 to zero
        # (i.e. we're writing an address to the bus)
        self._chipsBus().queueWrite(self._i2cProps.txReg,
                                    (self._slaveAddr << 1) | 0x01)
        # Set start and write bit in command reg
        self._chipsBus().queueWrite(self._i2cProps.cmdReg, 0x90)
        # Run the queue
        self._chipsBus().queueRun()
        # Wait for transaction to finish.
        self._i2cWaitUntilFinished()

        result=[]
        for ibyte in range(numBytes):
            if ibyte==numBytes-1:
                stop_bit=0x40
                ack_bit=0x08
            else:
                stop_bit=0
                ack_bit=0
                pass
            # Set read bit, acknowledge and stop bit in command reg
            self._chipsBus().write(self._i2cProps.cmdReg, 0x20+ack_bit+stop_bit)
            # Wait for transaction to finish.
            # Don't expect an ACK, do expect bus free at finish.
            if stop_bit:
                self._i2cWaitUntilFinished(requireAcknowledgement = False,
                                           requireBusIdleAtEnd = True)
            else:
                self._i2cWaitUntilFinished(requireAcknowledgement = False,
                                           requireBusIdleAtEnd = False)
                pass
            result.append(self._chipsBus().read(self._i2cProps.rxReg))

        return result


    def _privateWrite(self, listDataU8):

        # I2C write implementation.
        #
        #  Fast I2C write implementation,
        # i.e. done with the fewest packets possible.

        # transmit reg definitions
        # bits 7-1: 7-bit slave address during address transfer
        #           or first 7 bits of byte during data transfer
        # bit 0: RW flag during address transfer or LSB during data transfer.
        # '1' = reading from slave
        # '0' = writing to slave

        # command reg definitions
        # bit 7: Generate start condition
        # bit 6: Generate stop condition
        # bit 5: Read from slave
        # bit 4: Write to slave
        # bit 3: 0 when acknowledgement is received
        # bit 2:1: Reserved
        # bit 0: Interrupt acknowledge. When set, clears a pending interrupt
        # Reset bus before beginning
        self.resetI2cBus()

        # Set slave address in bits 7:1, and set bit 0 to zero (i.e. "write mode")
        self._chipsBus().queueWrite(self._i2cProps.txReg,
                                    (self._slaveAddr << 1) & 0xfe)
        # Set start and write bit in command reg
        self._chipsBus().queueWrite(self._i2cProps.cmdReg, 0x90)
        # Run the queue
        self._chipsBus().queueRun()
        # Wait for transaction to finish.
        self._i2cWaitUntilFinished()

        for ibyte in range(len(listDataU8)):
            dataU8 = listDataU8[ibyte]
            if ibyte==len(listDataU8)-1:
                stop_bit=0x40
            else:
                stop_bit=0x00
                pass
            # Set data to be written in transmit reg
            self._chipsBus().queueWrite(self._i2cProps.txReg, (dataU8 & 0xff))
            # Set write and stop bit in command reg
            self._chipsBus().queueWrite(self._i2cProps.cmdReg, 0x10+stop_bit)
            # Run the queue
            self._chipsBus().queueRun()
            # Wait for transaction to finish.
            # Do expect an ACK and do expect bus to be free at finish
            if stop_bit:
                self._i2cWaitUntilFinished(requireAcknowledgement = True,
                                           requireBusIdleAtEnd = True)
            else:
                self._i2cWaitUntilFinished(requireAcknowledgement = True,
                                           requireBusIdleAtEnd = False)
                pass
            pass

        return


    def _i2cWaitUntilFinished(self, requireAcknowledgement = True,
                              requireBusIdleAtEnd = False):

        # Ensures the current bus transaction has finished successfully
        # before allowing further I2C bus transactions

        # This method monitors the status register
        # and will not allow execution to continue until the
        # I2C bus has completed properly.  It will throw an exception
        # if it picks up bus problems or a bus timeout occurs.

        maxRetry = 20
        attempt = 1
        while attempt <= maxRetry:

            # Get the status
            i2c_status = self._chipsBus().read(self._i2cProps.statusReg)

            receivedAcknowledge = not bool(i2c_status & 0x80)
            busy = bool(i2c_status & 0x40)
            arbitrationLost = bool(i2c_status & 0x20)
            transferInProgress = bool(i2c_status & 0x02)
            interruptFlag = bool(i2c_status & 0x01)

            if arbitrationLost:  # This is an instant error at any time
                raise ChipsException("I2C error: Arbitration lost!")

            if not transferInProgress:
                break  # The transfer looks to have completed successfully, pending further checks

            attempt += 1

        # At this point, we've either had too many retries, or the
        # Transfer in Progress (TIP) bit went low.  If the TIP bit
        # did go low, then we do a couple of other checks to see if
        # the bus operated as expected:

        if attempt > maxRetry:
            raise ChipsException("I2C error: Transaction timeout - the 'Transfer in Progress' bit remained high for too long!")

        if requireAcknowledgement and not receivedAcknowledge:
            raise ChipsException("I2C error: No acknowledge received!")

        if requireBusIdleAtEnd and busy:
            raise ChipsException("I2C error: Transfer finished but bus still busy!")
