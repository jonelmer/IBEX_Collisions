SCREEN_SIZE = (800, 600)

from math import radians

from OpenGL.GL import *
from OpenGL.GLU import *
from OpenGL.GLUT import *

import pygame
from pygame.locals import *

from gameobjects.matrix44 import *
from gameobjects.vector3 import *

import ode

import numpy as np
import copy

from genie_python.genie_startup import *

from monitor import Monitor, MonitorQueue


def resize(width, height):
    glViewport(0, 0, width, height)
    glMatrixMode(GL_PROJECTION)
    glLoadIdentity()
    gluPerspective(60.0, float(width) / height, .1, 1000.)
    glMatrixMode(GL_MODELVIEW)
    glLoadIdentity()


def rotation_matrix(rx=0, ry=0, rz=0, angle=None):
    if angle: rz, ry, rz = angle
    Rx = np.array([[1, 0, 0], [0, cos(rx), -sin(rx)], [0, sin(rx), cos(rx)]])
    Ry = np.array([[cos(ry), 0, -sin(ry)], [0, 1, 0], [sin(ry), 0, cos(ry)]])
    Rz = np.array([[cos(rz), -sin(rz), 0], [sin(rz), cos(rz), 0], [0, 0, 1]])
    return np.dot(Rx, np.dot(Ry, Rz))


def init():
    glEnable(GL_DEPTH_TEST)

    glShadeModel(GL_FLAT)
    glClearColor(0, 0, 0, 0.0)

    glEnable(GL_COLOR_MATERIAL)

    glEnable(GL_LIGHTING)
    glEnable(GL_LIGHT0)
    glLight(GL_LIGHT0, GL_POSITION, (0, 1, 1, 0))


class GeometryBox(object):
    def __init__(self, world, space, position, size=(1, 1, 1), color=(1, 1, 1), origin=(0, 0, 0), angle=(0, 0, 0), oversize=1):

        # self.position = list(position)
        self.color = color

        # Create body
        self.body = ode.Body(world)
        # M = ode.Mass()
        # M.setBox(density, lx, ly, lz)
        # body.setMass(M)

        # Set parameters for drawing the body
        self.body.shape = "box"
        self.size = size
        # self.body.color = color
        self.body.setPosition(position)

        # Create a box geom for collision detection
        self.geom = ode.GeomBox(space, lengths=[s * oversize for s in self.size])
        self.geom.setBody(self.body)

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
        #vertices = [tuple(Vector3(v) + self.body.getPosition()) for v in vertices]

        x, y, z = self.body.getPosition()
        R = self.body.getRotation()
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
                    #print rot
                    #print np.dot(point, rot)

                    glVertex(np.dot(point, rot))
                    #glVertex(vertices[i])
            glEnd()

    def move(self, x=0, y=0, z=0):
        pos = self.body.getPosition()
        pos = tuple([pos[0] + x, pos[1] + y, pos[2] + z])
        self.body.setPosition(pos)

    def setPosition(self, x=None, y=None, z=None):
        pos = list(self.body.getPosition())
        if x is not None:
            pos[0] = x
        if y is not None:
            pos[1] = y
        if z is not None:
            pos[2] = z
        self.body.setPosition(pos)

    def getPosition(self):
        return self.body.getPosition()

    def setRotation(self, tx=0, ty=0, tz=0, origin=None, angles=None):
        if angles:
            tx, ty, tx = angles
        rx, ry, rz = [r - a for a, r in zip(self.angles, (tx, ty, tz))]

        if origin is None: origin = self.origin

        # Calculate the new position
        pos = list(self.body.getPosition())
        pos = [p - o for p, o in zip(pos, origin)]
        rot = rotation_matrix(rx, ry, rz)
        pos = np.dot(pos, rot)
        pos = [p + o for p, o in zip(pos, origin)]
        self.body.setPosition(pos)

        # Update the rotation
        self.angles = (tx, ty, tz)
        self.body.setRotation(rotation_matrix(angle=self.angles).T.reshape(9))

    def getRotation(self):
        return self.angles


class Grid(object):
    def __init__(self, scale=5, size=(20, 0, 20), position = (0, 0, 0), color=(0.2, 0.2, 0.2)):

        # self.position = list(position)
        self.color = color
        self.position = position
        self.size = size
        self.scale = scale

    vertices = [(0.0, 0.0, 0.0),
                (1.0, 0.0, 0.0),
                (1.0, 0.0, 1.0),
                (0.0, 0.0, 1.0)]

    edge_indices = [(0, 1),
                    (1, 2),
                    (2, 3),
                    (3, 0)]

    def render(self):

        glColor(self.color)

        glBegin(GL_LINES)

        for x in xrange(0, self.size[0], self.scale):
            for z in xrange(0, self.size[2], self.scale):

                offset = (x, 0, z);

                # Adjust all the vertices so that the grid is at self.position
                vertices = self.vertices
                vertices = [tuple(Vector3(v) * self.scale) for v in vertices]
                vertices = [tuple(Vector3(v) + self.position) for v in vertices]
                vertices = [tuple(Vector3(v) + offset) for v in vertices]

                for edge_no in xrange(4):
                    v1, v2 = self.edge_indices[edge_no]

                    glVertex(vertices[v1])
                    glVertex(vertices[v2])

        glEnd()


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


class DummyMonitor(object):
    def __init__(self, value):
        self.setValue(value)

    def setValue(self, value):
        self.value = value


def seekLimits(space, geometries, ignore, moves, monitors, limits, coarse=1.0, fine=0.01):
    counter = Counter()
    softlimits = []

    dofineseek = True
    if fine is None:
        dofineseek = False
        fine = 0.01

    for i in range(len(limits)):
        softlimits.append(list(limits[i][:]))
        dummies = [DummyMonitor(monitor.value) for monitor in monitors]

        min = np.min(limits[i])
        max = np.max(limits[i])

        # Do coarse seek
        # Seek backwards to the closest crash/limit
        if min < dummies[i].value:
            sequence = np.arange(dummies[i].value-coarse, min, -coarse)
            for value in sequence:
                dummies[i].setValue(value)
                # Move to the new position
                for move, geometry in zip(moves, geometries):
                    move(geometry, dummies)
                # Check for collisions
                #counter.reset()
                #space.collide(counter, limitCB)
                #if counter.count > 0:
                collisions = collide(geometries, ignore)
                if any(collisions):
                    if dofineseek:
                        sequence = np.arange(value, value + coarse, fine)
                        for value in sequence:
                            dummies[i].setValue(value)
                            # Move to the new position
                            for move, geometry in zip(moves, geometries):
                                move(geometry, dummies)
                            # Check for collisions
                            #counter.reset()
                            #space.collide(counter, limitCB)
                            #if counter.count == 0:
                            collisions = collide(geometries, ignore)
                            if not any(collisions):
                                break
                    softlimits[i][0] = value
                    break
        else:
            softlimits[i][0] = dummies[i].value

        # Seek forwards to the closest crash/limit
        if max > dummies[i].value:
            sequence = np.arange(dummies[i].value+coarse, max, coarse)
            for value in sequence:
                dummies[i].setValue(value)
                # Move to the new position
                for move, geometry in zip(moves, geometries):
                    move(geometry, dummies)
                # Check for collisions
                #counter.reset()
                #space.collide(counter, limitCB)
                #if counter.count > 0:
                collisions = collide(geometries, ignore)
                if any(collisions):
                    if dofineseek:
                        sequence = np.arange(value, value - coarse, -fine)
                        for value in sequence:
                            dummies[i].setValue(value)
                            # Move to the new position
                            for move, geometry in zip(moves, geometries):
                                move(geometry, dummies)
                            # Check for collisions
                            #counter.reset()
                            #space.collide(counter, limitCB)
                            #if counter.count == 0:
                            collisions = collide(geometries, ignore)
                            if not any(collisions):
                                break
                    softlimits[i][1] = value
                    break
        else:
            softlimits[i][1] = dummies[i].value

        # Restore positions
        for move, geometry in zip(moves, geometries):
            move(geometry, monitors)

    return softlimits


# This ignores geometries we have said we don't care about
def collide(geometries, ignore):
    collisions = [False] * len(geometries)
    for i, geom1 in enumerate(geometries):
        for j, geom2 in enumerate(geometries[i:]):
            if not ([i, i + j] in ignore or [i + j, i] in ignore):
                contacts = ode.collide(geom1.geom, geom2.geom)
                if contacts:
                    collisions[i] = True
                    collisions[i + j] = True
    #print collisions
    return collisions


def setLimits(limits, pvs):
    for limit, pv in zip(limits, pvs):
        set_pv(pv + '.LLM', np.min(limit))
        set_pv(pv + '.HLM', np.max(limit))


def square(x, y, w=50, h=50, color=(1, 0, 0)):
    glMatrixMode(GL_PROJECTION)
    glPushMatrix()
    glLoadIdentity()
    glOrtho(0, SCREEN_SIZE[0], SCREEN_SIZE[1], 0, 0, 1)
    glMatrixMode(GL_MODELVIEW)
    glLoadIdentity()
    glDisable(GL_CULL_FACE)
    glClear(GL_DEPTH_BUFFER_BIT)
    glColor(color)
    glBegin(GL_QUADS)
    glVertex((x, y))
    glVertex((x + w, y))
    glVertex((x + w, y + h))
    glVertex((x, y + h))
    glEnd()
    glMatrixMode(GL_PROJECTION)
    glPopMatrix()
    glMatrixMode(GL_MODELVIEW)


def text(x, y, string, color=(0.4, 0.4, 0.4), size=32):
    color = [c * 255 for c in color]
    color.append(255)

    y = y + size*0.7

    glMatrixMode(GL_PROJECTION)
    glPushMatrix()
    glLoadIdentity()
    glOrtho(0, SCREEN_SIZE[0], SCREEN_SIZE[1], 0, 0, 1)
    glMatrixMode(GL_MODELVIEW)
    glLoadIdentity()
    glDisable(GL_CULL_FACE)
    glClear(GL_DEPTH_BUFFER_BIT)
    glColor(color)

    font = pygame.font.Font(None, size)
    textSurface = font.render(string, True, color, (0, 0, 0, 255))
    textData = pygame.image.tostring(textSurface, "RGBA", True)
    glRasterPos2d(x, y)
    glDrawPixels(textSurface.get_width(), textSurface.get_height(), GL_RGBA, GL_UNSIGNED_BYTE, textData)

    glMatrixMode(GL_PROJECTION)
    glPopMatrix()
    glMatrixMode(GL_MODELVIEW)

    return textSurface.get_width()


def run():
    pygame.init()
    screen = pygame.display.set_mode(SCREEN_SIZE, HWSURFACE | OPENGL | DOUBLEBUF)

    pygame.display.set_caption("Collision Monitor")

    resize(*SCREEN_SIZE)
    init()

    print(SCREEN_SIZE)

    clock = pygame.time.Clock()

    glMaterial(GL_FRONT, GL_AMBIENT, (0.1, 0.1, 0.1, 1.0))
    glMaterial(GL_FRONT, GL_DIFFUSE, (1.0, 1.0, 1.0, 1.0))

    # Create a world object
    world = ode.World()

    # Create a space object for the live world
    space = ode.Space()
    stackspace = ode.Space()

    # Need a toggle to allow moving away from a crash
    stopMotors = False
    autoRestart = False

    # Heartbeat bool - toggles each frame
    heartbeat = 0

    # Colors!!
    colors = [(0, 1, 1),
              (1, 1, 0),
              (1, 0, 1)]

    # ------------------------------------------------------------------------------------------------------------------
    # Config happens here:

    # Define the geometry of the system
    geometries = []
    #geometries.append(GeometryBox(world, space, (0, 1, 10), color=(1, 0, 0), size=(2.0, 2.0, 2.0)))
    #geometries.append(GeometryBox(world, space, (10, 1, 0), color=(0, 1, 0), size=(2.0, 2.0, 2.0)))
    #geometries.append(GeometryBox(world, space, (5, 1, 10), color=(0, 0, 1), size=(2.0, 2.0, 2.0), origin=(10, 0, 10)))
    geometries.append(
        GeometryBox(world, stackspace, (0, 3, 0), color=colors[0], size=(2, 2, 2), origin=(10, 0, 10), oversize=1))
    geometries.append(GeometryBox(world, stackspace,
                        (0, 1.5, 10), color=colors[1], size=(2.0, 1.0, 22.0), origin=(10, 0, 10), oversize=1))
    geometries.append(GeometryBox(world, stackspace,
                                  (10, 0.5, 10), color=colors[2], size=(22.0, 1.0, 22.0), origin=(10, 0, 10),
                                  oversize=1))
    geometries.append(
        GeometryBox(world, stackspace, (20, 3.1, 10), color=(1, 1, 1), size=(10, 2, 2), oversize=1))

    # List of pairs to ignore
    ignore = [[0, 1], [0, 2], [1, 2]]

    # Generate move functions
    moves = []

    #def move(geometry, monitors):
    #    geometry.setPosition(x=monitors[0].value)
    #moves.append(move)

    #def move(geometry, monitors):
    #    geometry.setPosition(z=monitors[1].value)
    #moves.append(move)

    #def move(geometry, monitors):
    #    geometry.setRotation(ty=radians(monitors[2].value))
    #moves.append(move)

    def move(geometry, monitors):
        geometry.setRotation(angles=(0, 0, 0))
        geometry.setPosition(x=monitors[0].value, z=monitors[1].value)
        geometry.setRotation(ty=radians(monitors[2].value))
    moves.append(move)

    def move(geometry, monitors):
        geometry.setRotation(angles=(0, 0, 0))
        geometry.setPosition(x=monitors[0].value)
        geometry.setRotation(ty=radians(monitors[2].value))
    moves.append(move)

    def move(geometry, monitors):
        geometry.setRotation(ty=radians(monitors[2].value))
    moves.append(move)

    # Attach monitors to readbacks
    pvs = ["TE:NDW1720:MOT:MTR0201", "TE:NDW1720:MOT:MTR0202", "TE:NDW1720:MOT:MTR0203"]
    #pvs = ["TE:NDW1720:MOT:MTR0101", "TE:NDW1720:MOT:MTR0102", "TE:NDW1720:MOT:MTR0103"]
    monitors = []
    for pv in pvs:
        monitor = Monitor(pv + ".RBV")
        monitor.start()
        monitors.append(monitor)

    hardlimits = [[0.0, 20.0],
                  [0.0, 20.0],
                  [0.0, 360.0]]

    # ------------------------------------------------------------------------------------------------------------------

    # Make a grid
    grid = Grid(scale=1, position=(-1, 0, -1), size=(22, 0, 22))

    # Camera transform matrix
    def initialise_camera():
        camera_matrix = Matrix44()
        camera_matrix.translate = (15.0, 15.0, 30.0)
        camera_matrix *= Matrix44.xyz_rotation(0, radians(15), 0)
        camera_matrix *= Matrix44.xyz_rotation(radians(-35), 0, 0)
        return camera_matrix

    camera_matrix = initialise_camera()

    # Initialize speeds and directions for camera
    rotation_direction = Vector3()
    rotation_speed = radians(90.0)
    movement_direction = Vector3()
    movement_speed = 5.0

    collisions = Counter()
    collisionPairs = []

    while True:

        for event in pygame.event.get():
            if event.type == QUIT:
                setLimits(hardlimits, pvs)
                return
            if event.type == KEYUP and event.key == K_ESCAPE:
                setLimits(hardlimits, pvs)
                return

                # Clear the screen, and z-buffer
        glClear(GL_COLOR_BUFFER_BIT | GL_DEPTH_BUFFER_BIT)

        time_passed = clock.tick()
        time_passed_seconds = time_passed / 1000.

        #print(time_passed)

        pressed = pygame.key.get_pressed()

        # Reset rotation and movement directions
        rotation_direction.set(0.0, 0.0, 0.0)
        movement_direction.set(0.0, 0.0, 0.0)

        # Modify direction vectors for key presses
        if pressed[K_LEFT]:
            rotation_direction.y = +1.0
        elif pressed[K_RIGHT]:
            rotation_direction.y = -1.0
        if pressed[K_DOWN]:
            rotation_direction.x = -1.0
        elif pressed[K_UP]:
            rotation_direction.x = +1.0
        if pressed[K_z]:
            rotation_direction.z = -1.0
        elif pressed[K_x]:
            rotation_direction.z = +1.0
        if pressed[K_w]:
            movement_direction.z = -1.0
        elif pressed[K_s]:
            movement_direction.z = +1.0
        if pressed[K_a]:
            movement_direction.x = -1.0
        elif pressed[K_d]:
            movement_direction.x = +1.0
        if pressed[K_q]:
            movement_direction.y = -1.0
        elif pressed[K_e]:
            movement_direction.y = +1.0
        if pressed[K_1]:
            stopMotors = True
        elif pressed[K_2]:
            stopMotors = False
        if pressed[K_3]:
            autoRestart = True
        elif pressed[K_4]:
            autoRestart = False
        if pressed[K_SPACE]:
            camera_matrix = initialise_camera()
        if pressed[K_RETURN]:
            setLimits(hardlimits, pvs)

        # Calculate rotation matrix and multiply by camera matrix
        rotation = rotation_direction * rotation_speed * time_passed_seconds
        rotation_matrix = Matrix44.xyz_rotation(*rotation)
        camera_matrix *= rotation_matrix

        # Calculate forward movement and add it to camera matrix translate
        heading = Vector3(camera_matrix.forward)
        movement = heading * movement_direction.z * movement_speed
        forward = movement * time_passed_seconds
        camera_matrix.translate += forward

        # Calculate strafe movement and add it to camera matrix translate
        heading = Vector3(camera_matrix.right)
        movement = heading * movement_direction.x * movement_speed
        right = movement * time_passed_seconds
        camera_matrix.translate += right

        # Calculate strafe movement and add it to camera matrix translate
        heading = Vector3(camera_matrix.up)
        movement = heading * movement_direction.y * movement_speed
        up = movement * time_passed_seconds
        camera_matrix.translate += up

        # Upload the inverse camera matrix to OpenGL
        glLoadMatrixd(camera_matrix.get_inverse().to_opengl())

        # Light must be transformed as well
        glLight(GL_LIGHT0, GL_POSITION, (0, 1.5, 1, 0))

        for move, geometry in zip(moves, geometries):
            move(geometry, monitors)

        # Check for collisions
        #collisionPairs = []
        #stackspace.collide(collisionPairs, collisionCB)

        #collisions = [geometry.geom in [geom for pair in collisionPairs for geom in pair] for geometry in geometries]

        collisions = collide(geometries, ignore)

        #print collisions

        # Render!!
        for geometry, collided in zip(geometries, collisions):
            if collided:
                geometry.render((0.8, 0, 0))
            else:
                geometry.render()
            pass

        grid.render()

        # Seek the correct limit values
        softlimits = seekLimits(stackspace, geometries, ignore, moves, monitors, hardlimits, fine=0.01)
        setLimits(softlimits, pvs)

        # Display the status icon
        if any(collisions):
            if stopMotors:
                square(10, 10)
                for pv in pvs:
                    set_pv(pv + ".STOP", 1)
                text(70, 10, "Collision detected!")
            else:
                square(10, 10, color=(1, 0.5, 0))
                text(70, 10, "Collision ignored!")
        else:
            if stopMotors:
                square(10, 10, color=(0, 1, 0))
                text(70, 10, "Detecting collisions")
            else:
                square(10, 10, color=(1, 1, 0))
                stopMotors = autoRestart
                text(70, 10, "Ignoring collisions")

        if autoRestart:
            text(70, 35, "Auto-restart on")
        else:
            text(70, 35, "Auto-restart off")

        # Print some helpful numbers:
        for i, (monitor, limit) in enumerate(zip(monitors, softlimits)):
            width = text(10, 70+(30*i), "%.2f" % monitor.value, colors[i])
            width += text(20 + max(width, 70), 70+(30*i), "%.2f" % limit[0], colors[i])
            width += text(30 + max(width, 70*2), 70+(30*i), "%.2f" % limit[1], colors[i])

        # Show a heartbeat bar
        square(10, 565, 5*heartbeat, 25, (0.2, 0.2, 0.2))
        if heartbeat > 10:
            heartbeat = 0
        else:
            heartbeat += 1

        # Show the screen
        pygame.display.flip()

        #pygame.time.wait(10)

run()
