from math import radians
from transform import Transformation

# Config happens here:

colors = [(0.6, 0.6, 0.6), (1, 0, 1), (1, 1, 0), (0, 1, 1), (0, 1, 0), (1, 0.5, 0), (0.2, 0.2, 1), (0.2, 0.2, 1), (0, 1, 0), (1, 1, 1), (1, 1, 1)]

# Define the geometry of the system
geometries = [
              dict(size=(1000.0, 1000.0, 630.0)),
              dict(size=(700.0, 700.0, 165.0)),
              dict(size=(700.0, 700.0, 120.0)),
              dict(size=(700.0, 700.0, 200.0)),
              dict(size=(700.0, 700.0, 120.0)),

              dict(size=(700.0,  250.0, 20.0)),
              dict(size=(250.0,  250.0, 20.0)),

              dict(size=(150.0, 150.0, 150.0)),
              dict(size=(700.0, 1000.0, 50.0)),

              dict(position=(300, 0, 0), size=(500, 70, 70)),
              dict(position=(-450, 0, 0), size=(100, 300, 300))
              ]

# List of pairs to ignore
ignore = []
for i in range(0, 9):
    for j in range(i, 9):
        ignore.append([i, j])

centre_arc = 750
beam_ref = 1625

# Generate move functions
moves = []


def stationary(*args):
    pass

# Z stage
def move_z(geometry, monitors):
    t = Transformation()
    t.translate(z=-beam_ref + (monitors[0].value() + geometries[0]['size'][2]) / 2)
    geometry.setTransform(t)

    geometry.size[2] = monitors[0].value() + geometries[0]['size'][2]


moves.append(move_z)

# Rotation
def move_rot(geometry, monitors):
    t = Transformation()
    t.translate(z=-beam_ref + monitors[0].value() + geometries[0]['size'][2] + geometries[1]['size'][2]/2)
    t.rotate(rz=radians(monitors[1].value()))
    geometry.setTransform(t)


moves.append(move_rot)

# Bottom arc
def move_bottom_arc(geometry, monitors):
    t = Transformation()

    t.translate(z=-centre_arc - (geometries[2]['size'][2]/2 + geometries[3]['size'][2]))
    t.rotate(ry=radians(monitors[2].value()))
    t.translate(z= centre_arc + (geometries[2]['size'][2]/2 + geometries[3]['size'][2]))

    t.translate(z=-beam_ref + monitors[0].value() + geometries[0]['size'][2] + geometries[1]['size'][2] + geometries[2]['size'][2] / 2)
    t.rotate(rz=radians(monitors[1].value()))
    geometry.setTransform(t)

    return t


moves.append(move_bottom_arc)

# Top arc
def move_top_arc(geometry, monitors):
    t = move_bottom_arc(geometry, monitors)

    t.translate(z=+(centre_arc + geometries[3]['size'][2] / 2), forward=False)
    t.rotate(rx=radians(monitors[3].value()), forward=False)
    t.translate(z=-(centre_arc + geometries[3]['size'][2] / 2), forward=False)

    t.translate(z=geometries[3]['size'][2]/2 + geometries[2]['size'][2] / 2, forward=False)

    geometry.setTransform(t)

    return t


moves.append(move_top_arc)

# Fine Z
def move_fine_z(geometry, monitors):
    t = move_top_arc(geometry, monitors)

    size = monitors[4].value() + geometries[4]['size'][2]
    geometry.size[2] = size

    t.translate(z=size/2 + geometries[3]['size'][2]/2, forward=False)

    geometry.setTransform(t)

    return t

moves.append(move_fine_z)


# Base of Y stage (top of fine Z)
def move_y_base(geometry, monitors):
    t = move_top_arc(geometry, monitors)

    size = monitors[4].value() + geometries[4]['size'][2]

    t.translate(z=size + geometries[3]['size'][2]/2 + geometries[8]['size'][2]/2, forward=False)

    geometry.setTransform(t)

    return t


# Y stage
def move_y_stage(geometry, monitors):
    t = move_y_base(geometry, monitors)

    t.translate(y=monitors[5].value(), z=geometries[8]['size'][2]/2 + geometries[5]['size'][2]/2, forward=False)

    geometry.setTransform(t)

    return t

moves.append(move_y_stage)

# X stage
def move_x_stage(geometry, monitors):
    t = move_y_stage(geometry, monitors)

    t.translate(x=monitors[6].value(), z=geometries[5]['size'][2]/2 + geometries[6]['size'][2]/2, forward=False)

    geometry.setTransform(t)

    return t


moves.append(move_x_stage)

# Sample
def move_sample(geometry, monitors):
    t = move_x_stage(geometry, monitors)

    t.translate(z=geometries[6]['size'][2]/2 + geometries[7]['size'][2]/2, forward=False)

    geometry.setTransform(t)

    return t


moves.append(move_sample)

moves.append(move_y_base)

# Attach monitors to readbacks
pvs = ["TE:NDW1720:MOT:MTR0201",
       "TE:NDW1720:MOT:MTR0202",
       "TE:NDW1720:MOT:MTR0203",
       "TE:NDW1720:MOT:MTR0204",
       "TE:NDW1720:MOT:MTR0205",
       "TE:NDW1720:MOT:MTR0206",
       "TE:NDW1720:MOT:MTR0207"
       ]

# pvs = ["TE:NDW1720:MOT:MTR0101", "TE:NDW1720:MOT:MTR0102", "TE:NDW1720:MOT:MTR0103", "TE:NDW1720:MOT:MTR0104"]

hardlimits = [[-220, 100],
              [-180.0, 180.0],
              [-20, 20.0],
              [-20.0, 20.0],
              [0.0, 30.0],
              [-300, 300],
              [-200, 200]]
