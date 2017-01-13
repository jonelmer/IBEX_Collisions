from transform import Transformation

def move_all(monitors, geometries, moves):
    for move, geometry in zip(moves, geometries):
        m = move(monitors)
        if type(m) is Transformation:
            geometry.setTransform(m)
        else:
            t, s = m
            geometry.setTransform(t)
            geometry.setSize(**s)
