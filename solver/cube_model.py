"""
Rubik's Cube cubie-level representation.

Defines the cube as 8 corner cubies and 12 edge cubies,
each with a permutation and an orientation.
Implements the 6 basic face moves (U, R, F, D, L, B) and their compositions.

Conventions:
- cp[i] = j means: after the move, position i holds the cubie that was at position j.
- co[i] = orientation change (mod 3) for the cubie now at position i.
- ep[i], eo[i]: same for edges (eo mod 2).
"""

# ---------------------------------------------------------------------------
# Corner and edge position enums
# ---------------------------------------------------------------------------
URF, UFL, ULB, UBR, DFR, DLF, DBL, DRB = range(8)
UR, UF, UL, UB, DR, DF, DL, DB, FR, FL, BL, BR = range(12)

# Face color indices
U_FACE, R_FACE, F_FACE, D_FACE, L_FACE, B_FACE = range(6)

CORNER_NAMES = ["URF", "UFL", "ULB", "UBR", "DFR", "DLF", "DBL", "DRB"]
EDGE_NAMES = ["UR", "UF", "UL", "UB", "DR", "DF", "DL", "DB", "FR", "FL", "BL", "BR"]
FACE_NAMES = ["U", "R", "F", "D", "L", "B"]
COLOR_CHARS = "URFDLB"

# ---------------------------------------------------------------------------
# Facelet mapping
# ---------------------------------------------------------------------------
# Each face has 9 facelets numbered 0-8:
#   0 1 2
#   3 4 5
#   6 7 8
# Absolute facelet index = face * 9 + position

# Corner facelets: (U/D facelet, clockwise facelet, counter-clockwise facelet)
# "Clockwise" means the next facelet going clockwise when looking at the corner
# from outside the cube along the diagonal axis.
CORNER_FACELETS = [
    (U_FACE * 9 + 8, R_FACE * 9 + 0, F_FACE * 9 + 2),   # URF
    (U_FACE * 9 + 6, F_FACE * 9 + 0, L_FACE * 9 + 2),   # UFL
    (U_FACE * 9 + 0, L_FACE * 9 + 0, B_FACE * 9 + 2),   # ULB
    (U_FACE * 9 + 2, B_FACE * 9 + 0, R_FACE * 9 + 2),   # UBR
    (D_FACE * 9 + 2, F_FACE * 9 + 8, R_FACE * 9 + 6),   # DFR
    (D_FACE * 9 + 0, L_FACE * 9 + 8, F_FACE * 9 + 6),   # DLF
    (D_FACE * 9 + 6, B_FACE * 9 + 8, L_FACE * 9 + 6),   # DBL
    (D_FACE * 9 + 8, R_FACE * 9 + 8, B_FACE * 9 + 6),   # DRB
]

# Edge facelets: (primary facelet, secondary facelet)
# Primary = the U/D facelet for UD edges, or the F/B facelet for E-slice edges.
EDGE_FACELETS = [
    (U_FACE * 9 + 5, R_FACE * 9 + 1),   # UR
    (U_FACE * 9 + 7, F_FACE * 9 + 1),   # UF
    (U_FACE * 9 + 3, L_FACE * 9 + 1),   # UL
    (U_FACE * 9 + 1, B_FACE * 9 + 1),   # UB
    (D_FACE * 9 + 5, R_FACE * 9 + 7),   # DR
    (D_FACE * 9 + 7, F_FACE * 9 + 7),   # DF
    (D_FACE * 9 + 3, L_FACE * 9 + 7),   # DL
    (D_FACE * 9 + 1, B_FACE * 9 + 7),   # DB
    (F_FACE * 9 + 5, R_FACE * 9 + 3),   # FR
    (F_FACE * 9 + 3, L_FACE * 9 + 5),   # FL
    (B_FACE * 9 + 5, L_FACE * 9 + 3),   # BL
    (B_FACE * 9 + 3, R_FACE * 9 + 5),   # BR
]

# Colors at each corner position in the solved state (U/D color, CW color, CCW color)
CORNER_COLORS = [
    (U_FACE, R_FACE, F_FACE),  # URF
    (U_FACE, F_FACE, L_FACE),  # UFL
    (U_FACE, L_FACE, B_FACE),  # ULB
    (U_FACE, B_FACE, R_FACE),  # UBR
    (D_FACE, F_FACE, R_FACE),  # DFR
    (D_FACE, L_FACE, F_FACE),  # DLF
    (D_FACE, B_FACE, L_FACE),  # DBL
    (D_FACE, R_FACE, B_FACE),  # DRB
]

# Colors at each edge position in the solved state (primary, secondary)
EDGE_COLORS = [
    (U_FACE, R_FACE),  # UR
    (U_FACE, F_FACE),  # UF
    (U_FACE, L_FACE),  # UL
    (U_FACE, B_FACE),  # UB
    (D_FACE, R_FACE),  # DR
    (D_FACE, F_FACE),  # DF
    (D_FACE, L_FACE),  # DL
    (D_FACE, B_FACE),  # DB
    (F_FACE, R_FACE),  # FR
    (F_FACE, L_FACE),  # FL
    (B_FACE, L_FACE),  # BL
    (B_FACE, R_FACE),  # BR
]


# ---------------------------------------------------------------------------
# CubieCube class
# ---------------------------------------------------------------------------
class CubieCube:
    """Represents a Rubik's cube state at the cubie level."""

    def __init__(self, cp=None, co=None, ep=None, eo=None):
        self.cp = list(cp) if cp else list(range(8))
        self.co = list(co) if co else [0] * 8
        self.ep = list(ep) if ep else list(range(12))
        self.eo = list(eo) if eo else [0] * 12

    def copy(self):
        return CubieCube(self.cp, self.co, self.ep, self.eo)

    def multiply(self, other):
        """Return self * other (apply self first, then other).

        Convention: cp_result[i] = self.cp[other.cp[i]]
        This means other's permutation is applied first to determine which
        position in self's result to read from.
        """
        result = CubieCube()
        for i in range(8):
            result.cp[i] = self.cp[other.cp[i]]
            result.co[i] = (self.co[other.cp[i]] + other.co[i]) % 3
        for i in range(12):
            result.ep[i] = self.ep[other.ep[i]]
            result.eo[i] = (self.eo[other.ep[i]] + other.eo[i]) % 2
        return result

    def apply_move(self, move_cube):
        """Apply a move (given as CubieCube) to this state. Modifies in place."""
        new_cp = [0] * 8
        new_co = [0] * 8
        new_ep = [0] * 12
        new_eo = [0] * 12
        for i in range(8):
            new_cp[i] = self.cp[move_cube.cp[i]]
            new_co[i] = (self.co[move_cube.cp[i]] + move_cube.co[i]) % 3
        for i in range(12):
            new_ep[i] = self.ep[move_cube.ep[i]]
            new_eo[i] = (self.eo[move_cube.ep[i]] + move_cube.eo[i]) % 2
        self.cp = new_cp
        self.co = new_co
        self.ep = new_ep
        self.eo = new_eo

    def inverse(self):
        """Return the inverse of this cube state."""
        inv = CubieCube()
        for i in range(8):
            inv.cp[self.cp[i]] = i
            inv.co[self.cp[i]] = (3 - self.co[i]) % 3
        for i in range(12):
            inv.ep[self.ep[i]] = i
            inv.eo[self.ep[i]] = self.eo[i]  # eo is its own inverse mod 2
        return inv

    def is_solved(self):
        return (self.cp == list(range(8)) and self.co == [0] * 8
                and self.ep == list(range(12)) and self.eo == [0] * 12)

    def __eq__(self, other):
        return (self.cp == other.cp and self.co == other.co
                and self.ep == other.ep and self.eo == other.eo)

    def __repr__(self):
        return f"CubieCube(cp={self.cp}, co={self.co}, ep={self.ep}, eo={self.eo})"

    # -----------------------------------------------------------------------
    # Facelet string conversion
    # -----------------------------------------------------------------------
    def to_facelet_string(self):
        """Convert cubie state to a 54-character facelet string (URFDLB order)."""
        facelets = [0] * 54
        # Center facelets are always fixed
        for f in range(6):
            facelets[f * 9 + 4] = f

        # Corners
        for i in range(8):
            cubie = self.cp[i]
            ori = self.co[i]
            for k in range(3):
                facelet_idx = CORNER_FACELETS[i][(k + 3 - ori) % 3]
                facelets[facelet_idx] = CORNER_COLORS[cubie][k]

        # Edges
        for i in range(12):
            cubie = self.ep[i]
            ori = self.eo[i]
            for k in range(2):
                facelet_idx = EDGE_FACELETS[i][(k + ori) % 2]
                facelets[facelet_idx] = EDGE_COLORS[cubie][k]

        return "".join(COLOR_CHARS[c] for c in facelets)

    @classmethod
    def from_facelet_string(cls, s):
        """Create CubieCube from a 54-character facelet string (URFDLB order).

        The string uses characters U, R, F, D, L, B for the 6 face colors.
        """
        if len(s) != 54:
            raise ValueError(f"Facelet string must be 54 characters, got {len(s)}")

        color_map = {c: i for i, c in enumerate(COLOR_CHARS)}
        facelets = []
        for ch in s:
            if ch not in color_map:
                raise ValueError(f"Invalid character '{ch}' in facelet string")
            facelets.append(color_map[ch])

        cube = cls()

        # Decode corners
        for i in range(8):
            f0, f1, f2 = CORNER_FACELETS[i]
            c0, c1, c2 = facelets[f0], facelets[f1], facelets[f2]
            colors = (c0, c1, c2)

            # Find which corner cubie this is and its orientation
            found = False
            for j in range(8):
                tc = CORNER_COLORS[j]
                # Try each orientation
                for ori in range(3):
                    if (colors[0] == tc[(0 + ori) % 3]
                            and colors[1] == tc[(1 + ori) % 3]
                            and colors[2] == tc[(2 + ori) % 3]):
                        cube.cp[i] = j
                        cube.co[i] = ori
                        found = True
                        break
                if found:
                    break
            if not found:
                raise ValueError(f"Invalid corner at position {CORNER_NAMES[i]}: "
                                 f"colors {tuple(COLOR_CHARS[c] for c in colors)}")

        # Decode edges
        for i in range(12):
            f0, f1 = EDGE_FACELETS[i]
            c0, c1 = facelets[f0], facelets[f1]

            found = False
            for j in range(12):
                te = EDGE_COLORS[j]
                if c0 == te[0] and c1 == te[1]:
                    cube.ep[i] = j
                    cube.eo[i] = 0
                    found = True
                    break
                elif c0 == te[1] and c1 == te[0]:
                    cube.ep[i] = j
                    cube.eo[i] = 1
                    found = True
                    break
            if not found:
                raise ValueError(f"Invalid edge at position {EDGE_NAMES[i]}: "
                                 f"colors ({COLOR_CHARS[c0]}, {COLOR_CHARS[c1]})")

        return cube

    def validate(self):
        """Check if this is a valid, solvable cube state. Returns error message or None."""
        # Check corner permutation
        if sorted(self.cp) != list(range(8)):
            return "Invalid corner permutation"
        # Check edge permutation
        if sorted(self.ep) != list(range(12)):
            return "Invalid edge permutation"
        # Check corner orientation sum
        if sum(self.co) % 3 != 0:
            return "Corner orientation sum must be divisible by 3"
        # Check edge orientation sum
        if sum(self.eo) % 2 != 0:
            return "Edge orientation sum must be divisible by 2"
        # Check parity (corner parity must equal edge parity)
        cp_parity = _perm_parity(self.cp)
        ep_parity = _perm_parity(self.ep)
        if cp_parity != ep_parity:
            return "Corner and edge permutation parities must match"
        return None


def _perm_parity(perm):
    """Return 0 for even permutation, 1 for odd."""
    n = len(perm)
    visited = [False] * n
    parity = 0
    for i in range(n):
        if not visited[i]:
            visited[i] = True
            j = perm[i]
            cycle_len = 1
            while j != i:
                visited[j] = True
                j = perm[j]
                cycle_len += 1
            if cycle_len % 2 == 0:
                parity ^= 1
    return parity


# ---------------------------------------------------------------------------
# The 6 basic face moves as CubieCube objects
# ---------------------------------------------------------------------------

# U move (upper face clockwise from top)
# Cycle: UBR->URF->UFL->ULB->UBR (each cubie moves clockwise)
_move_U = CubieCube(
    cp=[UBR, URF, UFL, ULB, DFR, DLF, DBL, DRB],
    co=[0, 0, 0, 0, 0, 0, 0, 0],
    ep=[UB, UR, UF, UL, DR, DF, DL, DB, FR, FL, BL, BR],
    eo=[0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0],
)

# R move (right face clockwise from right)
# Cycle: URF->UBR->DRB->DFR->URF
_move_R = CubieCube(
    cp=[DFR, UFL, ULB, URF, DRB, DLF, DBL, UBR],
    co=[2, 0, 0, 1, 1, 0, 0, 2],
    ep=[FR, UF, UL, UB, BR, DF, DL, DB, DR, FL, BL, UR],
    eo=[0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0],
)

# F move (front face clockwise from front)
# Cycle: UFL->URF->DFR->DLF->UFL
_move_F = CubieCube(
    cp=[UFL, DLF, ULB, UBR, URF, DFR, DBL, DRB],
    co=[1, 2, 0, 0, 2, 1, 0, 0],
    ep=[UR, FL, UL, UB, DR, FR, DL, DB, UF, DF, BL, BR],
    eo=[0, 1, 0, 0, 0, 1, 0, 0, 1, 1, 0, 0],
)

# D move (down face clockwise from bottom)
# Cycle: DFR->DRB->DBL->DLF->DFR (clockwise from below)
_move_D = CubieCube(
    cp=[URF, UFL, ULB, UBR, DLF, DBL, DRB, DFR],
    co=[0, 0, 0, 0, 0, 0, 0, 0],
    ep=[UR, UF, UL, UB, DF, DL, DB, DR, FR, FL, BL, BR],
    eo=[0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0],
)

# L move (left face clockwise from left)
# Cycle: UFL->ULB->DBL->DLF->UFL
_move_L = CubieCube(
    cp=[URF, ULB, DBL, UBR, DFR, UFL, DLF, DRB],
    co=[0, 1, 2, 0, 0, 2, 1, 0],
    ep=[UR, UF, BL, UB, DR, DF, FL, DB, FR, UL, DL, BR],
    eo=[0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0],
)

# B move (back face clockwise from back)
# Cycle: UBR->ULB->DBL->DRB->UBR
_move_B = CubieCube(
    cp=[URF, UFL, UBR, DRB, DFR, DLF, ULB, DBL],
    co=[0, 0, 1, 2, 0, 0, 2, 1],
    ep=[UR, UF, UL, BR, DR, DF, DL, BL, FR, FL, UB, DB],
    eo=[0, 0, 0, 1, 0, 0, 0, 1, 0, 0, 1, 1],
)

# ---------------------------------------------------------------------------
# Build all 18 moves: U, U2, U', R, R2, R', F, F2, F', D, D2, D', L, L2, L', B, B2, B'
# ---------------------------------------------------------------------------
BASIC_MOVES = [_move_U, _move_R, _move_F, _move_D, _move_L, _move_B]
MOVE_CUBES = []  # 18 entries: [U, U2, U', R, R2, R', F, F2, F', D, D2, D', L, L2, L', B, B2, B']

for m in BASIC_MOVES:
    m2 = m.multiply(m)
    m3 = m2.multiply(m)  # m' = m^3
    MOVE_CUBES.append(m)
    MOVE_CUBES.append(m2)
    MOVE_CUBES.append(m3)

# Move name strings
MOVE_NAMES = []
for face in ["U", "R", "F", "D", "L", "B"]:
    MOVE_NAMES.append(face)
    MOVE_NAMES.append(face + "2")
    MOVE_NAMES.append(face + "'")

# Phase 2 allowed moves: U, U2, U', D, D2, D', R2, L2, F2, B2
# Indices in MOVE_CUBES: U=0,U2=1,U'=2, D=9,D2=10,D'=11, R2=4, L2=13, F2=7, B2=16
PHASE2_MOVES = [0, 1, 2, 9, 10, 11, 4, 13, 7, 16]
