import matplotlib.pyplot as plt

#from genie_python.genie_startup import *

from CaChannel import CaChannel
from CaChannel import CaChannelException
import ca
import threading
import time as time


def eventCB(epics_args, monitor):
    # print "new value for ", user_args[0], " = ", epics_args['pv_value']
    print("Got an update")
    threading.Thread(target=monitor.update, args=epics_args).start()


class Monitor(object):

    def __init__(self, pv):
        self.pv = pv
        self.value = None
        self.channel = CaChannel()
        self.running = False

    def start(self):
        if self.running: self.stop()

        try:
            self.channel.searchw(self.pv)
        except CaChannelException:
            print ("Unable to find pv " + self.pv)
            return

        self.channel.add_masked_array_event(
            ca.dbf_type_to_DBR_STS(self.channel.field_type()),
            None,
            ca.DBE_VALUE,
            self.update,
            None)
        self.channel.pend_event()
        self.running = True

    def update(self, epics_args, user_args):
        self.value = epics_args['pv_value']
        #print(self.value)

    def stop(self):
        self.channel.clear_event()
        self.running = False


class MonitorQueue(Monitor):
    def __init__(self, pv, initial=None):
        self.queue = []
        self.time = None
        self.frozen = False
        if initial:
            self.queue.append(initial)
        #super(MonitorQueue, self).__init__()
        Monitor.__init__(self, pv)

    def update(self, epics_args, user_args):
        value = epics_args['pv_value']
        if value == self.last():
            print "Duplicate value " + str(value)
            pass
        else:
            if not self.frozen:
                self.queue.append(value)
                self.time = time.time()
        print(self.pv, self.queue, self.time)


    def clear(self):
        """
        Sets the queue to the last value
        """
        self.queue[:] = [self.queue[-1]]
        #print self.queue

    def reset(self):
        """
        Sets the queue to the first value
        """
        self.queue[:] = [self.queue[0]]
        #print self.queue

    def initialised(self):
        """
        Is the queue populated?
        """
        if len(self.queue) > 0:
            return True
        else:
            return False

    def first(self):
        if len(self.queue) > 0:
            return self.queue[0]
        else:
            return None

    def last(self):
        if len(self.queue) > 0:
            return self.queue[-1]
        else:
            return None


def test():
    # Geometry
    high = 50.0
    low = 0.0

    # Prefixes for the motors
    prefA = 'TE:NDW1720:MOT:MTR0101'
    prefB = 'TE:NDW1720:MOT:MTR0102'

    '''fig1 = plt.figure(1)
    ax = fig1.add_subplot(1, 1, 1)

    x = ax.plot([low, high], [0, 0], 'k|-')
    # h = ax.plot([low,20,30,high],[0,0,0,0],'ro-')
    a = ax.plot([30], [1.5], 'ro')
    alim = ax.plot([0, 50], [1.5, 1.5], 'r|--')
    b = ax.plot([20], [0.5], 'bo')
    blim = ax.plot([0, 50], [0.5, 0.5], 'b|--')

    plt.ion()
    plt.show()
    plt.xlim([low - 10, high + 10])
    plt.ylim([-20, 20])

    timeA = time.time()
    timeB = time.time()
    dt = 0.2'''


    def updateGraph(name, pv_value):
        global timeA
        global timeB
        t = time.time()
        [motor, pv] = name.split('.')
        # data = h[0].get_data()
        if motor == prefA:
            if pv == 'RBV':
                # data[0][2] = pv_value
                if (timeA + dt) < t:
                    a[0].set_data([[pv_value], [1.5]])
                    timeA = t
            elif pv == 'LLM':
                data = alim[0].get_data()
                data[0][0] = pv_value
                alim[0].set_data(data)
            elif pv == 'HLM':
                data = alim[0].get_data()
                data[0][1] = pv_value
                alim[0].set_data(data)
        elif motor == prefB:
            if pv == 'RBV':
                # data[0][1] = pv_value
                if (timeB + dt) < t:
                    b[0].set_data([[pv_value], [0.5]])
                    timeB = t
            elif pv == 'LLM':
                data = blim[0].get_data()
                data[0][0] = pv_value
                blim[0].set_data(data)
            elif pv == 'HLM':
                data = blim[0].get_data()
                data[0][1] = pv_value
                blim[0].set_data(data)
        # h[0].set_data(data)
        ax.figure.canvas.draw()


    # Call back for the monitors
    #def eventCB(epics_args, user_args):
    #    # print "new value for ", user_args[0], " = ", epics_args['pv_value']
    #    threading.Thread(target=updateGraph, args=(user_args[0], epics_args['pv_value'])).start()

    mon = Monitor("TE:NDW1720:MOT:MTR0101.RBV")
    mon.start()

    input()

    '''rbvA = CaChannel()
    rbvA.searchw(prefA + '.RBV')
    # Add montitor for A
    rbvA.add_masked_array_event(
        ca.dbf_type_to_DBR_STS(rbvA.field_type()),
        None,
        ca.DBE_VALUE,
        eventCB,
        rbvA.name())

    # Connect to motor B
    rbvB = CaChannel()
    rbvB.searchw(prefB + '.RBV')
    # Add monitor for B
    rbvB.add_masked_array_event(
        ca.dbf_type_to_DBR_STS(rbvB.field_type()),
        None,
        ca.DBE_VALUE,
        eventCB,
        rbvB.name())

    # Push those monitors to the IOCs
    rbvA.pend_event()
    rbvB.pend_event()

    # Low limit monitors
    # Connect to motor A
    llmA = CaChannel()
    llmA.searchw(prefA + '.LLM')
    # Add montitor for A
    llmA.add_masked_array_event(
        ca.dbf_type_to_DBR_STS(llmA.field_type()),
        None,
        ca.DBE_VALUE,
        eventCB,
        llmA.name())

    # Connect to motor B
    llmB = CaChannel()
    llmB.searchw(prefB + '.LLM')
    # Add monitor for B
    llmB.add_masked_array_event(
        ca.dbf_type_to_DBR_STS(llmB.field_type()),
        None,
        ca.DBE_VALUE,
        eventCB,
        llmB.name())

    # Push those monitors to the IOCs
    llmA.pend_event()
    llmB.pend_event()

    # High limit monitors
    # Connect to motor A
    hlmA = CaChannel()
    hlmA.searchw(prefA + '.HLM')
    # Add montitor for A
    hlmA.add_masked_array_event(
        ca.dbf_type_to_DBR_STS(hlmA.field_type()),
        None,
        ca.DBE_VALUE,
        eventCB,
        hlmA.name())

    # Connect to motor B
    hlmB = CaChannel()
    hlmB.searchw(prefB + '.HLM')
    # Add monitor for B
    hlmB.add_masked_array_event(
        ca.dbf_type_to_DBR_STS(hlmB.field_type()),
        None,
        ca.DBE_VALUE,
        eventCB,
        hlmB.name())

    # Push those monitors to the IOCs
    hlmA.pend_event()
    hlmB.pend_event()


    def cleanup():
        rbvA.clear_channel()
        rbvB.clear_channel()
        llmA.clear_channel()
        llmB.clear_channel()
        hlmA.clear_channel()
        hlmB.clear_channel()


        # EOF

        '''