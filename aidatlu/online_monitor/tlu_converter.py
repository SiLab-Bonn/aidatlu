from online_monitor.converter.transceiver import Transceiver
import zmq
from online_monitor.utils import utils


class AIDATLUConverter(Transceiver):
    def deserialize_data(self, data):
        m = data.decode()
        m = "".join([i for i in m if i not in ["[", "]", "  "]])
        m = m.split(" ")
        m = list(filter(None, m))
        for i in range(len(m)):
            m[i] = m[i].replace(",", "")
        m = [float(i) for i in m]
        return m

    def interpret_data(self, data):
        interpreted_data = {
            "Address": data[0][0],
            "Run Time": data[0][1][0],
            "Event Number": data[0][1][1],
            "Total trigger numb": data[0][1][2],
            "Particle Rate": data[0][1][3],
            "Trigger freq": data[0][1][4],
        }
        return [interpreted_data]

    def serialize_data(self, data):
        return utils.simple_enc(None, data)
