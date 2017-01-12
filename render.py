from math import radians

import pygame
from OpenGL.GL import *
from OpenGL.GL.VERSION.GL_1_0 import glLoadMatrixd
from OpenGL.GL.exceptional import glBegin, glEnd
from OpenGL.GL.images import glDrawPixels
from OpenGL.raw.GL.VERSION.GL_1_0 import glViewport, glMatrixMode, glLoadIdentity, glEnable, glShadeModel, glClearColor, \
    glClear, glPushMatrix, glOrtho, glDisable, glPopMatrix, glRasterPos2d
from OpenGL.raw.GL.VERSION.GL_1_1 import GL_PROJECTION, GL_MODELVIEW, GL_DEPTH_TEST, GL_FLAT, GL_COLOR_MATERIAL, \
    GL_LIGHTING, GL_LIGHT0, GL_POSITION, GL_FRONT, GL_AMBIENT, GL_DIFFUSE, GL_COLOR_BUFFER_BIT, GL_DEPTH_BUFFER_BIT, \
    GL_CULL_FACE, GL_RGBA, GL_LINES
from OpenGL.raw.GL.VERSION.GL_4_0 import GL_QUADS
from OpenGL.raw.GL._types import GL_UNSIGNED_BYTE
from OpenGL.raw.GLU import gluPerspective
from genie_python.genie import set_pv
from pygame.constants import HWSURFACE, OPENGL, DOUBLEBUF, QUIT, KEYUP, K_ESCAPE, K_LEFT, K_RIGHT, K_DOWN, K_UP, K_z, \
    K_x, K_w, K_s, K_a, K_d, K_q, K_e, K_1, K_2, K_3, K_4, K_SPACE, K_RETURN

import threading
import logging

from gameobjects.matrix44 import Matrix44
from gameobjects.vector3 import Vector3


# This is super greedy on resources!! Can definitely optimise a ton!
class Grid(object):
    def __init__(self, scale=5, size=(20, 0, 20), position=(0, 0, 0), color=(0.2, 0.2, 0.2)):

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

                offset = (x, 0, z)

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


# Camera transform matrix
def initialise_camera():
    camera_matrix = Matrix44()
    camera_matrix.translate = (-700, -1400, 1800)
    #camera_matrix.translate = (-10, -25, 20)
    camera_matrix *= Matrix44.xyz_rotation(0, 0, -0.4)
    camera_matrix *= Matrix44.xyz_rotation(0.95, 0, 0)
    return camera_matrix


logging.basicConfig(level=logging.DEBUG,
                    format='%(asctime)s (%(threadName)-2s) %(message)s',
                    )

screensize = (820, 720)

import os
os.environ['SDL_VIDEO_WINDOW_POS'] = "%d,%d" % (5, 25)

clock = pygame.time.Clock()

# Need a toggle to allow moving away from a crash
stopMotors = False
autoRestart = False

heartbeat = 0
time_passed = 0


font = None



camera_matrix = initialise_camera()

# Initialize speeds and directions for camera
rotation_direction = Vector3()
rotation_speed = radians(90.0)
movement_direction = Vector3()
movement_speed = 50.0

# Make a grid
grid = Grid(scale=1, position=(-11, 0, -11), size=(22, 0, 22))


def glinit():
    pygame.init()

    screen = pygame.display.set_mode(screensize, HWSURFACE | OPENGL | DOUBLEBUF)

    global font
    font = pygame.font.SysFont("consolas", 18)

    pygame.display.set_caption("Collision Monitor")

    # set the screen size
    glViewport(0, 0, screensize[0], screensize[1])
    glMatrixMode(GL_PROJECTION)
    glLoadIdentity()
    # FOV angle, aspect ratio, near clipping plane, far clipping plane
    gluPerspective(60.0, float(screensize[0]) / screensize[1], 500, 10000.)
    glMatrixMode(GL_MODELVIEW)
    glLoadIdentity()

    # setup GL stuff

    glEnable(GL_DEPTH_TEST)

    glShadeModel(GL_FLAT)
    glClearColor(0, 0, 0, 0.0)

    glEnable(GL_COLOR_MATERIAL)

    glEnable(GL_LIGHTING)
    glEnable(GL_LIGHT0)

    glLight(GL_LIGHT0, GL_POSITION, [0, 0, 0])

    glMaterial(GL_FRONT, GL_AMBIENT_AND_DIFFUSE, (0.5, 0.5, 0.5, 1.0))

    # Clear the screen, and z-buffer
    glClear(GL_COLOR_BUFFER_BIT | GL_DEPTH_BUFFER_BIT)


class Renderer(threading.Thread):
    def __init__(self, parameters, geometries, colors, monitors, pvs, moves, close):
        threading.Thread.__init__(self, name="Renderer")

        #self.geometries = [copy(geometry) for geometry in geometries]
        self.geometries = geometries

        for geometry in self.geometries:
            geometry.fill = True

        self.colors = colors
        self.monitors = monitors
        self.pvs = pvs
        self.moves = moves

        self.parameters = parameters
        self.close = close

    def run(self):
        self.close.clear()
        glinit()
        while self.close.is_set() is False:
            loop(self.parameters, self.close, [self.geometries, self.colors, self.monitors, self.pvs, self.moves])


def check_controls(close):

    global camera_matrix, stopMotors, autoRestart, time_passed

    for event in pygame.event.get():
        if event.type == QUIT:
            close.set()
    #        setLimits(config.hardlimits, self.pvs)
            return
        if event.type == KEYUP and event.key == K_ESCAPE:
            close.set()
    #        setLimits(config.hardlimits, self.pvs)
            return

    time_passed = clock.tick()
    time_passed_seconds = time_passed / 1000.

    logging.debug("Frame drawn in %d", time_passed)

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
    #if pressed[K_RETURN]:
    #    setLimits(config.hardlimits, config.pvs)

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
    light = camera_matrix.transform([0, 0, 0])
    glLight(GL_LIGHT0, GL_POSITION, light)


def square(x, y, w=50, h=50, color=(1, 0, 0)):
    glMatrixMode(GL_PROJECTION)
    glPushMatrix()
    glLoadIdentity()
    glOrtho(0, screensize[0], screensize[1], 0, 0, 1)
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


def text(x, y, string, color=(0.4, 0.4, 0.4), align="left"):
    color = [c * 255 for c in color]
    color.append(255)

    y += 18

    glMatrixMode(GL_PROJECTION)
    glPushMatrix()
    glLoadIdentity()
    glOrtho(0, screensize[0], screensize[1], 0, 0, 1)
    glMatrixMode(GL_MODELVIEW)
    glLoadIdentity()
    glDisable(GL_CULL_FACE)
    glClear(GL_DEPTH_BUFFER_BIT)
    glColor(color)

    textSurface = font.render(string, True, color, (0, 0, 0, 255))
    textData = pygame.image.tostring(textSurface, "RGBA", True)

    if align is "right":
        glRasterPos2d(x - textSurface.get_width(), y)
    else:
        glRasterPos2d(x, y)

    glDrawPixels(textSurface.get_width(), textSurface.get_height(), GL_RGBA, GL_UNSIGNED_BYTE, textData)

    glMatrixMode(GL_PROJECTION)
    glPopMatrix()
    glMatrixMode(GL_MODELVIEW)

    return textSurface.get_width() + x


def draw(parameters, geometries, colors, monitors, pvs, moves):
    softlimits, collisions, duration = parameters.get_params()

    global stopMotors, autoRestart, heartbeat, time_passed

    # Clear the screen, and z-buffer
    glClear(GL_COLOR_BUFFER_BIT | GL_DEPTH_BUFFER_BIT)

    for move, geometry in zip(moves, geometries):
        move(geometry, monitors)

    # Render!
    for geometry, collided in zip(geometries, collisions):
        if collided:
            geometry.render((0.8, 0, 0))
        else:
            geometry.render()

    #grid.render()

    # Set the normal so that the hud is lit nicely
    glNormal3dv((0, 0, 1))

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

    for i, (monitor, limit) in enumerate(zip(monitors, softlimits)):
        text(80 * 1, 70 + (30 * i), "%.2f" % monitor.value(), colors[i % len(colors)], align="right")
        text(80 * 2, 70 + (30 * i), "%.2f" % limit[0], colors[i % len(colors)], align="right")
        text(80 * 3, 70 + (30 * i), "%.2f" % limit[1], colors[i % len(colors)], align="right")

    if duration > 0:
        text(screensize[0]-10, screensize[1]-45, "%.0f" % duration, align="right")

    text(screensize[0]-10, screensize[1]-25, "%.0f" % time_passed, align="right")

    # Show a heartbeat bar
    heartticks = 100
    square(0, screensize[1]-5, screensize[0] * heartbeat/ heartticks, 5, (0.3, 0.3, 0.3))
    if heartbeat > heartticks:
        heartbeat = 0
        # Need to return for sensible profiling
        # return
    else:
        heartbeat += 1

    # Show the screen
    pygame.display.flip()

    pygame.time.wait(10)


def loop(parameters, close, args):
    check_controls(close)
    if parameters.stale is False:

        # wait for fresh values??
        draw(parameters, *args)


class RenderParams(object):
    def __init__(self):
        self.lock = threading.Lock()
        self.softlimits = []
        self.collisions = []
        self.duration = None
        self.stale = True

    def update_params(self, softlimits, collisions, duration):
        with self.lock:
            logging.debug("Acquired lock for update")
            self.softlimits = softlimits
            self.collisions = collisions
            self.duration = duration

            if self.stale:
                self.stale = False
                pass

    def get_params(self):
        with self.lock:
            logging.debug("Acquired lock for read")
            #self.stale = True
            return self.softlimits, self.collisions, self.duration










