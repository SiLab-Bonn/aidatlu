from online_monitor.receiver.receiver import Receiver

import pyqtgraph as pg
from pyqtgraph.dockarea import DockArea, Dock
from PyQt5 import QtWidgets
import pyqtgraph as pg
from pyqtgraph.dockarea import DockArea, Dock

class AIDATLUReciever(Receiver):
        
        def setup_receiver(self):
            #self.set_bidirectional_communication()  # We want to change converter settings
            self.hitrate_data = []
            self.runtime = []

        def setup_widgets(self, parent, name):
            dock_area = DockArea()
            parent.addTab(dock_area, name)
            # Docks
            dock_rate = Dock("Particle rate (Trigger rate)", size=(400, 400))
            dock_status = Dock("Status", size=(800, 40))
            dock_area.addDock(dock_rate, 'above')
            dock_area.addDock(dock_status, 'top')

            # Status dock on top
            cw = QtWidgets.QWidget()
            cw.setStyleSheet("QWidget {background-color:white}")
            layout = QtWidgets.QGridLayout()
            cw.setLayout(layout)

            self.hit_rate_label = QtWidgets.QLabel("Trigger Frequency\n0 Hz")
            self.timestamp_label = QtWidgets.QLabel("Run Time\n0 s")
            self.event_numb_label = QtWidgets.QLabel("Event Number\n0")
            self.total_trig_numb = QtWidgets.QLabel("Total Trigger Number\n0")
            self.reset_button = QtWidgets.QPushButton('Reset')
            layout.addWidget(self.timestamp_label, 0, 0, 0, 1)
            layout.addWidget(self.event_numb_label, 0, 1, 0, 1)
            layout.addWidget(self.hit_rate_label, 0, 6, 0, 1)
            layout.addWidget(self.total_trig_numb, 0, 3, 0, 1)
            layout.addWidget(self.reset_button, 0, 7, 0, 1)
            dock_status.addWidget(cw)

            self.reset_button.clicked.connect(lambda: self._reset())

            # # particle rate dock
            trigger_rate_graphics = pg.GraphicsLayoutWidget()
            trigger_rate_graphics.show()
            plot_trigger_rate = pg.PlotItem(labels={'left': 'Trigger Rate / Hz', 'bottom': 'Run Time / s'})
            self.trigger_rate_acc_curve = pg.PlotCurveItem(pen='#B00B13')

            # # add legend
            legend_acc = pg.LegendItem(offset=(80, 10))
            legend_acc.setParentItem(plot_trigger_rate)
            legend_acc.addItem(self.trigger_rate_acc_curve, 'Trigger Rate')

            # # add items to plots and customize plots viewboxes
            plot_trigger_rate.addItem(self.trigger_rate_acc_curve)
            plot_trigger_rate.vb.setBackgroundColor('#E6E5F4')
            #plot_trigger_rate.setXRange(0, 200)
            plot_trigger_rate.getAxis('left').setZValue(0)
            plot_trigger_rate.getAxis('left').setGrid(155)

            # # add plots to graphicslayout and layout to dock
            trigger_rate_graphics.addItem(plot_trigger_rate, row=0, col=1, rowspan=1, colspan=2)
            dock_rate.addWidget(trigger_rate_graphics)

            # # add dict of all used plotcurveitems for individual handling of each plot
            self.plots = {'trigger_rate_acc': self.trigger_rate_acc_curve}
            self.plot_delay = 0

        def deserialize_data(self, data):
            #Ok alot of string decoding dont panic it works
            m = data.decode("utf-8") 
            m = ''.join([i for i in m if i not in ['[' ,']', '  ']])
            m = m.split(' ')
            address = m[0].replace(',','')
            address = m[0].replace('(','')
            data_array = m[1:5]
            data_array = list(filter(None, data_array))
            for i in range(len(data_array)):
                data_array[i] = data_array[i].replace(',', '')
                data_array[i] = data_array[i].replace(')', '')
            data_array = [float(i) for i in data_array]
            array = {'address': address, 'data': data_array}
            return array
            #res = jsonapi.loads(data, object_hook=utils.json_numpy_obj_hook)
        
        def refresh_data(self):
            if len(self.hitrate_data) > 0:
                self.trigger_rate_acc_curve.setData(x=self.runtime, y=self.hitrate_data)
            
        def handle_data(self, data):
            self.hitrate_data.append(data['data'][3])
            self.runtime.append(data['data'][0])
            self.timestamp_label.setText("Run Time\n%0.2f s" %data['data'][0])
            self.event_numb_label.setText("Event Number\n%i" %data['data'][1])
            self.total_trig_numb.setText("Total Trigger Number\n%i" %data['data'][2])
            self.hit_rate_label.setText("Trigger Frequency\n%0.2f Hz" %data['data'][3])

        def _reset(self):
            self.hitrate_data = []
            self.runtime = []