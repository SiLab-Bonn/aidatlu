import yaml


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
        "DUT_1": yaml_conf["dut_interfaces"]["dut_1"]["mode"],
        "DUT_2": yaml_conf["dut_interfaces"]["dut_2"]["mode"],
        "DUT_3": yaml_conf["dut_interfaces"]["dut_3"]["mode"],
        "DUT_4": yaml_conf["dut_interfaces"]["dut_4"]["mode"],
        "DUT_1_ignore_busy": 0,
        "DUT_2_ignore_busy": 0,
        "DUT_3_ignore_busy": 0,
        "DUT_4_ignore_busy": 0,
        "threshold_1": yaml_conf["trigger_inputs"]["input_1"]["threshold"],
        "threshold_2": yaml_conf["trigger_inputs"]["input_2"]["threshold"],
        "threshold_3": yaml_conf["trigger_inputs"]["input_3"]["threshold"],
        "threshold_4": yaml_conf["trigger_inputs"]["input_4"]["threshold"],
        "threshold_5": yaml_conf["trigger_inputs"]["input_5"]["threshold"],
        "threshold_6": yaml_conf["trigger_inputs"]["input_6"]["threshold"],
        "trigger_inputs_logic": yaml_conf["trigger_inputs"]["input_logic"],
        "stretch_1": yaml_conf["trigger_inputs"]["input_1"]["stretch"],
        "stretch_2": yaml_conf["trigger_inputs"]["input_2"]["stretch"],
        "stretch_3": yaml_conf["trigger_inputs"]["input_3"]["stretch"],
        "stretch_4": yaml_conf["trigger_inputs"]["input_4"]["stretch"],
        "stretch_5": yaml_conf["trigger_inputs"]["input_5"]["stretch"],
        "stretch_6": yaml_conf["trigger_inputs"]["input_6"]["stretch"],
        "delay_1": yaml_conf["trigger_inputs"]["input_1"]["delay"],
        "delay_2": yaml_conf["trigger_inputs"]["input_2"]["delay"],
        "delay_3": yaml_conf["trigger_inputs"]["input_3"]["delay"],
        "delay_4": yaml_conf["trigger_inputs"]["input_4"]["delay"],
        "delay_5": yaml_conf["trigger_inputs"]["input_5"]["delay"],
        "delay_6": yaml_conf["trigger_inputs"]["input_6"]["delay"],
        "trigger_polarity": [yaml_conf["trigger_inputs"]["input_%s" % (i + 1)]["polarity"] for i in range(6)],
        "enable_clock_lemo_output": yaml_conf["enable_clock_lemo_output"],
        "pmt_control_1": yaml_conf["pmt_power"]["control_voltage_1"],
        "pmt_control_2": yaml_conf["pmt_power"]["control_voltage_2"],
        "pmt_control_3": yaml_conf["pmt_power"]["control_voltage_3"],
        "pmt_control_4": yaml_conf["pmt_power"]["control_voltage_4"],
        "save_data": yaml_conf["save_data"],
        "output_data_path": yaml_conf["output_data_path"],
        "zmq_connection": yaml_conf["zmq_connection"],
        "max_trigger_number": yaml_conf["max_trigger_number"],
        "timeout": yaml_conf["timeout"],
        "clock_config": yaml_conf["clock_config"],
    }

    for i in range(4):
        if "ignore_busy" in yaml_conf["dut_interfaces"]["dut_%s" % (i + 1)]:
            conf["DUT_%s_ignore_busy" % (i + 1)] = yaml_conf["dut_interfaces"][
                "dut_%s" % (i + 1)
            ]["ignore_busy"]

    return conf
