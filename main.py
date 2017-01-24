import logging
import threading
from time import sleep, time

import numpy as np
import ode
from OpenGL.GL import *
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

    fill = False

    num_faces = 6
    num_edges = 12

    vertices = [(-0.5, -0.5, 0.5),
                (0.5, -0.5, 0.5),
                (0.5, 0.5, 0.5),
                (-0.5, 0.5, 0.5),
                (-0.5, -0.5, -0.5),
                (0.5, -0.5, -0.5),
                (0.5, 0.5, -0.5),
                (-0.5, 0.5, -0.5)]

    normals = [(0.0, 0.0, +1.0),  # top
               (0.0, 0.0, -1.0),  # bot
               (-1.0, 0.0, 0.0),  # left
               (+1.0, 0.0, 0.0),  # right
               (0.0, +1.0, 0.0),  # front
               (0.0, -1.0, 0.0),  # back
               ]

    vertex_indices = [(0, 1, 2, 3),  # front
                      (4, 5, 6, 7),  # back
                      (1, 5, 6, 2),  # right
                      (0, 4, 7, 3),  # left
                      (3, 2, 6, 7),  # top
                      (0, 1, 5, 4)]  # bottom

    edge_indices = [(0, 1),
                    (1, 2),
                    (2, 3),
                    (3, 0),
                    (4, 5),
                    (5, 6),
                    (6, 7),
                    (7, 4),
                    (0, 4),
                    (1, 5),
                    (2, 6),
                    (3, 7)]

    # Render the geometry - can supply color to override the geometry's own color e.g. make it red when collided
    def render(self, color=None):
        # Set the color for rendering
        if color:
            glColor(color)
        else:
            glColor(self.color)

        # Adjust all the vertices so that the cube is at self.position
        vertices = np.array(self.vertices)
        vertices = [v * self.size for v in vertices]

        # Get the position and rotation of the geometry
        x, y, z = self.geom.getPosition()
        r = self.geom.getRotation()

        # Get the transformation matrix for the geometry
        rot = [[r[0], r[3], r[6], 0.],
               [r[1], r[4], r[7], 0.],
               [r[2], r[5], r[8], 0.],
               [x, y, z, 1.0]]
        # And put it into an numpy array
        rot = np.array(rot)

        # If we want a filled in cube:
        if self.fill:
            # Start drawing quads
            glBegin(GL_QUADS)

            # Draw all 6 faces of the cube
            for face_no in xrange(self.num_faces):
                # Calculate and apply the normal - for lighting
                normal = np.array(self.normals[face_no]).T
                rotated = np.dot(normal, rot[:3, :3].T)
                glNormal3dv(rotated)

                # Calculate and draw each vertex
                for i in self.vertex_indices[face_no]:
                    point = np.array([vertices[i][0], vertices[i][1], vertices[i][2], 1]).T
                    glVertex(np.dot(point, rot))

            # Stop drawing quads
            glEnd()

        # We want a wire frame:
        else:
            glNormal3dv([0, 0, 1])
            # Start drawing lines
            glBegin(GL_LINES)

            # Draw all 12 edges of the cube
            for edge_no in xrange(self.num_edges):
                # Get the vertices for each edge
                vertex_index = self.edge_indices[edge_no]

                # Calculate and draw each vertex
                for i in vertex_index:
                    point = np.array([vertices[i][0], vertices[i][1], vertices[i][2], 1]).T
                    glVertex(np.dot(point, rot))

            # Stop drawing lines
            glEnd()

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
        rot = np.reshape(rot.T, 9, 1)

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
        min = np.min(limits[i])
        max = np.max(limits[i])

        # Find the lower limit
        if min >= start:
            # Already exceeded the configuration limit!!
            dynamic_limits[i][0] = min
        else:
            # Create a sequence from start, to the configuration minimum, in multiples of coarse
            sequence = np.arange(start, min, -coarse)
            # Make sure the last step is the limit
            sequence = np.append(sequence, min)

            # Search for a collision within the sequence
            step, collided = seek(sequence, dummies, i, moves, geometries, ignore)

            # Consider whether to do a fine seek
            if step == start:
                # There was already a crash before we started to seek
                dynamic_limits[i][0] = start

            # If there were no collisions, then don't bother doing a fine search
            elif step == min and not collided:
                # We didn't find any collisions so use the limit
                dynamic_limits[i][0] = min

            else:
                # There is a collision between step+coarse and step
                # Generate a sequence with between step+coarse, and step, in multiples of fine
                sequence = np.arange(step+coarse, step, -fine)

                # Search for a collision within the sequence
                step, collided = seek(sequence, dummies, i, moves, geometries, ignore)

                # Update the limit
                dynamic_limits[i][0] = step + fine

        # Find the upper limit
        if max <= start:
            # Already exceeded the configuration limit!!
            dynamic_limits[i][1] = max
        else:
            # Create a sequence from start, to the configuration maximum, in multiples of coarse
            sequence = np.arange(start, max, coarse)
            # Make sure the last step is the limit
            sequence = np.append(sequence, max)

            # Search for a collision within the sequence
            step, collided = seek(sequence, dummies, i, moves, geometries, ignore)

            # Consider whether to do a fine seek
            if step == start:
                # There was already a crash before we started to seek
                dynamic_limits[i][1] = start

            # If there were no collisions, then don't bother doing a fine search
            elif step == max and not collided:
                # We didn't find any collisions so use the limit
                dynamic_limits[i][1] = max

            else:
                # There is a collision between step-coarse and step
                # Generate a sequence with between step-coarse, and step, in multiples of fine
                sequence = np.arange(step-coarse, step, fine)

                # Search for a collision within the sequence
                step, collided = seek(sequence, dummies, i, moves, geometries, ignore)

                # Update the limit
                dynamic_limits[i][1] = step - fine

        # Cap the limits within the configuration limits
        if dynamic_limits[i][0] < min:
            dynamic_limits[i][0] = min
        if dynamic_limits[i][1] > max:
            dynamic_limits[i][1] = max

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
            # Log the collisions
            logging.debug("Collisions on %s", [i for i in np.where(collisions)[0]])
            driver.setParam('MSG', "Collisions on %s" % ", ".join(map(str, [geometries[i].name for i in np.where(collisions)[0]])))
            driver.setParam('SAFE', 0)

            if collision_reported is None:
                logger.write_to_log("Collisions on %s" % ", ".join(map(str, [geometries[i].name for i in np.where(collisions)[0]])), "MAJOR", "COLLIDE")
                collision_reported = collisions[:]
            elif any(np.logical_and(np.logical_not(collision_reported), collisions)):
                logger.write_to_log("Collisions on %s" % ", ".join(map(str, [geometries[i].name for i in np.where(collisions)[0]])), "MAJOR", "COLLIDE")
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
            driver.setParam('TRAVEL', [min([l[0] - m.value(), l[1] - m.value()], key=abs) for l, m in zip(dynamic_limits, frozen)])
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
