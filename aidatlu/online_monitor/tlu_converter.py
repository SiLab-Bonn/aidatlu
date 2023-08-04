
from online_monitor.converter.transceiver import Transceiver
import zmq


class AIDATLUConverter(Transceiver):

    def deserialize_data(self, data):
        m = data.decode()
        m = ''.join([i for i in m if i not in ['[' ,']', '  ']])
        m = m.split(' ')
        m = list(filter(None, m))
        for i in range(len(m)):
            m[i] = m[i].replace(',', '')
        m = [float(i) for i in m]
        return m
    
    def interpret_data(self, data):
        return data

    def serialize_data(self, data):
        return data
        #return jsonapi.dumps(data, cls=utils.NumpyEncoder)

    def send_data(self, data):
        for actual_backend in self.backends:
            actual_backend[1].send_string(str(data), flags=zmq.NOBLOCK)