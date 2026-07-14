from PyQt5.QtWidgets import QWidget, QScrollArea
from PyQt5.QtCore import Qt

class AdaptiveGridWidget(QWidget):
    """A pure QWidget that mathematically positions its children (Blender-style)"""
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

        # Base sizes
        base = self.state.base_icon_size
        aw, ah = float(self.state.aspect_w), float(self.state.aspect_h)
        if aw >= ah: item_w, item_h = int(base * (aw / ah)), base
        else: item_w, item_h = base, int(base * (ah / aw))

        total = len(self.slots)
        vp = self.parentWidget()
        w = vp_width if vp_width is not None else (vp.width() if vp else self.width())
        h = vp_height if vp_height is not None else (vp.height() if vp else self.height())
        div = max(1, self.state.main_divider)

        # 1. Position Math
        if self.eff_layout == "vertical":
            cols = max(1, w // item_w)
            if self.state.mode == "manual": cols = min(cols, div)
            eff_cols = max(1, min(cols, total))
            
            rows = (total + eff_cols - 1) // eff_cols
            grid_w, grid_h = eff_cols * item_w, rows * item_h
            self.setFixedSize(grid_w, grid_h)

            for i, slot in enumerate(self.slots):
                slot.setGeometry((i % eff_cols) * item_w, (i // eff_cols) * item_h, item_w, item_h)
        else:
            rows = max(1, h // item_h)
            if self.state.mode == "manual": rows = min(rows, div)
            eff_rows = max(1, min(rows, total))

            cols = (total + eff_rows - 1) // eff_rows
            grid_w, grid_h = cols * item_w, eff_rows * item_h
            self.setFixedSize(grid_w, grid_h)

            for i, slot in enumerate(self.slots):
                slot.setGeometry((i // eff_rows) * item_w, (i % eff_rows) * item_h, item_w, item_h)

class SlotScrollArea(QScrollArea):
    """Manages the Viewport and pushes resize events down to the Grid instantly"""
    def __init__(self, grid_widget):
        super().__init__()
        self.grid_widget = grid_widget
        self.setWidget(self.grid_widget)
        # We manually control the widget size. This fixes the Viewport empty space completely!
        self.setWidgetResizable(False) 
        self.setStyleSheet("QScrollArea { border: none; background: transparent; }")

    def resizeEvent(self, event):
        super().resizeEvent(event)
        self.grid_widget.recalculate_math(self.viewport().width(), self.viewport().height())