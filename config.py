from math import radians

# Config happens here:

# Define the geometry of the system
geometries = [dict(position=(0, 3, 0), size=(2, 2, 2), origin=(0, 0, 0)),
              dict(position=(0, 1.5, 0), size=(2.0, 1.0, 22.0), origin=(0, 0, 0)),
              dict(position=(0, 0.5, 0), size=(22.0, 1.0, 22.0), origin=(0, 0, 0)),
              dict(position=(10, 7, 0), size=(10, 1.9, 1.9)),
              dict(position=(0, 4.5, 0), size=(2, 1, 2), origin=(0, 7, 0))]

# List of pairs to ignore
ignore = [[0, 1], [0, 2], [1, 2], [4, 0], [4, 1], [4, 2]]

# Generate move functions
moves = []


def move(geometry, monitors):
    geometry.setRotation(angles=(0, 0, 0))
    geometry.setPosition(x=monitors[1].value(), y=monitors[2].value() + 3, z=monitors[0].value())
    geometry.setRotation(ty=radians(monitors[3].value()))

moves.append(move)


def move(geometry, monitors):
    geometry.setRotation(angles=(0, 0, 0))
    geometry.setPosition(x=monitors[1].value(),  y=monitors[2].value() + 1.5)
    geometry.setRotation(ty=radians(monitors[3].value()))

moves.append(move)


def move(geometry, monitors):
    geometry.setRotation(ty=radians(monitors[3].value()))
    geometry.size[1] = monitors[2].value() + 1
    geometry.setPosition(y=(monitors[2].value()+1)/2)

moves.append(move)


def move(geometry, monitors):
    pass

moves.append(move)


def move(geometry, monitors):
    geometry.setRotation(angles=(0, 0, 0))
    position = dict(x=monitors[1].value(), y=monitors[2].value() + 4.5, z=monitors[0].value())
    geometry.setPosition(**position)
    position['y'] = 7
    origin = [position['x'], position['y'], position['z']]
    geometry.setRotation(ty=radians(monitors[3].value()), tz=radians(monitors[4].value()), origin=origin)

moves.append(move)

# Attach monitors to readbacks
pvs = ["TE:NDW1720:MOT:MTR0201", "TE:NDW1720:MOT:MTR0202", "TE:NDW1720:MOT:MTR0203", "TE:NDW1720:MOT:MTR0204", "TE:NDW1720:MOT:MTR0205"]
# pvs = ["TE:NDW1720:MOT:MTR0101", "TE:NDW1720:MOT:MTR0102", "TE:NDW1720:MOT:MTR0103", "TE:NDW1720:MOT:MTR0104"]

hardlimits = [[-10.0, 10.0],
              [-10.0, 10.0],
              [0.0, 5.0],
              [-180.0, 180.0],
              [-90, 90]]
