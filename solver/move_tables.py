"""
Move tables for the Two-Phase algorithm.

For each coordinate and each of the 18 moves, pre-compute the resulting coordinate.
Tables are generated once and cached to disk for subsequent runs.
"""

import os
import pickle

from .cube_model import CubieCube, MOVE_CUBES, PHASE2_MOVES
from . import coord

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
# Phase 1 move tables
# ===========================================================================

def _gen_twist_move():
    """twist_move[twist][move] = new_twist after applying move."""
    table = [[0] * 18 for _ in range(coord.N_TWIST)]
    c = CubieCube()
    for i in range(coord.N_TWIST):
        coord.set_twist(c, i)
        for m in range(18):
            cc = c.copy()
            cc.apply_move(MOVE_CUBES[m])
            table[i][m] = coord.get_twist(cc)
        # Reset for next iteration
        c.co = [0] * 8
    return table


def _gen_flip_move():
    """flip_move[flip][move] = new_flip after applying move."""
    table = [[0] * 18 for _ in range(coord.N_FLIP)]
    c = CubieCube()
    for i in range(coord.N_FLIP):
        coord.set_flip(c, i)
        for m in range(18):
            cc = c.copy()
            cc.apply_move(MOVE_CUBES[m])
            table[i][m] = coord.get_flip(cc)
        c.eo = [0] * 12
    return table


def _gen_udslice_move():
    """udslice_move[udslice][move] = new_udslice after applying move."""
    table = [[0] * 18 for _ in range(coord.N_UDSLICE)]
    c = CubieCube()
    for i in range(coord.N_UDSLICE):
        coord.set_udslice(c, i)
        for m in range(18):
            cc = c.copy()
            cc.apply_move(MOVE_CUBES[m])
            table[i][m] = coord.get_udslice(cc)
        # Reset
        c.ep = list(range(12))
    return table


# ===========================================================================
# Phase 2 move tables
# ===========================================================================

def _gen_cperm_move():
    """cperm_move[cperm][move_index] = new_cperm.
    Only phase 2 moves (10 moves).
    """
    n_phase2 = len(PHASE2_MOVES)
    table = [[0] * n_phase2 for _ in range(coord.N_CPERM)]
    c = CubieCube()
    for i in range(coord.N_CPERM):
        coord.set_cperm(c, i)
        for mi, m in enumerate(PHASE2_MOVES):
            cc = c.copy()
            cc.apply_move(MOVE_CUBES[m])
            table[i][mi] = coord.get_cperm(cc)
        c.cp = list(range(8))
    return table


def _gen_ud_edges_move():
    """ud_edges_move[ud_edges_perm][move_index] = new_ud_edges_perm.
    Only phase 2 moves.
    """
    n_phase2 = len(PHASE2_MOVES)
    table = [[0] * n_phase2 for _ in range(coord.N_UD_EDGES)]
    c = CubieCube()
    for i in range(coord.N_UD_EDGES):
        coord.set_ud_edges_perm(c, i)
        # UD-slice edges must be identity in positions 8-11 for phase 2
        for k in range(4):
            c.ep[8 + k] = 8 + k
        for mi, m in enumerate(PHASE2_MOVES):
            cc = c.copy()
            cc.apply_move(MOVE_CUBES[m])
            table[i][mi] = coord.get_ud_edges_perm(cc)
        c.ep = list(range(12))
    return table


def _gen_udslice_sorted_move():
    """udslice_sorted_move[udslice_sorted][move_index] = new_udslice_sorted.
    Only phase 2 moves.
    """
    n_phase2 = len(PHASE2_MOVES)
    table = [[0] * n_phase2 for _ in range(coord.N_UDSLICE_SORTED)]
    c = CubieCube()
    for i in range(coord.N_UDSLICE_SORTED):
        # Set UD-edges to identity and only vary udslice_sorted
        c.ep[:8] = list(range(8))
        coord.set_udslice_sorted(c, i)
        for mi, m in enumerate(PHASE2_MOVES):
            cc = c.copy()
            cc.apply_move(MOVE_CUBES[m])
            table[i][mi] = coord.get_udslice_sorted(cc)
        c.ep = list(range(12))
    return table


# ===========================================================================
# Public API: lazy-loaded tables
# ===========================================================================

_tables = {}

def get_twist_move():
    if "twist" not in _tables:
        _tables["twist"] = _load_or_generate("twist_move", _gen_twist_move)
    return _tables["twist"]

def get_flip_move():
    if "flip" not in _tables:
        _tables["flip"] = _load_or_generate("flip_move", _gen_flip_move)
    return _tables["flip"]

def get_udslice_move():
    if "udslice" not in _tables:
        _tables["udslice"] = _load_or_generate("udslice_move", _gen_udslice_move)
    return _tables["udslice"]

def get_cperm_move():
    if "cperm" not in _tables:
        _tables["cperm"] = _load_or_generate("cperm_move", _gen_cperm_move)
    return _tables["cperm"]

def get_ud_edges_move():
    if "ud_edges" not in _tables:
        _tables["ud_edges"] = _load_or_generate("ud_edges_move", _gen_ud_edges_move)
    return _tables["ud_edges"]

def get_udslice_sorted_move():
    if "udslice_sorted" not in _tables:
        _tables["udslice_sorted"] = _load_or_generate(
            "udslice_sorted_move", _gen_udslice_sorted_move)
    return _tables["udslice_sorted"]
