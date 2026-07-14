from PyQt5.QtWidgets import QWidget, QScrollArea
from PyQt5.QtCore import Qt

class AdaptiveGridWidget(QWidget):
    def __init__(self, state):
        super().__init__()
        self.state = state
        self.slots = []
        self.eff_layout = "vertical"

    def update_architecture(self, eff_layout):
        self.eff_layout = eff_layout
        self.recalculate_math()

    def set_slots(self, slots):
        for slot in self.slots:
            slot.setParent(None)
            slot.deleteLater()
        self.slots = slots
        for slot in self.slots:
            slot.setParent(self)
            slot.show()
        self.recalculate_math()

    def recalculate_math(self, vp_width=None, vp_height=None):
        if not self.slots: return

        base = self.state.base_icon_size
        aw = max(1.0, float(self.state.aspect_w)) # Protected against div-by-zero
        ah = max(1.0, float(self.state.aspect_h))
        
        if aw >= ah: item_w, item_h = int(base * (aw / ah)), base
        else: item_w, item_h = base, int(base * (ah / aw))

        total = len(self.slots)
        div = max(1, self.state.main_divider)

        # Strict Enforcement of Columns/Rows
        if self.eff_layout == "vertical":
            eff_cols = div # Target Cols is absolute
            rows = (total + eff_cols - 1) // eff_cols
            grid_w, grid_h = eff_cols * item_w, rows * item_h
            self.setFixedSize(grid_w, grid_h)

            for i, slot in enumerate(self.slots):
                slot.setGeometry((i % eff_cols) * item_w, (i // eff_cols) * item_h, item_w, item_h)
        else:
            eff_rows = div # Target Rows is absolute
            cols = (total + eff_rows - 1) // eff_rows
            grid_w, grid_h = cols * item_w, eff_rows * item_h
            self.setFixedSize(grid_w, grid_h)

            for i, slot in enumerate(self.slots):
                slot.setGeometry((i // eff_rows) * item_w, (i % eff_rows) * item_h, item_w, item_h)

class SlotScrollArea(QScrollArea):
    def __init__(self, grid_widget):
        super().__init__()
        self.grid_widget = grid_widget
        self.setWidget(self.grid_widget)
        self.setWidgetResizable(False) 

    def resizeEvent(self, event):
        super().resizeEvent(event)
        self.grid_widget.recalculate_math(self.viewport().width(), self.viewport().height())