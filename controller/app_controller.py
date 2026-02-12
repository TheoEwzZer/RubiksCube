"""
Main application controller.

Orchestrates the cube state (model), 3D renderer (view), and UI panel.
Handles keyboard input for manual mode and AI solve sequencing.
"""

import threading
import time
from ursina import *


_MOVE_FR = {
    'R': "Droite \u21bb", "R'": "Droite \u21ba", 'R2': "Droite 180\u00b0",
    'U': "Haut \u21bb",   "U'": "Haut \u21ba",   'U2': "Haut 180\u00b0",
    'F': "Face \u21bb",   "F'": "Face \u21ba",   'F2': "Face 180\u00b0",
    'D': "Bas \u21bb",    "D'": "Bas \u21ba",    'D2': "Bas 180\u00b0",
    'L': "Gauche \u21bb", "L'": "Gauche \u21ba", 'L2': "Gauche 180\u00b0",
    'B': "Arriere \u21bb","B'": "Arriere \u21ba",'B2': "Arriere 180\u00b0",
}

_PHASE1_TITLE = "Phase 1 : Orientation"
_PHASE1_DESC = (
    "On oriente toutes les aretes et les coins correctement,\n"
    "et on place les 4 aretes de la tranche du milieu dans\n"
    "leur couche. Apres cette phase, chaque piece aura ses\n"
    "couleurs alignees avec les bons axes."
)
_PHASE2_TITLE = "Phase 2 : Permutation"
_PHASE2_DESC = (
    "Toutes les pieces sont bien orientees. On les deplace\n"
    "maintenant vers leur position finale en utilisant\n"
    "uniquement des demi-tours sur R, L, F, B\n"
    "et des rotations sur U, D."
)


class AppController:
    """Central controller linking model, view, and UI."""

    def __init__(self, game_state, renderer, ui_panel):
        self.state = game_state
        self.renderer = renderer
        self.ui = ui_panel
        self._solving = False
        self._solution = None
        self._phase1_length = 0

    def handle_input(self, key):
        """Handle keyboard input for manual cube moves."""
        if self._solving or self.renderer.animating:
            return

        move = None
        shift = held_keys['shift']

        key_map = {
            'u': ('U', "U'"),
            'd': ('D', "D'"),
            'r': ('R', "R'"),
            'l': ('L', "L'"),
            'f': ('F', "F'"),
            'b': ('B', "B'"),
        }

        if key in key_map:
            normal, inverse = key_map[key]
            move = inverse if shift else normal

        if move:
            self.state.apply_move(move)
            self.renderer.animate_move(move, callback=self._check_solved)
            self.ui.set_moves_display(' '.join(self.state.move_history[-20:]))

    def scramble(self):
        """Scramble the cube."""
        if self._solving or self.renderer.animating:
            return

        self.renderer.reset_visual()
        moves = self.state.scramble(20)
        self.ui.set_status(f'Melange: {" ".join(moves)}')
        self.ui.set_moves_display(' '.join(moves))
        self.ui.clear_displays()

        # Animate the scramble
        def on_done():
            self.ui.set_status('Cube melange. Resolvez manuellement ou cliquez Resoudre.')
        self.renderer.animate_sequence(moves, on_complete=on_done)

    def solve(self):
        """Solve the cube using the Two-Phase algorithm."""
        if self._solving or self.renderer.animating:
            return

        if self.state.is_solved():
            self.ui.set_status('Le cube est deja resolu !')
            return

        self._solving = True
        self._solve_start = time.time()
        self.ui.set_status('Resolution en cours...')

        # Run solver in a background thread to avoid freezing the UI
        def solve_thread():
            try:
                solution = self.state.solve(max_length=23, timeout=30)
                # Schedule UI update on main thread
                invoke(self._on_solve_complete, solution, delay=0)
            except Exception as e:
                invoke(self._on_solve_error, str(e), delay=0)

        t = threading.Thread(target=solve_thread, daemon=True)
        t.start()

    def _on_solve_complete(self, result):
        if result is None:
            self._solving = False
            self.ui.set_status('Aucune solution trouvee dans le temps imparti.')
            return

        solution = result["moves"]
        self._phase1_length = result["phase1_length"]
        self._solution = solution
        n = len(solution)
        self.ui.set_status(f'Solution trouvee: {n} mouvements. Animation...')
        self.ui.set_moves_display(' '.join(solution))

        phase1_len = self._phase1_length
        phase2_len = n - phase1_len

        def on_step(current, total, move):
            self.ui.set_step_display(current, total)
            # Apply move to logical state
            self.state.apply_move(move)

            idx = current - 1  # 0-based index
            if idx < phase1_len:
                phase_title = _PHASE1_TITLE
                phase_desc = _PHASE1_DESC
                step_in_phase = idx + 1
                phase_total = phase1_len
            else:
                phase_title = _PHASE2_TITLE
                phase_desc = _PHASE2_DESC
                step_in_phase = idx - phase1_len + 1
                phase_total = phase2_len

            phase_num = 1 if idx < phase1_len else 2
            progress = f"Phase {phase_num} : {step_in_phase}/{phase_total}"
            move_desc = _MOVE_FR.get(move, move)
            move_text = f"{move}  -  {move_desc}   [{progress}]"

            self.ui.set_phase_display(phase_title, phase_desc)
            self.ui.set_move_description(move_text)

        def on_done():
            self._solving = False
            elapsed = time.time() - self._solve_start
            if self.state.is_solved():
                self.ui.set_status(f'Cube RESOLU en {n} coups en {elapsed:.1f}s !')
            else:
                self.ui.set_status('Animation terminee.')
            self.ui.set_phase_display('', '')
            self.ui.set_move_description('')

        self.renderer.animate_sequence(
            solution,
            on_complete=on_done,
            step_callback=on_step,
        )

    def _on_solve_error(self, error_msg):
        self._solving = False
        self.ui.set_status(f'Erreur: {error_msg}')

    def reset(self):
        """Reset the cube to solved state."""
        if self._solving:
            return
        self.state.reset()
        self.renderer.reset_visual()
        self.ui.clear_displays()
        self.ui.set_status('Cube reinitialise.')

    def undo(self):
        """Undo the last move."""
        if self._solving or self.renderer.animating:
            return
        last = self.state.undo()
        if last:
            inv = self.state._inverse_move(last)
            self.renderer.animate_move(inv)
            self.ui.set_moves_display(' '.join(self.state.move_history[-20:]))

    def set_speed(self, speed):
        self.renderer.set_speed(speed)

    def pause(self):
        self.renderer.pause_sequence()

    def resume(self):
        self.renderer.resume_sequence()

    def step(self):
        self.renderer.step_sequence()

    def _check_solved(self):
        if self.state.is_solved():
            self.ui.set_status('FELICITATIONS ! Cube resolu !')
