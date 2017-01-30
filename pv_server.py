from pcaspy import SimpleServer, Driver
from pcaspy.tools import ServerThread
import random
import threading
import logging

# Make sure to run: `set EPICS_CA_ADDR_LIST=127.255.255.255 130.246.51.255 127.0.0.1:50640` then restart ibex server
# Use `caget -S` to print a char array as a string

# Configure this env with:
# `EPICS_CAS_BEACON_ADDR_LIST=127.255.255.255`
# `EPICS_CAS_INTF_ADDR_LIST=127.0.0.1`

count = 1

pvdb = {
    'RAND': {
        'prec': 3,
        # 'scan' : 1,
        'count': 1,
        'type': 'float',
    },
    'MSG': {
        'count': 300,
        'type': 'char',
    },
    'NAMES': {
        'count': count,
        'type': 'string',
    },
    'MODE': {
        'count': 1,
        'type': 'int',
        'scan': 1,
    },
    'AUTO_STOP': {
        'count': 1,
        'type': 'int',
    },
    'AUTO_LIMIT': {
        'count': 1,
        'type': 'int',
    },
    'SAFE': {
        'count': 1,
        'type': 'int',
    },
    'HI_LIM': {
        'count': count,
        'type': 'float',
        'prec': 3,
    },
    'LO_LIM': {
        'count': count,
        'type': 'float',
        'prec': 3,
    },
    'TRAVEL': {
        'count': count,
        'type': 'float',
        'prec': 3,
    },
    'TRAV_F': {
        'count': count,
        'type': 'float',
        'prec': 3,
    },
    'TRAV_R': {
        'count': count,
        'type': 'float',
        'prec': 3,
    },
    'COLLIDED': {
        'count': count,
        'type': 'int',
    },
    'OVERSIZE': {
        'count': 1,
        'type': 'float',
        'prec': 3,
        'unit': 'mm',
    },
    'COARSE': {
        'count': 1,
        'type': 'float',
        'prec': 3,
    },
    'FINE': {
        'count': 1,
        'type': 'float',
        'prec': 3,
    },
    'TIME': {
        'count': 1,
        'type': 'int',
        # 'scan': 1,
    },
}


class MyDriver(Driver):
    def __init__(self, data, op_mode):
        super(MyDriver, self).__init__()
        self.__data = data
        self.op_mode = op_mode

    def read(self, reason):
        # logging.debug("Reading '%s'...", reason)
        if reason == 'RAND':
            value = random.random()
        elif reason == 'MODE':
            self.setParam(reason, self.op_mode.code)
            value = self.getParam(reason)
        elif reason == 'AUTO_STOP':
            value = int(self.op_mode.auto_stop.is_set())
        elif reason == 'AUTO_LIMIT':
            value = int(self.op_mode.set_limits.is_set())
        else:
            value = self.getParam(reason)

        return value

    def write(self, reason, value):
        status = True
        if reason == 'MODE':
            self.op_mode.code = int(value)
            self.setParam(reason, int(value))
        elif reason == 'AUTO_STOP':
            if value == 1:
                self.op_mode.auto_stop.set()
            elif value == 0:
                self.op_mode.auto_stop.clear()
            self.setParam('MODE', self.op_mode.code)
        elif reason == 'AUTO_LIMIT':
            if value == 1:
                self.op_mode.set_limits.set()
            elif value == 0:
                self.op_mode.set_limits.clear()
        elif reason == 'OVERSIZE':
            self.__data.set_data(OVERSIZE=value, COARSE=4 * value, new_data=True)
            self.setParam(reason, value)
            self.setParam('COARSE', 4 * value)
        elif reason == 'COARSE':
            self.__data.set_data(OVERSIZE=value / 4, COARSE=value, new_data=True)
            self.setParam(reason, value)
            self.setParam('OVERSIZE', value / 4)
        elif reason == 'FINE':
            self.__data.set_data(FINE=value, new_data=True)
            self.setParam(reason, value)
        return status


class ServerDataException(Exception):
    pass


class ServerData(object):
    # Threadsafe class for holding arbitrary data
    def __init__(self):
        self.lock = threading.Lock()

        # A private dictionary to hold our data
        self.__data = dict(data="Some dummy data")

    def get_data(self, key=None):
        # Returns the dictionary of data
        # e.g.: get_data()['data'] ==> "Some dummy data"
        #   or: get_data('data')   ==> "Some dummy data"
        with self.lock:
            if key is None:
                return self.__data
            else:
                if key in self.__data:
                    return self.__data[key]
                else:
                    raise ServerDataException("The key supplied is not in the data dict")

    def set_data(self, **data):
        # Sets only the provided data
        # e.g.: set_data(x=10) will not affect __data['y']
        with self.lock:
            self.__data.update(data)


if __name__ == '__main__':
    pass


def start_thread(prefix, data, op_mode):

    server = SimpleServer()
    server.createPV(prefix, pvdb)
    # server.setDebugLevel(4)

    server_thread = ServerThread(server)
    server_thread.name = "PVServer"
    server_thread.daemon = True
    server_thread.start()

    driver = MyDriver(data, op_mode)

    return driver
