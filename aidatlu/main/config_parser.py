
import yaml
import logging
import logger

class TLUConfigure(object):
    def __init__(self, TLU, io_control, config_path) -> None:
        self.log = logger.setup_main_logger(__class__.__name__, logging.DEBUG)

        self.tlu = TLU
        self.io_control = io_control

        config_path = config_path
        with open(config_path, 'r') as file:
            self.conf = yaml.full_load(file)

    def configure(self) -> None:
        """Loads configuration file and configures the TLU accordingly.
            """
        self.conf_dut()
        self.conf_trigger_inputs()
        self.conf_trigger_logic()
        self.tlu.io_controller.clock_lemo_output(self.conf['clock_lemo']['enable_clock_lemo_output'])
        [self.tlu.dac_controller.set_voltage(i+1, self.conf['pmt_control']['pmt_%s'%(i+1)]) for i in range(len(self.conf['pmt_control']))]
        self.tlu.set_enable_record_data(1)
        self.log.success("TLU configured")
   
    def get_data_handling(self) -> tuple:
        """ Information about data handling.

            Returns:
                tuple: two bools, save and interpret data.
        """
        return self.conf['save_raw_data'], self.conf['interpret_data']

    def get_zmq_connection(self) -> str:
        """ Information about the zmq Address

        Returns:
            str: ZMQ Address
        """
        return self.conf['zmq_connection']

    def conf_dut(self) -> None:
        """ Parse the configuration for the DUT interface to the AIDATLU. 
        """
        dut = [0, 0, 0, 0]
        dut_mode = [0, 0, 0, 0]
        for i in range(4):
                if self.tlu.config_parser.conf['dut_module']['dut_%s'%(i+1)]['mode'] == 'eudet':
                        self.tlu.io_controller.switch_led(i+1, 'g')
                        dut[i] = 2**i
                if self.tlu.config_parser.conf['dut_module']['dut_%s'%(i+1)]['mode'] == 'aidatrig':
                        self.tlu.io_controller.switch_led(i+1, 'w')
                        dut[i] = 2**i
                        dut_mode[i] = 2**(2*i)    
                if self.tlu.config_parser.conf['dut_module']['dut_%s'%(i+1)]['mode'] == 'aida':
                        self.tlu.io_controller.switch_led(i+1, 'b')
                        dut[i] = 2**i
                        dut_mode[i] = 3*(2)**(2*i)
                self.tlu.io_controller.configure_hdmi(i+1, '0111')
                #The clock output needs to be enabled. If not the trigger number is not sent out in EUDET Mode with trigger number.
                self.tlu.io_controller.clock_hdmi_output(i+1, 'chip')

        #This sets the right bits to the set dut mask registers according to the configuration parameter.
        self.tlu.dut_logic.set_dut_mask(dut[0] | dut[1]  | dut[2]  | dut[3]) 
        self.tlu.dut_logic.set_dut_mask_mode(dut_mode[0]  | dut_mode[1]  | dut_mode[2]  | dut_mode[3] )

        #Special configs
        self.tlu.dut_logic.set_dut_mask_mode_modifier(0)
        self.tlu.dut_logic.set_dut_ignore_busy(0) 
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

        [self.tlu.dac_controller.set_threshold(i+1, self.conf['trigger_inputs']['threshold']['threshold_%s' %(i+1)]) for i in range(6)]

        trigger_word = 0
        for i in (self.conf['trigger_inputs']['trigger_inputs_logic']):
             logic_array = []
             for index,j in enumerate(self.conf['trigger_inputs']['trigger_inputs_logic'][i]):
                logic_array.append(self.conf['trigger_inputs']['trigger_inputs_logic'][i][j])
                if self.conf['trigger_inputs']['trigger_inputs_logic'][i][j] == 1:
                      self.io_control.switch_led(index+6, 'g')
                if self.conf['trigger_inputs']['trigger_inputs_logic'][i][j] == 0:
                      self.io_control.switch_led(index+6, 'r')
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