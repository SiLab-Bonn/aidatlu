
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


    def configure(self) -> None:
        self.conf_dut()
        self.conf_trigger_inputs()
        self.conf_trigger_logic()
        self.tlu.io_controller.clock_lemo_output(self.conf['clock_lemo']['enable_clock_lemo_output'])
        [self.tlu.voltage_controller.set_voltage(i+1, self.conf['pmt_control']['pmt_%s'%(i+1)]) for i in range(len(self.conf['pmt_control']))]
        self.log.success("TLU configured")
   

    def conf_dut(self) -> None:
        """ Parse the configuration for the DUT interface to the AIDATLU. 
            Each DUT interface can run in EUDET or AIDA mode. The function takes are of the required pin configurations.
        """
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
        #AIDA mode with trigger number
        if self.conf['dut_module']['dut_1']['mode'] == 'aidatrig':
                self.tlu.log.info("Configure DUT 1 in AIDA mode with trigger number")
                self.tlu.io_controller.configure_hdmi(1, '0111') #TODO what pin configuration is needed for AIDA mode??
                self.tlu.io_controller.clock_hdmi_output(1, 'off')
                dut_1 = 0b0001
                dut_mode_1 = 0b00000001
        if self.conf['dut_module']['dut_2']['mode'] == 'aidatrig':
                self.tlu.log.info("Configure DUT 2 in AIDA mode with trigger number")
                self.tlu.io_controller.configure_hdmi(2, '0111')
                self.tlu.io_controller.clock_hdmi_output(2, 'off')
                dut_2 = 0b0010
                dut_mode_1 = 0b00000100
        if self.conf['dut_module']['dut_3']['mode'] == 'aidatrig':
                self.tlu.log.info("Configure DUT 3 in AIDA mode with trigger number")
                self.tlu.io_controller.configure_hdmi(3, '0111')
                self.tlu.io_controller.clock_hdmi_output(3, 'off')
                dut_1 = 0b0100
                dut_mode_1 = 0b00010000
        if self.conf['dut_module']['dut_4']['mode'] == 'aidatrig':
                self.tlu.log.info("Configure DUT 4 in AIDA mode with trigger number")
                self.tlu.io_controller.configure_hdmi(4, '0111')
                self.tlu.io_controller.clock_hdmi_output(4, 'off')
                dut_1 = 0b1000
                dut_mode_1 = 0b01000000



        self.tlu.dut_logic.set_dut_mask(dut_1 | dut_2 | dut_3 | dut_4) 
        self.tlu.dut_logic.set_dut_mask_mode(dut_mode_1 | dut_mode_2 | dut_mode_3 | dut_mode_4)
        #special configs
        self.tlu.dut_logic.set_dut_mask_mode_modifier(0) #TODO Does this have to change for AIDA mode??
        self.tlu.dut_logic.set_dut_ignore_busy(0) #TODO this seems interesting check with the documentation
        self.tlu.dut_logic.set_dut_ignore_shutter(0x1)

    def conf_trigger_logic(self) -> None:
        """ Configures the trigger logic. So the trigger polarity and the trigger pulse length and stretch.
        """

        self.tlu.trigger_logic.set_trigger_polarity(self.conf['trigger_inputs']['trigger_polarity']['polarity'])

        self.tlu.trigger_logic.set_pulse_stretch_pack(self.conf['trigger_inputs']['trigger_signal_shape']['stretch'])
        self.tlu.trigger_logic.set_pulse_delay_pack(self.conf['trigger_inputs']['trigger_signal_shape']['delay'])
        self.tlu.trigger_logic.set_internal_trigger_frequency(self.conf['internal_trigger']['internal_trigger_rate'])

    def conf_trigger_inputs(self)-> None:
        """Configures the trigger inputs. Each input can have a different threshold.
           The two trigger words mask_low and mask_high are generated with the use of two support functions. 
        """

        [self.tlu.voltage_controller.set_threshold(i+1, self.conf['trigger_inputs']['threshold']['threshold_%s' %(i+1)]) for i in range(6)]

        trigger_word = 0
        for i in (self.conf['trigger_inputs']['trigger_inputs_logic']):
             logic_array = []
             for j in self.conf['trigger_inputs']['trigger_inputs_logic'][i]:
                logic_array.append(self.conf['trigger_inputs']['trigger_inputs_logic'][i][j])
             trigger_word += self._find_mask_word(logic_array)

        mask_low, mask_high = self._mask_words(trigger_word)

        self.log.info('mask high: %s, mask low: %s' %(hex(mask_high),hex(mask_low)))

        self.tlu.trigger_logic.set_trigger_mask(mask_high, mask_low)

    def _find_mask_word(self, logic_array: list) -> int:
        """This function creates all combination of trigger words and compares them to the one from the configuration file.
           When they match the word is returned.

        Args:
        logic_array (list): The combinations are compared to the logic array.

        Returns:
        int: Returns the long word variant of the trigger word.
        """
        long_word = 0x0
        for combination in range(64):
                #Transform a given integer in binary in reverse order to a list.
                pattern_list = [(combination >> element) & 0x1 for element in range(6)] 
                #Ignore DO NOT CARE input -1
                logic_array = [pattern_list[i] if logic_array[i] == -1 else logic_array[i] for i in range(len(logic_array))]
                valid = (logic_array == pattern_list)
                long_word = (valid << combination) | long_word
        return long_word


    def _mask_words(self, word: int) -> tuple:
        """ Transforms the long word variant of the trigger word to the mask_low mask_high variant.

        Args:
        word (int): Long word variant of the trigger word.

        Returns:
        tuple: mask_low and mask_high trigger words
        """
        mask_low = 0xFFFFFFFF & word
        mask_high = word >> 32
        return (mask_low, mask_high)