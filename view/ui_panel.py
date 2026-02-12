"""
UI panel with controls for the Rubik's Cube application.
Uses only Ursina Text and Button elements without background panels
to avoid z-fighting/flickering.
"""

from ursina import *


class UIPanel:
    """Bottom panel with all UI controls."""

    def __init__(self, on_scramble=None, on_solve=None, on_reset=None,
                 on_speed_change=None, on_mode_change=None,
                 on_pause=None, on_resume=None, on_step=None,
                 on_undo=None):
        self.on_scramble = on_scramble
        self.on_solve = on_solve
        self.on_reset = on_reset
        self.on_speed_change = on_speed_change
        self.on_mode_change = on_mode_change
        self.on_pause = on_pause
        self.on_resume = on_resume
        self.on_step = on_step
        self.on_undo = on_undo

        self._paused = False
        self._mode = 'Manuel'
        self._build_ui()

    def _btn(self, text, pos, scale, col, on_click):
        """Helper to create a button with consistent style."""
        return Button(
            text=text,
            parent=camera.ui,
            position=pos,
            scale=scale,
            color=col,
            highlight_color=col.tint(0.1),
            pressed_color=col.tint(-0.1),
            on_click=on_click,
        )

    def _build_ui(self):
        row1_y = -0.34
        row2_y = -0.42

        # --- Row 1: Mode + Speed ---
        Text('Mode:', parent=camera.ui, position=(-0.84, row1_y + 0.012),
             scale=0.9, color=color.light_gray)
        self.mode_btn = self._btn('Manuel', (-0.70, row1_y), (0.16, 0.05),
                                  color.azure, self._toggle_mode)

        Text('Vitesse:', parent=camera.ui, position=(-0.42, row1_y + 0.012),
             scale=0.9, color=color.light_gray)

        self._speed_btns = []
        speeds = [('Rapide', 0.05), ('Normal', 0.3), ('Lent', 0.8)]
        for i, (label, val) in enumerate(speeds):
            c = color.azure if i == 1 else color.rgb32(80, 80, 90)
            btn = self._btn(label, (-0.24 + i * 0.14, row1_y), (0.12, 0.045),
                            c, Func(self._set_speed, i, val))
            self._speed_btns.append(btn)

        # --- Row 2: Actions ---
        self.scramble_btn = self._btn(
            'Melanger', (-0.72, row2_y), (0.18, 0.05),
            color.orange, self._on_scramble_click)
        self.solve_btn = self._btn(
            'Resoudre (IA)', (-0.48, row2_y), (0.22, 0.05),
            color.rgb32(50, 180, 50), self._on_solve_click)
        self.reset_btn = self._btn(
            'Reset', (-0.22, row2_y), (0.12, 0.05),
            color.rgb32(200, 50, 50), self._on_reset_click)
        self.undo_btn = self._btn(
            'Annuler', (-0.06, row2_y), (0.14, 0.05),
            color.rgb32(120, 60, 180), self._on_undo_click)

        # Playback controls
        self.pause_btn = self._btn(
            '||', (0.16, row2_y), (0.06, 0.05),
            color.rgb32(80, 80, 90), self._toggle_pause)
        self.step_fwd_btn = self._btn(
            '>|', (0.24, row2_y), (0.06, 0.05),
            color.rgb32(80, 80, 90), self._on_step_click)

        # --- Info texts ---
        self.moves_text = Text(
            text='',
            parent=camera.ui,
            position=(-0.84, -0.48),
            scale=0.8,
            color=color.rgb32(200, 200, 220),
        )
        self.step_text = Text(
            text='',
            parent=camera.ui,
            position=(0.40, -0.48),
            scale=0.8,
            color=color.yellow,
        )
        self.status_text = Text(
            text='Pret. Touches U/D/R/L/F/B pour tourner (Shift=inverse). Souris pour orbiter.',
            parent=camera.ui,
            position=(-0.84, 0.37),
            scale=0.8,
            color=color.rgb32(160, 160, 180),
        )

    def _toggle_mode(self):
        if self._mode == 'Manuel':
            self._mode = 'IA'
            self.mode_btn.text = 'IA'
            self.mode_btn.color = color.rgb32(50, 180, 50)
        else:
            self._mode = 'Manuel'
            self.mode_btn.text = 'Manuel'
            self.mode_btn.color = color.azure
        if self.on_mode_change:
            self.on_mode_change(self._mode)

    def _set_speed(self, idx, val):
        for i, btn in enumerate(self._speed_btns):
            btn.color = color.azure if i == idx else color.rgb32(80, 80, 90)
        if self.on_speed_change:
            self.on_speed_change(val)

    def _toggle_pause(self):
        self._paused = not self._paused
        if self._paused:
            self.pause_btn.text = '>'
            self.pause_btn.color = color.rgb32(50, 180, 50)
            if self.on_pause:
                self.on_pause()
        else:
            self.pause_btn.text = '||'
            self.pause_btn.color = color.rgb32(80, 80, 90)
            if self.on_resume:
                self.on_resume()

    def _on_scramble_click(self):
        if self.on_scramble:
            self.on_scramble()

    def _on_solve_click(self):
        if self.on_solve:
            self.on_solve()

    def _on_reset_click(self):
        if self.on_reset:
            self.on_reset()

    def _on_undo_click(self):
        if self.on_undo:
            self.on_undo()

    def _on_step_click(self):
        if self.on_step:
            self.on_step()

    def set_moves_display(self, moves_str):
        if len(moves_str) > 90:
            moves_str = '...' + moves_str[-87:]
        self.moves_text.text = f'Moves: {moves_str}'

    def set_step_display(self, current, total):
        self.step_text.text = f'Etape: {current}/{total}'

    def set_status(self, text):
        self.status_text.text = text

    def clear_displays(self):
        self.moves_text.text = ''
        self.step_text.text = ''

    @property
    def mode(self):
        return self._mode
