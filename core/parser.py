import krita

class PresetMetadataReader:
    """Чтение метаданных пресета кисти из .kpp файла."""
    ENGINE_ICONS = {
        "pixelbrush": "🖌",
        "colorsmudge": "💧",
        "hairybrush": "🧹",
        "sketchbrush": "✏",
        "curvebrush": "〰",
        "tangentnormal": "🪨"
    }

    @classmethod
    def get_metadata(cls, preset_name):
        res = krita.Krita.instance().resources("preset").get(preset_name)
        if not res:
            return {"engine": "🖌", "mtime": 0}
        
        # Получаем время изменения для валидации кэша
        from PyQt5.QtCore import QFileInfo
        mtime = QFileInfo(res.filename()).lastModified().toSecsSinceEpoch()
        
        engine_icon = "🖌"
        try:
            with open(res.filename(), 'rb') as f:
                data = f.read(2048)
                idx = data.find(b'paintop="')
                if idx != -1:
                    start = idx + 9
                    end = data.find(b'"', start)
                    engine_name = data[start:end].decode('utf-8')
                    engine_icon = cls.ENGINE_ICONS.get(engine_name, "🖌")
        except Exception:
            pass
            
        return {"engine": engine_icon, "mtime": mtime}