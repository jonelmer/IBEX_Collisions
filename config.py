from math import radians
from transform import Transformation

# Config happens here:

colors = [(0.7, 0.7, 0.7), (1, 0, 1), (1, 1, 0), (0, 1, 1), (0, 1, 0), (1, 0.5, 0), (0.2, 0.2, 1), (0.2, 0.2, 1), (0, 1, 0), (1, 1, 1)]

# Define the geometry of the system
geometries = [
              dict(size=(1000.0, 1000.0, 620.0)),
              dict(size=(700.0, 700.0, 165.0)),
              dict(size=(700.0, 700.0, 120.0)),
              dict(size=(700.0, 700.0, 120.0)),
              dict(size=(700.0, 700.0, 120.0)),

              dict(size=(700.0,  250.0, 20.0)),
              dict(size=(250.0,  250.0, 20.0)),

              dict(size=(150.0, 150.0, 150.0)),
              dict(size=(700.0, 1000.0, 50.0)),

              dict(position=(300, 0, 1500), size=(500, 70, 70))
              ]

# List of pairs to ignore
ignore = []
for i in range(0, 9):
    for j in range(i, 9):
        ignore.append([i, j])

centre_arc = 750

# Generate move functions
moves = []


def stationary(*args):
    pass


def move(geometry, monitors):
    t = Transformation()
    t.translate(z=(monitors[0].value() + geometries[0]['size'][2]) / 2)
    geometry.setTransform(t)

    geometry.size[2] = monitors[0].value() + geometries[0]['size'][2]


moves.append(move)


def move(geometry, monitors):
    t = Transformation()
    t.translate(z=monitors[0].value() + geometries[1]['size'][2]/2 + geometries[0]['size'][2])
    t.rotate(rz=radians(monitors[1].value()))
    geometry.setTransform(t)


moves.append(move)


def move(geometry, monitors):
    t = Transformation()
    t.translate(z=-centre_arc-geometries[2]['size'][2])
    t.rotate(ry=radians(monitors[2].value()))
    t.translate(z=centre_arc+geometries[2]['size'][2])

    t.translate(z=monitors[0].value() + geometries[2]['size'][2]/2 +
                  geometries[1]['size'][2] + geometries[0]['size'][2])
    t.rotate(rz=radians(monitors[1].value()))
    geometry.setTransform(t)


moves.append(move)


def move(geometry, monitors):
    t = Transformation()

    t.translate(z=-centre_arc - geometries[3]['size'][2]/2 - geometries[2]['size'][2])
    t.rotate(rx=radians(monitors[3].value()))

    t.translate(z= + geometries[3]['size'][2])

    t.rotate(ry=radians(monitors[2].value()))
    t.translate(z=centre_arc + geometries[2]['size'][2])

    t.translate(z=(monitors[0].value() + geometries[2]['size'][2] +
                   geometries[1]['size'][2] + geometries[0]['size'][2]))
    t.rotate(rz=radians(monitors[1].value()))
    geometry.setTransform(t)


moves.append(move)


def move(geometry, monitors):
    t = Transformation()

    t.translate(z=monitors[4].value()/2 + geometries[4]['size'][2]/2)
    geometry.size[2] = monitors[4].value() + geometries[4]['size'][2]

    t.translate(z=-centre_arc - geometries[3]['size'][2]/2 - geometries[2]['size'][2])
    t.rotate(rx=radians(monitors[3].value()))

    t.translate(z= + geometries[3]['size'][2])

    t.rotate(ry=radians(monitors[2].value()))
    t.translate(z=centre_arc + geometries[2]['size'][2])

    t.translate(z=(monitors[0].value() + geometries[3]['size'][2]/2 + geometries[2]['size'][2] +
                   geometries[1]['size'][2]+ geometries[0]['size'][2]))
    t.rotate(rz=radians(monitors[1].value()))
    geometry.setTransform(t)


moves.append(move)





def move(geometry, monitors):
    t = Transformation()

    t.translate(y=monitors[5].value(), z=monitors[4].value() + geometries[4]['size'][2] +
                                         geometries[8]['size'][2] + geometries[5]['size'][2]/2)

    t.translate(z=-centre_arc - geometries[3]['size'][2]/2 - geometries[2]['size'][2])
    t.rotate(rx=radians(monitors[3].value()))

    t.translate(z= + geometries[3]['size'][2])

    t.rotate(ry=radians(monitors[2].value()))
    t.translate(z=centre_arc + geometries[2]['size'][2])

    t.translate(z=(monitors[0].value() + geometries[3]['size'][2]/2 + geometries[2]['size'][2] +
                   geometries[1]['size'][2]+ geometries[0]['size'][2]))
    t.rotate(rz=radians(monitors[1].value()))
    geometry.setTransform(t)


moves.append(move)


def move(geometry, monitors):
    t = Transformation()

    t.translate(x=monitors[6].value(), y=monitors[5].value(),
                z=monitors[4].value() + geometries[4]['size'][2] + geometries[8]['size'][2] +
                  geometries[5]['size'][2] + geometries[6]['size'][2] / 2)

    t.translate(z=-centre_arc - geometries[3]['size'][2] / 2 - geometries[2]['size'][2])
    t.rotate(rx=radians(monitors[3].value()))

    t.translate(z=+ geometries[3]['size'][2])

    t.rotate(ry=radians(monitors[2].value()))
    t.translate(z=centre_arc + geometries[2]['size'][2])

    t.translate(z=(
    monitors[0].value() + geometries[3]['size'][2] / 2 + geometries[2]['size'][2] + geometries[1]['size'][2] +
    geometries[0]['size'][2]))
    t.rotate(rz=radians(monitors[1].value()))
    geometry.setTransform(t)


moves.append(move)


def move(geometry, monitors):
    t = Transformation()

    t.translate(x=monitors[6].value(), y=monitors[5].value(),
                z=monitors[4].value() + geometries[4]['size'][2] + geometries[8]['size'][2] +
                  geometries[5]['size'][2] + geometries[6]['size'][2] + geometries[7]['size'][2] / 2)

    t.translate(z=-centre_arc - geometries[3]['size'][2] / 2 - geometries[2]['size'][2])
    t.rotate(rx=radians(monitors[3].value()))

    t.translate(z=+ geometries[3]['size'][2])

    t.rotate(ry=radians(monitors[2].value()))
    t.translate(z=centre_arc + geometries[2]['size'][2])

    t.translate(z=(
    monitors[0].value() + geometries[3]['size'][2] / 2 + geometries[2]['size'][2] + geometries[1]['size'][2] +
    geometries[0]['size'][2]))
    t.rotate(rz=radians(monitors[1].value()))
    geometry.setTransform(t)


moves.append(move)


def move(geometry, monitors):
    t = Transformation()

    t.translate(z=monitors[4].value() + geometries[4]['size'][2] + geometries[8]['size'][2]/2)

    t.translate(z=-centre_arc - geometries[3]['size'][2]/2 - geometries[2]['size'][2])
    t.rotate(rx=radians(monitors[3].value()))

    t.translate(z= + geometries[3]['size'][2])

    t.rotate(ry=radians(monitors[2].value()))
    t.translate(z=centre_arc + geometries[2]['size'][2])

    t.translate(z=(monitors[0].value() + geometries[3]['size'][2]/2 + geometries[2]['size'][2] +
                   geometries[1]['size'][2] + geometries[0]['size'][2]))
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

hardlimits = [[-160, 160],
              [-180.0, 180.0],
              [-20, 20.0],
              [-20.0, 20.0],
              [0.0, 20.0],
              [-500, 500],
              [-200, 200]]
