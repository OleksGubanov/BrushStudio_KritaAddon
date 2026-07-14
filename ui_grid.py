from PyQt5.QtWidgets import QListWidget, QListView, QStyle
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

    def recalculate_math(self):
        # 1. Absolute size math based on user rule (Shortest side = base_icon_size)
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
        scroll_w = self.style().pixelMetric(QStyle.PM_ScrollBarExtent) + 2

        # 2. Flow and strict bounding box constraints
        if self.state.manual_layout == "vertical":
            self.setFlow(QListView.LeftToRight)
            self.setVerticalScrollBarPolicy(Qt.ScrollBarAsNeeded)
            self.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
            
            # Constrain maximum width to strictly fit the columns. It won't stretch to empty space.
            max_width = (item_w * div) + scroll_w
            self.setMaximumWidth(max_width)
            self.setMaximumHeight(16777215) # Unbounded height
        else:
            self.setFlow(QListView.TopToBottom)
            self.setVerticalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
            self.setHorizontalScrollBarPolicy(Qt.ScrollBarAsNeeded)
            
            max_height = (item_h * div) + scroll_w
            self.setMaximumHeight(max_height)
            self.setMaximumWidth(16777215) # Unbounded width

        # 3. Handle Horizontal Alignment (Right vs Left Start)
        if "Right" in self.state.anchor_corner:
            self.setLayoutDirection(Qt.RightToLeft)
        else:
            self.setLayoutDirection(Qt.LeftToRight)

        self.update()