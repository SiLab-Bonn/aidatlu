
import yaml
import logging
import logger

class TLUConfigure(object):
    def __init__(self, TLU) -> None:
        self.log = logger.setup_main_logger(__class__.__name__, logging.DEBUG)

        self.tlu = TLU

        config_path = 'conf.yaml'
        with open(config_path, 'r') as file:
            self.conf = yaml.full_load(file)

        self.conf_dut()
        self.conf_trigger_inputs()
        self.conf_trigger_logic()
        self.tlu.io_controller.clock_lemo_output(self.conf['clock_lemo']['enable_clock_lemo_output'])

        self.log.success("TLU configured")

    def conf_dut(self) -> None:
        dut_1 = 0
        dut_2 = 0
        dut_3 = 0
        dut_4 = 0

        dut_mode_1 = 0
        dut_mode_2 = 0
        dut_mode_3 = 0
        dut_mode_4 = 0
# EUDET mode
        if self.conf['dut_module']['dut_1']['mode'] == 'eudet':
                self.tlu.log.info("Configure DUT 1 in EUDET mode")
                self.tlu.io_controller.configure_hdmi(1, '0111')
                self.tlu.io_controller.clock_hdmi_output(1, 'off')
                dut_1 = 0b0001
        if self.conf['dut_module']['dut_2']['mode'] == 'eudet':
                self.tlu.log.info("Configure DUT 2 in EUDET mode")
                self.tlu.io_controller.configure_hdmi(2, '0111')
                self.tlu.io_controller.clock_hdmi_output(2, 'off')
                dut_2 = 0b0010
        if self.conf['dut_module']['dut_3']['mode'] == 'eudet':
                self.tlu.log.info("Configure DUT 3 in EUDET mode")
                self.tlu.io_controller.configure_hdmi(3, '0111')
                self.tlu.io_controller.clock_hdmi_output(3, 'off')
                dut_1 = 0b0100
        if self.conf['dut_module']['dut_4']['mode'] == 'eudet':
                self.tlu.log.info("Configure DUT 4 in EUDET mode")
                self.tlu.io_controller.configure_hdmi(4, '0111')
                self.tlu.io_controller.clock_hdmi_output(4, 'off')
                dut_1 = 0b1000
# AIDA mode
        if self.conf['dut_module']['dut_1']['mode'] == 'aida':
                self.tlu.log.info("Configure DUT 1 in AIDA mode")
                self.tlu.io_controller.configure_hdmi(1, '0111') #TODO what pin configuration is needed for AIDA mode??
                self.tlu.io_controller.clock_hdmi_output(1, 'off')
                dut_1 = 0b0001
                dut_mode_1 = 0b00000011
        if self.conf['dut_module']['dut_2']['mode'] == 'aida':
                self.tlu.log.info("Configure DUT 2 in AIDA mode")
                self.tlu.io_controller.configure_hdmi(2, '0111')
                self.tlu.io_controller.clock_hdmi_output(2, 'off')
                dut_2 = 0b0010
                dut_mode_1 = 0b00001100
        if self.conf['dut_module']['dut_3']['mode'] == 'aida':
                self.tlu.log.info("Configure DUT 3 in AIDA mode")
                self.tlu.io_controller.configure_hdmi(3, '0111')
                self.tlu.io_controller.clock_hdmi_output(3, 'off')
                dut_1 = 0b0100
                dut_mode_1 = 0b00110000
        if self.conf['dut_module']['dut_4']['mode'] == 'aida':
                self.tlu.log.info("Configure DUT 4 in AIDA mode")
                self.tlu.io_controller.configure_hdmi(4, '0111')
                self.tlu.io_controller.clock_hdmi_output(4, 'off')
                dut_1 = 0b1000
                dut_mode_1 = 0b11000000

        self.tlu.dut_logic.set_dut_mask(dut_1 + dut_2 + dut_3 + dut_4)
        self.tlu.dut_logic.set_dut_mask_mode(dut_mode_1 + dut_mode_2 + dut_mode_3 + dut_mode_4)
        #special configs
        self.tlu.dut_logic.set_dut_mask_mode_modifier(0) #TODO Does this have to change for AIDA mode??
        self.tlu.dut_logic.set_dut_ignore_busy(0)
        self.tlu.dut_logic.set_dut_ignore_shutter(0x1)

    def conf_trigger_logic(self) -> None:
        

        self.tlu.trigger_logic.set_trigger_polarity(self.conf['trigger_inputs']['trigger_polarity']['polarity'])

        test_stretch = [1,1,1,1,1,1]
        test_delay = [0,0,0,0,0,0] 

        self.tlu.trigger_logic.set_pulse_stretch_pack(test_stretch)
        self.tlu.trigger_logic.set_pulse_delay_pack(test_delay)


    def conf_trigger_inputs(self)-> None:
        self.tlu.trigger_logic.set_trigger_mask(mask_high=self.conf['trigger_inputs']['trigger_inputs_logic']['mask_high'], mask_low=self.conf['trigger_inputs']['trigger_inputs_logic']['mask_low'],)

        self.tlu.voltage_controller.set_threshold(1, self.conf['trigger_inputs']['threshold']['threshold_1'])
        self.tlu.voltage_controller.set_threshold(2, self.conf['trigger_inputs']['threshold']['threshold_2'])
        self.tlu.voltage_controller.set_threshold(3, self.conf['trigger_inputs']['threshold']['threshold_3'])
        self.tlu.voltage_controller.set_threshold(4, self.conf['trigger_inputs']['threshold']['threshold_4'])
        self.tlu.voltage_controller.set_threshold(5, self.conf['trigger_inputs']['threshold']['threshold_5'])
        self.tlu.voltage_controller.set_threshold(6, self.conf['trigger_inputs']['threshold']['threshold_6'])