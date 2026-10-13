from PyQt6.QtCore import QObject, pyqtSignal
from pynput import keyboard
import threading


class HotkeyWorker(QObject):
    # ПРАВИЛЬНО: Сигнал теперь передает строку (например, имя аудиофайла) в главное окно
    hotkey_signal = pyqtSignal(str)

    def __init__(self):
        super().__init__()
        # Словарь будет хранить {frozenset(клавиш): "имя_действия_или_файла"}
        self.hotkeys = {} 
        self.listener = None
        self.current_pressed = set()
        
        # Блокировка для потокобезопасного изменения словаря горячих клавиш
        self.lock = threading.Lock()

    def update_hotkeys(self, new_hotkeys_dict):
        """
        Метод для динамического обновления горячих клавиш из главного окна.
        Принимает словарь, где ключи — это frozenset, а значения — имена действий.
        """
        with self.lock:
            self.hotkeys = new_hotkeys_dict
            # Очищаем зажатые клавиши, чтобы избежать "залипания" при смене настроек
            self.current_pressed.clear() 

    def start_listening(self):
        """Запуск глобального слушателя (вызывается ОДИН раз при старте программы)"""
        if self.listener and self.listener.running:
            return  # Если уже запущен, ничего не делаем

        def on_press(key):
            # Добавляем абсолютно любую нажатую клавишу в набор зажатых
            self.current_pressed.add(key)
            
            # Защищаем чтение словаря блокировкой
            with self.lock:
                # Проверяем каждую зарегистрированную комбинацию
                for hotkey_frozenset, action_name in self.hotkeys.items():
                    # Если комбинация не пустая и полностью входит в зажатые сейчас клавиши
                    if hotkey_frozenset and hotkey_frozenset.issubset(self.current_pressed):
                        # Отправляем сигнал с именем действия в главное окно PyQt6
                        self.hotkey_signal.emit(action_name)

        def on_release(key):
            # Удаляем клавишу из набора, когда её отпустили
            if key in self.current_pressed:
                self.current_pressed.remove(key)

        self.listener = keyboard.Listener(on_press=on_press, on_release=on_release)
        self.listener.start()

    def stop_listening(self):
        """Остановка слушателя при закрытии приложения"""
        if self.listener:
            self.listener.stop()
   

def qkeysequence_to_pynput(hotkey_str: str) -> frozenset:
    """
    Конвертирует строку горячей клавиши из PyQt6 (QKeySequence) 
    в frozenset объектов pynput для глобального слушателя.
    
    Пример: "Ctrl+Alt+S" -> frozenset({Key.ctrl_l, Key.alt_l, KeyCode(char='s')})
    """
    if not hotkey_str:
        return frozenset()

    pynput_keys = set()
    
    # 1. Разбиваем строку по знаку плюс (например, "Ctrl+Alt+S" -> ["Ctrl", "Alt", "S"])
    # Метод .strip() убирает случайные пробелы, .lower() приводит к нижнему регистру
    parts = [part.strip().lower() for part in hotkey_str.split('+')]
    
    # Карта соответствия текстовых модификаторов Qt и объектов pynput
    # Поддерживаем как Windows/Linux, так и macOS названия
    modifiers_map = {
        'ctrl': keyboard.Key.ctrl_l,
        'control': keyboard.Key.ctrl_l,
        'alt': keyboard.Key.alt_l,
        'opt': keyboard.Key.alt_l,       # macOS option
        'option': keyboard.Key.alt_l,    # macOS option
        'shift': keyboard.Key.shift,
        'meta': keyboard.Key.cmd,        # Windows key / Command key
        'win': keyboard.Key.cmd,
        'cmd': keyboard.Key.cmd,
        'command': keyboard.Key.cmd
    }
    
    # Карта для специальных клавиш, которые не являются модификаторами
    special_keys_map = {
        'f1': keyboard.Key.f1, 'f2': keyboard.Key.f2, 'f3': keyboard.Key.f3,
        'f4': keyboard.Key.f4, 'f5': keyboard.Key.f5, 'f6': keyboard.Key.f6,
        'f7': keyboard.Key.f7, 'f8': keyboard.Key.f8, 'f9': keyboard.Key.f9,
        'f10': keyboard.Key.f10, 'f11': keyboard.Key.f11, 'f12': keyboard.Key.f12,
        'esc': keyboard.Key.esc, 'escape': keyboard.Key.esc,
        'space': keyboard.Key.space, 'enter': keyboard.Key.enter, 
        'return': keyboard.Key.enter, 'tab': keyboard.Key.tab,
        'backspace': keyboard.Key.backspace, 'del': keyboard.Key.delete, 
        'delete': keyboard.Key.delete, 'caps lock': keyboard.Key.caps_lock
    }

    for part in parts:
        # Проверяем, модификатор ли это
        if part in modifiers_map:
            pynput_keys.add(modifiers_map[part])
        # Проверяем, специальная ли это клавиша (F1-F12, Esc, Space...)
        elif part in special_keys_map:
            pynput_keys.add(special_keys_map[part])
        # Если это обычная буква или цифра (например, 's' или '1')
        else:
            if len(part) == 1:
                # Важно: pynput ожидает символ в том регистре, в котором он физически нажимается.
                # Обычно для комбинаций используется нижний регистр.
                pynput_keys.add(keyboard.KeyCode.from_char(part))
                
    return frozenset(pynput_keys)
