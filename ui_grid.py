from PyQt5.QtWidgets import QListWidget, QListView, QStyle
from PyQt5.QtCore import Qt, QSize
from .ui_delegate import BrushItemDelegate
import math

class AdaptiveListWidget(QListWidget):
    def __init__(self, state_manager, parent_panel):
        super().__init__()
        self.state = state_manager
        self.parent_panel = parent_panel
        self._last_w = 0
        self._last_h = 0
        self._last_dir = "" 
        
        self.setViewMode(QListView.IconMode)
        self.setResizeMode(QListView.Adjust)
        self.setMovement(QListView.Static)
        self.setUniformItemSizes(True)
        self.setWordWrap(False)
        self.setSpacing(0) # Absolute zero spacing
        
        self.setItemDelegate(BrushItemDelegate())
        self.setStyleSheet("QListWidget { background: transparent; border: none; outline: none; }")

    def resizeEvent(self, event):
        super().resizeEvent(event)
        self.recalculate_math()

    def recalculate_math(self, force=False):
        w = self.viewport().width()
        h = self.viewport().height()
        
        if not force:
            if abs(w - self._last_w) < 1 and abs(h - self._last_h) < 1:
                return
                
        self._last_w = w
        self._last_h = h

        is_wide = w > h
        effective_layout = self.state.get_effective_layout(is_wide)
        effective_dir = self.state.get_effective_direction(is_wide)
        
        self.parent_panel.update_bar_orientation(effective_layout, effective_dir)
        
        dir_state_hash = f"{effective_layout}_{effective_dir}"
        if force or self._last_dir != dir_state_hash:
            self._last_dir = dir_state_hash
            self.parent_panel.load_real_brushes(effective_layout, effective_dir)

        # --- Blender-style Relative Scale Engine ---
        base_unit = 32
        scale = self.state.scale_factor
        aspect_ratio = self.state.get_safe_ratio()
        
        target_divider = max(1, self.state.main_divider)
        scroll_w = self.style().pixelMetric(QStyle.PM_ScrollBarExtent)

        if effective_layout == "vertical":
            self.setVerticalScrollBarPolicy(Qt.ScrollBarAlwaysOn)
            self.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
            
            available_w = self.width() - scroll_w
            if available_w < 1: available_w = 1
            
            # Desired minimum width based on scale and aspect
            desired_w = base_unit * scale * self.state.aspect_w
            
            # Rule 1: Reduce columns if they don't fit
            actual_cols = target_divider
            while actual_cols > 1 and (available_w / actual_cols) < desired_w:
                actual_cols -= 1
                
            # Rule 2: Stretch remaining to fill available space 100%
            item_w = available_w / actual_cols
            item_h = item_w / aspect_ratio
            
            self.state.actual_divider = actual_cols
            self.state.actual_w = item_w
            self.state.actual_h = item_h
            
            self.setFlow(QListView.LeftToRight)
            self.setLayoutDirection(Qt.RightToLeft if effective_dir == "right" else Qt.LeftToRight)
            
        else:
            self.setVerticalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
            self.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOn)
            
            available_h = self.height() - scroll_w
            if available_h < 1: available_h = 1
            
            desired_h = base_unit * scale * self.state.aspect_h
            
            actual_rows = target_divider
            while actual_rows > 1 and (available_h / actual_rows) < desired_h:
                actual_rows -= 1
                
            item_h = available_h / actual_rows
            item_w = item_h * aspect_ratio
            
            self.state.actual_divider = actual_rows
            self.state.actual_w = item_w
            self.state.actual_h = item_h
            
            self.setFlow(QListView.TopToBottom)
            self.setLayoutDirection(Qt.LeftToRight)

        # Set exact float sizes casted to int for Qt Grid
        self.setGridSize(QSize(int(item_w), int(item_h)))
        self.update()
        
        # Send actuals back to UI
        self.parent_panel.update_actuals_display()