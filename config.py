from math import radians
from transform import Transformation

# Config happens here:

colors = [(1, 1, 1), (1, 0, 1), (1, 1, 0), (0, 1, 1), (0, 1, 0), [1, 0.5, 0]]

# Define the geometry of the system
geometries = [dict(position=(10, 0, 8), size=(10, 1.9, 1.9)),
              dict(size=(22.0, 22.0, 1.0)),
              dict(size=(2.0, 22.0, 1.0)),
              dict(size=(2, 2, 2)),
              dict(size=(2, 2, 1)),
              dict(size=(2, 2, 1))]

# List of pairs to ignore
ignore = [[1, 2], [1, 3], [1, 4], [1, 5], [2, 3], [2, 4], [2, 5], [3, 4], [3, 5], [4, 5]]

# Generate move functions
moves = []


def move(geometry, monitors):
    pass


moves.append(move)


def move(geometry, monitors):
    t = Transformation()
    t.translate(z=(monitors[2].value() + 1) / 2)
    t.rotate(rz=radians(monitors[3].value()))
    geometry.setTransform(t)

    geometry.size[2] = monitors[2].value() + 1


moves.append(move)


def move(geometry, monitors):
    t = Transformation()
    t.translate(z=1.5)
    t.translate(x=monitors[1].value(), z=monitors[2].value())
    t.rotate(rz=radians(monitors[3].value()))
    geometry.setTransform(t)


moves.append(move)


def move(geometry, monitors):
    t = Transformation()
    t.translate(z=3)
    t.translate(x=monitors[1].value(), z=monitors[2].value(), y=monitors[0].value())
    t.rotate(rz=radians(monitors[3].value()))
    geometry.setTransform(t)


moves.append(move)


def move(geometry, monitors):
    t = Transformation()
    t.translate(z=-2)
    t.rotate(ry=radians(monitors[4].value()))
    t.translate(z=2 + 4.5)
    t.translate(x=monitors[1].value(), z=monitors[2].value(), y=monitors[0].value())
    t.rotate(rz=radians(monitors[3].value()))
    geometry.setTransform(t)


moves.append(move)


def move(geometry, monitors):
    t = Transformation()

    t.translate(z=-1)
    t.rotate(rx=radians(monitors[5].value()))
    t.translate(z=1)

    t.translate(z=-2)
    t.rotate(ry=radians(monitors[4].value()))
    t.translate(z=2 + 5.5)

    t.translate(x=monitors[1].value(), z=monitors[2].value(), y=monitors[0].value())
    t.rotate(rz=radians(monitors[3].value()))
    geometry.setTransform(t)


moves.append(move)

# Attach monitors to readbacks
pvs = ["TE:NDW1720:MOT:MTR0201",
       "TE:NDW1720:MOT:MTR0202",
       "TE:NDW1720:MOT:MTR0203",
       "TE:NDW1720:MOT:MTR0204",
       "TE:NDW1720:MOT:MTR0205",
       "TE:NDW1720:MOT:MTR0206"]

# pvs = ["TE:NDW1720:MOT:MTR0101", "TE:NDW1720:MOT:MTR0102", "TE:NDW1720:MOT:MTR0103", "TE:NDW1720:MOT:MTR0104"]

hardlimits = [[-10.0, 10.0],
              [-10.0, 10.0],
              [0.0, 5.0],
              [-180.0, 180.0],
              [-90, 90],
              [-90, 90]]
