import matplotlib.pyplot as plt
import numpy as np


class SimulatedMotor(object):

    def __init__(self, speed=4.096, acceleration=1.0, resolution=0.01):
        self.speed = speed
        self.acceleration = acceleration
        self.resolution = resolution

    # s = u*t + 0.5*a*t**2
    def move(self, start, finish):
        # Calculate displacement
        s = finish - start
        v = abs(self.speed)
        a = self.acceleration
        d = self.resolution
        dir = 1
        if s < 0:
            # Move is backwards
            s = -s
            dir = -1
        # Time to accelerate to full speed ta
        ta = v / a
        # Distance covered in acceleration
        sa = 0.5 * v * ta
        tt = 0
        # Does axis reach full speed?
        if sa <= 0.5 * s:
            # Reaches v
            # Calculate total time based on trapezoidal profile
            tt = 2 * ta + (s - (2 * sa)) / v
        else:
            # Does not reach v
            # Calculate distance covered using triangle profile
            sa = 0.5 * s
            # Calculate acceleration time
            ta = (sa / (0.5 * a)) ** 0.5
            # Calculate total time
            tt = 2 * ta
            # Calculate new max speed
            v = a * ta
        # Build an array of times, that is sure to cover the range of motion
        time = np.arange(0, tt + d, d)
        # Initialise arrays
        disp = np.array([])
        velo = np.array([])
        # Do the simulation
        for i, t in enumerate(time):
            if t <= ta:
                # Accelerating
                velo = np.append(velo, a * t)
                disp = np.append(disp, 0.5 * a * t ** 2)
            elif t > (tt - ta):
                # Decelerating
                velo = np.append(velo, max(-a * (t - tt), 0))
                disp = np.append(disp, s - (0.5 * a * min(t - tt, 0) ** 2))
            else:
                # Max speed
                velo = np.append(velo, v)
                disp = np.append(disp, sa + v * (t - ta))
        return start + (disp * dir)
        # return time, velo * dir, start + (disp * dir)


# Can't deal with different delta t
# Can just use the last value if we have exceeded the end of the list??
'''
Something like:
if i < len(a):
    # use a[i]
else:
    # use a[-1]
'''
def mergeSeries(T1, X1, T2, X2):
    T = np.array([])
    if len(T1) == len(T2):
        # Nothging to do here
        return (T1, X1, X2)
    elif len(T1) > len(T2):
        # T1 is the longer series
        T = T1
    else:
        # T2 is the longer series
        T = T2
    if len(X1) < len(T):
        # X1 needs stretching
        extend = np.ones(len(T) - len(X1))
        extend = extend * X1[-1]
        X1 = np.append(X1, extend)
    if len(X2) < len(T):
        # X2 needs stretching
        extend = np.ones(len(T) - len(X2))
        extend = extend * X2[-1]
        X2 = np.append(X2, extend)
    return (T, X1, X2)