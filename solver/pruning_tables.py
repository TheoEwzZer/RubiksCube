"""
Pruning tables for the Two-Phase algorithm.

Each pruning table stores the minimum number of moves needed to bring
a combined coordinate to its goal value (0). Generated via BFS.

Phase 1 pruning tables:
- flip_udslice_prune:  flip x udslice -> depth  (2048 * 495 = 1,013,760 entries)
- twist_udslice_prune: twist x udslice -> depth  (2187 * 495 = 1,082,565 entries)

Phase 2 pruning tables:
- cperm_udslice_sorted_prune:    cperm x udslice_sorted -> depth  (40320 * 24 = 967,680)
- ud_edges_udslice_sorted_prune: ud_edges x udslice_sorted -> depth (40320 * 24 = 967,680)
"""

import os
import pickle
from collections import deque

from . import coord
from .move_tables import (
    get_twist_move, get_flip_move, get_udslice_move,
    get_cperm_move, get_ud_edges_move, get_udslice_sorted_move,
)
from .cube_model import PHASE2_MOVES

CACHE_DIR = os.path.join(os.path.dirname(__file__), "tables_cache")


def _cache_path(name):
    os.makedirs(CACHE_DIR, exist_ok=True)
    return os.path.join(CACHE_DIR, f"{name}.pkl")


def _load_or_generate(name, generator):
    path = _cache_path(name)
    if os.path.exists(path):
        with open(path, "rb") as f:
            return pickle.load(f)
    table = generator()
    with open(path, "wb") as f:
        pickle.dump(table, f, protocol=pickle.HIGHEST_PROTOCOL)
    return table


# ===========================================================================
# Phase 1 pruning tables
# ===========================================================================

def _gen_flip_udslice_prune():
    """BFS over (flip, udslice) to compute minimum moves to reach (0, 0)."""
    n_flip = coord.N_FLIP
    n_udslice = coord.N_UDSLICE
    total = n_flip * n_udslice
    table = bytearray(b'\xff' * total)  # 0xFF = unvisited

    flip_move = get_flip_move()
    udslice_move = get_udslice_move()

    # Start from solved: flip=0, udslice=0
    table[0] = 0
    queue = deque()
    queue.append((0, 0, 0))  # (flip, udslice, depth)

    while queue:
        flip, udslice, depth = queue.popleft()
        for m in range(18):
            new_flip = flip_move[flip][m]
            new_udslice = udslice_move[udslice][m]
            idx = new_flip * n_udslice + new_udslice
            if table[idx] == 0xFF:
                table[idx] = depth + 1
                queue.append((new_flip, new_udslice, depth + 1))
    return bytes(table)


def _gen_twist_udslice_prune():
    """BFS over (twist, udslice) to compute minimum moves to reach (0, 0)."""
    n_twist = coord.N_TWIST
    n_udslice = coord.N_UDSLICE
    total = n_twist * n_udslice
    table = bytearray(b'\xff' * total)

    twist_move = get_twist_move()
    udslice_move = get_udslice_move()

    table[0] = 0
    queue = deque()
    queue.append((0, 0, 0))

    while queue:
        twist, udslice, depth = queue.popleft()
        for m in range(18):
            new_twist = twist_move[twist][m]
            new_udslice = udslice_move[udslice][m]
            idx = new_twist * n_udslice + new_udslice
            if table[idx] == 0xFF:
                table[idx] = depth + 1
                queue.append((new_twist, new_udslice, depth + 1))
    return bytes(table)


# ===========================================================================
# Phase 2 pruning tables
# ===========================================================================

def _gen_cperm_udslice_sorted_prune():
    """BFS over (cperm, udslice_sorted) with phase 2 moves."""
    n_cperm = coord.N_CPERM
    n_uds = coord.N_UDSLICE_SORTED
    total = n_cperm * n_uds
    table = bytearray(b'\xff' * total)

    cperm_move = get_cperm_move()
    uds_move = get_udslice_sorted_move()
    n_moves = len(PHASE2_MOVES)

    table[0] = 0
    queue = deque()
    queue.append((0, 0, 0))

    while queue:
        cperm, uds, depth = queue.popleft()
        for mi in range(n_moves):
            new_cperm = cperm_move[cperm][mi]
            new_uds = uds_move[uds][mi]
            idx = new_cperm * n_uds + new_uds
            if table[idx] == 0xFF:
                table[idx] = depth + 1
                queue.append((new_cperm, new_uds, depth + 1))
    return bytes(table)


def _gen_ud_edges_udslice_sorted_prune():
    """BFS over (ud_edges_perm, udslice_sorted) with phase 2 moves."""
    n_ud = coord.N_UD_EDGES
    n_uds = coord.N_UDSLICE_SORTED
    total = n_ud * n_uds
    table = bytearray(b'\xff' * total)

    ud_move = get_ud_edges_move()
    uds_move = get_udslice_sorted_move()
    n_moves = len(PHASE2_MOVES)

    table[0] = 0
    queue = deque()
    queue.append((0, 0, 0))

    while queue:
        ud, uds, depth = queue.popleft()
        for mi in range(n_moves):
            new_ud = ud_move[ud][mi]
            new_uds = uds_move[uds][mi]
            idx = new_ud * n_uds + new_uds
            if table[idx] == 0xFF:
                table[idx] = depth + 1
                queue.append((new_ud, new_uds, depth + 1))
    return bytes(table)


# ===========================================================================
# Public API: lazy-loaded tables
# ===========================================================================

_tables = {}

def get_flip_udslice_prune():
    if "flip_udslice" not in _tables:
        _tables["flip_udslice"] = _load_or_generate(
            "flip_udslice_prune", _gen_flip_udslice_prune)
    return _tables["flip_udslice"]

def get_twist_udslice_prune():
    if "twist_udslice" not in _tables:
        _tables["twist_udslice"] = _load_or_generate(
            "twist_udslice_prune", _gen_twist_udslice_prune)
    return _tables["twist_udslice"]

def get_cperm_udslice_sorted_prune():
    if "cperm_uds" not in _tables:
        _tables["cperm_uds"] = _load_or_generate(
            "cperm_udslice_sorted_prune", _gen_cperm_udslice_sorted_prune)
    return _tables["cperm_uds"]

def get_ud_edges_udslice_sorted_prune():
    if "ud_edges_uds" not in _tables:
        _tables["ud_edges_uds"] = _load_or_generate(
            "ud_edges_udslice_sorted_prune", _gen_ud_edges_udslice_sorted_prune)
    return _tables["ud_edges_uds"]
