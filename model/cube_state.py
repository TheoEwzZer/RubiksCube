"""
Game-level cube state that bridges the solver and the view.
Manages the logical state and dispatches moves.
"""

from solver.cube_model import CubieCube, MOVE_CUBES, MOVE_NAMES


MOVE_MAP = {name: i for i, name in enumerate(MOVE_NAMES)}


class GameCubeState:
    """High-level cube state for the application."""

    def __init__(self):
        self.cube = CubieCube()
        self.move_history = []
        self._on_move_callbacks = []
        self._on_state_change_callbacks = []

    def reset(self):
        self.cube = CubieCube()
        self.move_history.clear()
        self._notify_state_change()

    def apply_move(self, move_name):
        """Apply a move by name (e.g. 'R', "U'", 'F2')."""
        if move_name not in MOVE_MAP:
            raise ValueError(f"Unknown move: {move_name}")
        idx = MOVE_MAP[move_name]
        self.cube.apply_move(MOVE_CUBES[idx])
        self.move_history.append(move_name)
        self._notify_move(move_name)

    def undo(self):
        """Undo the last move."""
        if not self.move_history:
            return None
        last = self.move_history.pop()
        # Apply the inverse move
        inv = self._inverse_move(last)
        idx = MOVE_MAP[inv]
        self.cube.apply_move(MOVE_CUBES[idx])
        self._notify_state_change()
        return last

    def is_solved(self):
        return self.cube.is_solved()

    def scramble(self, n_moves=20):
        """Scramble the cube. Returns the list of scramble moves."""
        from solver.solver import scramble as do_scramble
        self.cube, moves = do_scramble(n_moves)
        self.move_history.clear()
        self._notify_state_change()
        return moves

    def solve(self, max_length=23, timeout=30):
        """Solve the current state. Returns dict with 'moves' and 'phase1_length', or None."""
        from solver.solver import solve
        return solve(self.cube, max_length=max_length, timeout=timeout)

    def get_facelet_string(self):
        return self.cube.to_facelet_string()

    def set_from_facelet_string(self, s):
        self.cube = CubieCube.from_facelet_string(s)
        self.move_history.clear()
        self._notify_state_change()

    def on_move(self, callback):
        """Register callback(move_name) called after each move."""
        self._on_move_callbacks.append(callback)

    def on_state_change(self, callback):
        """Register callback() called on reset/scramble/undo."""
        self._on_state_change_callbacks.append(callback)

    def _notify_move(self, move_name):
        for cb in self._on_move_callbacks:
            cb(move_name)

    def _notify_state_change(self):
        for cb in self._on_state_change_callbacks:
            cb()

    @staticmethod
    def _inverse_move(move_name):
        if move_name.endswith("'"):
            return move_name[:-1]
        elif move_name.endswith("2"):
            return move_name  # X2 is its own inverse
        else:
            return move_name + "'"
