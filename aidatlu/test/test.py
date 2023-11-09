import sys

sys.path.insert(1, "..")
sys.path.insert(1, "../hardware")

from main.tlu import AidaTLU
from hardware.i2c import I2CCore
from hardware.utils import _set_bit
from hardware.ioexpander_controller import IOControl
from hardware.dac_controller import DacControl
from hardware.clock_controller import ClockControl
from hardware.dut_controller import DUTLogic
from hardware.trigger_controller import TriggerLogic

import time
import numpy as np
import uhal
import logger
import logging


class Test_IOCControl(object):
    def __init__(self, i2c: I2CCore) -> None:
        self.i2c = i2c
        self.ioexpander = IOControl(i2c)

    def test_ioexpander(self):
        log.info("Testing IO Expander")
        self.test_clock_lemo_output()
        self.test_configure_hdmi()
        self.test_ioexpander_led()
        log.success("IO Expander tested")

    def test_ioexpander_led(self) -> None:
        self.ioexpander.all_off()
        self.ioexpander.test_leds(single=True)
        self.ioexpander.all_off()
        time.sleep(1)
        self.ioexpander.all_on()
        time.sleep(2)
        self.ioexpander.all_off()

    def test_configure_hdmi(self) -> None:
        for i in range(4):
            self.ioexpander.configure_hdmi(i + 1, "1111")
            self.ioexpander.clock_hdmi_output(i + 1, "chip")
            time.sleep(1)
            self.ioexpander.configure_hdmi(i + 1, "0000")
            self.ioexpander.clock_hdmi_output(i + 1, "off")

    def test_clock_lemo_output(self):
        self.ioexpander.clock_lemo_output(True)
        time.sleep(1)
        self.ioexpander.clock_lemo_output(False)


class Test_DacControl(object):
    def __init__(self, i2c: I2CCore) -> None:
        self.i2c = i2c
        self.dac_true = DacControl(i2c, True)
        self.dac_false = DacControl(i2c, False)

    def test_dac(self):
        log.info("Testing DAC")
        self.test_set_threshold()
        self.test_set_voltage()
        log.success("DAC tested")

    def test_set_threshold(self) -> None:
        for i in range(7):
            for volts in np.arange(-1.3, 1.3, 0.2):
                self.dac_true.set_threshold(i + 1, volts)
                time.sleep(0.2)
            self.dac_true.set_threshold(i + 1, 0)
        time.sleep(0.5)
        for i in range(7):
            for volts in np.arange(-1.3, 1.3, 0.2):
                self.dac_false.set_threshold(i + 1, volts)
                time.sleep(0.2)
            self.dac_false.set_threshold(i + 1, 0)

    def test_set_voltage(self) -> None:
        for i in range(4):
            for volts in np.arange(0, 1, 0.1):
                self.dac_true.set_voltage(i + 1, volts)
                time.sleep(0.2)
        self.dac_true.set_all_voltage(0)


class Test_ClockControl(object):
    def __init__(self, i2c: I2CCore) -> None:
        self.i2c = i2c
        self.ioexpander = IOControl(i2c)
        self.clock = ClockControl(i2c, self.ioexpander)

    def test_clock(self):
        log.info("Testing Clock Chip")

        clock.test_device_info()
        clock.test_write_clock_register()
        log.success("Clock Chip tested")

    def test_device_info(self) -> None:
        self.clock.log.info("Device Version: %i" % self.clock.get_device_version())
        self.clock.log.info("Design ID: %s" % self.clock.check_design_id())

    def test_write_clock_register(self):
        self.clock.write_clock_conf("misc/aida_tlu_clk_config.txt")


class Test_DUTLogic(object):
    def __init__(self, i2c: I2CCore) -> None:
        self.i2c = i2c
        self.dut = DUTLogic(i2c)

    def test_dut(self):
        log.info("Testing DUT Logic")
        time.sleep(1)
        self.test_set_dut_ignore_busy()
        self.test_set_dut_mask()
        self.test_set_dut_mask_mode()
        self.test_set_dut_mask_modifier()
        log.success("DUT Logic tested")

    def test_set_dut_mask(self) -> None:
        self.dut.set_dut_mask("1111")
        time.sleep(1)
        self.dut.set_dut_mask("0000")

    def test_set_dut_mask_mode(self):
        self.dut.set_dut_mask_mode("00000000")
        time.sleep(1)
        self.dut.set_dut_mask_mode("11111111")
        time.sleep(1)
        self.dut.set_dut_mask_mode("01010101")

    def test_set_dut_mask_modifier(self) -> None:
        # TODO What input here?
        self.dut.set_dut_mask_mode_modifier(1)
        time.sleep(1)
        self.dut.set_dut_mask_mode_modifier(0)

    def test_set_dut_ignore_busy(self):
        self.dut.set_dut_ignore_busy("1111")
        time.sleep(1)
        self.dut.set_dut_ignore_busy("0000")

    def test_set_dut_ignore_busy(self) -> None:
        self.dut.set_dut_ignore_shutter(0)


class Test_TriggerLogic(object):
    def __init__(self, i2c: I2CCore) -> None:
        self.i2c = i2c
        self.trigger = TriggerLogic(i2c)

    def test_trigger(self):
        log.info("Testing Trigger Logic")
        self.test_set_internal_trigger_frequency()
        self.test_set_pulse_delay_pack()
        self.test_set_pulse_stretch_pack()
        self.test_set_trigger_mask()
        self.test_set_trigger_polarity()
        self.test_set_trigger_veto()
        log.success("Trigger Logic tested")

    def test_set_internal_trigger_frequency(self) -> None:
        self.trigger.set_internal_trigger_frequency(0)

    def test_set_trigger_veto(self) -> None:
        self.trigger.set_trigger_veto(True)
        time.sleep(1)
        self.trigger.set_trigger_veto(False)

    def test_set_trigger_polarity(self):
        self.trigger.set_trigger_polarity(1)
        time.sleep(1)
        self.trigger.set_trigger_polarity(0)

    def test_set_trigger_mask(self):
        self.trigger.set_trigger_mask(0b0, 0b1)
        time.sleep(1)
        self.trigger.set_trigger_mask(0b0, 0b0)

    def test_set_pulse_stretch_pack(self) -> None:
        self.trigger.set_pulse_stretch_pack([1, 1, 1, 1, 1, 1])
        time.sleep(1)
        self.trigger.set_pulse_stretch_pack([2, 2, 2, 2, 2, 2])

    def test_set_pulse_delay_pack(self) -> None:
        self.trigger.set_pulse_delay_pack([0, 0, 0, 0, 0, 0])
        time.sleep(1)
        self.trigger.set_pulse_delay_pack([1, 1, 1, 1, 1, 1])


if __name__ == "__main__":
    uhal.setLogLevelTo(uhal.LogLevel.NOTICE)
    manager = uhal.ConnectionManager("file://../misc/aida_tlu_connection.xml")
    hw = uhal.HwInterface(manager.getDevice("aida_tlu.controlhub"))

    log = logger.setup_main_logger("Test AidaTLU", logging.DEBUG)

    log.info("Init I2C Core")
    i2c = I2CCore(hw)
    i2c.init()

    expander = Test_IOCControl(i2c)
    expander.test_ioexpander()

    dac = Test_DacControl(i2c)
    dac.test_dac()

    clock = Test_ClockControl(i2c)
    clock.test_clock()

    dut = Test_DUTLogic(i2c)
    dut.test_dut()

    trigger = Test_TriggerLogic(i2c)
    trigger.test_trigger()

    log.info("Testing TLU")
    tlu = AidaTLU(hw)
    log.info("TLU Device ID: %s" % tlu.get_device_id())
    log.info("TLU FW Version: %s" % tlu.get_fw_version())
    log.success("TLU ID found")
    tlu.test_configuration()
    tlu.default_configuration()
    log.success("TLU Test Configured")
