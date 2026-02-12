"""
Public API for the Rubik's Cube Two-Phase solver.

Usage:
    from solver import solve

    # Facelet string: 54 chars, each being U/R/F/D/L/B
    # Order: U1-U9, R1-R9, F1-F9, D1-D9, L1-L9, B1-B9
    solution = solve("DRLUUBFBRBLURRLRUBLRDDFDLFUFUFFDBRDUBRRL FBLLURDBFDFBBU")
    print(solution)  # e.g., ["R", "U'", "F2", ...]
"""

from .cube_model import CubieCube, MOVE_CUBES, MOVE_NAMES
from .search import TwoPhaseSearch

_solver = None


def _get_solver():
    global _solver
    if _solver is None:
        _solver = TwoPhaseSearch()
    return _solver


def solve(cube_input, max_length=23, timeout=30):
    """Solve a Rubik's Cube.

    Args:
        cube_input: Either a 54-character facelet string (URFDLB) or a CubieCube.
        max_length: Maximum solution length to search for.
        timeout: Maximum time in seconds.

    Returns:
        A list of move strings (e.g., ["R", "U'", "F2"]) or None if no solution found.
    """
    if isinstance(cube_input, str):
        cube_input = cube_input.replace(" ", "")
        cube = CubieCube.from_facelet_string(cube_input)
    elif isinstance(cube_input, CubieCube):
        cube = cube_input
    else:
        raise TypeError("cube_input must be a facelet string or CubieCube")

    solver = _get_solver()
    result = solver.solve(cube, max_length=max_length, timeout_seconds=timeout)
    if result is None:
        return None
    moves, phase1_length = result
    return {"moves": moves, "phase1_length": phase1_length}


def solve_from_moves(scramble_moves, max_length=23, timeout=30):
    """Solve a cube that has been scrambled with the given moves.

    Args:
        scramble_moves: List of move strings (e.g., ["R", "U'", "F2"])

    Returns:
        A list of move strings for the solution.
    """
    move_map = {name: i for i, name in enumerate(MOVE_NAMES)}

    cube = CubieCube()
    for move_str in scramble_moves:
        if move_str not in move_map:
            raise ValueError(f"Unknown move: {move_str}")
        cube.apply_move(MOVE_CUBES[move_map[move_str]])

    return solve(cube, max_length=max_length, timeout=timeout)


def scramble(n_moves=20):
    """Generate a random scramble.

    Returns:
        Tuple of (CubieCube, list of move names).
    """
    import random
    cube = CubieCube()
    moves = []
    last_axis = -1
    for _ in range(n_moves):
        while True:
            m = random.randint(0, 17)
            axis = m // 3
            if axis != last_axis:
                break
        cube.apply_move(MOVE_CUBES[m])
        moves.append(MOVE_NAMES[m])
        last_axis = axis
    return cube, moves


def initialize():
    """Pre-load all tables. Call this at startup to avoid delay on first solve."""
    _get_solver()
