# -*- coding: utf-8 -*-
import uhal
from I2CuHal import I2CCore
import StringIO


class PCA9548ADW:
    #Class to configure the I2C multiplexer

    def __init__(self, i2c, slaveaddr=0x74):
        self.i2c = i2c
        self.slaveaddr = slaveaddr

    def disableAllChannels(self, verbose=False):
        #Disable all channels so that none of the MUX outputs is visible
        # to the upstream I2C bus
        mystop=True
        cmd= [0x0]
        self.i2c.write( self.slaveaddr, cmd, mystop)

    def getChannelStatus(self, verbose=False):
        #Basic functionality to read the status of the control register and determine
        # which channel is currently enabled.
        mystop=False
        cmd= []
        self.i2c.write( self.slaveaddr, cmd, mystop)
        res= self.i2c.read( self.slaveaddr, 1)
        return res[0]

    def setActiveChannel(self, channel, verbose=False):
        #Basic functionality to activate one channel
        # In principle multiple channels can be active at the same time (see
        # function "setMultipleChannels")
        if (channel < 0) | (channel > 7):
            print "PCA9539PW - ERROR: channel number should be in range [0:7]"
            return
        mystop=True
        cmd= [0x1 << channel]
        #print "\tChannel is ", channel, "we write ", cmd
        self.i2c.write( self.slaveaddr, cmd, mystop)

    def setMultipleChannels(self, channels, verbose=False):
        #Basic functionality to activate multiple channels
        # channels is a byte: each bit set to one will set the corresponding channels
        # as active. The slave connected to that channel will be visible on the I2C bus.
        # NOTE: this can lead to address clashes!
        channels = channels & 0xFF
        mystop=True
        cmd= [channels]
        #print "\tChannel is ", channel, "we write ", cmd
        self.i2c.write( self.slaveaddr, cmd, mystop)
