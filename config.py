from math import radians
from transform import Transformation

# Config happens here:

colors = [(1, 1, 1), (1, 0, 1), (1, 1, 0), (0, 1, 1), (0, 1, 0), [1, 0.5, 0], [0.2, 0.2, 1], [0, 1, 0]]

# Define the geometry of the system
geometries = [
              dict(size=(22.0, 22.0, 1.0)),
              dict(size=(15.0, 15.0, 1.0)),
              dict(size=(15.0, 15.0, 1.0)),
              dict(size=(15.0, 15.0, 1.0)),
              dict(size=(15.0, 15.0, 1.0)),

              dict(size=(15.0,  5.0, 1.0)),
              dict(size=( 5.0,  5.0, 1.0)),

              dict(size=(15.0, 22.0, 1.0)),

              dict(position=(7, 0, 15), size=(10, 1.5, 1.5))
              ]

# List of pairs to ignore
ignore = [
          [0, 1], [0, 2], [0, 3], [0, 4], [0, 5], [0, 6], [0, 7],
          [1, 2], [1, 3], [1, 4], [1, 5], [1, 6], [1, 7],
          [2, 3], [2, 4], [2, 5], [2, 6], [2, 7],
          [3, 4], [3, 5], [3, 6], [3, 7],
          [4, 5], [4, 6], [4, 7],
          [5, 6], [5, 7],
          [6, 7]
          ]

# Generate move functions
moves = []


def stationary(*args):
    pass


def move(geometry, monitors):
    t = Transformation()
    t.translate(z=(monitors[0].value() + 1) / 2)
    geometry.setTransform(t)

    geometry.size[2] = monitors[0].value() + 1


moves.append(move)


def move(geometry, monitors):
    t = Transformation()
    t.translate(z=(monitors[0].value() + 1.5))
    t.rotate(rz=radians(monitors[1].value()))
    geometry.setTransform(t)


moves.append(move)


def move(geometry, monitors):
    t = Transformation()
    t.translate(z=-10)
    t.rotate(ry=radians(monitors[2].value()))
    t.translate(z=10)

    t.translate(z=(monitors[0].value() + 2.5))
    t.rotate(rz=radians(monitors[1].value()))
    geometry.setTransform(t)


moves.append(move)


def move(geometry, monitors):
    t = Transformation()

    t.translate(z=-9)
    t.rotate(rx=radians(monitors[3].value()))
    t.translate(z=9)

    t.translate(z=-10)
    t.rotate(ry=radians(monitors[2].value()))
    t.translate(z=10)

    t.translate(z=(monitors[0].value() + 3.5))
    t.rotate(rz=radians(monitors[1].value()))
    geometry.setTransform(t)


moves.append(move)


def move(geometry, monitors):
    t = Transformation()

    t.translate(z=0.5+((monitors[4].value() + 1) / 2))
    geometry.size[2] = monitors[4].value() + 1

    t.translate(z=-9)
    t.rotate(rx=radians(monitors[3].value()))
    t.translate(z=9)

    t.translate(z=-10)
    t.rotate(ry=radians(monitors[2].value()))
    t.translate(z=10)

    t.translate(z=(monitors[0].value() + 3.5))
    t.rotate(rz=radians(monitors[1].value()))
    geometry.setTransform(t)


moves.append(move)





def move(geometry, monitors):
    t = Transformation()

    t.translate(y=monitors[5].value(), z=3 + monitors[4].value())

    t.translate(z=-9)
    t.rotate(rx=radians(monitors[3].value()))
    t.translate(z=9)

    t.translate(z=-10)
    t.rotate(ry=radians(monitors[2].value()))
    t.translate(z=10)

    t.translate(z=(monitors[0].value() + 3.5))
    t.rotate(rz=radians(monitors[1].value()))
    geometry.setTransform(t)


moves.append(move)


def move(geometry, monitors):
    t = Transformation()

    t.translate(x=monitors[6].value(), y=monitors[5].value(), z=4 + monitors[4].value())

    t.translate(z=-9)
    t.rotate(rx=radians(monitors[3].value()))
    t.translate(z=9)

    t.translate(z=-10)
    t.rotate(ry=radians(monitors[2].value()))
    t.translate(z=10)

    t.translate(z=(monitors[0].value() + 3.5))
    t.rotate(rz=radians(monitors[1].value()))
    geometry.setTransform(t)


moves.append(move)




def move(geometry, monitors):
    t = Transformation()

    t.translate(z=2 + monitors[4].value())

    t.translate(z=-9)
    t.rotate(rx=radians(monitors[3].value()))
    t.translate(z=9)

    t.translate(z=-10)
    t.rotate(ry=radians(monitors[2].value()))
    t.translate(z=10)

    t.translate(z=(monitors[0].value() + 3.5))
    t.rotate(rz=radians(monitors[1].value()))
    geometry.setTransform(t)


moves.append(move)

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

hardlimits = [[0.0, 5.0],
              [-180.0, 180.0],
              [-20, 20.0],
              [-20.0, 20.0],
              [0.0, 2.0],
              [-10, 10],
              [-5, 5]]
