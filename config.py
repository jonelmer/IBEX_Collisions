from math import radians, sin, cos
import numpy as np
from transform import Transformation

# Config happens here:

colors = [(0, 1, 0),
          (0, 1, 1),
          (1, 1, 0),
          (1, 0, 1),
          (1, 1, 1)
          ]


# Define the geometry of the system
geometries = [
              dict(position=(0, 4.5, 0), size=(2, 1, 2), origin=(0, 8, 0)),
              dict(position=(0, 3, 0), size=(2, 2, 2), origin=(0, 0, 0)),
              dict(position=(0, 1.5, 0), size=(2.0, 1.0, 22.0), origin=(0, 0, 0)),
              dict(position=(0, 0.5, 0), size=(22.0, 1.0, 22.0), origin=(0, 0, 0)),
              dict(position=(10, 7, 0), size=(10, 1.9, 1.9))
              ]

# List of pairs to ignore
ignore = [[0, 1], [0, 2], [0, 3], [1, 2], [1, 3], [2, 3]]

# Generate move functions
moves = []


def move(geometry, monitors):
    geometry.setRotation(angles=(0, 0, 0))
    position = [monitors[1].value(), monitors[2].value() + 4.5, monitors[0].value()]

    ry = radians(monitors[3].value())

    rot = np.array([[cos(ry), 0, -sin(ry)], [0, 1, 0], [sin(ry), 0, cos(ry)]])

    position = np.dot(rot.T, position)
    geometry.setPosition(coords=position)

    origin = position[:]
    origin[1] = 8

    geometry.setRotation(ty=ry, tz=radians(monitors[4].value()), origin=origin)

moves.append(move)


def move(geometry, monitors):
    geometry.setPosition(x=monitors[1].value(), y=monitors[2].value() + 3, z=monitors[0].value())
    geometry.setRotation(ty=radians(monitors[3].value()))

moves.append(move)


def move(geometry, monitors):
    geometry.setPosition(x=monitors[1].value(),  y=monitors[2].value() + 1.5)
    geometry.setRotation(ty=radians(monitors[3].value()))

moves.append(move)


def move(geometry, monitors):
    t = Transformation()
    t.translate(y=(monitors[2].value() + 1) / 2)
    t.rotate(ry=radians(monitors[3].value()))
    geometry.setTransform(t)

    geometry.size[1] = monitors[2].value() + 1

moves.append(move)


def move(geometry, monitors):
    pass

moves.append(move)

# Attach monitors to readbacks
pvs = ["TE:NDW1720:MOT:MTR0201", "TE:NDW1720:MOT:MTR0202", "TE:NDW1720:MOT:MTR0203", "TE:NDW1720:MOT:MTR0204", "TE:NDW1720:MOT:MTR0205"]
# pvs = ["TE:NDW1720:MOT:MTR0101", "TE:NDW1720:MOT:MTR0102", "TE:NDW1720:MOT:MTR0103", "TE:NDW1720:MOT:MTR0104"]

hardlimits = [[-10.0, 10.0],
              [-10.0, 10.0],
              [0.0, 5.0],
              [-180.0, 180.0],
              [-90, 90]]
