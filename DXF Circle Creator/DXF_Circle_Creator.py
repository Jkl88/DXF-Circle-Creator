import sys
import math
import os
import ezdxf
from PyQt6.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
    QLabel, QDoubleSpinBox, QSpinBox, QLineEdit, QPushButton, QFileDialog,
    QMessageBox, QScrollArea, QGraphicsView, QGraphicsScene
)
from PyQt6.QtCore import Qt, QUrl
from PyQt6.QtGui import QPainter, QTransform, QColor, QPen, QDesktopServices

# Виджет для ввода параметров массива отверстий
class ArrayEntry(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        layout = QHBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)

        self.label = QLabel("Массив:")

        # Поле ввода для диаметра массива (окружность)
        self.spinArrayDiameter = QDoubleSpinBox()
        self.spinArrayDiameter.setMinimum(0.0)
        self.spinArrayDiameter.setMaximum(10000.0)
        self.spinArrayDiameter.setDecimals(2)
        self.spinArrayDiameter.setValue(100.0)
        self.spinArrayDiameter.setSuffix(" мм")
        self.spinArrayDiameter.setToolTip("Диаметр окружности, по которой располагаются отверстия")

        # Поле ввода для количества отверстий
        self.spinHolesCount = QSpinBox()
        self.spinHolesCount.setMinimum(1)
        self.spinHolesCount.setMaximum(1000)
        self.spinHolesCount.setValue(6)
        self.spinHolesCount.setToolTip("Количество отверстий в массиве")

        # Поле ввода для диаметра отверстия
        self.spinHoleDiameter = QDoubleSpinBox()
        self.spinHoleDiameter.setMinimum(0.0)
        self.spinHoleDiameter.setMaximum(10000.0)
        self.spinHoleDiameter.setDecimals(2)
        self.spinHoleDiameter.setValue(10.0)
        self.spinHoleDiameter.setSuffix(" мм")
        self.spinHoleDiameter.setToolTip("Диаметр отверстия")
        
        # Поле ввода для поворота массива (в градусах)
        self.spinRotation = QDoubleSpinBox()
        self.spinRotation.setMinimum(-360.0)
        self.spinRotation.setMaximum(360.0)
        self.spinRotation.setDecimals(1)
        self.spinRotation.setValue(0.0)
        self.spinRotation.setSuffix("°")
        self.spinRotation.setToolTip("Поворот относительно 0 (в градусах)")

        self.removeButton = QPushButton("Х")
        self.removeButton.setFixedWidth(40)

        layout.addWidget(self.label)
        layout.addWidget(self.spinArrayDiameter)
        layout.addWidget(self.spinHolesCount)
        layout.addWidget(self.spinHoleDiameter)
        layout.addWidget(self.spinRotation)
        layout.addWidget(self.removeButton)

        self.removeButton.clicked.connect(self.remove_self)

    def remove_self(self):
        parent_layout = self.parentWidget().layout()
        parent_layout.removeWidget(self)
        self.deleteLater()

    def get_values(self):
        array_diameter = self.spinArrayDiameter.value()
        holes_count = self.spinHolesCount.value()
        hole_diameter = self.spinHoleDiameter.value()
        rotation = self.spinRotation.value()
        return array_diameter, holes_count, hole_diameter, rotation

# Основное окно приложения
class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("DXF Конструктор: Круги и Отверстия")

        centralWidget = QWidget()
        self.setCentralWidget(centralWidget)
        # Горизонтальное разделение: слева – элементы управления, справа – предпросмотр
        mainLayout = QHBoxLayout(centralWidget)

        # Левый блок – элементы управления
        controlsWidget = QWidget()
        controlsWidget.setMinimumWidth(400)  # увеличенная ширина для удобного ввода данных
        controlsLayout = QVBoxLayout(controlsWidget)
        controlsLayout.setAlignment(Qt.AlignmentFlag.AlignTop)

        # Поля для обозначения и названия файла
        designationLayout = QHBoxLayout()
        labelDesignation = QLabel("Обозначение:")
        self.lineDesignation = QLineEdit()
        self.lineDesignation.setToolTip("Введите обозначение (необязательно)")
        designationLayout.addWidget(labelDesignation)
        designationLayout.addWidget(self.lineDesignation)
        controlsLayout.addLayout(designationLayout)

        nameLayout = QHBoxLayout()
        labelName = QLabel("Название:")
        self.lineName = QLineEdit()
        self.lineName.setToolTip("Название подставляется автоматически в формате D_[диаметр основного круга]")
        nameLayout.addWidget(labelName)
        nameLayout.addWidget(self.lineName)
        controlsLayout.addLayout(nameLayout)

        # Ввод параметров основного круга
        mainCircleLayout = QHBoxLayout()
        mainCircleLabel = QLabel("Диаметр основного круга:")
        self.spinMainCircle = QDoubleSpinBox()
        self.spinMainCircle.setMinimum(0.0)
        self.spinMainCircle.setMaximum(10000.0)
        self.spinMainCircle.setDecimals(2)
        self.spinMainCircle.setValue(200.0)
        self.spinMainCircle.setSuffix(" мм")
        self.spinMainCircle.setToolTip("Введите диаметр основного круга")
        mainCircleLayout.addWidget(mainCircleLabel)
        mainCircleLayout.addWidget(self.spinMainCircle)
        controlsLayout.addLayout(mainCircleLayout)

        self.spinMainCircle.valueChanged.connect(self.update_preview)

        # Метка для массивов отверстий
        arraysLabel = QLabel("Массивы отверстий:")
        controlsLayout.addWidget(arraysLabel)

        # Прокручиваемая область для ввода массивов
        self.scrollArea = QScrollArea()
        self.scrollArea.setWidgetResizable(True)
        self.arraysContainer = QWidget()
        self.arraysLayout = QVBoxLayout(self.arraysContainer)
        self.arraysLayout.setAlignment(Qt.AlignmentFlag.AlignTop)
        self.scrollArea.setWidget(self.arraysContainer)
        controlsLayout.addWidget(self.scrollArea, stretch=1)

        # Кнопка для добавления нового массива
        self.addArrayButton = QPushButton("Добавить массив")
        self.addArrayButton.clicked.connect(self.add_array)
        controlsLayout.addWidget(self.addArrayButton)

        # Кнопка для генерации DXF файла
        self.generateButton = QPushButton("Сгенерировать DXF")
        self.generateButton.clicked.connect(self.generate_dxf)
        controlsLayout.addWidget(self.generateButton)

        mainLayout.addWidget(controlsWidget, stretch=1)

        # Правый блок – предпросмотр
        self.previewScene = QGraphicsScene(self)
        self.previewView = QGraphicsView(self.previewScene)
        self.previewView.setRenderHint(QPainter.RenderHint.Antialiasing)
        self.previewView.setMinimumSize(400, 400)
        # Инвертируем ось Y для стандартной декартовой системы координат
        self.previewView.setTransform(QTransform().scale(1, -1))
        mainLayout.addWidget(self.previewView, stretch=2)

        # Список цветов для массивов (цвет назначается циклически)
        self.color_list = ["red", "blue", "green", "orange", "purple", "magenta", "cyan"]

        self.update_preview()

    def add_array(self):
        array_entry = ArrayEntry(self.arraysContainer)
        self.arraysLayout.addWidget(array_entry)
        array_entry.spinArrayDiameter.valueChanged.connect(self.update_preview)
        array_entry.spinHolesCount.valueChanged.connect(self.update_preview)
        array_entry.spinHoleDiameter.valueChanged.connect(self.update_preview)
        array_entry.spinRotation.valueChanged.connect(self.update_preview)
        array_entry.removeButton.clicked.connect(self.update_preview)
        self.update_preview()

    def update_preview(self):
        self.previewScene.clear()
        margin = 10
        max_extent = 0

        # Рисуем основной круг с косметическим пером (фиксированная толщина)
        main_diameter = self.spinMainCircle.value()
        main_radius = main_diameter / 2.0
        pen_main = QPen(Qt.GlobalColor.black)
        pen_main.setCosmetic(True)
        self.previewScene.addEllipse(-main_radius, -main_radius, main_diameter, main_diameter, pen_main)
        max_extent = max(max_extent, main_radius)

        # Рисуем массивы отверстий. Отображаются только отверстия, с учётом поворота.
        for idx in range(self.arraysLayout.count()):
            widget = self.arraysLayout.itemAt(idx).widget()
            if widget is not None:
                array_diameter, holes_count, hole_diameter, rotation = widget.get_values()
                array_radius = array_diameter / 2.0
                max_extent = max(max_extent, array_radius + hole_diameter / 2.0)
                # Выбор цвета для массива
                color_name = self.color_list[idx % len(self.color_list)]
                pen = QPen(QColor(color_name))
                pen.setCosmetic(True)
                # Устанавливаем цвет надписи "Массив:" для данного массива
                widget.label.setStyleSheet(f"color: {color_name};")
                # Вычисляем смещение поворота (в радианах)
                rotation_rad = rotation * math.pi / 180.0
                # Отрисовка отверстий с учетом поворота
                for j in range(holes_count):
                    angle = 2 * math.pi * j / holes_count + rotation_rad
                    x = array_radius * math.cos(angle)
                    y = array_radius * math.sin(angle)
                    hole_radius = hole_diameter / 2.0
                    self.previewScene.addEllipse(x - hole_radius, y - hole_radius, hole_diameter, hole_diameter, pen)
                # Визуально показываем поворот: рисуем линию от центра до первой позиции отверстия
                line_x = array_radius * math.cos(rotation_rad)
                line_y = array_radius * math.sin(rotation_rad)
                self.previewScene.addLine(0, 0, line_x, line_y, pen)

        # Настройка области отображения с отступом
        self.previewScene.setSceneRect(-max_extent - margin, -max_extent - margin,
                                       2 * (max_extent + margin), 2 * (max_extent + margin))
        # Масштабирование элементов под текущий размер виджета предпросмотра (линии сохраняют толщину)
        self.previewView.fitInView(self.previewScene.sceneRect(), Qt.AspectRatioMode.KeepAspectRatio)

        # Обновление поля "Название" с основным диаметром круга с префиксом "D_"
        self.lineName.setText(f"D_{main_diameter:.2f}")

    def generate_dxf(self):
        main_diameter = self.spinMainCircle.value()
        doc = ezdxf.new(dxfversion="R2010")
        msp = doc.modelspace()

        main_radius = main_diameter / 2.0
        msp.add_circle(center=(0, 0), radius=main_radius)

        for idx in range(self.arraysLayout.count()):
            widget = self.arraysLayout.itemAt(idx).widget()
            if widget is not None:
                array_diameter, holes_count, hole_diameter, rotation = widget.get_values()
                array_radius = array_diameter / 2.0
                rotation_rad = rotation * math.pi / 180.0
                for j in range(holes_count):
                    angle = 2 * math.pi * j / holes_count + rotation_rad
                    x = array_radius * math.cos(angle)
                    y = array_radius * math.sin(angle)
                    msp.add_circle(center=(x, y), radius=hole_diameter / 2.0)

        # Формирование имени файла согласно введённым полям
        designation = self.lineDesignation.text().strip()
        name = self.lineName.text().strip() if self.lineName.text().strip() else f"D_{main_diameter:.2f}"
        if designation:
            default_filename = f"{designation}_{name}.dxf"
        else:
            default_filename = f"{name}.dxf"

        file_path, _ = QFileDialog.getSaveFileName(self, "Сохранить DXF", default_filename, filter="DXF файлы (*.dxf)")
        if file_path:
            if not file_path.lower().endswith(".dxf"):
                file_path += ".dxf"
            try:
                doc.saveas(file_path)
                # Диалог с кнопками "Открыть папку" и "Закрыть"
                msg_box = QMessageBox(self)
                msg_box.setWindowTitle("Успех")
                msg_box.setText(f"Файл успешно сохранён:\n{file_path}")
                open_folder_button = msg_box.addButton("Открыть папку", QMessageBox.ButtonRole.ActionRole)
                msg_box.addButton("Закрыть", QMessageBox.ButtonRole.RejectRole)
                msg_box.exec()
                if msg_box.clickedButton() == open_folder_button:
                    folder = os.path.dirname(file_path)
                    QDesktopServices.openUrl(QUrl.fromLocalFile(folder))
            except Exception as e:
                QMessageBox.critical(self, "Ошибка", f"Ошибка при сохранении файла:\n{str(e)}")

def main():
    app = QApplication(sys.argv)
    window = MainWindow()
    window.resize(1000, 600)
    window.show()
    sys.exit(app.exec())

if __name__ == '__main__':
    main()
