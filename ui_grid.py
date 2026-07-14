from PyQt5.QtWidgets import QListWidget, QListView, QStyle, QWIDGETSIZE_MAX
from PyQt5.QtCore import Qt, QSize
from .ui_delegate import BrushItemDelegate

class AdaptiveListWidget(QListWidget):
    def __init__(self, state_manager):
        super().__init__()
        self.state = state_manager
        
        self.setViewMode(QListView.IconMode)
        self.setResizeMode(QListView.Adjust)
        self.setMovement(QListView.Static)
        self.setUniformItemSizes(True)
        self.setWordWrap(True)
        self.setSpacing(0)
        
        self.setItemDelegate(BrushItemDelegate(self.state))
        self.setStyleSheet("QListWidget { background: transparent; border: none; outline: none; }")

    def recalculate_math(self, eff_layout, parent_width=0, parent_height=0):
        # 1. Absolute size math based strictly on base pixel size
        base = self.state.base_icon_size
        aw = float(self.state.aspect_w)
        ah = float(self.state.aspect_h)

        if aw >= ah:
            item_h = base
            item_w = int(base * (aw / ah))
        else:
            item_w = base
            item_h = int(base * (ah / aw))

        self.setGridSize(QSize(item_w, item_h))

        div = max(1, self.state.main_divider)
        total_slots = self.state.total_slots

        # 2. Strict bounding box constraints (Prevents slot drifting & fractional gaps)
        if eff_layout == "vertical":
            # Calculate how many columns can physically fit in the available width
            fit_cols = max(1, parent_width // item_w) if parent_width > 0 else div
            effective_cols = min(div, fit_cols, total_slots)
            
            # Number of rows needed for total slots with effective columns
            rows = (total_slots + effective_cols - 1) // effective_cols
            
            # Dynamic scrollbar compensation to eliminate "ghost margins"
            needed_height = rows * item_h
            if parent_height > 0 and needed_height > parent_height:
                scroll_w = self.style().pixelMetric(QStyle.PM_ScrollBarExtent) + 2
            else:
                scroll_w = 0
                
            self.setFlow(QListView.LeftToRight)
            self.setVerticalScrollBarPolicy(Qt.ScrollBarAsNeeded)
            self.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
            
            # Bound exact width dynamically (the stretch spacer will handle the fractional rest)
            self.setMaximumWidth((item_w * effective_cols) + scroll_w)
            self.setMaximumHeight(QWIDGETSIZE_MAX)
        else:
            # Calculate how many rows can physically fit in the available height
            fit_rows = max(1, parent_height // item_h) if parent_height > 0 else div
            effective_rows = min(div, fit_rows, total_slots)
            
            # Number of columns needed
            cols = (total_slots + effective_rows - 1) // effective_rows
            
            # Dynamic scrollbar compensation for horizontal scrollbar
            needed_width = cols * item_w
            if parent_width > 0 and needed_width > parent_width:
                scroll_w = self.style().pixelMetric(QStyle.PM_ScrollBarExtent) + 2
            else:
                scroll_w = 0
                
            self.setFlow(QListView.TopToBottom)
            self.setVerticalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
            self.setHorizontalScrollBarPolicy(Qt.ScrollBarAsNeeded)
            
            # Bound exact height dynamically
            self.setMaximumHeight((item_h * effective_rows) + scroll_w)
            self.setMaximumWidth(QWIDGETSIZE_MAX)
            
        self.update()