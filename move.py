from transform import Transformation


class MoveError(Exception):
    def __init__(self, description):
        Exception.__init__(self)
        self.description = description

    def __str__(self):
        return self.description


def move_all(geometries, moves, monitors=None, values=None):
    if monitors is not None:
        axes = [m.value() for m in monitors]
    elif values is not None:
        axes = values
    else:
        raise MoveError("No monitors or values provided")

    for move, geometry in zip(moves, geometries):
        m = move(axes)
        if type(m) is Transformation:
            geometry.set_transform(m)
        elif m is None:
            pass
        else:
            t, s = m
            geometry.set_transform(t)
            geometry.set_size(**s)
