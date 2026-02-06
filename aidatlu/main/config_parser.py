import yaml
import tomllib


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
        "DUT_1_ignore_busy": 0,
        "DUT_2_ignore_busy": 0,
        "DUT_3_ignore_busy": 0,
        "DUT_4_ignore_busy": 0,
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
    conf["DUT_1_ignore_busy"] = 0
    conf["DUT_2_ignore_busy"] = 0
    conf["DUT_3_ignore_busy"] = 0
    conf["DUT_4_ignore_busy"] = 0

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

        # Loads custom clock configuration file if provided
        try:
            conf["clock_config"] = toml_conf["clock_config"]
        except:
            conf["clock_config"] = None

    return conf
