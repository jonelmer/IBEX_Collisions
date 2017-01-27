from transform import Transformation


def move_all(monitors, geometries, moves):
    axes = [m.value() for m in monitors]
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
