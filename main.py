import numpy as np
import ode
import pygame
from OpenGL.GL import *
from genie_python.genie_startup import *
from time import sleep, time

import config
from gameobjects.vector3 import *
from monitor import Monitor, DummyMonitor
import render
import threading
import logging


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

    normals = [(0.0, 0.0, +1.0),  # front
               (0.0, 0.0, -1.0),  # back
               (+1.0, 0.0, 0.0),  # right
               (-1.0, 0.0, 0.0),  # left
               (0.0, +1.0, 0.0),  # top
               (0.0, -1.0, 0.0)]  # bottom

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
        rot = [[R[0], R[3], R[6], 0.],
               [R[1], R[4], R[7], 0.],
               [R[2], R[5], R[8], 0.],
               [x, y, z, 1.0]]
        rot = np.array(rot)

        if self.fill:
            # Draw all 6 faces of the cube
            glBegin(GL_QUADS)

            for face_no in xrange(self.num_faces):
                glNormal3dv(self.normals[face_no])

                v1, v2, v3, v4 = self.vertex_indices[face_no]

                glVertex(vertices[v1])
                glVertex(vertices[v2])
                glVertex(vertices[v3])
                glVertex(vertices[v4])

            glEnd()
        else:
            # Draw all 12 edges of the cube
            glBegin(GL_LINES)

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


#### Not needed but has some tricks in it
class Map(object):
    def __init__(self):

        map_surface = pygame.image.load("map.png")
        map_surface.lock()

        w, h = map_surface.get_size()

        self.cubes = []

        # Create a cube for every non-white pixel
        for y in range(h):
            for x in range(w):

                r, g, b, a = map_surface.get_at((x, y))

                if (r, g, b) != (255, 255, 255):
                    gl_col = (r / 255.0, g / 255.0, b / 255.0)
                    position = (float(x), 0.0, float(y))
                    cube = GeometryBox(position, gl_col)
                    self.cubes.append(cube)

        map_surface.unlock()

        self.display_list = None

    def render(self):

        if self.display_list is None:

            # Create a display list
            self.display_list = glGenLists(1)
            glNewList(self.display_list, GL_COMPILE)

            # Draw the cubes
            for cube in self.cubes:
                cube.render()

            # End the display list
            glEndList()

        else:

            # Render the display list
            glCallList(self.display_list)


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


def seekLimits(geometries, ignore, moves, monitors, ismoving, limits, coarse=1.0, fine=0.1):
    softlimits = []

    dofineseek = True
    if fine is None:
        dofineseek = False
        fine = 0.01

    for i in range(len(limits)):
        softlimits.append(list(limits[i][:]))
        dummies = [DummyMonitor(monitor.value()) for monitor in monitors]

        min = np.min(limits[i])
        max = np.max(limits[i])

        # Do coarse seek
        # Seek backwards to the closest crash/limit
        if min < dummies[i].value:
            sequence = np.arange(dummies[i].value(), min-coarse, -coarse)
            #sequence = sequencer(dummies[i].value() - coarse, min, -coarse)
            for value in sequence:
                dummies[i].update(value)
                # Move to the new position
                for move, geometry in zip(moves, geometries):
                    move(geometry, dummies)
                # Check for collisions
                collisions = collide(geometries, ignore)
                if any(collisions):
                    if dofineseek:
                        sequence = np.arange(value, value + coarse, fine)
                        #sequence = sequencer(value, value + coarse, fine)
                        for value in sequence:
                            dummies[i].update(value)
                            # Move to the new position
                            for move, geometry in zip(moves, geometries):
                                move(geometry, dummies)
                            # Check for collisions
                            collisions = collide(geometries, ignore)
                            if not any(collisions):
                                break
                    softlimits[i][0] = value
                    break
        else:
            softlimits[i][0] = dummies[i].value()

        # Seek forwards to the closest crash/limit
        if max > dummies[i].value():
            sequence = np.arange(dummies[i].value(), max+coarse, coarse)
            #sequence = sequencer(dummies[i].value() + coarse, max, coarse)
            for value in sequence:
                dummies[i].update(value)
                # Move to the new position
                for move, geometry in zip(moves, geometries):
                    move(geometry, dummies)
                # Check for collisions
                collisions = collide(geometries, ignore)
                if any(collisions):
                    if dofineseek:
                        sequence = np.arange(value, value - coarse, -fine)
                        #sequence = sequencer(value, value - coarse, -fine)
                        for value in sequence:
                            dummies[i].update(value)
                            # Move to the new position
                            for move, geometry in zip(moves, geometries):
                                move(geometry, dummies)
                            # Check for collisions
                            collisions = collide(geometries, ignore)
                            if not any(collisions):
                                break
                    softlimits[i][1] = value
                    break
        else:
            softlimits[i][1] = dummies[i].value()

        if softlimits[i][0] < min:
            softlimits[i][0] = min

        if softlimits[i][1] > max:
            softlimits[i][1] = max


    # Restore positions
    for move, geometry in zip(moves, geometries):
        move(geometry, monitors)

    return softlimits


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


def setLimits(limits, pvs):
    for limit, pv in zip(limits, pvs):
        set_pv(pv + '.DLLM', np.min(limit))
        set_pv(pv + '.DHLM', np.max(limit))


def run():

    # Colors!!
    colors = config.colors

    moves = config.moves
    ignore = config.ignore
    pvs = config.pvs
    hardlimits = config.hardlimits

    # Create a space object for the live world
    space = ode.Space()

    # Create and populate lists of geometries
    geometries = []
    rendergeometries = []
    for i, geometry in enumerate(config.geometries):
        geometries.append(GeometryBox(space, color=colors[i % len(colors)], **geometry))
        rendergeometries.append(GeometryBox(space, color=colors[i % len(colors)], **geometry))

    # Create and populate a list of monitors
    monitors = []
    ismoving = []
    for pv in pvs:
        monitor = Monitor(pv + ".DRBV")
        monitor.start()
        monitors.append(monitor)

        moving = Monitor(pv + ".MOVN")
        moving.start()
        ismoving.append(moving)

    close = threading.Event()
    parameters = render.RenderParams()
    renderer = render.Renderer(parameters, rendergeometries, colors, monitors, pvs, moves, close)
    renderer.daemon = True
    renderer.start()

    collisions = collide(geometries, ignore)

    softlimits = seekLimits(geometries, ignore, moves, monitors, ismoving, hardlimits, coarse=1.0, fine=0.1)
    setLimits(softlimits, pvs)

    parameters.update_params(softlimits, collisions, 0)

    while True:

        for move, geometry in zip(moves, geometries):
            move(geometry, monitors)

        # Check for collisions
        collisions = collide(geometries, ignore)

        if any([m.value() for m in ismoving]):
            time_passed = time()

            # Seek the correct limit values
            softlimits = seekLimits(geometries, ignore, moves, monitors, ismoving, hardlimits, coarse=1.0, fine=0.1)
            setLimits(softlimits, pvs)

            logging.debug("New limits are " + str(softlimits))

            time_passed = (time() - time_passed) * 1000
            logging.debug("Calculated limits in %d", time_passed)

            parameters.update_params(softlimits, collisions, time_passed)

        if any(collisions):
            for moving, pv in zip(ismoving, pvs):
                if moving:
                    #set_pv(pv + '.STOP', 1)
                    pass

        if close.is_set():
            setLimits(hardlimits, pvs)
            return

        sleep(0.01)



run()
