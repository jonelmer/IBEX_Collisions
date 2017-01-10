import numpy as np
from math import radians, sin, cos


class Transformation(object):
    def __init__(self):
        self.matrix = self.identity()

    def identity(self):
        return np.array([[1, 0, 0, 0], [0, 1, 0, 0], [0, 0, 1, 0], [0, 0, 0, 1]])

    def rotate(self, rx=0, ry=0, rz=0):
        if rx is not 0:
            rotate = np.array([[1,       0,        0, 0],
                               [0, cos(rx), -sin(rx), 0],
                               [0, sin(rx),  cos(rx), 0],
                               [0,       0,        0, 1]])
            self.matrix = np.dot(rotate, self.matrix)

        if ry is not 0:
            rotate = np.array([[cos(ry), 0, -sin(ry), 0],
                               [      0, 1,        0, 0],
                               [sin(ry), 0,  cos(ry), 0],
                               [      0, 0,        0, 1]])
            self.matrix = np.dot(rotate, self.matrix)

        if rz is not 0:
            rotate = np.array([[cos(rz), -sin(rz), 0, 0],
                               [sin(rz),  cos(rz), 0, 0],
                               [      0,        0, 1, 0],
                               [      0,        0, 0, 1]])
            self.matrix = np.dot(rotate, self.matrix)

    def translate(self, x=0, y=0, z=0):
        self.matrix = np.dot(np.array([[1, 0, 0, x],
                                       [0, 1, 0, y],
                                       [0, 0, 1, z],
                                       [0, 0, 0, 1]]), self.matrix)

    def scale(self, x=1, y=1, z=1):
        self.matrix = np.dot(np.array([[x, 0, 0, 0],
                                       [0, y, 0, 0],
                                       [0, 0, z, 0],
                                       [0, 0, 0, 1]]), self.matrix)

    def evaluate(self, position):

        position = position[0:3] + [1]

        result = np.dot(self.matrix, position)

        return result[0:3]

    def split(self):
        rotation = self.matrix[0:3, 0:3]
        position = self.matrix[0:3, 3]

        return rotation, position

