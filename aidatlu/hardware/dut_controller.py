from aidatlu import logger
from aidatlu.hardware.i2c import I2CCore


class DUTLogic(object):
    def __init__(self, i2c: I2CCore):
        self.log = logger.setup_derived_logger("DUT Logic")
        self.i2c = i2c

    def set_dut_mask(self, enable: int | str) -> None:
        """Enables HDMI Outputs the enable is here an 4-bit WORD as integer or binary string to enable each HDMI channel.
            With HDMI channel 1 = bit 0, channel 2 = bit 2, channel 3 = bit 3 and channel 4 = bit 4.
            E.q. 0b0001 or '0001' enables HDMI channel 1, '0011' enables channel 1 and 2 and so on.

        Args:
            value (int | str): 4-bit WORD to enable the the HDMI outputs. Can be an integer or binary string.
        """
        if type(enable) == str:
            enable = int(enable, 2)

        if enable > 0b1111 or enable < 0b0000:
            raise ValueError("Enable has to be between 0 and 15 ('1111')")

        self.i2c.write_register("DUTInterfaces.DUTMaskW", enable & 0xF)
        self.log.info("DUT mask set to %s" % self.get_dut_mask())

    def set_dut_mask_mode(self, mode: int | str) -> None:
        """Sets the DUT interface mode. Mode consits of one 8-bit WORD or more specific 4 2-bit WORDs.
            Each 2-bit WORD corresponds to one HDMI output and its mode.
            With HDMI channel 1 = bit 0 and 1, channel 2 = bit 2 and 3, channel 3 = bit 4 and 5 and channel 4 = bit 6 and 7.
            The mode is set with X0 = EUDET and X1 = AIDA. #TODO They mention the leading bit X can be used for future modes. Is this still up to date?
            E.q. 0b00000011 sets HDMI channel 1 to AIDA mode and channels 2,3 and 4 to EUDET.

        Args:
            mode (int | str): 8-bit WORD to set the mode for each DUT. Can be an integer or binary string.
        """

        if type(mode) == str:
            mode = int(mode, 2)

        if mode > 0b11111111 or mode < 0b00000000:
            raise ValueError("Mode has to be between 0 and 256 ('100000000').")

        self.i2c.write_register("DUTInterfaces.DUTInterfaceModeW", mode)
        self.log.info("DUT mask mode is set to %s" % self.get_dut_mask_mode())

    def set_dut_mask_mode_modifier(self, value: int) -> None:
        """#TODO Only affects the EUDET mode of operation, looks like some special EUDET configuration.

        Args:
            value (int): _description_ #TODO
        """
        self.i2c.write_register("DUTInterfaces.DUTInterfaceModeModifierW", value)
        self.log.info(
            "DUT mask mode modifier is set to %s" % self.get_dut_mask_mode_modifier()
        )

    def set_dut_ignore_busy(self, channels: int | str) -> None:
        """If set the TLU ignores the BUSY signal from a DUT in AIDA mode.
            Channels consits of a 4-bit WORD describing the DUT interfaces.
            With DUT interface 1 = bit 0, interface 2 = bit 1, interface 3 = bit 2 and interface 4 = bit 3.
            #TODO not sure if this is true here. No answers in documentation.

        Args:
            channels (int | str): _description_#TODO
        """
        if type(channels) == str:
            channels = int(channels, 2)

        if channels > 0b1111 or channels < 0b0000:
            raise ValueError("Channels has to be between 0 and 16 ('10000').")

        self.i2c.write_register("DUTInterfaces.IgnoreDUTBusyW", channels)
        self.log.info("DUT ignore busy is set to %s" % self.get_dut_ignore_busy())

    def get_dut_mask(self) -> int:
        """Reads the contend in the register 'DUTMaskR'.

        Returns:
            int: Integer content of the register.
        """
        return self.i2c.read_register("DUTInterfaces.DUTMaskR")

    def get_dut_mask_mode(self) -> int:
        """Reads the contend in the register 'DUTInterfaceModeR'.

        Returns:
            int: Integer content of the register.
        """
        return self.i2c.read_register("DUTInterfaces.DUTInterfaceModeR")

    def get_dut_mask_mode_modifier(self) -> int:
        """Reads the content in the register 'DUTInterfaceModeModifierR'.

        Returns:
            int: Integer content of the register.
        """
        return self.i2c.read_register("DUTInterfaces.DUTInterfaceModeModifierR")

    def get_dut_ignore_busy(self) -> int:
        """Reads the content in the register 'IgnoreDUTBusyR'.

        Returns:
            int: Integer content of the register.
        """
        return self.i2c.read_register("DUTInterfaces.IgnoreDUTBusyR")

    def set_dut_ignore_shutter(self, value: int) -> None:
        self.i2c.write_register("DUTInterfaces.IgnoreShutterVetoW", value)
        self.log.info("DUT ignore shutter set to %s" % self.get_dut_ignore_shutter())

    def get_dut_ignore_shutter(self):
        return self.i2c.read_register("DUTInterfaces.IgnoreShutterVetoR")
