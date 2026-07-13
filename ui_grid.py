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
        self._last_dir = "" # Tracks layout changes to trigger brush re-ordering
        
        # Grid settings
        self.setViewMode(QListView.IconMode)
        self.setResizeMode(QListView.Adjust)
        self.setMovement(QListView.Static)
        self.setUniformItemSizes(True)
        self.setWordWrap(False)
        self.setSpacing(0) # Zero internal spacing, padding is handled by Delegate
        
        self.setItemDelegate(BrushItemDelegate(padding=1))
        self.setStyleSheet("QListWidget { background: transparent; border: none; }")

    def resizeEvent(self, event):
        super().resizeEvent(event)
        self.recalculate_math()

    def recalculate_math(self, force=False):
        w = self.viewport().width()
        h = self.viewport().height()
        
        # Anti-jitter guard
        if not force:
            if abs(w - self._last_w) < 2 and abs(h - self._last_h) < 2:
                return
                
        self._last_w = w
        self._last_h = h

        # Calculate floating aspect ratio (Width > Height)
        is_wide = w > h
        effective_layout = self.state.get_effective_layout(is_wide)
        effective_dir = self.state.get_effective_direction(is_wide)
        
        # If layout direction changed, reload the brushes natively to handle "bottom" origin reverse
        dir_state_hash = f"{effective_layout}_{effective_dir}"
        if force or self._last_dir != dir_state_hash:
            self._last_dir = dir_state_hash
            self.parent_panel.load_real_brushes(effective_layout, effective_dir)

        ratio = self.state.get_safe_ratio()
        div = max(1, self.state.main_divider)
        scroll_w = self.style().pixelMetric(QStyle.PM_ScrollBarExtent)

        if effective_layout == "vertical":
            self.setVerticalScrollBarPolicy(Qt.ScrollBarAlwaysOn)
            self.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
            
            available_w = self.width() - scroll_w - 2
            item_w = max(10, available_w / div)
            item_h = item_w / ratio
            
            self.setFlow(QListView.LeftToRight)
            self.setLayoutDirection(Qt.RightToLeft if effective_dir == "right" else Qt.LeftToRight)
        else:
            self.setVerticalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
            self.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOn)
            
            available_h = self.height() - scroll_w - 2
            item_h = max(10, available_h / div)
            item_w = item_h * ratio
            
            self.setFlow(QListView.TopToBottom)
            self.setLayoutDirection(Qt.LeftToRight)

        # Apply ideal dimensions
        self.setGridSize(QSize(int(item_w), int(item_h)))
        self.update()