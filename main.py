SCREEN_SIZE = (800, 600)

from math import radians

from OpenGL.GL import *
from OpenGL.GLU import *

import pygame
from pygame.locals import *

from gameobjects.matrix44 import *
from gameobjects.vector3 import *

import ode

import numpy as np

from monitor import Monitor
from simulate import SimulatedMotor


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


class Cube(object):
    def __init__(self, world, space, position, size=(1, 1, 1), color=(1, 1, 1), origin=(0, 0, 0), angle=(0, 0, 0)):

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
        self.geom = ode.GeomBox(space, lengths=self.size)
        self.geom.setBody(self.body)

        self.origin = origin
        self.angle = angle

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

    def render(self):

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
        if x:
            pos[0] = x
        if y:
            pos[1] = y
        if z:
            pos[2] = z
        self.body.setPosition(pos)

    def setRotatation(self, tx=0, ty=0, tz=0, origin=None):
        rx, ry, rz = [r - a for a, r in zip(self.angle, (tx, ty, tz))]

        if origin is None: origin = self.origin

        # Calculate the new position
        pos = list(self.body.getPosition())
        pos = [p - o for p, o in zip(pos, origin)]
        rot = rotation_matrix(rx, ry, rz)
        pos = np.dot(pos, rot)
        pos = [p + o for p, o in zip(pos, origin)]
        self.body.setPosition(pos)

        # Update the rotation
        self.angle = (tx, ty, tz)
        self.body.setRotation(rotation_matrix(angle=self.angle).T.reshape(9))



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
                    cube = Cube(position, gl_col)
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


def collision(args, geom1, geom2):
    contacts = ode.collide(geom1, geom2)
    if contacts:
        # print("Looks like a crash!")
        square(10, 10)


def simCollision(args, geom1, geom2):
    contacts = ode.collide(geom1, geom2)
    if contacts:
        # print("Looks like a crash!")
        square(70, 10, color=(1, 0.5, 0))


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
    glMatrixMode(GL_PROJECTION);
    glPopMatrix();
    glMatrixMode(GL_MODELVIEW);


def run():
    pygame.init()
    screen = pygame.display.set_mode(SCREEN_SIZE, HWSURFACE | OPENGL | DOUBLEBUF)

    pygame.display.set_caption("Collision Monitor")

    resize(*SCREEN_SIZE)
    init()

    clock = pygame.time.Clock()

    glMaterial(GL_FRONT, GL_AMBIENT, (0.1, 0.1, 0.1, 1.0))
    glMaterial(GL_FRONT, GL_DIFFUSE, (1.0, 1.0, 1.0, 1.0))

    # Create a world object
    world = ode.World()

    # Create a space object for the live world
    space = ode.Space()

    # Create a space object for the simulated world
    simulation = ode.Space()

    # Create a readback list
    readbacks = []
    readbacks.append(Cube(world, space, (0, 1, 10), color=(1, 0, 0), size=(2.0, 2.0, 2.0)))
    readbacks.append(Cube(world, space, (10, 1, 0), color=(0, 1, 0), size=(2.0, 2.0, 2.0)))
    readbacks.append(Cube(world, space, (5, 1, 10), color=(0, 0, 1), size=(2.0, 2.0, 2.0), origin=(10, 0, 10)))

    # Create ghost cube list
    ghosts = []
    ghosts.append(Cube(world, simulation, (0, 1, 10), color=(1, 0.8, 0.8), size=(2.0, 2.0, 2.0)))
    ghosts.append(Cube(world, simulation, (10, 1, 0), color=(0.8, 1, 0.8), size=(2.0, 2.0, 2.0)))
    ghosts.append(Cube(world, simulation, (5, 1, 10), color=(0.8, 0.8, 1), size=(2.0, 2.0, 2.0), origin=(10, 0, 10)))

    # Attach monitors to readbacks
    monitors = []
    monitors.append(Monitor("TE:NDW1720:MOT:MTR0101.RBV"))
    monitors.append(Monitor("TE:NDW1720:MOT:MTR0102.RBV"))
    monitors.append(Monitor("TE:NDW1720:MOT:MTR0103.RBV"))
    for monitor in monitors: monitor.start()

    # Attach monitors to setpoints
    setpoints = []
    setpoints.append(Monitor("TE:NDW1720:MOT:MTR0101"))
    setpoints.append(Monitor("TE:NDW1720:MOT:MTR0102"))
    setpoints.append(Monitor("TE:NDW1720:MOT:MTR0103"))

    for monitor in setpoints: monitor.start()

    # Create some simulated motors
    motors = []
    motors.append(SimulatedMotor())
    motors.append(SimulatedMotor())
    motors.append(SimulatedMotor(speed=32.76800, acceleration=32.76800))

    # Generate some profiles
    profiles = []
    profiles.append(np.append(motors[0].move(0, 20), motors[0].move(20, 0)))
    profiles.append(np.append(motors[1].move(2, 18), motors[1].move(18, 2)))
    profiles.append(np.append(np.append(motors[2].move(0, 90), motors[2].move(90, 180)), motors[2].move(180, 360)))


    # Make a grid
    grid = Grid(scale=1, position=(0, 0, 0))

    # Camera transform matrix
    camera_matrix = Matrix44()
    camera_matrix.translate = (15.0, 10.0, 30.0)
    camera_matrix *= Matrix44.xyz_rotation(0, radians(15), 0)
    camera_matrix *= Matrix44.xyz_rotation(radians(-25), 0, 0)

    # Initialize speeds and directions
    rotation_direction = Vector3()
    rotation_speed = radians(90.0)
    movement_direction = Vector3()
    movement_speed = 5.0

    move_box = 0

    counter = 0

    while True:

        for event in pygame.event.get():
            if event.type == QUIT:
                return
            if event.type == KEYUP and event.key == K_ESCAPE:
                return

                # Clear the screen, and z-buffer
        glClear(GL_COLOR_BUFFER_BIT | GL_DEPTH_BUFFER_BIT);

        time_passed = clock.tick()
        time_passed_seconds = time_passed / 1000.

        pressed = pygame.key.get_pressed()

        # Reset rotation and movement directions
        rotation_direction.set(0.0, 0.0, 0.0)
        movement_direction.set(0.0, 0.0, 0.0)
        move_box = 0

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
        if pressed[K_PLUS] or pressed[K_EQUALS]:
            move_box = 1
        elif pressed[K_MINUS]:
            move_box = -1

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

        # Upload the inverse camera matrix to OpenGL
        glLoadMatrixd(camera_matrix.get_inverse().to_opengl())

        # Light must be transformed as well
        glLight(GL_LIGHT0, GL_POSITION, (0, 1.5, 1, 0))

        # Move the cube
        readbacks[0].move(move_box * movement_speed * time_passed_seconds)

        # Move the cubes

        readbacks[0].setPosition(x=monitors[0].value)
        readbacks[1].setPosition(z=monitors[1].value)
        readbacks[2].setRotatation(ty=radians(monitors[2].value))

        ghosts[0].setPosition(x=profiles[0][counter % len(profiles[0])])
        ghosts[1].setPosition(z=profiles[1][counter % len(profiles[1])])
        ghosts[2].setRotatation(ty=radians(profiles[2][counter % len(profiles[2])]))

        #ghosts[2].setPosition(x=1)

        # Render!!
        for cube in readbacks:
            cube.render()
        for cube in ghosts:
            cube.render()

        grid.render()

        # Check for collisions
        space.collide(None, collision)
        simulation.collide(None, simCollision)

        # Show the screen
        pygame.display.flip()

        pygame.time.wait(10)

        counter += 1

run()