"""
CView - WorldToScreen.
CS2 view matrix row-major.
Calistirilmis formul: W=row[3], X=row[0], Y=row[1] (negatif)
"""
import threading
from typing import Tuple, Optional


class CView:
    def __init__(self):
        self.matrix: list = [[0.0] * 4 for _ in range(4)]
        self.screen_w: float = 1920.0
        self.screen_h: float = 1080.0
        self._matrix_lock = threading.Lock()

    def set_screen_size(self, w: float, h: float):
        self.screen_w = w
        self.screen_h = h

    def world_to_screen(self, pos: Tuple[float, float, float]) -> Optional[Tuple[float, float]]:
        """
        _test_wts2.py ile dogrulanmis formul:
        W   = row[3][0]*x + row[3][1]*y + row[3][2]*z + row[3][3]
        sx  = SightX + row[0][...] / W * SightX
        sy  = SightY - row[1][...] / W * SightY
        """
        sx, sy = self.screen_w / 2, self.screen_h / 2
        x, y, z = pos

        with self._matrix_lock:
            m = [row[:] for row in self.matrix]  # snapshot al

        w = m[3][0]*x + m[3][1]*y + m[3][2]*z + m[3][3]
        if w <= 0.01:
            return None

        out_x = sx + (m[0][0]*x + m[0][1]*y + m[0][2]*z + m[0][3]) / w * sx
        out_y = sy - (m[1][0]*x + m[1][1]*y + m[1][2]*z + m[1][3]) / w * sy

        # Cok uzak koordinatlari reddet
        if abs(out_x) > self.screen_w * 5 or abs(out_y) > self.screen_h * 5:
            return None

        return (out_x, out_y)
