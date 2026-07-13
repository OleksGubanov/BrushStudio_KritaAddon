from PyQt5.QtWidgets import QListWidget, QListView, QStyle
from PyQt5.QtCore import Qt, QSize
from .ui_delegate import BrushItemDelegate

class AdaptiveListWidget(QListWidget):
    def __init__(self, state_manager):
        super().__init__()
        self.state = state_manager
        self._last_w = 0
        self._last_h = 0
        
        # Настройки списка
        self.setViewMode(QListView.IconMode)
        self.setResizeMode(QListView.Adjust)
        self.setMovement(QListView.Static)
        self.setUniformItemSizes(True)
        self.setWordWrap(False)
        self.setSpacing(0) # Отступы делает Delegate внутри слота
        
        self.setItemDelegate(BrushItemDelegate(padding=3))
        self.setStyleSheet("QListWidget { background: transparent; border: none; }")

    def resizeEvent(self, event):
        super().resizeEvent(event)
        self.recalculate_math()

    # Измени сигнатуру функции (добавь параметр force)
    def recalculate_math(self, force=False):
        w = self.viewport().width()
        h = self.viewport().height()
        
        # Если это не принудительный вызов из настроек - работает предохранитель ресайза
        if not force:
            if abs(w - self._last_w) < 2 and abs(h - self._last_h) < 2:
                return
                
        self._last_w = w
        self._last_h = h

        effective_layout = self.state.get_effective_layout()
        ratio = self.state.get_safe_ratio()
        div = max(1, self.state.main_divider)
        scroll_w = self.style().pixelMetric(QStyle.PM_ScrollBarExtent)

        if effective_layout == "vertical":
            self.setVerticalScrollBarPolicy(Qt.ScrollBarAlwaysOn)
            self.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
            
            available_w = self.width() - scroll_w - 4
            item_w = available_w / div
            item_h = item_w / ratio
            
            self.setFlow(QListView.LeftToRight)
            if self.state.start_dir_vert == "right":
                self.setLayoutDirection(Qt.RightToLeft)
            else:
                self.setLayoutDirection(Qt.LeftToRight)
        else:
            self.setVerticalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
            self.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOn)
            
            available_h = self.height() - scroll_w - 4
            item_h = available_h / div
            item_w = item_h * ratio
            
            self.setFlow(QListView.TopToBottom)
            self.setLayoutDirection(Qt.LeftToRight)

        # Передаем размеры
        self.setGridSize(QSize(int(item_w), int(item_h)))
        
        # ВАЖНО: Принудительно заставляем Qt перерисовать кисти
        self.update()