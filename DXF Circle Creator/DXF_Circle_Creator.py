import sys
import math
import ezdxf
from PyQt6.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
    QLabel, QLineEdit, QPushButton, QFileDialog, QMessageBox, QScrollArea, QFrame
)
from PyQt6.QtCore import Qt

# Виджет для ввода параметров массива отверстий
class ArrayEntry(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        layout = QHBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)

        self.label = QLabel("Массив:")
        self.arrayDiameterEdit = QLineEdit()
        self.arrayDiameterEdit.setPlaceholderText("Диаметр массива")
        self.holesCountEdit = QLineEdit()
        self.holesCountEdit.setPlaceholderText("Кол-во отверстий")
        self.holeDiameterEdit = QLineEdit()
        self.holeDiameterEdit.setPlaceholderText("Диаметр отверстия")
        self.removeButton = QPushButton("Удалить")
        self.removeButton.setFixedWidth(70)

        layout.addWidget(self.label)
        layout.addWidget(self.arrayDiameterEdit)
        layout.addWidget(self.holesCountEdit)
        layout.addWidget(self.holeDiameterEdit)
        layout.addWidget(self.removeButton)

        # По нажатию кнопки удалить данный виджет из родительского контейнера
        self.removeButton.clicked.connect(self.remove_self)

    def remove_self(self):
        # Удаляем себя из родительского layout
        parent_layout = self.parentWidget().layout()
        parent_layout.removeWidget(self)
        self.deleteLater()

    def get_values(self):
        try:
            array_diameter = float(self.arrayDiameterEdit.text())
            holes_count = int(self.holesCountEdit.text())
            hole_diameter = float(self.holeDiameterEdit.text())
            return array_diameter, holes_count, hole_diameter
        except ValueError:
            raise ValueError("Некорректное значение в параметрах массива.")

# Основное окно приложения
class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Генерация DXF файла с кругом и массивами отверстий")

        centralWidget = QWidget()
        self.setCentralWidget(centralWidget)
        mainLayout = QVBoxLayout(centralWidget)

        # Ввод параметров основного круга
        mainCircleLayout = QHBoxLayout()
        mainCircleLabel = QLabel("Диаметр основного круга:")
        self.mainCircleEdit = QLineEdit()
        self.mainCircleEdit.setPlaceholderText("Введите диаметр")
        mainCircleLayout.addWidget(mainCircleLabel)
        mainCircleLayout.addWidget(self.mainCircleEdit)
        mainLayout.addLayout(mainCircleLayout)

        # Раздел для добавления массивов отверстий
        arraysLabel = QLabel("Массивы отверстий:")
        mainLayout.addWidget(arraysLabel)

        # Прокручиваемая область для массивов (если их много)
        self.scrollArea = QScrollArea()
        self.scrollArea.setWidgetResizable(True)
        self.arraysContainer = QWidget()
        self.arraysLayout = QVBoxLayout(self.arraysContainer)
        self.arraysLayout.setAlignment(Qt.AlignmentFlag.AlignTop)
        self.scrollArea.setWidget(self.arraysContainer)
        mainLayout.addWidget(self.scrollArea, stretch=1)

        # Кнопка для добавления нового массива
        self.addArrayButton = QPushButton("Добавить массив")
        self.addArrayButton.clicked.connect(self.add_array)
        mainLayout.addWidget(self.addArrayButton)

        # Кнопка для генерации DXF файла
        self.generateButton = QPushButton("Сгенерировать DXF")
        self.generateButton.clicked.connect(self.generate_dxf)
        mainLayout.addWidget(self.generateButton)

    def add_array(self):
        array_entry = ArrayEntry(self.arraysContainer)
        self.arraysLayout.addWidget(array_entry)

    def generate_dxf(self):
        # Чтение и проверка ввода для основного круга
        try:
            main_diameter = float(self.mainCircleEdit.text())
        except ValueError:
            QMessageBox.critical(self, "Ошибка", "Введите корректное значение для диаметра основного круга.")
            return

        # Создаем новый чертеж DXF
        doc = ezdxf.new(dxfversion="R2010")
        msp = doc.modelspace()

        # Рисуем основной круг (центр в (0,0))
        main_radius = main_diameter / 2.0
        msp.add_circle(center=(0, 0), radius=main_radius)

        # Обрабатываем каждый добавленный массив
        for i in range(self.arraysLayout.count()):
            widget = self.arraysLayout.itemAt(i).widget()
            if widget is not None:
                try:
                    array_diameter, holes_count, hole_diameter = widget.get_values()
                except ValueError as e:
                    QMessageBox.critical(self, "Ошибка", str(e))
                    return

                array_radius = array_diameter / 2.0
                # Располагаем отверстия равномерно по окружности
                for j in range(holes_count):
                    angle = 2 * math.pi * j / holes_count
                    x = array_radius * math.cos(angle)
                    y = array_radius * math.sin(angle)
                    # Рисуем отверстие как круг
                    msp.add_circle(center=(x, y), radius=hole_diameter / 2.0)

        # Выбор пути для сохранения файла
        file_path, _ = QFileDialog.getSaveFileName(self, "Сохранить DXF", filter="DXF Files (*.dxf)")
        if file_path:
            try:
                doc.saveas(file_path)
                QMessageBox.information(self, "Успех", f"Файл успешно сохранён:\n{file_path}")
            except Exception as e:
                QMessageBox.critical(self, "Ошибка", f"Ошибка при сохранении файла:\n{str(e)}")

def main():
    app = QApplication(sys.argv)
    window = MainWindow()
    window.resize(600, 400)
    window.show()
    sys.exit(app.exec())

if __name__ == '__main__':
    main()
