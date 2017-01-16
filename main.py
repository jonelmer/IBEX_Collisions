import logging
import threading
from time import sleep, time

import numpy as np
import ode
import pygame
from OpenGL.GL import *
from genie_python.genie_startup import *

import config
import render
from gameobjects.vector3 import *
from monitor import Monitor, DummyMonitor
from move import move_all


def rotation_matrix(rx=0, ry=0, rz=0, angle=None):
    if angle:
        rz, ry, rz = angle
    # Can check if we are only rotating about one axis, then only do that rotation?
    #R = np.identity(3) # not very quick!
    R = np.array([[1, 0, 0], [0, 1, 0], [0, 0, 1]])

    if rx is not 0:
        R = np.dot(np.array([[1, 0, 0], [0, cos(rx), -sin(rx)], [0, sin(rx), cos(rx)]]), R)

    if ry is not 0:
        R = np.dot(np.array([[cos(ry), 0, -sin(ry)], [0, 1, 0], [sin(ry), 0, cos(ry)]]), R)

    if rz is not 0:
        R = np.dot(np.array([[cos(rz), -sin(rz), 0], [sin(rz), cos(rz), 0], [0, 0, 1]]), R)

    return R


class GeometryBox(object):
    def __init__(self, space, position=(0, 0, 0), size=(1, 1, 1), color=(1, 1, 1), origin=(0, 0, 0), angle=(0, 0, 0), oversize=1):
        # type: (object, object, object, object, object, object, object) -> object
        # Set parameters for drawing the body
        self.color = color
        self.size = list(size)

        # Create a box geom for collision detection
        self.geom = ode.GeomBox(space, lengths=[s * oversize for s in self.size])
        self.geom.setPosition(position)

        self.origin = origin
        self.angles = angle

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
               (0.0, +1.0, 0.0),  # front
               (0.0, -1.0, 0.0),  # back
               (+1.0, 0.0, 0.0),  # left
               (-1.0, 0.0, 0.0),  # right
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

    def render(self, color=None):

        if color:
            glColor(color)
        else:
            glColor(self.color)

        # Adjust all the vertices so that the cube is at self.position
        vertices = self.vertices
        vertices = [tuple(Vector3(v) * self.size) for v in vertices]
        # vertices = [tuple(Vector3(v) + self.body.getPosition()) for v in vertices]

        x, y, z = self.geom.getPosition()
        R = self.geom.getRotation()

        if self.fill:
            # Draw all 6 faces of the cube
            glBegin(GL_QUADS)

            rot = [[R[0], R[3], R[6], 0.],
                   [R[1], R[4], R[7], 0.],
                   [R[2], R[5], R[8], 0.],
                   [x, y, z, 1.0]]
            rot = np.array(rot)

            for face_no in xrange(self.num_faces):
                normal = np.array(self.normals[face_no]).T
                rotated = np.dot(normal, rot[:3, :3].T)
                glNormal3dv(rotated)

                for i in self.vertex_indices[face_no]:
                    point = np.array([vertices[i][0], vertices[i][1], vertices[i][2], 1]).T
                    glVertex(np.dot(point, rot))

            glEnd()
        else:
            # Draw all 12 edges of the cube
            glBegin(GL_LINES)

            rot = [[R[0], R[3], R[6], 0.],
                   [R[1], R[4], R[7], 0.],
                   [R[2], R[5], R[8], 0.],
                   [x, y, z, 1.0]]
            rot = np.array(rot)

            for edge_no in xrange(self.num_edges):
                vertex_index = self.edge_indices[edge_no]

                for i in vertex_index:
                    point = np.array([vertices[i][0], vertices[i][1], vertices[i][2], 1]).T
                    # print rot
                    # print np.dot(point, rot)

                    glVertex(np.dot(point, rot))
                    # glVertex(vertices[i])
            glEnd()

    def move(self, x=0, y=0, z=0):
        pos = self.geom.getPosition()
        pos = tuple([pos[0] + x, pos[1] + y, pos[2] + z])
        self.geom.setPosition(pos)

    def setSize(self, x=None, y=None, z=None):
        if x is not None:
            self.size[0] = x
        if y is not None:
            self.size[1] = y
        if z is not None:
            self.size[2] = z

    def setPosition(self, x=None, y=None, z=None, coords=None):
        if coords is not None:
            x, y, z = coords
        pos = list(self.geom.getPosition())
        if x is not None:
            pos[0] = x
        if y is not None:
            pos[1] = y
        if z is not None:
            pos[2] = z
        self.geom.setPosition(pos)

    def getPosition(self):
        return self.geom.getPosition()

    def setRotation(self, tx=0, ty=0, tz=0, origin=None, angles=None):
        if angles:
            tx, ty, tx = angles

        # Don't need to calculate if the angles haven't changed!! Saves a lot of effort!!
        if (tx, ty, tz) is self.angles:
            return

        rx, ry, rz = [r - a for a, r in zip(self.angles, (tx, ty, tz))]

        if origin is None: origin = self.origin

        # Calculate the new position
        pos = list(self.geom.getPosition())
        pos = [p - o for p, o in zip(pos, origin)]
        rot = rotation_matrix(rx, ry, rz)
        pos = np.dot(pos, rot)
        pos = [p + o for p, o in zip(pos, origin)]
        self.geom.setPosition(pos)

        # Update the rotation
        self.angles = (tx, ty, tz)
        self.geom.setRotation(rotation_matrix(angle=self.angles).T.reshape(9))

    def getRotation(self):
        return self.angles

    def setTransform(self, transform):
        rot, pos = transform.split()

        rot = np.reshape(rot.T, 9, 1)

        self.geom.setPosition(pos)
        self.geom.setRotation(rot)


class Counter(object):
    def __init__(self):
        self.count = 0

    def increment(self):
        self.count += 1
        return self.count

    def reset(self):
        self.count = 0


def collisionCB(pairs, geom1, geom2):
    contacts = ode.collide(geom1, geom2)
    if contacts:
        pairs.append([geom1, geom2])


def limitCB(counter, geom1, geom2):
    contacts = ode.collide(geom1, geom2)
    if contacts:
        counter.increment()


def sequencer(start, stop, step):
    i = 0
    count = (stop-start)/step
    while i <= count:
        yield start + step * i
        i += 1


# Do coarse and fine searches for limits in both forward and backward directions
def seekLimits(geometries, ignore, moves, monitors, limits, coarse=1.0, fine=0.1):

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


# The main routine to execute
def main():

    # Load config:
    colors = config.colors
    moves = config.moves
    ignore = config.ignore
    pvs = config.pvs
    config_limits = config.hardlimits

    # Create space objects for the live and rendered world
    space = ode.Space()
    renderspace = ode.Space()

    # Create and populate lists of geometries
    geometries = []
    rendergeometries = []
    for i, geometry in enumerate(config.geometries):
        geometries.append(GeometryBox(space, color=colors[i % len(colors)], **geometry))
        rendergeometries.append(GeometryBox(renderspace, color=colors[i % len(colors)], **geometry))

    # Create and populate two lists of monitors
    monitors = []
    ismoving = []
    for pv in pvs:
        monitor = Monitor(pv + ".DRBV")
        monitor.start()
        monitors.append(monitor)

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
    first_run = True

    # Main loop
    while True:

        # Freeze the positions of our current monitors by creating some dummies
        # This stops the threads from trying to reading each monitor sequentially, and holding each other up
        frozen = [DummyMonitor(monitor.value()) for monitor in monitors]

        # Execute the move
        move_all(frozen, geometries, moves)

        # Check for collisions
        collisions = collide(geometries, ignore)

        # Check if there have been any changes to the .MOVN monitors
        fresh = any([m.fresh() for m in ismoving])
        # Check if any of the motors monitors are moving
        moving = any([m.value() for m in ismoving])

        if fresh or moving or first_run:
            # Start timing for diagnostics
            time_passed = time()

            # Seek the correct limit values
            dynamic_limits = seekLimits(geometries, ignore, moves, frozen, config_limits, coarse=10.0, fine=0.1)

            # Calculate and log the time taken to calculate
            time_passed = (time() - time_passed) * 1000
            logging.debug("Calculated limits in %d", time_passed)

            # Log the new limits
            logging.debug("New limits are " + str(dynamic_limits))

            # Set the limits according to the set_limits operating mode
            if op_mode.set_limits.is_set():
                # Apply the calculated limits
                set_limits(dynamic_limits, pvs)
            else:
                # Restore the configuration limits
                set_limits(config_limits, pvs)

            # Update the render thread parameters
            parameters.update_params(dynamic_limits, collisions, time_passed)

            # On the first run, start the renderer
            if first_run:
                renderer.start()
                first_run = False
        else:
            # Restore the configuration limits
            if op_mode.set_limits.is_set() is False:
                set_limits(config_limits, pvs)

        # If there has been a collision:
        if any(collisions):
            # Log the collisions
            logging.debug("Collisions on %s", [i for i in np.where(collisions)[0]])
            # Stop the moving motors based on the operating mode auto_stop
            if op_mode.auto_stop.is_set():
                for moving, pv in zip(ismoving, pvs):
                    if moving:
                        set_pv(pv + '.STOP', 1)

        # Exit the program
        if op_mode.close.is_set():
            # Restore the configuration limits
            set_limits(config_limits, pvs)
            return

        # Give the CPU a break
        sleep(0.01)

# Execute main
main()
