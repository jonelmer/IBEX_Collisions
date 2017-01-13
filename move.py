def move_all(monitors, geometries, moves):
    for move, geometry in zip(moves, geometries):
        move(geometry, monitors)