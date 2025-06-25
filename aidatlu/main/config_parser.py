import yaml
import tomllib

from aidatlu import logger


class Configure:
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

    def get_data_handling(self) -> tuple:
        """Information about data handling.

        Returns:
            tuple: two bools, save and interpret data.
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
        for i in range(4):
            if self.tlu.config_parser.conf["DUT_%s" % (i + 1)] == "eudet":
                self.tlu.io_controller.switch_led(i + 1, "g")
                dut[i] = 2**i
                # Clock output needs to be disabled for EUDET mode.
                self.tlu.io_controller.clock_hdmi_output(i + 1, "off")
            if self.tlu.config_parser.conf["DUT_%s" % (i + 1)] == "aidatrig":
                self.tlu.io_controller.switch_led(i + 1, "w")
                dut[i] = 2**i
                dut_mode[i] = 2 ** (2 * i)
                # In AIDA mode the clock output is needed.
                self.tlu.io_controller.clock_hdmi_output(i + 1, "chip")
            if self.tlu.config_parser.conf["DUT_%s" % (i + 1)] == "aida":
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
                    self.tlu.config_parser.conf["DUT_%s" % (i + 1)],
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
        self.tlu.dut_logic.set_dut_ignore_busy(0)
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


def yaml_parser(conf_file_path: str) -> dict:
    """Parses a yaml configuration file to a configuration dictionary.

    Args:
        conf_file_path (str): Path to yaml configuration file

    Returns:
        conf: configuration dictionary
    """

    with open(conf_file_path, "r") as file:
        yaml_conf = yaml.full_load(file)

    conf = {
        "internal_trigger_rate": yaml_conf["internal_trigger_rate"],
        "DUT_1": yaml_conf["dut_module"]["dut_1"]["mode"],
        "DUT_2": yaml_conf["dut_module"]["dut_2"]["mode"],
        "DUT_3": yaml_conf["dut_module"]["dut_3"]["mode"],
        "DUT_4": yaml_conf["dut_module"]["dut_4"]["mode"],
        "threshold_1": yaml_conf["trigger_inputs"]["threshold"]["threshold_1"],
        "threshold_2": yaml_conf["trigger_inputs"]["threshold"]["threshold_2"],
        "threshold_3": yaml_conf["trigger_inputs"]["threshold"]["threshold_3"],
        "threshold_4": yaml_conf["trigger_inputs"]["threshold"]["threshold_4"],
        "threshold_5": yaml_conf["trigger_inputs"]["threshold"]["threshold_5"],
        "threshold_6": yaml_conf["trigger_inputs"]["threshold"]["threshold_6"],
        "trigger_inputs_logic": yaml_conf["trigger_inputs"]["trigger_inputs_logic"],
        "trigger_signal_shape_stretch": yaml_conf["trigger_inputs"][
            "trigger_signal_shape"
        ]["stretch"],
        "trigger_signal_shape_delay": yaml_conf["trigger_inputs"][
            "trigger_signal_shape"
        ]["delay"],
        "trigger_polarity": yaml_conf["trigger_inputs"]["trigger_polarity"],
        "enable_clock_lemo_output": yaml_conf["enable_clock_lemo_output"],
        "pmt_control_1": yaml_conf["pmt_control"]["pmt_1"],
        "pmt_control_2": yaml_conf["pmt_control"]["pmt_2"],
        "pmt_control_3": yaml_conf["pmt_control"]["pmt_3"],
        "pmt_control_4": yaml_conf["pmt_control"]["pmt_4"],
        "save_data": yaml_conf["save_data"],
        "output_data_path": yaml_conf["output_data_path"],
        "zmq_connection": yaml_conf["zmq_connection"],
        "max_trigger_number": yaml_conf["max_trigger_number"],
        "timeout": yaml_conf["timeout"],
    }
    return conf


def toml_parser(conf_file_path: str, constellation: bool = False) -> dict:
    """Parses a toml configuration file to a configuration dictionary.

    Args:
        conf_file_path (str | conf): Path to toml configuration file, or constellation configuration
        constellation (bool, optional): Disables some parser features that are not needed when using constellation. Defaults to False.

    Returns:
        conf: configuration dictionary
    """
    if not constellation:
        with open(conf_file_path, "rb") as file:
            toml_conf = tomllib.load(file)
            keys = toml_conf.keys()
    else:
        toml_conf = conf_file_path
        keys = conf_file_path.get_keys()

    # Throw an error when the length of the list of required parameters does not match.
    if len(toml_conf["dut_interfaces"]) != 4:
        raise ValueError(
            "Set operating mode of all 4 DUT interfaces. The length of dut_interfaces has to be 4!"
        )
    if len(toml_conf["trigger_threshold"]) != 6:
        raise ValueError(
            "Set threshold of all 6 trigger inputs. The length of trigger_threshold has to be 6!"
        )
    if len(toml_conf["pmt_power"]) != 4:
        raise ValueError(
            "Set PMT power of all 4 outputs. The length of pmt_power has to be 4!"
        )
    if len(toml_conf["trigger_signal_stretch"]) != 6:
        raise ValueError(
            "Set the signal stretch of all 6 trigger inputs. The length of trigger_signal_stretch has to be 6!"
        )
    if len(toml_conf["trigger_signal_delay"]) != 6:
        raise ValueError(
            "Set the signal delay of all 6 trigger inputs. The length of trigger_signal_delay has to be 6!"
        )

    conf = {}

    # default configuration parameters
    if "internal_trigger_rate" not in keys:
        conf["internal_trigger_rate"] = 0
    else:
        conf["internal_trigger_rate"] = toml_conf["internal_trigger_rate"]
    if "trigger_polarity" not in keys:
        conf["trigger_polarity"] = "falling"
    else:
        conf["trigger_polarity"] = toml_conf["trigger_polarity"]
    if "enable_clock_lemo_output" not in keys:
        conf["enable_clock_lemo_output"] = False
    else:
        conf["enable_clock_lemo_output"] = (
            False
            if toml_conf["enable_clock_lemo_output"] in ["False", "None"]
            else True
        )

    # required configuration parameters
    conf["DUT_1"] = (
        False
        if toml_conf["dut_interfaces"][0] in ["False", "None", "off"]
        else toml_conf["dut_interfaces"][0]
    )
    conf["DUT_2"] = (
        False
        if toml_conf["dut_interfaces"][1] in ["False", "None", "off"]
        else toml_conf["dut_interfaces"][1]
    )
    conf["DUT_3"] = (
        False
        if toml_conf["dut_interfaces"][2] in ["False", "None", "off"]
        else toml_conf["dut_interfaces"][2]
    )
    conf["DUT_4"] = (
        False
        if toml_conf["dut_interfaces"][3] in ["False", "None", "off"]
        else toml_conf["dut_interfaces"][3]
    )
    conf["threshold_1"] = toml_conf["trigger_threshold"][0]
    conf["threshold_2"] = toml_conf["trigger_threshold"][1]
    conf["threshold_3"] = toml_conf["trigger_threshold"][2]
    conf["threshold_4"] = toml_conf["trigger_threshold"][3]
    conf["threshold_5"] = toml_conf["trigger_threshold"][4]
    conf["threshold_6"] = toml_conf["trigger_threshold"][5]
    conf["trigger_inputs_logic"] = toml_conf["trigger_inputs_logic"]
    conf["trigger_signal_shape_stretch"] = toml_conf["trigger_signal_stretch"]
    conf["trigger_signal_shape_delay"] = toml_conf["trigger_signal_delay"]
    conf["pmt_control_1"] = toml_conf["pmt_power"][0]
    conf["pmt_control_2"] = toml_conf["pmt_power"][1]
    conf["pmt_control_3"] = toml_conf["pmt_power"][2]
    conf["pmt_control_4"] = toml_conf["pmt_power"][3]

    # Specifically disable some configuration parameters for use with constellation.
    if not constellation:
        if "output_data_path" not in keys:
            conf["output_data_path"] = None
        else:
            conf["output_data_path"] = (
                None
                if toml_conf["output_data_path"] in ["None", ""]
                else toml_conf["output_data_path"]
            )
        conf["zmq_connection"] = (
            False
            if toml_conf["zmq_connection"] in ["False", "None", "off"]
            else toml_conf["zmq_connection"]
        )
        conf["max_trigger_number"] = (
            None
            if toml_conf["max_trigger_number"] in ["False", "None", "off"]
            else toml_conf["max_trigger_number"]
        )
        conf["timeout"] = (
            None
            if toml_conf["timeout"] in ["False", "None", "off"]
            else toml_conf["timeout"]
        )
        conf["save_data"] = (
            False if toml_conf["save_data"] in ["False", "None", "off"] else True
        )

    else:
        conf["output_data_path"] = None
        conf["zmq_connection"] = False
        conf["max_trigger_number"] = None
        conf["timeout"] = None
        conf["save_data"] = False

    return conf
