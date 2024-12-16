import yaml
from aidatlu import logger


class TLUConfigure():
    def __init__(self, TLU, io_control, config_path) -> None:
        self.log = logger.setup_main_logger(__class__.__name__)

        self.tlu = TLU
        self.io_control = io_control

        with open(config_path, "r") as file:
            self.conf = yaml.full_load(file)

    def configure(self) -> None:
        """Loads configuration file and configures the TLU accordingly."""
        self.conf_dut()
        self.conf_trigger_inputs()
        self.conf_trigger_logic()
        self.tlu.io_controller.clock_lemo_output(
            self.conf["clock_lemo"]["enable_clock_lemo_output"]
        )
        [
            self.tlu.dac_controller.set_voltage(
                i + 1, self.conf["pmt_control"]["pmt_%s" % (i + 1)]
            )
            for i in range(len(self.conf["pmt_control"]))
        ]
        self.tlu.set_enable_record_data(1)
        self.log.success("TLU configured")

    def get_configuration_table(self) -> list:
        """Creates the configuration list to save in the data files

        Returns:
            list: configuration list
        """
        conf = [
            (
                "internal_trigger_rate",
                self.conf["internal_trigger"]["internal_trigger_rate"],
            ),
            ("DUT_1", self.conf["dut_module"]["dut_1"]["mode"]),
            ("DUT_2", self.conf["dut_module"]["dut_2"]["mode"]),
            ("DUT_3", self.conf["dut_module"]["dut_3"]["mode"]),
            ("DUT_4", self.conf["dut_module"]["dut_4"]["mode"]),
            ("threshold_1", self.conf["trigger_inputs"]["threshold"]["threshold_1"]),
            ("threshold_2", self.conf["trigger_inputs"]["threshold"]["threshold_2"]),
            ("threshold_3", self.conf["trigger_inputs"]["threshold"]["threshold_3"]),
            ("threshold_4", self.conf["trigger_inputs"]["threshold"]["threshold_4"]),
            ("threshold_5", self.conf["trigger_inputs"]["threshold"]["threshold_3"]),
            ("threshold_6", self.conf["trigger_inputs"]["threshold"]["threshold_4"]),
            (
                "trigger_inputs_logic",
                "%s" % (self.conf["trigger_inputs"]["trigger_inputs_logic"]),
            ),
            (
                "trigger_signal_shape_stretch",
                "%s"
                % str(self.conf["trigger_inputs"]["trigger_signal_shape"]["stretch"]),
            ),
            (
                "trigger_signal_shape_delay",
                "%s"
                % str(self.conf["trigger_inputs"]["trigger_signal_shape"]["delay"]),
            ),
            (
                "trigger_polarity",
                "%s"
                % (
                    "falling"
                    if self.conf["trigger_inputs"]["trigger_polarity"]["polarity"] == 1
                    else "rising"
                ),
            ),
            (
                "enable_clock_lemo_output",
                self.conf["clock_lemo"]["enable_clock_lemo_output"],
            ),
            ("pmt_control_1", self.conf["pmt_control"]["pmt_1"]),
            ("pmt_control_2", self.conf["pmt_control"]["pmt_2"]),
            ("pmt_control_3", self.conf["pmt_control"]["pmt_3"]),
            ("pmt_control_4", self.conf["pmt_control"]["pmt_4"]),
            ("save_data", self.conf["save_data"]),
            ("output_data_path", self.conf["output_data_path"]),
            ("zmq_connection", self.conf["zmq_connection"]),
        ]
        return conf

    def get_data_handling(self) -> tuple:
        """Information about data handling.

        Returns:
            tuple: two bools, save and interpret data.
        """

        return self.conf["save_data"], self.conf["save_data"]

    def get_stop_condition(self) -> tuple:
        """Information about tlu stop condition.

        Returns:
            tuple: maximum trigger number and timeout in seconds.
        """
        try:
            max_number = int(self.conf["max_trigger_number"])
            self.log.info("Stop condition maximum triggers: %s" % max_number)
        except KeyError:
            max_number = None
        try:
            timeout = float(self.conf["timeout"])
            self.log.info("Stop condition timeout: %s s" % timeout)
        except KeyError:
            timeout = None
        return max_number, timeout

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

    def conf_dut(self) -> None:
        """Parse the configuration for the DUT interface to the AIDATLU."""
        dut = [0, 0, 0, 0]
        dut_mode = [0, 0, 0, 0]
        for i in range(4):
            if (
                self.tlu.config_parser.conf["dut_module"]["dut_%s" % (i + 1)]["mode"]
                == "eudet"
            ):
                self.tlu.io_controller.switch_led(i + 1, "g")
                dut[i] = 2**i
                # Clock output needs to be disabled for EUDET mode.
                self.tlu.io_controller.clock_hdmi_output(i + 1, "off")
            if (
                self.tlu.config_parser.conf["dut_module"]["dut_%s" % (i + 1)]["mode"]
                == "aidatrig"
            ):
                self.tlu.io_controller.switch_led(i + 1, "w")
                dut[i] = 2**i
                dut_mode[i] = 2 ** (2 * i)
                # In AIDA mode the clock output is needed.
                self.tlu.io_controller.clock_hdmi_output(i + 1, "chip")
            if (
                self.tlu.config_parser.conf["dut_module"]["dut_%s" % (i + 1)]["mode"]
                == "aida"
            ):
                self.tlu.io_controller.switch_led(i + 1, "b")
                dut[i] = 2**i
                dut_mode[i] = 3 * (2) ** (2 * i)
                self.tlu.io_controller.clock_hdmi_output(i + 1, "chip")
            self.tlu.io_controller.configure_hdmi(i + 1, "0111")

        [
            self.log.info(
                "DUT %i configured in %s"
                % (
                    (i + 1),
                    self.tlu.config_parser.conf["dut_module"]["dut_%s" % (i + 1)][
                        "mode"
                    ],
                )
            )
            for i in range(4)
        ]

        # This sets the right bits to the set dut mask registers according to the configuration parameter.
        self.tlu.dut_logic.set_dut_mask(dut[0] | dut[1] | dut[2] | dut[3])
        self.tlu.dut_logic.set_dut_mask_mode(
            dut_mode[0] | dut_mode[1] | dut_mode[2] | dut_mode[3]
        )

        # Special configs
        self.tlu.dut_logic.set_dut_mask_mode_modifier(0)
        self.tlu.dut_logic.set_dut_ignore_busy(0)
        self.tlu.dut_logic.set_dut_ignore_shutter(0x1)

    def conf_trigger_logic(self) -> None:
        """Configures the trigger logic. So the trigger polarity and the trigger pulse length and stretch."""

        self.tlu.trigger_logic.set_trigger_polarity(
            self.conf["trigger_inputs"]["trigger_polarity"]["polarity"]
        )

        self.tlu.trigger_logic.set_pulse_stretch_pack(
            self.conf["trigger_inputs"]["trigger_signal_shape"]["stretch"]
        )
        self.tlu.trigger_logic.set_pulse_delay_pack(
            self.conf["trigger_inputs"]["trigger_signal_shape"]["delay"]
        )
        self.log.info(
            "Trigger input stretch: %s"
            % self.conf["trigger_inputs"]["trigger_signal_shape"]["stretch"]
        )
        self.log.info(
            "Trigger input delay  : %s"
            % self.conf["trigger_inputs"]["trigger_signal_shape"]["delay"]
        )

        self.tlu.trigger_logic.set_internal_trigger_frequency(
            self.conf["internal_trigger"]["internal_trigger_rate"]
        )

    def conf_trigger_inputs(self) -> None:
        """Configures the trigger inputs. Each input can have a different threshold.
        The two trigger words mask_low and mask_high are generated with the use of two support functions.
        """
        [
            self.tlu.dac_controller.set_threshold(
                i + 1,
                self.conf["trigger_inputs"]["threshold"]["threshold_%s" % (i + 1)],
            )
            for i in range(6)
        ]

        trigger_configuration = self.conf["trigger_inputs"]["trigger_inputs_logic"]

        self.log.info("Trigger Configuration: %s" % (trigger_configuration))

        # Sets the Trigger Leds to green if the Input is enabled and to red if the input is set to VETO.
        # TODO this breaks when there are multiple enabled and veto statements.
        if trigger_configuration is not None:
            for trigger_led in range(6):
                if "~CH%i" % (trigger_led + 1) in trigger_configuration:
                    self.io_control.switch_led(trigger_led + 6, "r")
                elif "CH%i" % (trigger_led + 1) in trigger_configuration:
                    self.io_control.switch_led(trigger_led + 6, "g")

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
                valid = (
                    lambda CH1, CH2, CH3, CH4, CH5, CH6: eval(trigger_configuration)
                )(CCH0, CCH1, CCH2, CCH3, CCH4, CCH5)
                long_word = (valid << combination) | long_word

            mask_low, mask_high = self._mask_words(long_word)
            self.log.debug(
                "mask high: %s, mask low: %s" % (hex(mask_high), hex(mask_low))
            )
            self.tlu.trigger_logic.set_trigger_mask(mask_high, mask_low)

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
