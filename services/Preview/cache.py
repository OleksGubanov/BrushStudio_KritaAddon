import os
import hashlib
from PyQt5.QtCore import QStandardPaths
from PyQt5.QtGui import QPixmap, QPixmapCache

class PreviewCache:
    """Двухуровневое кэширование с проверкой версии и модификации кисти."""
    def __init__(self, version="v3"):
        self.version = version
        cache_base = QStandardPaths.writableLocation(QStandardPaths.CacheLocation)
        self.disk_dir = os.path.join(cache_base, "smart_brush_panel", f"strokes_{self.version}")
        os.makedirs(self.disk_dir, exist_ok=True)

    def _get_hash(self, preset_name, mtime):
        raw = f"{preset_name}_{mtime}".encode('utf-8')
        return hashlib.md5(raw).hexdigest()

    def get(self, preset_name, mtime):
        cache_key = self._get_hash(preset_name, mtime)
        
        # 1. RAM Cache
        pixmap = QPixmapCache.find(cache_key)
        if pixmap and not pixmap.isNull():
            return pixmap
            
        # 2. Disk Cache
        disk_path = os.path.join(self.disk_dir, f"{cache_key}.png")
        if os.path.exists(disk_path):
            pixmap = QPixmap()
            if pixmap.load(disk_path):
                QPixmapCache.insert(cache_key, pixmap)
                return pixmap
        return None

    def put(self, preset_name, mtime, pixmap):
        cache_key = self._get_hash(preset_name, mtime)
        QPixmapCache.insert(cache_key, pixmap)
        disk_path = os.path.join(self.disk_dir, f"{cache_key}.png")
        pixmap.save(disk_path, "PNG")