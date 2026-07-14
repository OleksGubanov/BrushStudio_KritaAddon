import krita

class BrushEngineParser:
    """Низкоуровневое чтение типа движка кисти из бинарного заголовка .kpp."""
    ENGINE_ICONS = {
        "pixelbrush": "🖌",
        "colorsmudge": "💧",
        "hairybrush": "🧹",
        "sketchbrush": "✏",
        "curvebrush": "〰",
        "tangentnormal": "🪨",
        "particlebrush": "✨",
        "hatchingbrush": "///"
    }

    @classmethod
    def get_engine_icon(cls, preset_name):
        res = krita.Krita.instance().resources("preset").get(preset_name)
        if not res:
            return "?"
        
        filepath = res.filename()
        try:
            with open(filepath, 'rb') as f:
                data = f.read(2048)  # Ограниченный буфер парсинга XML описания
                idx = data.find(b'paintop="')
                if idx != -1:
                    start = idx + 9
                    end = data.find(b'"', start)
                    engine_name = data[start:end].decode('utf-8')
                    return cls.ENGINE_ICONS.get(engine_name, "🖌")
        except Exception:
            return "🖌"
        return "🖌"