from PyQt5.QtCore import Qt
from PyQt5.QtWidgets import QScrollArea, QWidget


class AdaptiveGridWidget(QWidget):
    """Places brush slots mathematically instead of relying on a fixed grid."""

    def __init__(self, state):
        super().__init__()
        self.state = state
        self.slots = []
        self.flow_axis = "vertical"

    def update_layout(self, layout_spec):
        self.flow_axis = layout_spec.flow_axis
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

    def recalculate_math(self, viewport_width=None, viewport_height=None):
        if not self.slots:
            return

        item_width, item_height, padding = self._item_metrics()
        total = len(self.slots)
        parent = self.parentWidget()
        width = viewport_width if viewport_width is not None else (parent.width() if parent else self.width())
        height = viewport_height if viewport_height is not None else (parent.height() if parent else self.height())

        if self.flow_axis == "horizontal":
            rows = self._cross_axis_count(height, item_height, total)
            columns = (total + rows - 1) // rows
        else:
            columns = self._cross_axis_count(width, item_width, total)
            rows = (total + columns - 1) // columns

        self.setFixedSize(columns * item_width, rows * item_height)
        for index, slot in enumerate(self.slots):
            if self.flow_axis == "horizontal":
                column, row = index // rows, index % rows
            else:
                column, row = index % columns, index // columns

            if self.state.grid.flip_x:
                column = columns - 1 - column
            if self.state.grid.flip_y:
                row = rows - 1 - row

            slot.setGeometry(
                column * item_width + padding,
                row * item_height + padding,
                item_width - padding * 2,
                item_height - padding * 2,
            )

    def _item_metrics(self):
        base = max(8, self.state.appearance.base_icon_size)
        aspect_width = max(0.01, self.state.grid.aspect_w)
        aspect_height = max(0.01, self.state.grid.aspect_h)
        if aspect_width >= aspect_height:
            content_width = round(base * aspect_width / aspect_height)
            content_height = base
        else:
            content_width = base
            content_height = round(base * aspect_height / aspect_width)

        padding = max(0, self.state.appearance.slot_padding)
        return content_width + padding * 2, content_height + padding * 2, padding

    def _cross_axis_count(self, available_size, item_size, total):
        count = max(1, int(available_size) // item_size)
        if self.state.appearance.mode == "manual":
            count = min(count, max(1, self.state.grid.main_divider))
        return max(1, min(count, total))


class SlotScrollArea(QScrollArea):
    """Owns scroll direction and viewport alignment for the adaptive grid."""

    def __init__(self, grid_widget):
        super().__init__()
        self.grid_widget = grid_widget
        self.setWidget(self.grid_widget)
        self.setWidgetResizable(False)
        self.setStyleSheet("QScrollArea { border: none; background: transparent; }")

    def apply_layout(self, layout_spec):
        if layout_spec.flow_axis == "horizontal":
            self.setVerticalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
            self.setHorizontalScrollBarPolicy(Qt.ScrollBarAsNeeded)
            alignment = Qt.AlignLeft | (Qt.AlignBottom if layout_spec.anchor == "Bottom" else Qt.AlignTop)
        else:
            self.setVerticalScrollBarPolicy(Qt.ScrollBarAsNeeded)
            self.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
            alignment = Qt.AlignTop | (Qt.AlignRight if layout_spec.anchor == "Right" else Qt.AlignLeft)
        self.setAlignment(alignment)

    def resizeEvent(self, event):
        super().resizeEvent(event)
        self.grid_widget.recalculate_math(self.viewport().width(), self.viewport().height())
