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


class TLUConfigure:
    def __init__(self, tlu, config_dict):
        self.log = logger.setup_main_logger(__class__.__name__)

        self.tlu = tlu
        self.conf = config_dict

    def configure(self) -> None:
        """Loads configuration file and configures the TLU accordingly."""
        self.conf_dut()
        self.conf_trigger_inputs()
        self.conf_trigger_logic()
        self.conf_auxillary()
        self.tlu.set_enable_record_data(1)
        self.log.info("TLU configured")

    def get_data_handling(self) -> bool:
        """Information about data handling.

        Returns:
            bool: save and interpret data.
        """

        return self.conf["save_data"]

    def get_stop_condition(self) -> tuple:
        """Information about tlu stop condition.

        Returns:
            tuple: maximum trigger number and timeout in seconds.
        """
        max_trigger_number = (
            None
            if self.conf["max_trigger_number"] in ["None", "off"]
            else self.conf["max_trigger_number"]
        )
        timeout = (
            None if self.conf["timeout"] in ["None", "off"] else self.conf["timeout"]
        )
        return max_trigger_number, timeout

    def get_output_data_path(self) -> str:
        """Parses the output data path

        Returns:
            str: output path
        """
        return self.conf["output_data_path"]

    def get_zmq_connection(self) -> str:
        """Information about the zmq Address

        Returns:
            str: ZMQ Address
        """
        return self.conf["zmq_connection"]

    def conf_auxillary(self):
        """Configures PMT power outputs and clock LEMO I/O"""
        self.tlu.io_controller.clock_lemo_output(self.conf["enable_clock_lemo_output"])
        [
            self.tlu.dac_controller.set_voltage(
                i + 1, self.conf["pmt_control_%s" % (i + 1)]
            )
            for i in range(4)
        ]

    def conf_dut(self) -> None:
        """Parse the configuration for the DUT interface to the AIDATLU."""
        dut = [0, 0, 0, 0]
        dut_mode = [0, 0, 0, 0]
        ignore_busy = 0
        for i in range(4):
            if self.conf["DUT_%s" % (i + 1)] == "eudet":
                self.tlu.io_controller.switch_led(i + 1, "g")
                dut[i] = 2**i
                # Clock output needs to be disabled for EUDET mode.
                self.tlu.io_controller.clock_hdmi_output(i + 1, "off")
            if self.conf["DUT_%s" % (i + 1)] == "aidatrig":
                self.tlu.io_controller.switch_led(i + 1, "w")
                dut[i] = 2**i
                dut_mode[i] = 2 ** (2 * i)
                # In AIDA mode the clock output is needed.
                self.tlu.io_controller.clock_hdmi_output(i + 1, "chip")
            if self.conf["DUT_%s" % (i + 1)] == "aida":
                self.tlu.io_controller.switch_led(i + 1, "b")
                dut[i] = 2**i
                dut_mode[i] = 3 * (2) ** (2 * i)
                self.tlu.io_controller.clock_hdmi_output(i + 1, "chip")
            self.tlu.io_controller.configure_hdmi(i + 1, "0111")
            ignore_busy ^= self.conf["DUT_%s_ignore_busy" % (i + 1)] << i

            if self.conf["DUT_%s_ignore_busy" % (i + 1)]:
                self.log.info("DUT interface %i ignores busy" % (i + 1))

        [
            self.log.info(
                "DUT %i configured in %s"
                % (
                    (i + 1),
                    self.conf["DUT_%s" % (i + 1)],
                )
            )
            for i in range(4)
        ]

        # This sets the right bits to the set dut mask registers according to the configuration parameter.
        self.tlu.dut_logic.set_dut_mask(dut[0] | dut[1] | dut[2] | dut[3])
        self.tlu.dut_logic.set_dut_mask_mode(
            dut_mode[0] | dut_mode[1] | dut_mode[2] | dut_mode[3]
        )
        self.log.debug("Set DUT mask: %s" % (dut[0] | dut[1] | dut[2] | dut[3]))
        self.log.debug(
            "Set DUT mask mode: %s"
            % (dut_mode[0] | dut_mode[1] | dut_mode[2] | dut_mode[3])
        )
        # Special configs
        self.tlu.dut_logic.set_dut_mask_mode_modifier(0)
        self.tlu.dut_logic.set_dut_ignore_busy(ignore_busy)
        self.tlu.dut_logic.set_dut_ignore_shutter(0x1)

    def conf_trigger_logic(self) -> None:
        """Configures the trigger logic. So the trigger polarity and the trigger pulse length and stretch."""

        if self.conf["trigger_polarity"] in [
            0,
            "0",
            "rising",
        ]:
            self.tlu.trigger_logic.set_trigger_polarity(0)
        elif self.conf["trigger_polarity"] in [
            1,
            "1",
            "falling",
        ]:
            self.tlu.trigger_logic.set_trigger_polarity(1)

        self.tlu.trigger_logic.set_pulse_stretch_pack(
            self.conf["trigger_signal_shape_stretch"]
        )
        self.tlu.trigger_logic.set_pulse_delay_pack(
            self.conf["trigger_signal_shape_delay"]
        )
        self.log.info(
            "Trigger input stretch: %s" % self.conf["trigger_signal_shape_stretch"]
        )
        self.log.info(
            "Trigger input delay  : %s" % self.conf["trigger_signal_shape_delay"]
        )

        self.tlu.trigger_logic.set_internal_trigger_frequency(
            self.conf["internal_trigger_rate"]
        )

    def conf_trigger_inputs(self) -> None:
        """Configures the trigger inputs. Each input can have a different threshold.
        The two trigger words mask_low and mask_high are generated with the use of two support functions.
        """
        [
            self.tlu.dac_controller.set_threshold(
                i + 1,
                self.conf["threshold_%s" % (i + 1)],
            )
            for i in range(6)
        ]

        trigger_configuration = self.conf["trigger_inputs_logic"]

        self.log.info("Trigger Configuration: %s" % (trigger_configuration))

        if trigger_configuration is not None:
            # Sets the Trigger Leds to green if the Input is enabled and to red if the input is set to VETO.
            # TODO this breaks when there are multiple enabled and veto statements for the same trigger input.
            for trigger_led in range(6):
                if "not CH%i" % (trigger_led + 1) in trigger_configuration:
                    self.tlu.io_controller.switch_led(trigger_led + 6, "r")
                elif "CH%i" % (trigger_led + 1) in trigger_configuration:
                    self.tlu.io_controller.switch_led(trigger_led + 6, "g")

            long_word = self._create_trigger_masking_word(trigger_configuration)
            mask_low, mask_high = self._mask_words(long_word)
            self.log.debug(
                "mask high: %s, mask low: %s" % (hex(mask_high), hex(mask_low))
            )
            self.tlu.trigger_logic.set_trigger_mask(mask_high, mask_low)
        else:
            self.log.warning("No trigger configuration provided!")

    def _create_trigger_masking_word(self, trigger_configuration) -> int:
        """Create specific long trigger configuration word by iterating over all possible
        configurations and comparing with the one provided in the configuration file.

        Args:
            trigger_configuration (str): Evaluates configurations, trigger inputs are denoted as CH1-CH6.

        Returns:
            int: long trigger configuration word
        """
        long_word = 0x0
        # Goes through all possible trigger combinations and checks if the combination is valid with the trigger logic.
        # When the word is valid this is added to the longword.
        for combination in range(64):
            pattern_list = [(combination >> element) & 0x1 for element in range(6)]
            CCH5 = pattern_list[5]
            CCH4 = pattern_list[4]
            CCH3 = pattern_list[3]
            CCH2 = pattern_list[2]
            CCH1 = pattern_list[1]
            CCH0 = pattern_list[0]
            valid = (lambda CH1, CH2, CH3, CH4, CH5, CH6: eval(trigger_configuration))(
                CCH0, CCH1, CCH2, CCH3, CCH4, CCH5
            )
            long_word = (valid << combination) | long_word

        return long_word

    def _mask_words(self, word: int) -> tuple:
        """Transforms the long word variant of the trigger word to the mask_low mask_high variant.

        Args:
        word (int): Long word variant of the trigger word.

        Returns:
        tuple: mask_low and mask_high trigger words
        """
        mask_low = 0xFFFFFFFF & word
        mask_high = word >> 32
        return (mask_low, mask_high)

    def get_configuration_table(self) -> list:
        """Creates a list of tuples from the configuration file for the output data files

        Returns:
            list: configuration list
        """
        conf_table = self.conf.copy()
        conf_table["trigger_signal_shape_stretch"] = str(
            self.conf["trigger_signal_shape_stretch"]
        )
        conf_table["trigger_signal_shape_delay"] = str(
            self.conf["trigger_signal_shape_delay"]
        )
        conf_table["trigger_polarity"] = str(self.conf["trigger_polarity"])
        conf_table["trigger_inputs_logic"] = str(self.conf["trigger_inputs_logic"])
        self.log.debug(f"Configuration table: {conf_table}")
        return list(conf_table.items())
