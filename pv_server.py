from pcaspy import SimpleServer, Driver
import random
import threading

prefix = 'TEST:'
pvdb = {
    'RAND' : {
        'prec' : 3,
       # 'scan' : 1,
        'count': 1,
        'type' : 'float',
    },
}

class myDriver(Driver):
    def __init__(self):
        super(myDriver, self).__init__()

    def read(self, reason):
        print "Reading..."
        print reason
        if reason == 'RAND':
            value = random.random()
        else:
            value = self.getParam(reason)
        return value

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
    server = SimpleServer()
    server.createPV(prefix, pvdb)

    driver = myDriver()

    # process CA transactions
    while True:
        server.process(0.1)