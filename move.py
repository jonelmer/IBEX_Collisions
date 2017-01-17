from transform import Transformation


def move_all(monitors, geometries, moves):
    for move, geometry in zip(moves, geometries):
        m = move(monitors)
        if type(m) is Transformation:
            geometry.set_transform(m)
        else:
            t, s = m
            geometry.set_transform(t)
            geometry.set_size(**s)
