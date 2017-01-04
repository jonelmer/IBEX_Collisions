import threading
from copy import copy
from math import radians

import pygame
from OpenGL.GL import glLight, glMaterial, glColor, glVertex
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

from gameobjects.matrix44 import Matrix44
from gameobjects.vector3 import Vector3


class Renderer(object):
    def __init__(self, geometries, colors, monitors, pvs, screensize=(800, 600)):
        self.geometries = [copy(geometry) for geometry in geometries]
        self.colors = colors
        self.monitors = monitors
        self.pvs = pvs
        (self.width, self.height) = screensize

        self.lock = threading.Lock()
        self.running = False
        self.softlimits = []
        self.collisions = []

        pygame.init()
        self.screen = pygame.display.set_mode((self.width, self.height), HWSURFACE | OPENGL | DOUBLEBUF)

        self.font = pygame.font.SysFont("consolas", 18)

        pygame.display.set_caption("Collision Monitor")

        # set the screen size
        glViewport(0, 0, self.width, self.height)
        glMatrixMode(GL_PROJECTION)
        glLoadIdentity()
        gluPerspective(60.0, float(self.width) / self.height, .1, 1000.)
        glMatrixMode(GL_MODELVIEW)
        glLoadIdentity()

        # setup GL stuff
        glEnable(GL_DEPTH_TEST)

        glShadeModel(GL_FLAT)
        glClearColor(0, 0, 0, 0.0)

        glEnable(GL_COLOR_MATERIAL)

        glEnable(GL_LIGHTING)
        glEnable(GL_LIGHT0)
        glLight(GL_LIGHT0, GL_POSITION, (0, 1, 1, 0))

        self.clock = pygame.time.Clock()

        glMaterial(GL_FRONT, GL_AMBIENT, (0.1, 0.1, 0.1, 1.0))
        glMaterial(GL_FRONT, GL_DIFFUSE, (1.0, 1.0, 1.0, 1.0))

        # Need a toggle to allow moving away from a crash
        self.stopMotors = False
        self.autoRestart = False

        self.heartbeat = 0
        self.time_passed = 0

        self.camera_matrix = self.initialise_camera()

        # Initialize speeds and directions for camera
        self.rotation_direction = Vector3()
        self.rotation_speed = radians(90.0)
        self.movement_direction = Vector3()
        self.movement_speed = 5.0

        # Make a grid
        self.grid = Grid(scale=1, position=(-11, 0, -11), size=(22, 0, 22))

    # Camera transform matrix
    def initialise_camera(self):
        camera_matrix = Matrix44()
        camera_matrix.translate = (-5.0, 20.0, 25.0)
        camera_matrix *= Matrix44.xyz_rotation(0, radians(-15), 0)
        camera_matrix *= Matrix44.xyz_rotation(radians(-35), 0, 0)
        return camera_matrix

    def check_controls(self):
        #for event in pygame.event.get():
        #    if event.type == QUIT:
        #        setLimits(config.hardlimits, self.pvs)
        #        return
        #    if event.type == KEYUP and event.key == K_ESCAPE:
        #        setLimits(config.hardlimits, self.pvs)
        #        return

                # Clear the screen, and z-buffer
        glClear(GL_COLOR_BUFFER_BIT | GL_DEPTH_BUFFER_BIT)

        self.time_passed = self.clock.tick()
        time_passed_seconds = self.time_passed / 1000.

        # print(time_passed)

        pressed = pygame.key.get_pressed()

        # Reset rotation and movement directions
        self.rotation_direction.set(0.0, 0.0, 0.0)
        self.movement_direction.set(0.0, 0.0, 0.0)

        # Modify direction vectors for key presses
        if pressed[K_LEFT]:
            self.rotation_direction.y = +1.0
        elif pressed[K_RIGHT]:
            self.rotation_direction.y = -1.0
        if pressed[K_DOWN]:
            self.rotation_direction.x = -1.0
        elif pressed[K_UP]:
            self.rotation_direction.x = +1.0
        if pressed[K_z]:
            self.rotation_direction.z = -1.0
        elif pressed[K_x]:
            self.rotation_direction.z = +1.0
        if pressed[K_w]:
            self.movement_direction.z = -1.0
        elif pressed[K_s]:
            self.movement_direction.z = +1.0
        if pressed[K_a]:
            self.movement_direction.x = -1.0
        elif pressed[K_d]:
            self.movement_direction.x = +1.0
        if pressed[K_q]:
            self.movement_direction.y = -1.0
        elif pressed[K_e]:
            self.movement_direction.y = +1.0
        if pressed[K_1]:
            self.stopMotors = True
        elif pressed[K_2]:
            self.stopMotors = False
        if pressed[K_3]:
            self.autoRestart = True
        elif pressed[K_4]:
            self.autoRestart = False
        if pressed[K_SPACE]:
            self.camera_matrix = self.initialise_camera()
        #if pressed[K_RETURN]:
        #    setLimits(config.hardlimits, config.pvs)

        # Calculate rotation matrix and multiply by camera matrix
        rotation = self.rotation_direction * self.rotation_speed * time_passed_seconds
        rotation_matrix = Matrix44.xyz_rotation(*rotation)
        self.camera_matrix *= rotation_matrix

        # Calculate forward movement and add it to camera matrix translate
        heading = Vector3(self.camera_matrix.forward)
        movement = heading * self.movement_direction.z * self.movement_speed
        forward = movement * time_passed_seconds
        self.camera_matrix.translate += forward

        # Calculate strafe movement and add it to camera matrix translate
        heading = Vector3(self.camera_matrix.right)
        movement = heading * self.movement_direction.x * self.movement_speed
        right = movement * time_passed_seconds
        self.camera_matrix.translate += right

        # Calculate strafe movement and add it to camera matrix translate
        heading = Vector3(self.camera_matrix.up)
        movement = heading * self.movement_direction.y * self.movement_speed
        up = movement * time_passed_seconds
        self.camera_matrix.translate += up

        # Upload the inverse camera matrix to OpenGL
        glLoadMatrixd(self.camera_matrix.get_inverse().to_opengl())

        # Light must be transformed as well
        glLight(GL_LIGHT0, GL_POSITION, (0, 1.5, 1, 0))

    def square(self, x, y, w=50, h=50, color=(1, 0, 0)):
        glMatrixMode(GL_PROJECTION)
        glPushMatrix()
        glLoadIdentity()
        glOrtho(0, self.width, self.height, 0, 0, 1)
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

    def text(self, font, x, y, string, color=(0.4, 0.4, 0.4), align="left"):
        color = [c * 255 for c in color]
        color.append(255)

        y += 18

        glMatrixMode(GL_PROJECTION)
        glPushMatrix()
        glLoadIdentity()
        glOrtho(0, self.width, self.height, 0, 0, 1)
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

    def draw(self):
        with self.lock:
            collisions = self.collisions[:]

        # Render!
        for geometry, collided in zip(self.geometries, collisions):
            if collided:
                geometry.render((0.8, 0, 0))
            else:
                geometry.render()

        self.grid.render()

        # Display the status icon
        if any(collisions):
            if self.stopMotors:
                self.square(10, 10)
                for pv in self.pvs:
                    set_pv(pv + ".STOP", 1)
                self.text(self.font, 70, 10, "Collision detected!")
            else:
                self.square(10, 10, color=(1, 0.5, 0))
                self.text(self.font, 70, 10, "Collision ignored!")
        else:
            if self.stopMotors:
                self.square(10, 10, color=(0, 1, 0))
                self.text(self.font, 70, 10, "Detecting collisions")
            else:
                self.square(10, 10, color=(1, 1, 0))
                self.stopMotors = self.autoRestart
                self.text(self.font, 70, 10, "Ignoring collisions")

        if self.autoRestart:
            self.text(self.font, 70, 35, "Auto-restart on")
        else:
            self.text(self.font, 70, 35, "Auto-restart off")

        # Print some helpful numbers:
        with self.lock:
            limits = self.softlimits[:]

        for i, (monitor, limit) in enumerate(zip(self.monitors, limits)):
            self.text(self.font, 80 * 1, 70 + (30 * i), "%.2f" % monitor.value(), self.colors[i], align="right")
            self.text(self.font, 80 * 2, 70 + (30 * i), "%.2f" % limit[0], self.colors[i], align="right")
            self.text(self.font, 80 * 3, 70 + (30 * i), "%.2f" % limit[1], self.colors[i], align="right")

        self.text(self.font, 790, 575, "%.0f" % self.time_passed, align="right")

        # Show a heartbeat bar
        self.square(0, 595, 8 * self.heartbeat, 5, (0.3, 0.3, 0.3))
        if self.heartbeat > 100:
            self.heartbeat = 0
            # Need to return for sensible profiling
            # return
        else:
            self.heartbeat += 1

        # Show the screen
        pygame.display.flip()

        # pygame.time.wait(10)

    def loop(self):
        while True:
            self.run()

    def run(self):
        self.check_controls()
        # wait for fresh values??
        self.draw()

    def start(self):
        threading.Thread(target=self.loop).start()

    def update_params(self, softlimits, collisions):
        with self.lock:
            self.softlimits = softlimits
            self.collisions = collisions

            return
            if self.running is False:
                self.start()
                self.running = True


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


