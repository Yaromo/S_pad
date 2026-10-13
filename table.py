from PyQt6.QtWidgets import QTableWidget, QHeaderView
from PyQt6.QtCore import Qt, pyqtSignal
from PyQt6.QtGui import QKeySequence

class HotkeyTable(QTableWidget):
    
    hotkey_updated = pyqtSignal(int, str) # передача обновления hotkey
    
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setSelectionMode(QTableWidget.SelectionMode.SingleSelection)
        self.setColumnCount(5)
        self.setMinimumWidth(500)
        self.setHorizontalHeaderLabels(["   ", "Заголовок", "Гор. клавиша", "Громкость","Длительность"])
        self.horizontalHeader().setSectionResizeMode(0, QHeaderView.ResizeMode.Stretch)
        self.verticalHeader().setVisible(False)
        self.setColumnWidth(4, 100)
        self.horizontalHeader().setSectionResizeMode(
            4, QHeaderView.ResizeMode.Fixed
        )
        self.setColumnWidth(3, 100)
        self.horizontalHeader().setSectionResizeMode(
            3, QHeaderView.ResizeMode.Fixed
        )
        self.setColumnWidth(2, 100)
        self.horizontalHeader().setSectionResizeMode(
            2, QHeaderView.ResizeMode.Fixed
        )
        self.horizontalHeader().setSectionResizeMode(
            0, QHeaderView.ResizeMode.ResizeToContents
        )
        self.horizontalHeader().setSectionResizeMode(
            1, QHeaderView.ResizeMode.Stretch
        )


    def keyPressEvent(self, event):
        # Получаем текущую ячейку и индекс её колонки
        current_item = self.currentItem()
        current_col = self.currentColumn()
        current_row = self.currentRow()
        
        # Если ячейка не выбрана ИЛИ это НЕ второй столбец (индекс 1, "Гор. клавиша")
        if not current_item or current_col != 2:
            super().keyPressEvent(event)
            return

        # Защита от мыши и пустых системных прерываний
        if event.key() == Qt.Key.Key_unknown or event.key() == 0:
            event.ignore()
            return

        # Игнорируем одиночные нажатия клавиш-модификаторов (Ctrl, Shift, Alt...)
        if event.key() in (Qt.Key.Key_Control, Qt.Key.Key_Shift, Qt.Key.Key_Alt, Qt.Key.Key_Meta):
            super().keyPressEvent(event)
            return

        # Очистка ячейки по кнопкам Delete/Backspace
        if event.key() in (Qt.Key.Key_Delete, Qt.Key.Key_Backspace):
            current_item.setText("")
            return

        # Считываем комбинацию
        modifiers = event.modifiers()
        key = event.key()

        # Собираем в строку (например: "Ctrl+Shift+A")
        key_sequence = QKeySequence(modifiers.value | key)
        hotkey_string = key_sequence.toString(QKeySequence.SequenceFormat.NativeText)

        # Записываем комбинацию в ячейку
        current_item.setText(hotkey_string)
        event.accept()
        
        self.hotkey_updated.emit(current_row, hotkey_string) # передача обновления hotkey
