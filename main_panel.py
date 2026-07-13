import krita
from PyQt5.QtWidgets import (QDockWidget, QWidget, QVBoxLayout, QHBoxLayout, 
                             QPushButton, QComboBox, QLabel, QSpinBox, 
                             QMenu, QWidgetAction, QListWidgetItem)
from PyQt5.QtCore import Qt, QPoint
from PyQt5.QtGui import QIcon, QPixmap

from .core_state import PanelState
from .ui_grid import AdaptiveListWidget

class SmartPanelDocker(QDockWidget):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Brush Studio")
        
        # 1. Загружаем состояние
        self.state = PanelState()
        
        # 2. Строим главный UI
        self.main_widget = QWidget()
        self.layout = QVBoxLayout()
        self.layout.setContentsMargins(0, 0, 0, 0)
        self.layout.setSpacing(0)
        
        self.top_bar = QWidget()
        top_layout = QHBoxLayout()
        top_layout.setContentsMargins(4, 4, 4, 0)
        
        self.btn_settings = QPushButton("⚙")
        self.btn_settings.setFixedSize(24, 24)
        self.btn_settings.setStyleSheet("QPushButton { background: transparent; color: #888; border: none; font-size: 16px; } QPushButton:hover { color: white; }")
        
        top_layout.addStretch()
        top_layout.addWidget(self.btn_settings)
        self.top_bar.setLayout(top_layout)
        
        # 3. Инициализируем сетку
        self.grid = AdaptiveListWidget(self.state)
        
        self.layout.addWidget(self.top_bar)
        self.layout.addWidget(self.grid)
        self.main_widget.setLayout(self.layout)
        self.setWidget(self.main_widget)
        
        # 4. Строим меню настроек
        self.build_popup_menu()
        
        # 5. Подключаем глобальные сигналы (строго после сборки UI!)
        self.btn_settings.clicked.connect(self.show_popup_settings)
        self.grid.itemClicked.connect(self.on_brush_clicked)
        self.dockLocationChanged.connect(self.on_dock_changed)
        self.topLevelChanged.connect(self.on_float_changed)
        
        # 6. Загружаем данные Криты
        self.load_real_brushes()

    def build_popup_menu(self):
        self.settings_menu = QMenu(self)
        self.settings_menu.setStyleSheet("QMenu { background-color: #2D2D2D; border: 1px solid #555; border-radius: 8px; color: #EEE; }")
        
        settings_widget = QWidget()
        vbox = QVBoxLayout()
        vbox.setContentsMargins(10, 10, 10, 10)
        
        # Инициализация виджетов меню
        self.cmb_mode = QComboBox(); self.cmb_mode.addItems(["auto", "manual"]); self.cmb_mode.setCurrentText(self.state.mode)
        self.cmb_layout = QComboBox(); self.cmb_layout.addItems(["vertical", "horizontal"]); self.cmb_layout.setCurrentText(self.state.manual_layout)
        self.spin_divider = QSpinBox(); self.spin_divider.setRange(1, 10); self.spin_divider.setValue(self.state.main_divider)
        
        aspect_layout = QHBoxLayout()
        self.spin_asp_w = QSpinBox(); self.spin_asp_w.setRange(1, 100); self.spin_asp_w.setValue(int(self.state.aspect_w))
        self.spin_asp_h = QSpinBox(); self.spin_asp_h.setRange(1, 100); self.spin_asp_h.setValue(int(self.state.aspect_h))
        aspect_layout.addWidget(self.spin_asp_w); aspect_layout.addWidget(QLabel(":")); aspect_layout.addWidget(self.spin_asp_h)
        
        self.cmb_dir = QComboBox()
        
        # Добавление в Layout
        vbox.addWidget(QLabel("Режим:")); vbox.addWidget(self.cmb_mode)
        self.lbl_layout = QLabel("Раскладка:"); vbox.addWidget(self.lbl_layout); vbox.addWidget(self.cmb_layout)
        vbox.addWidget(QLabel("Разделитель:")); vbox.addWidget(self.spin_divider)
        vbox.addWidget(QLabel("Пропорции:")); vbox.addLayout(aspect_layout)
        vbox.addWidget(QLabel("Начало:")); vbox.addWidget(self.cmb_dir)
        
        settings_widget.setLayout(vbox)
        action = QWidgetAction(self.settings_menu)
        action.setDefaultWidget(settings_widget)
        self.settings_menu.addAction(action)
        
        self.update_settings_visibility()

        # ПОДКЛЮЧАЕМ СИГНАЛЫ ТОЛЬКО ЗДЕСЬ (чтобы не было ложных срабатываний)
        self.cmb_mode.currentTextChanged.connect(self.on_settings_changed)
        self.cmb_layout.currentTextChanged.connect(self.on_settings_changed)
        self.spin_divider.valueChanged.connect(self.on_settings_changed)
        self.spin_asp_w.valueChanged.connect(self.on_settings_changed)
        self.spin_asp_h.valueChanged.connect(self.on_settings_changed)
        self.cmb_dir.currentTextChanged.connect(self.on_dir_changed)

    def update_settings_visibility(self):
        is_manual = (self.cmb_mode.currentText() == "manual")
        self.cmb_layout.setVisible(is_manual)
        self.lbl_layout.setVisible(is_manual)
        
        # Блокируем сигналы, пока пересобираем список, чтобы не зациклить программу
        self.cmb_dir.blockSignals(True)
        self.cmb_dir.clear()
        
        effective = "vertical" if not is_manual else self.cmb_layout.currentText()
        if effective == "vertical":
            self.cmb_dir.addItems(["left", "right"])
            self.cmb_dir.setCurrentText(self.state.start_dir_vert)
        else:
            self.cmb_dir.addItems(["top", "bottom"])
            self.cmb_dir.setCurrentText(self.state.start_dir_horiz)
            
        self.cmb_dir.blockSignals(False)

    def show_popup_settings(self):
        pos = self.btn_settings.mapToGlobal(QPoint(0, self.btn_settings.height()))
        self.settings_menu.exec_(pos)

    def on_settings_changed(self):
        self.state.mode = self.cmb_mode.currentText()
        self.state.manual_layout = self.cmb_layout.currentText()
        self.state.main_divider = self.spin_divider.value()
        self.state.aspect_w = float(self.spin_asp_w.value())
        self.state.aspect_h = float(self.spin_asp_h.value())
        
        self.update_settings_visibility()
        self.state.save()
        
        # Добавляем force=True, чтобы пробить предохранитель ресайза
        self.grid.recalculate_math(force=True)
        
    def on_dir_changed(self, val):
        if self.state.get_effective_layout() == "vertical":
            self.state.start_dir_vert = val
        else:
            self.state.start_dir_horiz = val
            
        self.state.save()
        self.load_real_brushes()
        
        # Тоже добавляем force=True
        self.grid.recalculate_math(force=True)

    def on_dock_changed(self, area):
        self.state.current_dock_area = area
        self.grid.recalculate_math(force=True) # Добавлен force

    def on_float_changed(self, is_floating):
        self.state.is_floating = is_floating
        self.grid.recalculate_math(force=True) # Добавлен force

    def load_real_brushes(self):
        self.grid.clear()
        app = krita.Krita.instance()
        all_presets = list(app.resources("preset").items())[:30]
        
        if self.state.get_effective_layout() == "horizontal" and self.state.start_dir_horiz == "bottom":
            all_presets.reverse()
            
        for name, preset in all_presets:
            icon = QIcon(QPixmap.fromImage(preset.image()))
            item = QListWidgetItem()
            item.setData(Qt.DecorationRole, icon)
            item.setData(Qt.UserRole, name)
            item.setToolTip(name)
            self.grid.addItem(item)

    def on_brush_clicked(self, item):
        preset_name = item.data(Qt.UserRole)
        app = krita.Krita.instance()
        action = app.action('KritaShape/KritaToolFreehand')
        if action: action.trigger()
        window = app.activeWindow()
        if window and window.activeView():
            preset = app.resources("preset").get(preset_name)
            if preset: window.activeView().setCurrentBrushPreset(preset)