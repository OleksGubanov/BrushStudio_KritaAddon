from PyQt5.QtWidgets import QWidget, QScrollArea
from PyQt5.QtCore import Qt

class AdaptiveGridWidget(QWidget):
    """Контейнер, пересчитывающий положение слотов на базе выбранного квадранта."""
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
        aw = max(1.0, float(self.state.aspect_w))
        ah = max(1.0, float(self.state.aspect_h))
        padding = self.state.slot_padding
        
        if aw >= ah: 
            item_w, item_h = int(base * (aw / ah)), base
        else: 
            item_w, item_h = base, int(base * (ah / aw))

        item_w += padding * 2
        item_h += padding * 2

        total = len(self.slots)
        div = max(1, self.state.main_divider)
        corner = self.state.grid_corner  # 'LT', 'RT', 'LB', 'RB'

        if self.eff_layout == "vertical":
            eff_cols = div 
            rows = (total + eff_cols - 1) // eff_cols
            grid_w, grid_h = eff_cols * item_w, rows * item_h
            self.setFixedSize(grid_w, grid_h)

            for i, slot in enumerate(self.slots):
                base_x = (i % eff_cols) * item_w
                base_y = (i // eff_cols) * item_h
                
                # Трансформация осей под выбранный угол привязки
                final_x = (grid_w - item_w - base_x) if 'R' in corner else base_x
                final_y = (grid_h - item_h - base_y) if 'B' in corner else base_y
                
                slot.setGeometry(final_x + padding, final_y + padding, item_w - padding*2, item_h - padding*2)
        else:
            eff_rows = div 
            cols = (total + eff_rows - 1) // eff_rows
            grid_w, grid_h = cols * item_w, eff_rows * item_h
            self.setFixedSize(grid_w, grid_h)

            for i, slot in enumerate(self.slots):
                base_x = (i // eff_rows) * item_w
                base_y = (i % eff_rows) * item_h
                
                final_x = (grid_w - item_w - base_x) if 'R' in corner else base_x
                final_y = (grid_h - item_h - base_y) if 'B' in corner else base_y
                
                slot.setGeometry(final_x + padding, final_y + padding, item_w - padding*2, item_h - padding*2)

class SlotScrollArea(QScrollArea):
    """Область прокрутки для сетки кистей."""
    def __init__(self, grid_widget):
        super().__init__()
        self.grid_widget = grid_widget
        self.setWidget(self.grid_widget)
        self.setWidgetResizable(False) 

    def resizeEvent(self, event):
        super().resizeEvent(event)
        self.grid_widget.recalculate_math(self.viewport().width(), self.viewport().height())