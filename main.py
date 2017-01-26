import logging
import threading
from time import sleep, time

import numpy as np
import ode
from genie_python.genie_startup import *

import config
import render
import pv_server
from monitor import Monitor, DummyMonitor
from move import move_all

# This should be from C:\Instrument\Apps\EPICS\ISIS\inst_servers\master\server_common\loggers\isis_logger.py
from isis_logger import IsisLogger


class GeometryBox(object):
    def __init__(self, space, position=(0, 0, 0), size=(1, 1, 1), color=(1, 1, 1), oversize=1, name=None):

        # Set parameters for drawing the body
        self.color = color
        self.size = list(size)
        self.oversize = oversize

        # Create a box geom for collision detection
        self.geom = ode.GeomBox(space, lengths=[s + 2 + oversize for s in self.size])
        self.geom.setPosition(position)

        # A friendly name
        self.name = name

    # Set the size of the ODE geometry
    def set_size(self, x=None, y=None, z=None, oversize=None):
        # Only need to set the size of dimensions supplied
        if x is not None:
            self.size[0] = x
        if y is not None:
            self.size[1] = y
        if z is not None:
            self.size[2] = z
        if oversize is not None:
            self.oversize = oversize
        self.geom.setLengths([s + 2 + self.oversize for s in self.size])

    # Set the transform for the geometry
    def set_transform(self, transform):
        # Get the rotation and position elements from the transformation matrix
        rot, pos = transform.split()

        # Reshape the rotation matrix into a ODE friendly format
        rot = np.reshape(rot, 9)

        # Apply the translation and rotation to the ODE geometry
        self.geom.setPosition(pos)
        self.geom.setRotation(rot)


# Do coarse and fine searches for limits in both forward and backward directions
def seek_limits(geometries, ignore, moves, monitors, limits, coarse=1.0, fine=0.1):

    # Initialise dynamic limits - be careful to copy, not reference
    dynamic_limits = [l[:] for l in limits[:]]

    # Loop over the number of monitors provided
    for i in range(len(monitors)):
        # Create some dummy monitors for seeking about
        dummies = [DummyMonitor(monitor.value()) for monitor in monitors]

        # Store the current position of the motor in question
        start = dummies[i].value()

        # Get the max and min configuration limits
        min_limit = np.min(limits[i])
        max_limit = np.max(limits[i])

        # Find the lower limit
        if min_limit >= start:
            # Already exceeded the configuration limit!!
            dynamic_limits[i][0] = min_limit
        else:
            # Create a sequence from start, to the configuration minimum, in multiples of coarse
            sequence = np.arange(start, min_limit, -coarse)
            # Make sure the last step is the limit
            sequence = np.append(sequence, min_limit)

            # Search for a collision within the sequence
            step, collided = seek(sequence, dummies, i, moves, geometries, ignore)

            # Consider whether to do a fine seek
            if step == start:
                # There was already a crash before we started to seek
                dynamic_limits[i][0] = start

            # If there were no collisions, then don't bother doing a fine search
            elif step == min_limit and not collided:
                # We didn't find any collisions so use the limit
                dynamic_limits[i][0] = min_limit

            else:
                # There is a collision between step+coarse and step
                # Generate a sequence with between step+coarse, and step, in multiples of fine
                sequence = np.arange(step+coarse, step, -fine)

                # Search for a collision within the sequence
                step, collided = seek(sequence, dummies, i, moves, geometries, ignore)

                # Update the limit
                dynamic_limits[i][0] = step + fine

        # Find the upper limit
        if max_limit <= start:
            # Already exceeded the configuration limit!!
            dynamic_limits[i][1] = max_limit
        else:
            # Create a sequence from start, to the configuration maximum, in multiples of coarse
            sequence = np.arange(start, max_limit, coarse)
            # Make sure the last step is the limit
            sequence = np.append(sequence, max_limit)

            # Search for a collision within the sequence
            step, collided = seek(sequence, dummies, i, moves, geometries, ignore)

            # Consider whether to do a fine seek
            if step == start:
                # There was already a crash before we started to seek
                dynamic_limits[i][1] = start

            # If there were no collisions, then don't bother doing a fine search
            elif step == max_limit and not collided:
                # We didn't find any collisions so use the limit
                dynamic_limits[i][1] = max_limit

            else:
                # There is a collision between step-coarse and step
                # Generate a sequence with between step-coarse, and step, in multiples of fine
                sequence = np.arange(step-coarse, step, fine)

                # Search for a collision within the sequence
                step, collided = seek(sequence, dummies, i, moves, geometries, ignore)

                # Update the limit
                dynamic_limits[i][1] = step - fine

        # Cap the limits within the configuration limits
        if dynamic_limits[i][0] < min_limit:
            dynamic_limits[i][0] = min_limit
        if dynamic_limits[i][1] > max_limit:
            dynamic_limits[i][1] = max_limit

    return dynamic_limits


# Search for the first collision within the given sequence of steps
def seek(sequence, dummies, i, moves, geometries, ignore):
    # Initialise some variables
    collided = False
    step = None

    # Iterate over the sequence
    for s in sequence:
        # Update the current step
        step = s
        # Update the dummy monitor
        dummies[i].update(step)
        # Move to position
        move_all(dummies, geometries, moves)
        # Check for collisions
        collisions = collide(geometries, ignore)
        # If we've collided, then stop iterating
        if any(collisions):
            collided = True
            break
    # Return the current step, and whether any collisions have occurred
    # Could just check if the step was the last value in the sequence?
    return step, collided


# This ignores geometries we have said we don't care about
# As there are only [(len(geometries)-1)!] combinations, and we don't care about some, there isn't much effort saved
# by using spaces (which do a quicker estimate of collisions first)
def collide(geometries, ignore):
    collisions = [False] * len(geometries)
    for i, geom1 in enumerate(geometries):
        for j, geom2 in enumerate(geometries[i:]):
            if not ([i, i + j] in ignore or [i + j, i] in ignore):
                contacts = ode.collide(geom1.geom, geom2.geom)
                if contacts:
                    collisions[i] = True
                    collisions[i + j] = True
    # print collisions
    return collisions


# Set the high and low dial limits for each motor
def set_limits(limits, pvs):
    for limit, pv in zip(limits, pvs):
        set_pv(pv + '.DLLM', np.min(limit))
        set_pv(pv + '.DHLM', np.max(limit))


# Contains operating mode events
class OperatingMode(object):
    def __init__(self):
        # Close event to be triggered by the render thread
        self.close = threading.Event()

        # Set dynamic limits automatically
        self.set_limits = threading.Event()

        # Stop the motors on a collision
        self.auto_stop = threading.Event()

    @property
    def code(self):
        code = 0
        if self.auto_stop.is_set():
            code |= 0b001

        if self.set_limits.is_set():
            code |= 0b010

        if self.close.is_set():
            code |= 0b100

        return code

    @code.setter
    def code(self, code):
        if code & 0b001:
            self.auto_stop.set()
        else:
            self.auto_stop.clear()

        if code & 0b010:
            self.set_limits.set()
        else:
            self.set_limits.clear()

        if code & 0b100:
            self.close.set()
        else:
            self.close.clear()


# The main routine to execute
def main():

    # Load config:
    colors = config.colors
    moves = config.moves
    ignore = config.ignore
    pvs = config.pvs
    config_limits = config.hardlimits
    old_limits = config_limits[:]

    # Create space objects for the live and rendered world
    space = ode.Space()
    renderspace = ode.Space()

    # Create and populate lists of geometries
    geometries = []
    rendergeometries = []
    for i, geometry in enumerate(config.geometries):
        geometries.append(GeometryBox(space, color=colors[i % len(colors)], oversize=config.oversize, **geometry))
        rendergeometries.append(GeometryBox(renderspace, color=colors[i % len(colors)], **geometry))

    # Create and populate two lists of monitors
    monitors = []
    ismoving = []
    for pv in pvs:
        m = Monitor(pv + ".DRBV")
        m.start()
        monitors.append(m)

        moving = Monitor(pv + ".MOVN")
        moving.start()
        ismoving.append(moving)

    # Create a shared operating mode object to control the main thread
    op_mode = OperatingMode()
    # Set the default behaviour to set_limits as calculated, and auto_stop on collision
    op_mode.set_limits.set()
    op_mode.auto_stop.set()

    # Create a shared render parameter object to update the render thread
    parameters = render.RenderParams()

    # Initialise the render thread, and set it to daemon - won't prevent the main thread from exiting
    renderer = render.Renderer(parameters, rendergeometries, colors, monitors, pvs, moves, op_mode)
    renderer.daemon = True

    # Need to know if this is the first execution of the main loop
    calc_limits = True

    # Only report for new collisions
    collision_reported = None

    # Initialise the pv server
    data = pv_server.ServerData()
    data.set_data(new_data=False)

    pv_server.pvdb['HI_LIM']['count'] = len(config.pvs)
    pv_server.pvdb['LO_LIM']['count'] = len(config.pvs)
    pv_server.pvdb['TRAVEL']['count'] = len(config.pvs)
    pv_server.pvdb['TRAV_F']['count'] = len(config.pvs)
    pv_server.pvdb['TRAV_R']['count'] = len(config.pvs)
    pv_server.pvdb['NAMES']['count'] = len(config.geometries)
    pv_server.pvdb['COLLIDED']['count'] = len(config.geometries)

    driver = pv_server.start_thread(config.control_pv, data, op_mode)

    driver.setParam('MSG', 'Hello world!!??!')
    driver.setParam('OVERSIZE', config.oversize)
    driver.setParam('COARSE', config.coarse)
    driver.setParam('FINE', config.fine)
    driver.setParam('NAMES', [g['name'] for g in config.geometries])

    # Start a logger
    logger = IsisLogger()

    # Main loop
    while True:

        # Freeze the positions of our current monitors by creating some dummies
        # This stops the threads from trying to reading each monitor sequentially, and holding each other up
        frozen = [DummyMonitor(m.value()) for m in monitors]

        # Execute the move
        move_all(frozen, geometries, moves)

        # Check if the oversize has been changed, ahead of any collision calcs
        if data.get_data('new_data'):
            data.set_data(new_data=False)
            for geometry in geometries:
                geometry.set_size(oversize=driver.getParam('OVERSIZE'))
            calc_limits = True

        # Check for collisions
        collisions = collide(geometries, ignore)

        # Get some data to the user:
        driver.setParam('COLLIDED', [int(c) for c in collisions])

        # If there has been a collision:
        if any(collisions):
            # Message:
            msg = "Collisions on %s" % ", ".join(map(str, [geometries[i].name for i in np.where(collisions)[0]]))

            # Log the collisions
            logging.debug("Collisions on %s", [i for i in np.where(collisions)[0]])
            driver.setParam('MSG', msg)
            driver.setParam('SAFE', 0)

            # Log to the IOC log
            if collision_reported is None or not collisions == collision_reported:
                logger.write_to_log(msg, "MAJOR", "COLLIDE")
                collision_reported = collisions[:]

            # Stop the moving motors based on the operating mode auto_stop
            if op_mode.auto_stop.is_set():
                logging.debug("Stopping motors %s" % [i for i, m in enumerate(ismoving) if m.value()])
                for moving, pv in zip(ismoving, pvs):
                    if moving.value():
                        set_pv(pv + '.STOP', 1)
        else:
            driver.setParam('MSG', "No collisions detected.")
            driver.setParam('SAFE', 1)
            collision_reported = None

        # Check if there have been any changes to the .MOVN monitors
        fresh = any([m.fresh() for m in ismoving])
        # Check if any of the motors monitors are moving
        moving = any([m.value() for m in ismoving])

        new_limits = []

        if fresh or moving or calc_limits:
            # Start timing for diagnostics
            time_passed = time()

            # Seek the correct limit values
            dynamic_limits = seek_limits(geometries, ignore, moves, frozen, config_limits,
                                         coarse=driver.getParam('COARSE'), fine=driver.getParam('FINE'))

            # Calculate and log the time taken to calculate
            time_passed = (time() - time_passed) * 1000
            logging.debug("Calculated limits in %d", time_passed)

            # Log the new limits
            logging.debug("New limits are " + str(dynamic_limits))

            # Set the limits according to the set_limits operating mode
            if op_mode.set_limits.is_set():
                # Apply the calculated limits
                new_limits = dynamic_limits[:]
            else:
                # Restore the configuration limits
                new_limits = config_limits[:]

            # Update the render thread parameters
            parameters.update_params(dynamic_limits, collisions, time_passed)

            # # Update the PVs
            driver.setParam('TIME', time_passed)
            driver.setParam('HI_LIM', [l[1] for l in dynamic_limits])
            driver.setParam('LO_LIM', [l[0] for l in dynamic_limits])
            driver.setParam('TRAVEL', [min([l[0] - m.value(), l[1] - m.value()], key=abs)
                                       for l, m in zip(dynamic_limits, frozen)])
            driver.setParam('TRAV_F', [l[1] - m.value() for l, m in zip(dynamic_limits, frozen)])
            driver.setParam('TRAV_R', [l[0] - m.value() for l, m in zip(dynamic_limits, frozen)])

            driver.updatePVs()

            # On the first run, start the renderer
            if renderer.is_alive() is False:
                renderer.start()

            calc_limits = False
        else:
            # Restore the configuration limits
            if op_mode.set_limits.is_set() is False:
                new_limits = config_limits[:]

        # Stop us overloading the limits
        if not new_limits == old_limits:
            set_limits(new_limits, pvs)

        old_limits = new_limits[:]

        # Exit the program
        if op_mode.close.is_set():
            # Restore the configuration limits
            set_limits(config_limits, pvs)
            return

        # Give the CPU a break
        sleep(0.01)

# Execute main
main()
