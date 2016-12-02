'''

https://pythonprogramming.net/opengl-rotating-cube-example-pyopengl-tutorial/

'''

import pygame
from pygame.locals import *
from OpenGL.GL import *
from OpenGL.GLU import *
import ode

def scale_point(coord, scale):
    return list(c * s for c, s in zip(coord, scale))


def Cube(scale=(1,1,1), color = (1, 0, 0), fill = False):

    scale = list(s/2.0 for s in scale)

    vertices = (
        (1, -1, -1),
        (1, 1, -1),
        (-1, 1, -1),
        (-1, -1, -1),
        (1, -1, 1),
        (1, 1, 1),
        (-1, -1, 1),
        (-1, 1, 1)
    )

    edges = (
        (0, 1),
        (0, 3),
        (0, 4),
        (2, 1),
        (2, 3),
        (2, 7),
        (6, 3),
        (6, 4),
        (6, 7),
        (5, 1),
        (5, 4),
        (5, 7)
    )

    surfaces = (
        (0, 1, 2, 3),
        (3, 2, 7, 6),
        (6, 7, 5, 4),
        (4, 5, 1, 0),
        (1, 5, 7, 2),
        (4, 0, 3, 6)
    )

    colors = (
        (1, 0, 0),
        (0, 1, 0),
        (0, 0, 1),
        (0, 1, 0),
        (1, 1, 1),
        (0, 1, 1),
        (1, 0, 0),
        (0, 1, 0),
        (0, 0, 1),
        (1, 0, 0),
        (1, 1, 1),
        (0, 1, 1),
    )

    vertices = list(scale_point(v,scale) for v in vertices)

    if fill:
        # Faces
        glBegin(GL_QUADS)
        for surface in surfaces:
            x = 0
            for vertex in surface:
                x += 1
                glColor3fv(colors[x])
                glVertex3fv(vertices[vertex])
        glEnd()

    # Edges
    glBegin(GL_LINES)
    for edge in edges:
        for vertex in edge:
            glColor3fv(color)
            glVertex3fv(vertices[vertex])
    glEnd()

def prepare_GL(x = 800, y = 600):
    """Prepare drawing.
    """

    # Viewport
    glViewport(0, 0, x, y)

    # Initialize
    glClearColor(0, 0, 0, 0)
    glClear(GL_COLOR_BUFFER_BIT | GL_DEPTH_BUFFER_BIT);
    glEnable(GL_DEPTH_TEST)
    glDisable(GL_LIGHTING)
    #glEnable(GL_LIGHTING)
    glEnable(GL_NORMALIZE)
    glShadeModel(GL_FLAT)

    # Projection
    glMatrixMode(GL_PROJECTION)
    glLoadIdentity()
    gluPerspective(45, 1.3333, 0.2, 20)

    # Initialize ModelView matrix
    glMatrixMode(GL_MODELVIEW)
    glLoadIdentity()

    # Light source
    #glLightfv(GL_LIGHT0, GL_POSITION, [0, 0, 1, 0])
    #glLightfv(GL_LIGHT0, GL_DIFFUSE, [1, 1, 1, 1])
    #glLightfv(GL_LIGHT0, GL_SPECULAR, [1, 1, 1, 1])
    #glEnable(GL_LIGHT0)

    # View transformation
    gluLookAt(2.4, 3.6, 4.8, 0.5, 0.5, 0, 0, 1, 0)


# create_box
def create_box(world, space, (lx, ly, lz), color = (1, 0, 0)):
    """Create a box body and its corresponding geom."""

    # Create body
    body = ode.Body(world)
    #M = ode.Mass()
    #M.setBox(density, lx, ly, lz)
    #body.setMass(M)

    # Set parameters for drawing the body
    body.shape = "box"
    body.boxsize = (lx, ly, lz)
    body.color = color

    # Create a box geom for collision detection
    geom = ode.GeomBox(space, lengths=body.boxsize)
    geom.setBody(body)

    return body, geom


# draw_body
def draw_body(body):
    """Draw an ODE body.
    """

    x,y,z = body.getPosition()
    R = body.getRotation()
    rot = [R[0], R[3], R[6], 0.,
           R[1], R[4], R[7], 0.,
           R[2], R[5], R[8], 0.,
           x, y, z, 1.0]
    glPushMatrix()
    glMultMatrixd(rot)
    if body.shape=="box":
        #sx,sy,sz = body.boxsize
        #glScalef(sx, sy, sz)
        Cube(body.boxsize, body.color)
    glPopMatrix()

#############################################

# Create a world object
world = ode.World()

# Create a space object
space = ode.Space()

# A list with ODE bodies
bodies = []

# The geoms for each of the bodies
geoms = []

pygame.init()
display = (800, 600)
pygame.display.set_mode(display, DOUBLEBUF | OPENGL)

# Set our FOV, aspect, and clipping planes
#gluPerspective(45, (display[0] / display[1]), 0.1, 50.0)

# Move the cube away from us
#glTranslatef(0.0, 0.0, -5)

prepare_GL(display[0], display[1])

body, geom = create_box(world, space, (1, 1, 1))
body.setPosition((0, 0, 0))
bodies.append(body)
geoms.append(geom)

body, geom = create_box(world, space, (1, 1, 1), (0, 1, 0))
body.setPosition((1, 0, 0))
bodies.append(body)
geoms.append(geom)

while True:
    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            pygame.quit()
            quit()
        if event.type == pygame.KEYDOWN:
            if event.key == pygame.K_LEFT:
                glTranslatef(-0.5,0,0)
            if event.key == pygame.K_RIGHT:
                glTranslatef(0.5,0,0)

            if event.key == pygame.K_UP:
                glTranslatef(0,1,0)
            if event.key == pygame.K_DOWN:
                glTranslatef(0,-1,0)

        if event.type == pygame.MOUSEBUTTONDOWN:
            if event.button == 4:
                glTranslatef(0,0,1.0)

            if event.button == 5:
                glTranslatef(0,0,-1.0)

    #glRotatef(1, 3, 1, 1)
    glClear(GL_COLOR_BUFFER_BIT | GL_DEPTH_BUFFER_BIT)



    #Cube()

    for b in bodies: draw_body(body)




    pygame.display.flip()
    pygame.time.wait(10)


