from PyQt5.QtWidgets import QListWidget, QListView, QStyle
from PyQt5.QtCore import Qt, QSize
from .ui_delegate import BrushItemDelegate

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
        self.setSpacing(0) # Spacing is fully handled internally by the Delegate
        
        # Pass state to delegate for dynamic padding updates
        self.setItemDelegate(BrushItemDelegate(self.state))
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
            
            desired_w = base_unit * scale * self.state.aspect_w
            
            actual_cols = target_divider
            while actual_cols > 1 and (available_w / actual_cols) < desired_w:
                actual_cols -= 1
                
            # PERFECT MATH: Sub-pixel compensation
            remainder_w = available_w % actual_cols
            perfect_w = available_w - remainder_w
            item_w = perfect_w // actual_cols
            item_h = int(item_w / aspect_ratio)
            
            # Distribute remainder as Viewport Margins to center the grid perfectly
            margin_left = remainder_w // 2
            margin_right = remainder_w - margin_left
            self.viewport().setContentsMargins(margin_left, 0, margin_right, 0)
            
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
                
            # PERFECT MATH: Sub-pixel compensation
            remainder_h = available_h % actual_rows
            perfect_h = available_h - remainder_h
            item_h = perfect_h // actual_rows
            item_w = int(item_h * aspect_ratio)
            
            # Distribute remainder to center vertically
            margin_top = remainder_h // 2
            margin_bottom = remainder_h - margin_top
            self.viewport().setContentsMargins(0, margin_top, 0, margin_bottom)
            
            self.state.actual_divider = actual_rows
            self.state.actual_w = item_w
            self.state.actual_h = item_h
            
            self.setFlow(QListView.TopToBottom)
            self.setLayoutDirection(Qt.LeftToRight)

        # Set strict grid with exact integers
        self.setGridSize(QSize(item_w, item_h))
        self.update()
        
        self.parent_panel.update_actuals_display()