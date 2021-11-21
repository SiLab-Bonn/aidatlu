# -*- coding: utf-8 -*-
import uhal
from packages.I2CuHal import I2CCore
import numpy as np


class ATSHA204A:
    #Class for Atmel ATSHA204A eeprom

    def __init__(self, i2c, slaveaddr= 0x64):
        self.i2c = i2c
        self.slaveaddr = slaveaddr

    #Slot size, in bytes.
        self.SLOT_SIZE_BYTES = 32;
    #Word size, in bytes. This is the base unit for all reads and writes.
        self.WORD_SIZE_BYTES = 4;
    #Maximum word offset per slot
        self.MAX_WORD_OFFSET = 7;
    #Size of the configuration zone, in bytes
        self.CONFIGURATION_ZONE_SIZE_BYTES = 88;
    #Number of slots in the configuration zone
        self.CONFIGURATION_ZONE_SIZE_SLOTS = 3;
    #Slot 3 in the configuration zone is only 24 bytes rather than 32, so the max word offset is limited to 5.
        self.CONFIGURATION_ZONE_SLOT_2_MAX_WORD_OFFSET = 5;
    #Size of the OTP zone, in bytes
        self.OTP_ZONE_SIZE_BYTES = 64;
    #Number of slots in the OTP zone
        self.OTP_ZONE_SIZE_SLOTS = 2;
    #Size of the data zone, in bytes
        self.DATA_ZONE_SIZE_BYTES = 512;
    #Number of slots in the data zone
        self.DATA_ZONE_SIZE_SLOTS = 16;
    #The data slot used for module configuration data
        self.DATA_ZONE_SLOT_MODULE_CONFIGURATION = 0;
    #Byte index of the OTP mode byte within its configuration word.
        self.OTP_MODE_WORD_BYTE_INDEX = 2;

#-------------------------------------------------------------------------------------------------
# Command packets and I/O
#-------------------------------------------------------------------------------------------------
    #Command execution status response block size
        self.STATUS_RESPONSE_BLOCK_SIZE_BYTES = 4;
    #Byte index of count in response block
        self.STATUS_RESPONSE_COUNT_BYTE_INDEX = 0;
    #Byte index of status code in response block
        self.STATUS_RESPONSE_STATUS_BYTE_INDEX = 1;
    #Checksum size
        self.CHECKSUM_LENGTH_BYTES = 2;
    #Index of the count byte in a command packet
        self.COMMAND_PACKET_COUNT_BYTE_INDEX = 0;
    #Size of count in a command packet
        self.COMMAND_PACKET_COUNT_SIZE_BYTES = 1;
    #Index of the opcode byte in a command packet
        self.COMMAND_PACKET_OPCODE_BYTE_INDEX = 1;
    #Size of the opcode byte in a command packet
        self.COMMAND_PACKET_OPCODE_LENGTH_BYTES = 1;
    #Index of param 1 in a command packet
        self.COMMAND_PACKET_PARAM1_BYTE_INDEX = 2;
    #Size of param 1 in a command packet
        self.COMMAND_PACKET_PARAM1_SIZE_BYTES = 1;
    #Index of param 2 in a command packet
        self.COMMAND_PACKET_PARAM2_BYTE_INDEX = 3;
    #Size of param 2 in a command packet
        self.COMMAND_PACKET_PARAM2_SIZE_BYTES = 2;

    def _CalculateCrc(self, pData, dataLengthBytes):
        # Calculate a CRC-16 used when communicating with the device. Code taken from Atmel's library.
        #The Atmel documentation only specifies that the CRC algorithm used on the ATSHA204A is CRC-16 with polynomial
        #0x8005; compared to a standard CRC-16, however, the used algorithm doesn't use remainder reflection.
        #@param pData				The data to calculate the CRC for
        #@param dataLengthBytes	The number of bytes to process
        #@return					The CRC
        polynomial = 0x8005
        crcRegister = 0
        if not pData:
            print("_CalculateCrc: No data to process")
            return 0
        for counter in range(0, dataLengthBytes):
            shiftRegister= 0x01
            for iShift in range(0, 8):
                if (pData[counter] & shiftRegister) :
                    dataBit= 1
                else:
                    dataBit=0
                crcBit= ((crcRegister) >> 15)
                crcRegister <<= 1
                crcRegister= crcRegister & 0xffff
                #print shiftRegister, "\t", dataBit, "\t", crcBit, "\t", crcRegister
                shiftRegister=  shiftRegister << 1
                if (dataBit != crcBit):
                    #print "poly"
                    crcRegister ^= polynomial;
        return crcRegister

    def _wake(self, verifyDeviceIsAtmelAtsha204a, debug):
        dummyWriteData = 0x00
        mystop=True
        self.i2c.write( self.slaveaddr, [dummyWriteData], mystop)

        if (verifyDeviceIsAtmelAtsha204a):
            expectedStatusBlock= [ 0x04, 0x11, 0x33, 0x43 ];
            nwords= 4
            res= self.i2c.read( self.slaveaddr, nwords)
            if (res != expectedStatusBlock):
                print("Attempt to awake Atmel ATSHA204A failed")
            print(res)

    def _GetCommandPacketSize(self, additionalDataLengthBytes):
        packetSizeBytes = self.COMMAND_PACKET_COUNT_SIZE_BYTES + self.COMMAND_PACKET_OPCODE_LENGTH_BYTES  \
                          + self.COMMAND_PACKET_PARAM1_SIZE_BYTES + self.COMMAND_PACKET_PARAM2_SIZE_BYTES \
                          + additionalDataLengthBytes + self.CHECKSUM_LENGTH_BYTES;

        return packetSizeBytes
