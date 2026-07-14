from dataclasses import dataclass
from PyQt5.QtGui import QPixmap

@dataclass
class BrushData:
    """Чистая структура данных для передачи в UI."""
    name: str
    engine_icon: str = ""
    icon_pixmap: QPixmap = None
    stroke_pixmap: QPixmap = None
    is_favorite: bool = False
    is_selected: bool = False