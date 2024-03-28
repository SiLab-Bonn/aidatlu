from online_monitor.receiver.receiver import Receiver

import pyqtgraph as pg
from pyqtgraph.dockarea import DockArea, Dock
from PyQt5 import QtWidgets
import pyqtgraph as pg
from pyqtgraph.dockarea import DockArea, Dock
from online_monitor.utils import utils


class AIDATLUReciever(Receiver):
    def setup_receiver(self):
        # self.set_bidirectional_communication()  # We want to change converter settings
        self.hitrate_data = []
        self.runtime = []
        self.particlerate_data = []

    def setup_widgets(self, parent, name):
        dock_area = DockArea()
        parent.addTab(dock_area, name)
        # Docks
        dock_rate = Dock("Particle rate (Trigger rate)", size=(400, 400))
        dock_status = Dock("Status", size=(800, 40))
        dock_area.addDock(dock_rate, "above")
        dock_area.addDock(dock_status, "top")

        # Status dock on top
        cw = QtWidgets.QWidget()
        cw.setStyleSheet("QWidget {background-color:white}")
        layout = QtWidgets.QGridLayout()
        cw.setLayout(layout)

        self.hit_rate_label = QtWidgets.QLabel("Trigger Frequency\n0 Hz")
        self.timestamp_label = QtWidgets.QLabel("Run Time\n0 s")
        self.event_numb_label = QtWidgets.QLabel("Event Number\n0")
        self.total_trig_numb = QtWidgets.QLabel("Total Trigger Number\n0")
        self.particle_rate_label = QtWidgets.QLabel("Particle Rate\n0")
        self.reset_button = QtWidgets.QPushButton("Reset")
        layout.addWidget(self.timestamp_label, 0, 0, 0, 1)
        layout.addWidget(self.event_numb_label, 0, 1, 0, 1)
        layout.addWidget(self.hit_rate_label, 0, 6, 0, 1)
        layout.addWidget(self.particle_rate_label, 0, 3, 0, 1)
        layout.addWidget(self.total_trig_numb, 0, 2, 0, 1)
        layout.addWidget(self.reset_button, 0, 7, 0, 1)
        dock_status.addWidget(cw)

        self.reset_button.clicked.connect(lambda: self._reset())

        # # particle rate dock
        trigger_rate_graphics = pg.GraphicsLayoutWidget()
        trigger_rate_graphics.show()
        plot_trigger_rate = pg.PlotItem(
            labels={"left": "Rate / Hz", "bottom": "Run Time / s"}
        )
        self.trigger_rate_acc_curve = pg.PlotCurveItem(pen="#B00B13")
        self.particle_rate_acc_curve = pg.PlotCurveItem(pen="#0000FF")

        # # add legend
        legend_acc = pg.LegendItem(offset=(80, 10))
        legend_acc.setParentItem(plot_trigger_rate)
        legend_acc.addItem(self.trigger_rate_acc_curve, "Accepted Trigger Rate")
        legend_real = pg.LegendItem(offset=(80, 50))
        legend_real.setParentItem(plot_trigger_rate)
        legend_real.addItem(self.particle_rate_acc_curve, "Particle Rate")

        # # add items to plots and customize plots viewboxes
        plot_trigger_rate.addItem(self.trigger_rate_acc_curve)
        plot_trigger_rate.addItem(self.particle_rate_acc_curve)

        plot_trigger_rate.vb.setBackgroundColor("#E6E5F4")
        # plot_trigger_rate.setXRange(0, 200)
        plot_trigger_rate.getAxis("left").setZValue(0)
        plot_trigger_rate.getAxis("left").setGrid(155)

        # # add plots to graphicslayout and layout to dock
        trigger_rate_graphics.addItem(
            plot_trigger_rate, row=0, col=1, rowspan=1, colspan=2
        )
        dock_rate.addWidget(trigger_rate_graphics)

        # # add dict of all used plotcurveitems for individual handling of each plot
        self.plots = {
            "trigger_rate_acc": self.trigger_rate_acc_curve,
            "particle_rate_acc": self.particle_rate_acc_curve,
        }
        self.plot_delay = 0

    def deserialize_data(self, data):
        return utils.simple_dec(data)[1]

    def refresh_data(self):
        if len(self.hitrate_data) > 0:
            self.trigger_rate_acc_curve.setData(x=self.runtime, y=self.hitrate_data)
        if len(self.particlerate_data) > 0:
            self.particle_rate_acc_curve.setData(
                x=self.runtime, y=self.particlerate_data
            )

    def handle_data(self, data):
        self.hitrate_data.append(data["Trigger freq"])
        self.particlerate_data.append(data["Particle Rate"])
        self.runtime.append(data["Run Time"])
        self.timestamp_label.setText("Run Time\n%0.2f s" % data["Run Time"])
        self.event_numb_label.setText("Event Number\n%i" % data["Event Number"])
        self.total_trig_numb.setText(
            "Total Trigger Number\n%i" % data["Total trigger numb"]
        )
        self.particle_rate_label.setText(
            "Particle Rate\n%0.2f Hz" % data["Particle Rate"]
        )
        self.hit_rate_label.setText(
            "Trigger Frequency\n%0.2f Hz" % data["Trigger freq"]
        )

    def _reset(self):
        self.hitrate_data = []
        self.runtime = []
        self.particlerate_data = []
