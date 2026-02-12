"""
Coordinate system for the Two-Phase Kociemba algorithm.

Phase 1 coordinates:
- twist:    Corner orientation (0..2186), 3^7 values
- flip:     Edge orientation (0..2047), 2^11 values
- udslice:  Position of the 4 UD-slice edges FR,FL,BL,BR (0..494), C(12,4) values

Phase 2 coordinates:
- cperm:          Corner permutation (0..40319), 8! values
- ud_edges_perm:  Permutation of the 8 U/D edges (0..40319), 8! values
- udslice_sorted: Permutation of the 4 UD-slice edges in their positions (0..23), 4! values
"""

from .cube_model import CubieCube, MOVE_CUBES, FR, FL, BL, BR

# ---------------------------------------------------------------------------
# Combinatorial helpers
# ---------------------------------------------------------------------------

def _cnk(n, k):
    """Binomial coefficient C(n, k)."""
    if k < 0 or k > n:
        return 0
    if k == 0 or k == n:
        return 1
    k = min(k, n - k)
    result = 1
    for i in range(k):
        result = result * (n - i) // (i + 1)
    return result


_FACTORIAL = [1]
for _i in range(1, 13):
    _FACTORIAL.append(_FACTORIAL[-1] * _i)


def _perm_to_index(perm):
    """Convert a permutation to its Lehmer code index.
    perm is a list of distinct integers 0..n-1.
    Returns an index in range [0, n!).
    """
    n = len(perm)
    p = list(perm)
    index = 0
    for i in range(n):
        index += p[i] * _FACTORIAL[n - 1 - i]
        for j in range(i + 1, n):
            if p[j] > p[i]:
                p[j] -= 1
    return index


def _index_to_perm(index, n):
    """Convert a Lehmer code index to a permutation of n elements."""
    perm = [0] * n
    elements = list(range(n))
    for i in range(n):
        fact = _FACTORIAL[n - 1 - i]
        perm[i] = elements[index // fact]
        elements.remove(perm[i])
        index %= fact
    return perm


# ===========================================================================
# Phase 1 coordinates
# ===========================================================================

# --- Twist (corner orientation) ---

N_TWIST = 2187  # 3^7

def get_twist(cube):
    """Extract twist coordinate from CubieCube."""
    twist = 0
    for i in range(7):
        twist = twist * 3 + cube.co[i]
    return twist


def set_twist(cube, twist):
    """Set corner orientation of CubieCube from twist coordinate."""
    parity = 0
    for i in range(6, -1, -1):
        cube.co[i] = twist % 3
        parity += cube.co[i]
        twist //= 3
    cube.co[7] = (3 - parity % 3) % 3


def twist_to_cube(twist):
    """Create a CubieCube with only the twist coordinate set (identity otherwise)."""
    c = CubieCube()
    set_twist(c, twist)
    return c


# --- Flip (edge orientation) ---

N_FLIP = 2048  # 2^11

def get_flip(cube):
    """Extract flip coordinate from CubieCube."""
    flip = 0
    for i in range(11):
        flip = flip * 2 + cube.eo[i]
    return flip


def set_flip(cube, flip):
    """Set edge orientation of CubieCube from flip coordinate."""
    parity = 0
    for i in range(10, -1, -1):
        cube.eo[i] = flip % 2
        parity += cube.eo[i]
        flip //= 2
    cube.eo[11] = (2 - parity % 2) % 2


def flip_to_cube(flip):
    c = CubieCube()
    set_flip(c, flip)
    return c


# --- UD-Slice (which 4 of 12 edge positions hold UD-slice edges) ---

N_UDSLICE = 495  # C(12, 4)

UDSLICE_EDGES = {FR, FL, BL, BR}  # edge indices 8, 9, 10, 11

def get_udslice(cube):
    """Extract udslice coordinate (0 = solved, UD-slice edges at positions 8-11).
    Encodes which 4 of the 12 edge positions hold a UD-slice edge (FR/FL/BL/BR).
    """
    # Find positions occupied by UD-slice edges (sorted ascending)
    occ = [i for i in range(12) if cube.ep[i] >= 8]
    # Combinatorial number system encoding
    raw = sum(_cnk(occ[k], k + 1) for k in range(4))
    # Reverse so that solved position (8,9,10,11) gives index 0
    return N_UDSLICE - 1 - raw


def set_udslice(cube, index):
    """Set which 4 of 12 edge positions contain UD-slice edges.
    Only affects which positions have UD-slice vs non-UD-slice edges.
    The actual identity of the edges within each group is not set.
    """
    # Reverse the index mapping
    raw = N_UDSLICE - 1 - index

    # Decode combination: determine which 4 positions are occupied
    occupied = [False] * 12
    k = 3
    for i in range(11, -1, -1):
        c = _cnk(i, k + 1)
        if raw >= c:
            raw -= c
            occupied[i] = True
            k -= 1

    # Place UD-slice edges (8,9,10,11) in occupied positions
    # Place non-UD-slice edges (0..7) in unoccupied positions
    ud_idx = 8
    non_ud_idx = 0
    for i in range(12):
        if occupied[i]:
            cube.ep[i] = ud_idx
            ud_idx += 1
        else:
            cube.ep[i] = non_ud_idx
            non_ud_idx += 1


def udslice_to_cube(index):
    c = CubieCube()
    set_udslice(c, index)
    return c


# ===========================================================================
# Phase 2 coordinates
# ===========================================================================

# --- Corner Permutation ---

N_CPERM = 40320  # 8!

def get_cperm(cube):
    return _perm_to_index(cube.cp)


def set_cperm(cube, index):
    cube.cp = _index_to_perm(index, 8)


def cperm_to_cube(index):
    c = CubieCube()
    set_cperm(c, index)
    return c


# --- UD Edges Permutation (the 8 non-UD-slice edges: UR,UF,UL,UB,DR,DF,DL,DB) ---

N_UD_EDGES = 40320  # 8!

def get_ud_edges_perm(cube):
    """Extract the permutation of the 8 U/D layer edges (indices 0-7).
    Only valid when UD-slice edges are already in the UD-slice (phase 2).
    """
    return _perm_to_index(cube.ep[:8])


def set_ud_edges_perm(cube, index):
    """Set the permutation of the 8 U/D edges."""
    cube.ep[:8] = _index_to_perm(index, 8)


def ud_edges_to_cube(index):
    c = CubieCube()
    set_ud_edges_perm(c, index)
    return c


# --- UD-Slice Sorted (permutation of the 4 UD-slice edges within their positions) ---

N_UDSLICE_SORTED = 24  # 4!

def get_udslice_sorted(cube):
    """Extract the permutation of the 4 UD-slice edges among positions 8-11.
    Only valid when UD-slice edges are in the UD-slice (phase 2).
    Maps ep[8..11] (which should be a permutation of {8,9,10,11}) to index 0..23.
    """
    # Normalize: subtract 8 so we have a permutation of {0,1,2,3}
    perm = [cube.ep[i] - 8 for i in range(8, 12)]
    return _perm_to_index(perm)


def set_udslice_sorted(cube, index):
    """Set the permutation of the 4 UD-slice edges in positions 8-11."""
    perm = _index_to_perm(index, 4)
    for i in range(4):
        cube.ep[8 + i] = perm[i] + 8


def udslice_sorted_to_cube(index):
    c = CubieCube()
    set_udslice_sorted(c, index)
    return c


# ===========================================================================
# Combined Phase 1 coordinate: flip_udslice
# ===========================================================================

N_FLIP_UDSLICE = N_FLIP * N_UDSLICE       # 2048 * 495 = 1,013,760
N_TWIST_UDSLICE = N_TWIST * N_UDSLICE     # 2187 * 495 = 1,082,565

# ===========================================================================
# Combined Phase 2 coordinates
# ===========================================================================

N_CPERM_UDSLICE_SORTED = N_CPERM * N_UDSLICE_SORTED        # 40320 * 24 = 967,680
N_UD_EDGES_UDSLICE_SORTED = N_UD_EDGES * N_UDSLICE_SORTED  # 40320 * 24 = 967,680
