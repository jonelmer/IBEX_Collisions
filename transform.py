import numpy as np
from math import radians, sin, cos


class Transformation(object):
    def __init__(self):
        self.matrix = np.array([[1, 0, 0, 0], [0, 1, 0, 0], [0, 0, 1, 0], [0, 0, 0, 1]])
        self.identity()

    def identity(self):
        self.matrix = [[1, 0, 0, 0], [0, 1, 0, 0], [0, 0, 1, 0], [0, 0, 0, 1]]

    def rotate(self, rx=0, ry=0, rz=0, forward=True):
        if rx is not 0:
            rotate = np.array([[1, 0, 0, 0],
                               [0, cos(rx), -sin(rx), 0],
                               [0, sin(rx), cos(rx), 0],
                               [0, 0, 0, 1]])
            if forward:
                self.matrix = np.dot(rotate, self.matrix)
            else:
                self.matrix = np.dot(self.matrix, rotate)

        if ry is not 0:
            rotate = np.array([[cos(ry), 0, -sin(ry), 0],
                               [0, 1, 0, 0],
                               [sin(ry), 0, cos(ry), 0],
                               [0, 0, 0, 1]])
            if forward:
                self.matrix = np.dot(rotate, self.matrix)
            else:
                self.matrix = np.dot(self.matrix, rotate)

        if rz is not 0:
            rotate = np.array([[cos(rz), -sin(rz), 0, 0],
                               [sin(rz), cos(rz), 0, 0],
                               [0, 0, 1, 0],
                               [0, 0, 0, 1]])
            if forward:
                self.matrix = np.dot(rotate, self.matrix)
            else:
                self.matrix = np.dot(self.matrix, rotate)

    def translate(self, x=0, y=0, z=0, forward=True):
        if forward:
            self.matrix = np.dot(
                np.array([[1, 0, 0, x],
                          [0, 1, 0, y],
                          [0, 0, 1, z],
                          [0, 0, 0, 1]]), self.matrix)
        else:
            self.matrix = np.dot(self.matrix,
                                 np.array([[1, 0, 0, x],
                                           [0, 1, 0, y],
                                           [0, 0, 1, z],
                                           [0, 0, 0, 1]]))

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

    def to_opengl(self):
        return np.reshape(self.matrix.T, (1, 16))[0]

    def get_inverse(self):
        return np.linalg.inv(self.matrix)

    def get_inverse(self):

        """Returns the inverse (matrix with the opposite effect) of this
        matrix."""

        [[i0, i1, i2, i3], [i4, i5, i6, i7], [i8, i9, i10, i11], [i12, i13, i14, i15]] = self.matrix.T

        negpos = [0., 0.]
        temp = i0 * i5 * i10
        negpos[temp > 0.] += temp

        temp = i1 * i6 * i8
        negpos[temp > 0.] += temp

        temp = i2 * i4 * i9
        negpos[temp > 0.] += temp

        temp = -i2 * i5 * i8
        negpos[temp > 0.] += temp

        temp = -i1 * i4 * i10
        negpos[temp > 0.] += temp

        temp = -i0 * i6 * i9
        negpos[temp > 0.] += temp

        det_1 = negpos[0] + negpos[1]

        if (det_1 == 0.) or (abs(det_1 / (negpos[1] - negpos[0])) < (2. * 0.00000000000000001)):
            #raise Matrix44Error("This Matrix44 can not be inverted")
            print "Oops"

        det_1 = 1. / det_1

        ret = [(i5 * i10 - i6 * i9) * det_1, -(i1 * i10 - i2 * i9) * det_1, (i1 * i6 - i2 * i5) * det_1, 0.0,
                  -(i4 * i10 - i6 * i8) * det_1, (i0 * i10 - i2 * i8) * det_1, -(i0 * i6 - i2 * i4) * det_1, 0.0,
                  (i4 * i9 - i5 * i8) * det_1, -(i0 * i9 - i1 * i8) * det_1, (i0 * i5 - i1 * i4) * det_1, 0.0,
                  0.0, 0.0, 0.0, 1.0]

        m = ret
        m[12] = - (i12 * m[0] + i13 * m[4] + i14 * m[8])
        m[13] = - (i12 * m[1] + i13 * m[5] + i14 * m[9])
        m[14] = - (i12 * m[2] + i13 * m[6] + i14 * m[10])

        return np.reshape(ret, (4, 4))
