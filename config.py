from math import radians
from transform import Transformation

# Config happens here:

# Colors for each body
colors = [(0.6, 0.6, 0.6), (1, 0, 1), (1, 1, 0), (0, 1, 1), (0, 1, 0), (1, 0.5, 0), (0.2, 0.2, 1), (0.2, 0.2, 1), (0, 1, 0), (1, 1, 1), (1, 1, 1)]

# PV prefix for controlling the system
control_pv = "TE:NDW1720:COLLIDE:"

# Define the geometry of the system in mm
# Coordinate origin at arc centre, with nominal beam height
z_stage =   dict(name="Z Stage",    size=(1000.0, 1000.0, 630.0))
rot_stage = dict(name="Rotation",   size=(700.0, 700.0, 165.0))
bot_arc =   dict(name="Bottom Arc", size=(700.0, 700.0, 120.0))
top_arc =   dict(name="Top Arc",    size=(700.0, 700.0, 120.0))
fine_z =    dict(name="Fine Z",     size=(700.0, 700.0, 120.0))
y_stage =   dict(name="Y Carriage", size=(700.0,  250.0, 20.0))
x_stage =   dict(name="X Carriage", size=(250.0,  250.0, 20.0))
sample =    dict(name="Sample",     size=(150.0, 150.0, 150.0))
y_base =    dict(name="Y Stage",    size=(700.0, 1000.0, 50.0))
snout =     dict(name="Snout", position=(-300, 0, 0), size=(500, 70, 70))
slits =     dict(name="Slits", position=(450, 0, 0), size=(100, 300, 300))

# Put them in a list
geometries = [z_stage, rot_stage, bot_arc, top_arc, fine_z, y_stage, x_stage, sample, y_base, snout, slits]

# Define some variables to describe the geometry
centre_arc = 750
beam_ref = 1625

# Define some search parameters
coarse = 20
fine = 0.5

# Define the oversized-ness of each body - a global value in mm
oversize = coarse/4

# List of pairs to ignore [0, 1]...[7, 8]
ignore = []
for i in range(0, 9):
    for j in range(i, 9):
        ignore.append([i, j])

# Generate move functions

def stationary(*args):
    pass

# Z stage
def move_z_stage(monitors):
    t = Transformation()

    size = monitors[0].value() + z_stage['size'][2]

    t.translate(z=-beam_ref + size / 2)

    return t, dict(z=size)


# Rotation
def move_rot_stage(monitors):
    t = Transformation()
    t.translate(z=-beam_ref + monitors[0].value() + z_stage['size'][2] + rot_stage['size'][2]/2)
    t.rotate(rz=radians(monitors[1].value()))

    return t


# Bottom arc
def move_bot_arc(monitors):
    t = Transformation()

    t.translate(z=-centre_arc - (bot_arc['size'][2]/2 + top_arc['size'][2]))
    t.rotate(ry=radians(monitors[2].value()))
    t.translate(z= centre_arc + (bot_arc['size'][2]/2 + top_arc['size'][2]))

    t.translate(z=-beam_ref + monitors[0].value() + z_stage['size'][2] + rot_stage['size'][2] + bot_arc['size'][2] / 2)
    t.rotate(rz=radians(monitors[1].value()))

    return t


# Top arc
def move_top_arc(monitors):
    t = move_bot_arc(monitors)

    t.translate(z=+(centre_arc + top_arc['size'][2] / 2), forward=False)
    t.rotate(rx=radians(monitors[3].value()), forward=False)
    t.translate(z=-(centre_arc + top_arc['size'][2] / 2), forward=False)

    t.translate(z=top_arc['size'][2]/2 + bot_arc['size'][2] / 2, forward=False)

    return t


# Fine Z
def move_fine_z(monitors):
    t = move_top_arc(monitors)

    size = monitors[4].value() + fine_z['size'][2]

    t.translate(z=size/2 + top_arc['size'][2]/2, forward=False)

    return t, dict(z=size)


# Base of Y stage (top of fine Z)
def move_y_base(monitors):
    t = move_top_arc(monitors)

    size = monitors[4].value() + fine_z['size'][2]

    t.translate(z=size + top_arc['size'][2]/2 + y_base['size'][2]/2, forward=False)

    return t


# Y stage
def move_y_stage(monitors):
    t = move_y_base(monitors)

    t.translate(y=monitors[5].value(), z=y_base['size'][2]/2 + y_stage['size'][2]/2, forward=False)

    return t


# X stage
def move_x_stage(monitors):
    t = move_y_stage(monitors)

    t.translate(x=monitors[6].value(), z=y_stage['size'][2]/2 + x_stage['size'][2]/2, forward=False)

    return t

# Sample
def move_sample(monitors):
    t = move_x_stage(monitors)

    t.translate(z=x_stage['size'][2]/2 + sample['size'][2]/2, forward=False)

    return t


moves = [move_z_stage, move_rot_stage, move_bot_arc, move_top_arc, move_fine_z, move_y_stage, move_x_stage, move_sample,
         move_y_base]

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
