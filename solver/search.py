"""
IDA* two-phase search for the Kociemba algorithm.

Phase 1: Search for a sequence of moves that brings the cube into subgroup G1,
         where twist=0, flip=0, udslice=0.
Phase 2: From the G1 state, search using only G1-preserving moves (U,U2,U',D,D2,D',
         R2,L2,F2,B2) to solve the cube completely.

The search iterates over increasing total solution lengths to find short solutions.
"""

from . import coord
from .cube_model import CubieCube, MOVE_CUBES, MOVE_NAMES, PHASE2_MOVES
from .move_tables import (
    get_twist_move, get_flip_move, get_udslice_move,
    get_cperm_move, get_ud_edges_move, get_udslice_sorted_move,
)
from .pruning_tables import (
    get_flip_udslice_prune, get_twist_udslice_prune,
    get_cperm_udslice_sorted_prune, get_ud_edges_udslice_sorted_prune,
)


# Which face axis each move belongs to (for move filtering)
# U=0,U2=0,U'=0, R=1,R2=1,R'=1, F=2,F2=2,F'=2, D=3,D2=3,D'=3, L=4,L2=4,L'=4, B=5,B2=5,B'=5
_MOVE_AXIS = [i // 3 for i in range(18)]

# Opposite faces: U-D, R-L, F-B
_OPPOSITE = {0: 3, 3: 0, 1: 4, 4: 1, 2: 5, 5: 2}


def _moves_compatible(last_move, move):
    """Check if move is compatible with last_move (prune redundant sequences).

    Rules:
    - Don't move the same face twice in a row (e.g., U then U2)
    - For opposite faces, enforce an ordering (e.g., always U before D)
    """
    if last_move == -1:
        return True
    last_axis = _MOVE_AXIS[last_move]
    this_axis = _MOVE_AXIS[move]
    if last_axis == this_axis:
        return False
    if _OPPOSITE.get(last_axis) == this_axis and last_axis > this_axis:
        return False
    return True


class TwoPhaseSearch:
    """Kociemba two-phase IDA* solver."""

    def __init__(self):
        # Load all tables
        self.twist_move = get_twist_move()
        self.flip_move = get_flip_move()
        self.udslice_move = get_udslice_move()
        self.cperm_move = get_cperm_move()
        self.ud_edges_move = get_ud_edges_move()
        self.udslice_sorted_move = get_udslice_sorted_move()

        self.flip_udslice_prune = get_flip_udslice_prune()
        self.twist_udslice_prune = get_twist_udslice_prune()
        self.cperm_uds_prune = get_cperm_udslice_sorted_prune()
        self.ud_edges_uds_prune = get_ud_edges_udslice_sorted_prune()

    def solve(self, cube, max_length=23, timeout_seconds=30):
        """Find a solution for the given CubieCube.

        Returns a list of move names (e.g., ["R", "U'", "F2", ...]).
        Tries to find progressively shorter solutions.
        """
        import time
        start_time = time.time()

        # Validate
        err = cube.validate()
        if err:
            raise ValueError(f"Invalid cube state: {err}")

        if cube.is_solved():
            return ([], 0)

        # Extract phase 1 coordinates
        twist = coord.get_twist(cube)
        flip = coord.get_flip(cube)
        udslice = coord.get_udslice(cube)

        # We need the full cubie state to extract phase 2 coords after phase 1
        # Store the cube for phase 2 initialization
        self._cube = cube
        self._best_solution = None
        self._phase1_length = 0
        self._timeout = start_time + timeout_seconds

        # Try increasing phase 1 depths
        for phase1_depth in range(max_length + 1):
            if time.time() > self._timeout:
                break

            # phase1_moves stores the move indices found so far
            phase1_moves = [-1] * phase1_depth

            # Coordinate stacks for phase 1
            twist_stack = [0] * (phase1_depth + 1)
            flip_stack = [0] * (phase1_depth + 1)
            udslice_stack = [0] * (phase1_depth + 1)
            twist_stack[0] = twist
            flip_stack[0] = flip
            udslice_stack[0] = udslice

            if self._phase1_search(
                phase1_moves, 0, phase1_depth,
                twist_stack, flip_stack, udslice_stack,
                max_length
            ):
                # Found a solution within max_length
                break

            if self._best_solution is not None:
                break

        if self._best_solution is not None:
            return ([MOVE_NAMES[m] for m in self._best_solution], self._phase1_length)

        return None  # No solution found

    def _phase1_prune(self, twist, flip, udslice):
        """Phase 1 pruning: lower bound on moves to reach G1."""
        idx1 = flip * coord.N_UDSLICE + udslice
        idx2 = twist * coord.N_UDSLICE + udslice
        d1 = self.flip_udslice_prune[idx1]
        d2 = self.twist_udslice_prune[idx2]
        return max(d1, d2)

    def _phase1_search(self, moves, depth, max_depth,
                       twist_s, flip_s, udslice_s, total_max):
        """Recursive IDA* for phase 1.

        Returns True if we should stop searching (solution found or timeout).
        """
        import time

        twist = twist_s[depth]
        flip = flip_s[depth]
        udslice = udslice_s[depth]

        if depth == max_depth:
            # Check if we reached G1
            if twist == 0 and flip == 0 and udslice == 0:
                # Phase 1 solved! Now try phase 2.
                return self._start_phase2(moves[:depth], total_max - depth)
            return False

        # Pruning
        remaining = max_depth - depth
        if self._phase1_prune(twist, flip, udslice) > remaining:
            return False

        last_move = moves[depth - 1] if depth > 0 else -1
        for m in range(18):
            if not _moves_compatible(last_move, m):
                continue

            if time.time() > self._timeout:
                return True

            moves[depth] = m
            twist_s[depth + 1] = self.twist_move[twist][m]
            flip_s[depth + 1] = self.flip_move[flip][m]
            udslice_s[depth + 1] = self.udslice_move[udslice][m]

            if self._phase1_search(moves, depth + 1, max_depth,
                                   twist_s, flip_s, udslice_s, total_max):
                return True
        return False

    def _start_phase2(self, phase1_moves, max_phase2_depth):
        """Initialize and run phase 2 search after phase 1 solution found."""
        import time

        # Apply phase 1 moves to get the G1 state
        cube2 = self._cube.copy()
        for m in phase1_moves:
            cube2.apply_move(MOVE_CUBES[m])

        # Extract phase 2 coordinates
        cperm = coord.get_cperm(cube2)
        ud_edges = coord.get_ud_edges_perm(cube2)
        udslice_sorted = coord.get_udslice_sorted(cube2)

        if cperm == 0 and ud_edges == 0 and udslice_sorted == 0:
            # Already solved after phase 1!
            self._best_solution = list(phase1_moves)
            self._phase1_length = len(phase1_moves)
            return True

        n_phase2_moves = len(PHASE2_MOVES)

        # Try increasing phase 2 depths
        for phase2_depth in range(1, max_phase2_depth + 1):
            if time.time() > self._timeout:
                return True

            phase2_moves = [-1] * phase2_depth  # indices into PHASE2_MOVES

            cperm_s = [0] * (phase2_depth + 1)
            ud_edges_s = [0] * (phase2_depth + 1)
            uds_s = [0] * (phase2_depth + 1)
            cperm_s[0] = cperm
            ud_edges_s[0] = ud_edges
            uds_s[0] = udslice_sorted

            if self._phase2_search(
                phase2_moves, 0, phase2_depth,
                cperm_s, ud_edges_s, uds_s,
                phase1_moves
            ):
                return True
        return False

    def _phase2_prune(self, cperm, ud_edges, udslice_sorted):
        """Phase 2 pruning: lower bound on moves to solve within G1."""
        n_uds = coord.N_UDSLICE_SORTED
        idx1 = cperm * n_uds + udslice_sorted
        idx2 = ud_edges * n_uds + udslice_sorted
        d1 = self.cperm_uds_prune[idx1]
        d2 = self.ud_edges_uds_prune[idx2]
        return max(d1, d2)

    def _phase2_search(self, moves, depth, max_depth,
                       cperm_s, ud_edges_s, uds_s,
                       phase1_moves):
        """Recursive IDA* for phase 2."""
        import time

        cperm = cperm_s[depth]
        ud_edges = ud_edges_s[depth]
        uds = uds_s[depth]

        if depth == max_depth:
            if cperm == 0 and ud_edges == 0 and uds == 0:
                # Solved!
                full_solution = list(phase1_moves)
                for i in range(depth):
                    full_solution.append(PHASE2_MOVES[moves[i]])
                self._best_solution = full_solution
                self._phase1_length = len(phase1_moves)
                return True
            return False

        remaining = max_depth - depth
        if self._phase2_prune(cperm, ud_edges, uds) > remaining:
            return False

        # Determine last move for filtering
        if depth > 0:
            last_real_move = PHASE2_MOVES[moves[depth - 1]]
        elif phase1_moves:
            last_real_move = phase1_moves[-1]
        else:
            last_real_move = -1

        for mi, m in enumerate(PHASE2_MOVES):
            if not _moves_compatible(last_real_move, m):
                continue

            if time.time() > self._timeout:
                return True

            moves[depth] = mi
            cperm_s[depth + 1] = self.cperm_move[cperm][mi]
            ud_edges_s[depth + 1] = self.ud_edges_move[ud_edges][mi]
            uds_s[depth + 1] = self.udslice_sorted_move[uds][mi]

            if self._phase2_search(moves, depth + 1, max_depth,
                                   cperm_s, ud_edges_s, uds_s,
                                   phase1_moves):
                return True
        return False
