"""
Rubik's Cube Solver - Main Entry Point

Controls:
- U/D/R/L/F/B keys: rotate faces (+ Shift for inverse)
- Mouse: right-click drag to orbit, scroll to zoom
"""

import sys
import os
import threading

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from ursina import *

# Pre-load solver tables in background
def _preload_tables():
    from solver.solver import initialize
    initialize()
    print("[Solver] Tables chargees.")

threading.Thread(target=_preload_tables, daemon=True).start()

app = Ursina(
    title="Rubik's Cube Solver",
    borderless=False,
    fullscreen=False,
    development_mode=False,
)

# Dark background
from panda3d.core import LVecBase4f
base.setBackgroundColor(LVecBase4f(0.12, 0.12, 0.16, 1))
window.fps_counter.enabled = False
window.exit_button.visible = False

# Camera: use EditorCamera properties for initial view (not camera.position)
ec = EditorCamera(rotation_smoothing=4, zoom_speed=1.5)
ec.rotation_x = 25    # tilt down
ec.rotation_y = -40   # orbit right
camera.z = -10        # zoom distance

# Title
Text(
    text="Rubik's Cube Solver",
    parent=camera.ui,
    position=(-0.84, 0.47),
    scale=1.4,
    color=color.white,
)
Text(
    text='Two-Phase Kociemba | Custom Implementation',
    parent=camera.ui,
    position=(-0.84, 0.43),
    scale=0.75,
    color=color.rgb32(140, 140, 170),
)

# MVC
from model.cube_state import GameCubeState
from view.cube_renderer import CubeRenderer
from view.ui_panel import UIPanel
from controller.app_controller import AppController

game_state = GameCubeState()
renderer = CubeRenderer()
controller = None

def on_scramble(): controller.scramble()
def on_solve(): controller.solve()
def on_reset(): controller.reset()
def on_speed_change(val): controller.set_speed(val)
def on_mode_change(mode): pass
def on_pause(): controller.pause()
def on_resume(): controller.resume()
def on_step(): controller.step()
def on_undo(): controller.undo()

ui = UIPanel(
    on_scramble=on_scramble, on_solve=on_solve, on_reset=on_reset,
    on_speed_change=on_speed_change, on_mode_change=on_mode_change,
    on_pause=on_pause, on_resume=on_resume, on_step=on_step, on_undo=on_undo,
)

controller = AppController(game_state, renderer, ui)

def input(key):
    controller.handle_input(key)

app.run()
