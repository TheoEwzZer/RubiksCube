"""
3D Rubik's Cube renderer using Ursina Engine.

Creates 26 visible cubies (3x3x3 minus the invisible center) as Entity objects.
Each cubie is a black cube with colored face quads placed flush on the surface.
Animates face rotations using a rotation helper entity.
"""

from ursina import *

# Official Rubik's Cube colors
COLOR_MAP = {
    'U': color.rgb32(255, 255, 255),   # White
    'D': color.rgb32(255, 213, 0),     # Yellow
    'R': color.rgb32(183, 18, 52),     # Red
    'L': color.rgb32(255, 88, 0),      # Orange
    'F': color.rgb32(0, 155, 72),      # Green
    'B': color.rgb32(0, 70, 173),      # Blue
}

# Move name -> (axis, layer_val, angle)
MOVE_DEFS = {
    'U':  ('y',  1, -90),
    "U'": ('y',  1,  90),
    'U2': ('y',  1, -180),
    'D':  ('y', -1,  90),
    "D'": ('y', -1, -90),
    'D2': ('y', -1,  180),
    'R':  ('x',  1, -90),
    "R'": ('x',  1,  90),
    'R2': ('x',  1, -180),
    'L':  ('x', -1,  90),
    "L'": ('x', -1, -90),
    'L2': ('x', -1,  180),
    'F':  ('z', -1, -90),
    "F'": ('z', -1,  90),
    'F2': ('z', -1, -180),
    'B':  ('z',  1,  90),
    "B'": ('z',  1, -90),
    'B2': ('z',  1,  180),
}


class CubeRenderer:
    """Manages the 3D Rubik's Cube visual representation."""

    def __init__(self):
        self.cubies = []
        self.rotation_helper = Entity()
        self.animating = False
        self._move_queue = []
        self._speed = 0.3
        self._sequence_paused = False
        self._sequence_stepping = False
        self._sequence_moves = []
        self._sequence_index = 0
        self._sequence_on_complete = None
        self._sequence_step_callback = None
        self._create_cubies()

    def _create_cubies(self):
        """Create 26 cubies (skip the invisible center at 0,0,0)."""
        for x in range(-1, 2):
            for y in range(-1, 2):
                for z in range(-1, 2):
                    if x == 0 and y == 0 and z == 0:
                        continue
                    cubie = self._make_cubie(x, y, z)
                    self.cubies.append(cubie)

    def _make_cubie(self, x, y, z):
        """Create a single cubie at position (x, y, z) with colored faces."""
        cubie = Entity(
            position=Vec3(x, y, z),
            model='cube',
            color=color.rgb32(15, 15, 15),
            scale=0.95,
        )

        # Offset for face quads: must be > 0.5 in LOCAL coords
        # because parent scale (0.95) is applied to child position.
        # Local 0.501 * parent 0.95 = world 0.476, just outside surface at 0.475
        offset = 0.501
        face_size = 0.85  # quad size relative to cubie face

        # Add colored face quads for each outward-facing side
        if y == 1:   # U face (white) - quad faces up
            self._add_face(cubie, Vec3(0, offset, 0), Vec3(-90, 0, 0), COLOR_MAP['U'], face_size)
        if y == -1:  # D face (yellow) - quad faces down
            self._add_face(cubie, Vec3(0, -offset, 0), Vec3(90, 0, 0), COLOR_MAP['D'], face_size)
        if x == 1:   # R face (red) - quad faces right
            self._add_face(cubie, Vec3(offset, 0, 0), Vec3(0, 90, 0), COLOR_MAP['R'], face_size)
        if x == -1:  # L face (orange) - quad faces left
            self._add_face(cubie, Vec3(-offset, 0, 0), Vec3(0, -90, 0), COLOR_MAP['L'], face_size)
        if z == -1:  # F face (green) - quad faces front (-Z)
            self._add_face(cubie, Vec3(0, 0, -offset), Vec3(0, 180, 0), COLOR_MAP['F'], face_size)
        if z == 1:   # B face (blue) - quad faces back (+Z)
            self._add_face(cubie, Vec3(0, 0, offset), Vec3(0, 0, 0), COLOR_MAP['B'], face_size)

        return cubie

    def _add_face(self, parent, pos, rot, face_color, size):
        """Add a colored face quad to a cubie."""
        Entity(
            parent=parent,
            model='quad',
            color=face_color,
            position=pos,
            rotation=rot,
            scale=size,
            double_sided=True,
        )

    def set_speed(self, speed):
        self._speed = max(0.05, speed)

    def animate_move(self, move_name, callback=None):
        self._move_queue.append((move_name, callback))
        if not self.animating:
            self._process_next_move()

    def animate_sequence(self, moves, on_complete=None, step_callback=None):
        self._sequence_moves = list(moves)
        self._sequence_index = 0
        self._sequence_on_complete = on_complete
        self._sequence_step_callback = step_callback
        self._sequence_paused = False
        self._sequence_stepping = False
        self._play_next_in_sequence()

    def _play_next_in_sequence(self):
        if self._sequence_paused and not self._sequence_stepping:
            return
        self._sequence_stepping = False

        if self._sequence_index >= len(self._sequence_moves):
            if self._sequence_on_complete:
                self._sequence_on_complete()
            return

        move = self._sequence_moves[self._sequence_index]
        self._sequence_index += 1

        if self._sequence_step_callback:
            self._sequence_step_callback(self._sequence_index, len(self._sequence_moves), move)

        self.animate_move(move, callback=self._play_next_in_sequence)

    def pause_sequence(self):
        self._sequence_paused = True

    def resume_sequence(self):
        self._sequence_paused = False
        if not self.animating:
            self._play_next_in_sequence()

    def step_sequence(self):
        self._sequence_stepping = True
        self._sequence_paused = True
        if not self.animating:
            self._play_next_in_sequence()

    def _process_next_move(self):
        if not self._move_queue:
            self.animating = False
            return

        self.animating = True
        move_name, callback = self._move_queue.pop(0)

        if move_name not in MOVE_DEFS:
            self.animating = False
            if callback:
                callback()
            return

        axis, layer_val, angle = MOVE_DEFS[move_name]
        selected = self._select_cubies(axis, layer_val)

        # Reparent selected cubies to the rotation helper
        self.rotation_helper.rotation = Vec3(0, 0, 0)
        for cubie in selected:
            cubie.world_parent = self.rotation_helper

        # Determine rotation target
        target = Vec3(0, 0, 0)
        if axis == 'x':
            target = Vec3(angle, 0, 0)
        elif axis == 'y':
            target = Vec3(0, angle, 0)
        elif axis == 'z':
            target = Vec3(0, 0, angle)

        self.rotation_helper.animate_rotation(
            target,
            duration=self._speed,
            curve=curve.linear,
        )

        def on_done():
            # Force exact target rotation BEFORE reparenting
            # This prevents errors when callback fires before animation ends
            self.rotation_helper.rotation = target

            for cubie in selected:
                cubie.world_parent = scene
                # Snap position to integer grid
                cubie.position = Vec3(
                    round(cubie.world_position.x),
                    round(cubie.world_position.y),
                    round(cubie.world_position.z),
                )
                # Snap rotation to nearest 90° to prevent drift
                cubie.rotation = Vec3(
                    round(cubie.rotation_x / 90) * 90,
                    round(cubie.rotation_y / 90) * 90,
                    round(cubie.rotation_z / 90) * 90,
                )
            self.rotation_helper.rotation = Vec3(0, 0, 0)

            if callback:
                callback()
            self._process_next_move()

        invoke(on_done, delay=self._speed + 0.05)

    def _select_cubies(self, axis, layer_val):
        selected = []
        for cubie in self.cubies:
            pos = cubie.world_position
            if axis == 'x' and round(pos.x) == layer_val:
                selected.append(cubie)
            elif axis == 'y' and round(pos.y) == layer_val:
                selected.append(cubie)
            elif axis == 'z' and round(pos.z) == layer_val:
                selected.append(cubie)
        return selected

    def reset_visual(self):
        self._move_queue.clear()
        self.animating = False
        for cubie in self.cubies:
            destroy(cubie)
        self.cubies.clear()
        self._create_cubies()
