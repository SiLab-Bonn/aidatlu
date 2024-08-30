from aidatlu.main.tlu import AidaTLU
from aidatlu.hardware.i2c import I2CCore
from aidatlu.hardware.ioexpander_controller import IOControl
from aidatlu.hardware.dac_controller import DacControl
from aidatlu.hardware.clock_controller import ClockControl
from aidatlu.hardware.dut_controller import DUTLogic
from aidatlu.hardware.trigger_controller import TriggerLogic
from aidatlu.main.config_parser import TLUConfigure

import uhal
import time
import numpy as np


class Test_IOCControl:
    uhal.setLogLevelTo(uhal.LogLevel.NOTICE)
    manager = uhal.ConnectionManager("file://../misc/aida_tlu_connection.xml")
    hw = uhal.HwInterface(manager.getDevice("aida_tlu.controlhub"))

    i2c = I2CCore(hw)
    i2c.init()
    ioexpander = IOControl(i2c)

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


class Test_DacControl:
    uhal.setLogLevelTo(uhal.LogLevel.NOTICE)
    manager = uhal.ConnectionManager("file://../misc/aida_tlu_connection.xml")
    hw = uhal.HwInterface(manager.getDevice("aida_tlu.controlhub"))

    i2c = I2CCore(hw)
    i2c.init()
    dac_true = DacControl(i2c, True)
    dac_false = DacControl(i2c, False)

    def test_set_threshold(self) -> None:
        for i in range(7):
            for volts in np.arange(-1.3, 1.3, 1.3):
                self.dac_true.set_threshold(i + 1, volts)
                time.sleep(0.2)
            self.dac_true.set_threshold(i + 1, 0)
        time.sleep(0.5)
        for i in range(7):
            for volts in np.arange(-1.3, 1.3, 1.3):
                self.dac_false.set_threshold(i + 1, volts)
                time.sleep(0.2)
            self.dac_false.set_threshold(i + 1, 0)

    def test_set_voltage(self) -> None:
        for i in range(4):
            for volts in np.arange(0, 1, 0.5):
                self.dac_true.set_voltage(i + 1, volts)
                time.sleep(0.2)
        self.dac_true.set_all_voltage(0)


class Test_ClockControl:
    uhal.setLogLevelTo(uhal.LogLevel.NOTICE)
    manager = uhal.ConnectionManager("file://../misc/aida_tlu_connection.xml")
    hw = uhal.HwInterface(manager.getDevice("aida_tlu.controlhub"))
    i2c = I2CCore(hw)
    i2c.init()
    ioexpander = IOControl(i2c)
    clock = ClockControl(i2c, ioexpander)

    def test_device_info(self) -> None:
        self.clock.log.info("Device Version: %i" % self.clock.get_device_version())
        self.clock.log.info("Design ID: %s" % self.clock.check_design_id())

    def test_write_clock_register(self):
        self.clock.write_clock_conf("../misc/aida_tlu_clk_config.txt")


class Test_DUTLogic:
    uhal.setLogLevelTo(uhal.LogLevel.NOTICE)
    manager = uhal.ConnectionManager("file://../misc/aida_tlu_connection.xml")
    hw = uhal.HwInterface(manager.getDevice("aida_tlu.controlhub"))

    i2c = I2CCore(hw)
    i2c.init()
    dut = DUTLogic(i2c)

    def test_set_dut_mask(self) -> None:
        time.sleep(1)
        self.dut.set_dut_mask("1010")
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


class Test_TriggerLogic:
    uhal.setLogLevelTo(uhal.LogLevel.NOTICE)
    manager = uhal.ConnectionManager("file://../misc/aida_tlu_connection.xml")
    hw = uhal.HwInterface(manager.getDevice("aida_tlu.controlhub"))

    i2c = I2CCore(hw)
    trigger = TriggerLogic(i2c)

    def test_set_internal_trigger_frequency(self) -> None:
        self.trigger.set_internal_trigger_frequency(0)
        self.trigger.set_internal_trigger_frequency(10000)
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


def test_run():
    uhal.setLogLevelTo(uhal.LogLevel.NOTICE)
    manager = uhal.ConnectionManager("file://.././misc/aida_tlu_connection.xml")
    hw = uhal.HwInterface(manager.getDevice("aida_tlu.controlhub"))

    config_path = "tlu_test_configuration.yaml"
    clock_path = "../misc/aida_tlu_clk_config.txt"
    tlu = AidaTLU(hw, config_path, clock_path)

    tlu.configure()
    tlu.run()


if __name__ == "__main__":
    test_io = Test_IOCControl()
    test_io.test_clock_lemo_output()
    test_io.test_configure_hdmi()
    test_io.test_ioexpander_led()

    test_dac = Test_DacControl()
    test_dac.test_set_threshold()
    test_dac.test_set_threshold()

    test_dut = Test_DUTLogic()
    test_dut.test_set_dut_ignore_busy()
    test_dut.test_set_dut_mask()
    test_dut.test_set_dut_mask_mode()
    test_dut.test_set_dut_mask_modifier()

    test_clock = Test_ClockControl()
    test_clock.test_device_info()
    test_clock.test_write_clock_register()

    test_trigger = Test_TriggerLogic()
    test_trigger.test_set_internal_trigger_frequency()
    test_trigger.test_set_pulse_delay_pack()
    test_trigger.test_set_pulse_stretch_pack()
    test_trigger.test_set_trigger_mask()
    test_trigger.test_set_trigger_polarity()
    test_trigger.test_set_trigger_veto()

    test_run = test_run()
