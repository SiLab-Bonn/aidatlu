import numpy as np

from aidatlu import logger
from aidatlu.hardware.clock_controller import ClockControl
from aidatlu.hardware.dac_controller import DacControl
from aidatlu.hardware.dut_controller import DUTLogic
from aidatlu.hardware.i2c import I2CCore
from aidatlu.hardware.ioexpander_controller import IOControl
from aidatlu.hardware.trigger_controller import TriggerLogic


class TLUControl:
    """Controls general TLU functionalities."""

    def __init__(self, hw, i2c=I2CCore) -> None:
        self.log = logger.setup_main_logger(__class__.__name__)
        self.i2c = i2c(hw)
        self.i2c_hw = hw
        self.log.info("Initializing IPbus interface")
        self.i2c.init()

        if self.i2c.modules["eeprom"]:
            self.log.info("Found device with ID %s" % hex(self.get_device_id()))

        # TODO some configuration also sends out ~70 triggers.
        self.io_controller = IOControl(self.i2c)
        self.dac_controller = DacControl(self.i2c)
        self.clock_controller = ClockControl(self.i2c, self.io_controller)
        self.trigger_logic = TriggerLogic(self.i2c)
        self.dut_logic = DUTLogic(self.i2c)

    ### General TLU Functions ###

    def reset_configuration(self) -> None:
        # Disable all outputs
        self.io_controller.clock_lemo_output(False)
        for i in range(4):
            self.io_controller.configure_hdmi(i + 1, 1)
        self.dac_controller.set_voltage(5, 0)
        self.io_controller.all_off()
        # sets all thresholds to 1.2 V
        for i in range(6):
            self.dac_controller.set_threshold(i + 1, 0)
        # Resets all internal counters and raise the trigger veto.
        self.set_run_active(False)
        self.reset_status()
        self.reset_counters()
        self.trigger_logic.set_trigger_veto(True)
        self.reset_fifo()
        self.reset_timestamp()

    def start_run(self) -> None:
        """Start run configurations"""
        self.reset_counters()
        self.reset_fifo()
        self.reset_timestamp()
        self.set_run_active(True)
        self.trigger_logic.set_trigger_veto(False)

    def stop_run(self) -> None:
        """Stop run configurations"""
        self.trigger_logic.set_trigger_veto(True)
        self.set_run_active(False)

    ### Basic TLU Control Functions ###

    def write_clock_config(self, clock_config_path):
        self.clock_controller.write_clock_conf(clock_config_path)

    def get_device_id(self) -> int:
        """Read back board id. Consists of six blocks of hex data

        Returns:
            int: Board id as 48 bits integer
        """
        id = []
        for addr in range(6):
            id.append(self.i2c.read(self.i2c.modules["eeprom"], 0xFA + addr) & 0xFF)
        return int("0x" + "".join(["{:x}".format(i) for i in id]), 16) & 0xFFFFFFFFFFFF

    def get_fw_version(self) -> int:
        return self.i2c.read_register("version")

    def reset_timestamp(self) -> None:
        """Sets bit to  'ResetTimestampW' register to reset the time stamp."""
        self.i2c.write_register("Event_Formatter.ResetTimestampW", 1)

    def reset_counters(self) -> None:
        """Resets the trigger counters."""
        self.write_status(0x2)
        self.write_status(0x0)

    def reset_status(self) -> None:
        """Resets the complete status and all counters."""
        self.write_status(0x3)
        self.write_status(0x0)
        self.write_status(0x4)
        self.write_status(0x0)

    def reset_fifo(self) -> None:
        """Sets 0 to 'EventFifoCSR' this resets the FIFO."""
        self.set_event_fifo_csr(0x0)

    def set_event_fifo_csr(self, value: int) -> None:
        """Sets value to the EventFifoCSR register.

        Args:
            value (int): 0 resets the FIFO. #TODO can do other stuff that is not implemented

        """
        self.i2c.write_register("eventBuffer.EventFifoCSR", value)

    def write_status(self, value: int) -> None:
        """Sets value to the 'SerdesRstW' register.

        Args:
            value (int): Bit 0 resets the status, bit 1 resets trigger counters and bit 2 calibrates IDELAY.
        """
        self.i2c.write_register("triggerInputs.SerdesRstW", value)

    def set_run_active(self, state: bool) -> None:
        """Raises internal run active signal.

        Args:
            state (bool): True sets run active, False disables it.
        """
        if type(state) != bool:
            raise TypeError("State has to be bool")
        self.i2c.write_register("Shutter.RunActiveRW", int(state))
        self.log.info("Run active: %s" % self.get_run_active())

    def get_run_active(self) -> bool:
        """Reads register 'RunActiveRW'

        Returns:
            bool: Returns bool of the run active register.
        """
        return bool(self.i2c.read_register("Shutter.RunActiveRW"))

    def set_enable_record_data(self, value: int) -> None:
        """#TODO not sure what this does. Looks like a separate internal event buffer to the FIFO.

        Args:
            value (int): #TODO I think this does not work
        """
        self.i2c.write_register("Event_Formatter.Enable_Record_Data", value)

    def get_event_fifo_csr(self) -> int:
        """Reads value from 'EventFifoCSR', corresponds to status flags of the FIFO.

        Returns:
            int: number of events
        """
        return self.i2c.read_register("eventBuffer.EventFifoCSR")

    def get_event_fifo_fill_level(self) -> int:
        """Reads value from 'EventFifoFillLevel'
           Returns the number of words written in
           the FIFO. The lowest 14-bits are the actual data.

        Returns:
            int: buffer level of the fifi
        """
        return self.i2c.read_register("eventBuffer.EventFifoFillLevel")

    def get_timestamp(self) -> int:
        """Get current time stamp.

        Returns:
            int: Time stamp in 40MHz clock cycles.
        """
        time = self.i2c.read_register("Event_Formatter.CurrentTimestampHR")
        time = time << 32
        time = time + self.i2c.read_register("Event_Formatter.CurrentTimestampLR")
        return time

    def pull_fifo_event(self) -> list:
        """Pulls event from the FIFO. This is needed in the run loop to prevent the buffer to get stuck.
            if this register is full the fifo needs to be reset or new triggers are generated but not sent out.
            #TODO check here if the FIFO is full and reset it if needed would prob. make sense.

        Returns:
            list: 6 element long vector containing bitwords of the data.
        """
        event_numb = self.get_event_fifo_fill_level()
        if event_numb:
            fifo_content = self.i2c_hw.getNode("eventBuffer.EventFifoData").readBlock(
                event_numb
            )
            self.i2c_hw.dispatch()
            return np.array(fifo_content)
        pass

    def get_scaler(self, channel: int) -> int:
        """reads current scaler value from register"""
        if channel < 0 or channel > 5:
            raise ValueError("Only channels 0 to 5 are valid")
        return self.i2c.read_register(f"triggerInputs.ThrCount{channel:d}R")

    def get_scalers(self) -> list:
        """reads current sc values from registers

        Returns:
            list: all 6 trigger sc values
        """
        return [self.get_scaler(n) for n in range(6)]

    def get_pre_veto_trigger_number(self) -> int:
        """Obtains the number of triggers recorded in the TLU before the veto is applied from the trigger logic register"""
        return self.trigger_logic.get_pre_veto_trigger()

    def get_post_veto_trigger_number(self) -> int:
        """Obtains the number of triggers recorded in the TLU after the veto is applied from the trigger logic register"""
        return self.trigger_logic.get_post_veto_trigger()
