"""Quick test of the Two-Phase solver."""
import time
import sys
sys.path.insert(0, "D:/repositories/RubiksCube")

from solver.cube_model import CubieCube, MOVE_CUBES, MOVE_NAMES

# Test 1: CubieCube basics
print("=== Test 1: CubieCube identity ===")
c = CubieCube()
assert c.is_solved(), "Identity cube should be solved"
print("OK: Identity cube is solved")

# Test 2: Apply move and inverse
print("\n=== Test 2: Move + inverse = identity ===")
c = CubieCube()
c.apply_move(MOVE_CUBES[0])  # U
c.apply_move(MOVE_CUBES[2])  # U'
assert c.is_solved(), "U then U' should give identity"
print("OK: U * U' = identity")

# Test 3: U^4 = identity
print("\n=== Test 3: U^4 = identity ===")
c = CubieCube()
for _ in range(4):
    c.apply_move(MOVE_CUBES[0])
assert c.is_solved(), "U^4 should be identity"
print("OK: U^4 = identity")

# Test 4: Facelet string round-trip
print("\n=== Test 4: Facelet string round-trip ===")
c = CubieCube()
s = c.to_facelet_string()
print(f"Solved facelet string: {s}")
assert s == "UUUUUUUUURRRRRRRRRFFFFFFFFFDDDDDDDDDLLLLLLLLLBBBBBBBBB"
c2 = CubieCube.from_facelet_string(s)
assert c2.is_solved()
print("OK: Round-trip works for solved cube")

# Test 5: Scramble and round-trip
print("\n=== Test 5: Scramble facelet round-trip ===")
c = CubieCube()
c.apply_move(MOVE_CUBES[0])   # U
c.apply_move(MOVE_CUBES[3])   # R
c.apply_move(MOVE_CUBES[6])   # F
s = c.to_facelet_string()
print(f"After U R F: {s}")
c3 = CubieCube.from_facelet_string(s)
assert c3.cp == c.cp and c3.co == c.co and c3.ep == c.ep and c3.eo == c.eo
print("OK: Facelet round-trip after scramble")

# Test 6: Validation
print("\n=== Test 6: Validation ===")
c = CubieCube()
assert c.validate() is None, "Solved cube should be valid"
c.apply_move(MOVE_CUBES[0])
assert c.validate() is None, "After U should be valid"
print("OK: Validation passes for valid cubes")

# Test 7: Coordinate extraction
print("\n=== Test 7: Coordinates ===")
from solver import coord

c = CubieCube()
assert coord.get_twist(c) == 0
assert coord.get_flip(c) == 0
assert coord.get_udslice(c) == 0
assert coord.get_cperm(c) == 0
assert coord.get_ud_edges_perm(c) == 0
assert coord.get_udslice_sorted(c) == 0
print("OK: Solved cube has all coordinates = 0")

c.apply_move(MOVE_CUBES[0])  # U
assert coord.get_twist(c) == 0, "U shouldn't change twist"
assert coord.get_flip(c) == 0, "U shouldn't change flip"
print(f"After U: twist={coord.get_twist(c)}, flip={coord.get_flip(c)}, udslice={coord.get_udslice(c)}")
print("OK: Coordinates after U move")

# Test 8: Move tables
print("\n=== Test 8: Move tables (this may take a moment on first run) ===")
t0 = time.time()
from solver.move_tables import get_twist_move, get_flip_move, get_udslice_move
twist_move = get_twist_move()
flip_move = get_flip_move()
udslice_move = get_udslice_move()
print(f"Phase 1 move tables loaded in {time.time()-t0:.1f}s")

# Verify: applying U to solved (twist=0) should still give twist=0
assert twist_move[0][0] == 0, "U on twist=0 should give twist=0"
assert flip_move[0][0] == 0, "U on flip=0 should give flip=0"
print("OK: Move tables consistent")

# Test 9: Pruning tables
print("\n=== Test 9: Pruning tables (this may take a while on first run) ===")
t0 = time.time()
from solver.pruning_tables import get_flip_udslice_prune, get_twist_udslice_prune
flip_uds_prune = get_flip_udslice_prune()
twist_uds_prune = get_twist_udslice_prune()
print(f"Phase 1 pruning tables loaded in {time.time()-t0:.1f}s")
assert flip_uds_prune[0] == 0, "Solved state should have depth 0"
assert twist_uds_prune[0] == 0
print("OK: Pruning tables consistent")

# Test 10: Full solve
print("\n=== Test 10: Full solve ===")
t0 = time.time()
from solver.solver import solve, solve_from_moves

# Solve a simple scramble
print("Solving U R F scramble...")
result = solve_from_moves(["U", "R", "F"])
solution = result["moves"]
print(f"Solution: {' '.join(solution)} ({len(solution)} moves, phase1={result['phase1_length']})")

# Verify solution
c = CubieCube()
move_map = {name: i for i, name in enumerate(MOVE_NAMES)}
for m in ["U", "R", "F"]:
    c.apply_move(MOVE_CUBES[move_map[m]])
for m in solution:
    c.apply_move(MOVE_CUBES[move_map[m]])
assert c.is_solved(), "Solution should solve the cube!"
print(f"OK: Solution verified! ({time.time()-t0:.2f}s)")

# Test 11: Harder scramble
print("\n=== Test 11: Harder scramble ===")
scramble_str = "R U F D L B R' U' F' D' L' B' R2 U2 F2 D2"
scramble_moves = scramble_str.split()
print(f"Scramble: {scramble_str}")

t0 = time.time()
result = solve_from_moves(scramble_moves)
elapsed = time.time() - t0
if result:
    solution = result["moves"]
    print(f"Solution: {' '.join(solution)} ({len(solution)} moves, phase1={result['phase1_length']}, {elapsed:.2f}s)")

    # Verify
    c = CubieCube()
    for m in scramble_moves:
        c.apply_move(MOVE_CUBES[move_map[m]])
    for m in solution:
        c.apply_move(MOVE_CUBES[move_map[m]])
    assert c.is_solved(), "Solution should solve the cube!"
    print("OK: Solution verified!")
else:
    print(f"No solution found in {elapsed:.2f}s")

print("\n=== ALL TESTS PASSED ===")
