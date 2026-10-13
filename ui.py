import sys
from PyQt6.QtWidgets import (QApplication, QMainWindow, QTableWidgetItem, 
                             QVBoxLayout, QHBoxLayout, QWidget,
                             QPushButton, QMenu, QSplitter,
                             QScrollArea, QFrame)
from PyQt6.QtCore import Qt
from PyQt6.QtGui import QAction, QActionGroup
from files import *
from mixer import SinkMixer
from pw import *
import soundcard as sc
from table import HotkeyTable
from hotkeys import HotkeyWorker, qkeysequence_to_pynput


class S_pad(QMainWindow):
    def __init__(self, mixer, h_worker, config):
        super().__init__()
        self.setWindowTitle("S_pad")
        self.resize(1000, 600)
        self.setFixedSize(1000, 600)
        
        # Стилизация: темный фон и тонкие границы
        self.setStyleSheet("""
            QMainWindow, QWidget { background-color: #2b2b2b; color: #ffffff; font-family: 'Segoe UI', sans-serif; }
            QListWidget { background-color: #313335; border: 1px solid #444; outline: none; }
            QListWidget::item { padding: 5px; }
            QListWidget::item:selected { background-color: #4b4d4d; }
            QTableWidget { background-color: #313335; gridline-color: #444; border: 1px solid #444; }
            QHeaderView::section { background-color: #3c3f41; padding: 4px; border: 1px solid #555; }
        """)
        
        # допустимые разрешения
        self.extensions = ['wav', 'flac', 'ogg', 'mat', 'aiff', 'au', 'caf', 'flac', 'htk',
                            'svx', 'voc', 'wve', 'raw', 'mpc', 'w64', 'aif', 'aifc', 'mp3']
        
        # Инициация миксера и проигрывателя
        self.mixer = mixer
        self.hotkey_worker = h_worker
        self.hotkey_worker.hotkey_signal.connect(self.hotkey_clicked)
        self.hotkey_dct = {}
        # UI
        # --- Меню ---
        self.audio_config = config
        self.mics_list, self.audio_list = self.get_audio_names()
        self.init_menu()

        # --- Центральный виджет ---
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        main_layout = QVBoxLayout(central_widget)

        # --- Верхняя панель (Toolbar) ---
        toolbar = QHBoxLayout()
        btn1 = QPushButton('change mode')
        toolbar.addWidget(btn1)
        btn1.clicked.connect(self.mixer.change_mode)
        
        btn2 = QPushButton('stop/start')
        toolbar.addWidget(btn2)
        btn2.clicked.connect(self.mixer.change_pause)
        
        btn3 = QPushButton('clear')
        toolbar.addWidget(btn3)
        btn3.clicked.connect(self.mixer.clear_sounds)

        toolbar.addStretch()
        main_layout.addLayout(toolbar)

        # --- Основная часть (Splitter) ---
        # QSplitter позволяет менять размер панелей мышкой
        self.splitter = QSplitter(Qt.Orientation.Horizontal)

        # 1. Левая панель: Список категорий
        # 2. Создаем QScrollArea
        self.mscroll = QScrollArea()
        self.mscroll.setWidgetResizable(True) # Позволяет внутреннему виджету менять размер
        self.mscroll.setFrameShape(QFrame.Shape.NoFrame) # Убираем лишние рамки

        # 3. Создаем "контейнер" для кнопок
        sounds_pack = QWidget()
        sounds_pack.setMinimumWidth(100)
        self.sounds_pack_layout = QVBoxLayout(sounds_pack)
        
        # 2. Правая панель: Таблица звуков
        self.s_table = HotkeyTable()
        self.s_table.cellChanged.connect(self.on_cell_changed)
        self.s_table.hotkey_updated.connect(self.on_hotkey_changed_in_table)
        
        # Добавляем в сплиттерwindow
        self.splitter.addWidget(self.mscroll)
        self.splitter.addWidget(self.s_table)
        
        # Устанавливаем начальное распределение ширины (20% на категории, 80% на таблицу)
        self.splitter.setStretchFactor(2, 3)
        main_layout.addWidget(self.splitter)
        # Данные
        self.update_tb = False
        self.maindir = 'sounds'
        self.config = None
        create_dir('sounds') # создание на случай если ее удалили
        self.change_dir('sounds')
        self.update_dirs()
        # паки зауков
        self.sounds_pack_layout.setAlignment(Qt.AlignmentFlag.AlignTop) # Кнопки прижаты к верху
        for mdir in self.dirs:
            btn = QPushButton(os.path.basename(mdir))
            btn.clicked.connect(lambda checked, path=mdir: self.change_dir(path))
            self.sounds_pack_layout.addWidget(btn)
        self.mscroll.setWidget(sounds_pack)

    def update_dirs(self):
        files = list_in_dir(self.maindir)
        self.dirs = ['sounds'] + filter_list(files)
    
    def add_sound_row(self, title, hotkey, volume, file):
        row = self.s_table.rowCount()
        self.s_table.insertRow(row)
        btn = QPushButton("▶") # Или иконку/номер
        btn.clicked.connect(lambda: self.mixer.add_sound(file if not os.path.isdir(file) else random_sound(filter_list(list_in_dir(file), self.extensions)), float(self.config[file]["volume"])))
        btn.setFixedSize(40, 30)
        duration = get_duration(file)
        # Устанавливаем кнопку ВНУТРЬ ячейки (0-я колонка)
        # создание не изменяемых переменных в таблице
        item1 = QTableWidgetItem(title)
        item1.setFlags(item1.flags() & ~Qt.ItemFlag.ItemIsEditable)
        item2 = QTableWidgetItem(duration)
        item2.setFlags(item2.flags() & ~Qt.ItemFlag.ItemIsEditable)
        item3 = QTableWidgetItem(str(hotkey))
        item3.setFlags(item2.flags() & ~Qt.ItemFlag.ItemIsEditable)
        # Заполнения в ячейки
        self.s_table.setCellWidget(row, 0, btn)
        self.s_table.setItem(row, 1, item1)
        self.s_table.setItem(row, 2, item3)
        self.s_table.setItem(row, 3, QTableWidgetItem(str(volume)))
        self.s_table.setItem(row, 4, item2)
        
    def change_dir(self, directory):
        if self.config is not None:
            create_config(f'{self.mydir}/config.json', self.config)
        self.mydir = directory
        self.files = list_in_dir(self.mydir)
        self.config = get_config(directory)
        if not self.config:
            self.config = {}
            create_config(f'{directory}/config.json', dict())

        self.update_table()
    
    def update_table(self):
        self.update_tb = True # Флаг для оптимизации callback от изменений таблицы
        self.s_table.setRowCount(0)
        self.hotkey_dct = {}
        for file in self.files:
            if file.split('.')[-1] in self.extensions or os.path.isdir(file):
                file_conf = self.config.setdefault(file, {"hotkey": "", "volume": 1})
                name = os.path.basename(file)
                hotkey, volume = file_conf["hotkey"], file_conf["volume"]
                self.add_sound_row(name, hotkey, volume, file)
                f_hotkey = qkeysequence_to_pynput(hotkey)
                self.hotkey_dct[f_hotkey] = file
        self.hotkey_worker.update_hotkeys(self.hotkey_dct)
        self.update_tb = False
    
    def update_sounds_pack(self):
        self.clear_sounds_pack()
        for mdir in self.base_dirs:
            btn = QPushButton(os.path.basename(mdir))
            btn.clicked.connect(lambda: self.change_dir(mdir))
            self.sounds_pack_layout.addWidget(btn)
    

    def clear_sounds_pack(self):
        while self.sounds_pack_layout.count():
            item = self.sounds_pack_layout.takeAt(0)
            widget = item.widget()
            if widget is not None:
                widget.deleteLater()

    # таблица
    def on_cell_changed(self, row, column):
        if not self.update_tb:
            if column == 3:
                item = self.s_table.item(row, column).text()
                key = f'{self.mydir}/{self.s_table.item(row, 1).text()}'
                self.config[key]["volume"] = float(item)
    
    def on_hotkey_changed_in_table(self, row, new_hotkey):
    #"""Метод вызывается автоматически при изменении горячей клавиши в таблице"""
        # 1. Получаем название аудиофайла или звука из первой колонки (индекс 0) этой же строки
        key = f'{self.mydir}/{self.s_table.item(row, 1).text()}'
        last_hotkey = qkeysequence_to_pynput(self.config[key]["hotkey"])
        self.config[key]["hotkey"] = new_hotkey
        del self.hotkey_dct[last_hotkey]
        self.hotkey_dct[qkeysequence_to_pynput(new_hotkey)] = key
        
    def hotkey_clicked(self, file):
        self.mixer.add_sound(file if not os.path.isdir(file) else random_sound(filter_list(list_in_dir(file), self.extensions)), float(self.config[file]["volume"]))

    def init_menu(self):
        menu_bar = self.menuBar()
        # Очищаем бар, если функция вызывается повторно для обновления
        menu_bar.clear() 

        # 1. Раздел Microphone
        self.mic_menu = menu_bar.addMenu("Microphone")
        self.mic_group = QActionGroup(self) # Группа для радиокнопок
        self.fill_radio_menu(self.mic_menu, self.mic_group, self.mics_list, self.on_microphone_changed, 'micro')

        # 2. Раздел Audio
        self.audio_menu = menu_bar.addMenu("Audio")
        self.audio_group = QActionGroup(self) # Группа для радиокнопок
        self.fill_radio_menu(self.audio_menu, self.audio_group, self.audio_list, self.on_audio_changed, "audio")

        # 3. Раздел Update (работает как обычная кнопка-меню)
        update_action = QAction("Update", self)
        update_action.triggered.connect(self.on_update_clicked) # Используем triggered
        menu_bar.addAction(update_action)

    def fill_radio_menu(self, menu: QMenu, group: QActionGroup, data_list: list, callback, mode):
        """Вспомогательный метод для заполнения меню радиокнопками"""
        # Объединяем элемент None и основной список данных self.get_audio_names()
        full_list = ["None"] + data_list

        for item in full_list:
            action = QAction(item, self)
            action.setCheckable(True) # Делаем пункт переключаемым
            
            # Если это элемент None, выбираем его по умолчанию
            if item == config[mode]:
                action.setChecked(True)

            # Добавляем в группу (это превращает чекбоксы в радиокнопки)
            group.addAction(action)
            menu.addAction(action), [mic.name for mic in sc.all_microphones()]

        # Привязываем callback при переключении элементов в группе
        group.triggered.connect(callback)
    
    def get_audio_names(self):
        mics = list(filter(lambda x: x != "My_Virtual_Microphone", [mic.name for mic in sc.all_microphones()]))
        speak = list(filter(lambda x: x not in ("Music_Sender", "Mixer_Audio_Sender"), [speaker.name for speaker in sc.all_speakers()]))
        return mics, speak
    
    # --- CALLBACK ФУНКЦИИ ---

    def on_microphone_changed(self, action: QAction):
        """Вызывается при смене микрофона"""
        micro = get_microphone_name(search_term=config["micro"])
        disconnect_cable(micro)
        config["micro"] = action.text()
        if action.text() != "None":
            micro = get_microphone_name(search_term=config["micro"])
            connect_to_cable(micro)

    def on_audio_changed(self, action: QAction):
        """Вызывается при смене аудиовыхода"""
        audio = get_microphone_name(config["audio"], False)
        disconnect_cable("m_sender", audio, False, False)
        config["audio"] = action.text()
        if action.text() != "None":
            audio = get_microphone_name(config["audio"], False)
            connect_to_cable('m_sender', audio, False, False)

    def on_update_clicked(self):
        self.mics_list, self.audio_list = self.get_audio_names()
        
        # Обновляем микрофоны
        self.mic_menu.clear()
        self.mic_group = QActionGroup(self) # Старая группа удалится автоматически
        self.fill_radio_menu(self.mic_menu, self.mic_group, self.mics_list, self.on_microphone_changed, "micro")
        
        # Обновляем аудио
        self.audio_menu.clear()
        self.audio_group = QActionGroup(self)
        self.fill_radio_menu(self.audio_menu, self.audio_group, self.audio_list, self.on_audio_changed, "audio")
        

def on_app_exit(mixer, pw_proc, pw_proc2, h_worker):
    # Ваш код завершения
    pw_proc.terminate()
    pw_proc2.terminate()
    mixer.stop()
    h_worker.stop_listening()
    create_config(f'{"."}/config.json', config)


global config
config = get_config(".")
if not config:
    config = {"micro": sc.default_microphone().name, "audio": sc.default_speaker().name}
    create_config(f'{"."}/config.json', config)
            
            
if __name__ == "__main__":
    try:
        mixer = SinkMixer()
        pw_proc, pw_proc2, sink_name, sink_name2 = create_pipewire_cable()
        for s in sc.all_speakers():
            if s.name == 'Music_Sender':
                device = s
                break
        
        if config['micro'] != "None":
            mic_name = get_microphone_name(config['micro']) # Выбор микрофона
        try:
            connect_to_cable(mic_name)
            connect_to_cable('m_sender', get_microphone_name(config["audio"], False), False, False)
        except:
            exit()
            
        mixer.start(device) 
    except:
        pw_proc.terminate()
        pw_proc2.terminate()
        exit()
    try:
        h_worker = HotkeyWorker()
        h_worker.start_listening()
        app = QApplication(sys.argv)
        window = S_pad(mixer, h_worker, config)
        app.aboutToQuit.connect(lambda: on_app_exit(mixer, pw_proc, pw_proc2, h_worker))
        window.show()
        sys.exit(app.exec())
    except : # на всякий случай
        pw_proc.terminate()
        pw_proc2.terminate()
        mixer.stop()
        h_worker.stop_listening()
