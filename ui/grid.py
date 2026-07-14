from PyQt5.QtWidgets import QWidget
from PyQt5.QtCore import QRect

class AdaptiveGridWidget(QWidget):
    def __init__(self, state):
        super().__init__()
        self.state = state
        self.slots = []

    def set_slots(self, slots):
        for slot in self.slots: slot.deleteLater()
        self.slots = slots
        for slot in self.slots: slot.setParent(self)
        self.recalculate_math()

    def recalculate_math(self):
        if not self.slots: return

        base = self.state.appearance.base_icon_size
        item_w = int(base * self.state.grid.aspect_w)
        item_h = int(base * self.state.grid.aspect_h)
        padding = self.state.appearance.slot_padding

        item_w += padding * 2
        item_h += padding * 2

        cols = self.state.grid.main_divider
        rows = (len(self.slots) + cols - 1) // cols
        
        grid_w, grid_h = cols * item_w, rows * item_h
        self.setFixedSize(grid_w, grid_h)

        flip_x = self.state.grid.flip_x
        flip_y = self.state.grid.flip_y

        for i, slot in enumerate(self.slots):
            c, r = i % cols, i // cols
            
            # Матричная трансформация координат вместо жесткого if/else
            base_x = (cols - 1 - c) * item_w if flip_x else c * item_w
            base_y = (rows - 1 - r) * item_h if flip_y else r * item_h
            
            slot.setGeometry(base_x + padding, base_y + padding, item_w - padding*2, item_h - padding*2)