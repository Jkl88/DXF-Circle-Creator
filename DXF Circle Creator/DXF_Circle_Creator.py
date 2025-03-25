import sys
import math
import os
import ezdxf
from PyQt6.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
    QLabel, QDoubleSpinBox, QSpinBox, QLineEdit, QPushButton, QFileDialog,
    QMessageBox, QScrollArea, QGraphicsView, QGraphicsScene, QInputDialog
)
from PyQt6.QtCore import Qt, QUrl
from PyQt6.QtGui import QPainter, QTransform, QColor, QPen, QDesktopServices

# Виджет для ввода параметров массива отверстий
class ArrayEntry(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        layout = QHBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)

        # Надпись "Массив:" – цвет будет изменяться согласно выбранному для данного массива
        self.label = QLabel("Массив:")

        # Диаметр окружности, по которой располагаются отверстия
        self.spinArrayDiameter = QDoubleSpinBox()
        self.spinArrayDiameter.setMinimum(0.0)
        self.spinArrayDiameter.setMaximum(10000.0)
        self.spinArrayDiameter.setDecimals(2)
        self.spinArrayDiameter.setValue(100.0)
        self.spinArrayDiameter.setSuffix(" мм")
        self.spinArrayDiameter.setToolTip("Диаметр окружности, по которой располагаются отверстия")

        # Количество отверстий в массиве
        self.spinHolesCount = QSpinBox()
        self.spinHolesCount.setMinimum(1)
        self.spinHolesCount.setMaximum(1000)
        self.spinHolesCount.setValue(6)
        self.spinHolesCount.setToolTip("Количество отверстий в массиве")

        # Диаметр отверстия
        self.spinHoleDiameter = QDoubleSpinBox()
        self.spinHoleDiameter.setMinimum(0.0)
        self.spinHoleDiameter.setMaximum(10000.0)
        self.spinHoleDiameter.setDecimals(2)
        self.spinHoleDiameter.setValue(10.0)
        self.spinHoleDiameter.setSuffix(" мм")
        self.spinHoleDiameter.setToolTip("Диаметр отверстия")

        # Поворот массива относительно 0 (в градусах)
        self.spinRotation = QDoubleSpinBox()
        self.spinRotation.setMinimum(-360.0)
        self.spinRotation.setMaximum(360.0)
        self.spinRotation.setDecimals(1)
        self.spinRotation.setValue(0.0)
        self.spinRotation.setSuffix("°")
        self.spinRotation.setToolTip("Поворот относительно 0 (в градусах)")

        # Кнопка удаления массива – обозначена как "Х"
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
        # Разделение окна: слева – элементы управления, справа – предпросмотр
        mainLayout = QHBoxLayout(centralWidget)

        # Левая панель – элементы управления (ширина увеличена для удобного ввода)
        controlsWidget = QWidget()
        controlsWidget.setMinimumWidth(400)
        controlsLayout = QVBoxLayout(controlsWidget)
        controlsLayout.setAlignment(Qt.AlignmentFlag.AlignTop)

        # Поле "Обозначение"
        designationLayout = QHBoxLayout()
        labelDesignation = QLabel("Обозначение:")
        self.lineDesignation = QLineEdit()
        self.lineDesignation.setToolTip("Введите обозначение (необязательно)")
        designationLayout.addWidget(labelDesignation)
        designationLayout.addWidget(self.lineDesignation)
        controlsLayout.addLayout(designationLayout)

        # Поле "Название" (автоматически подставляется как D_[диаметр основного круга])
        nameLayout = QHBoxLayout()
        labelName = QLabel("Название:")
        self.lineName = QLineEdit()
        self.lineName.setToolTip("Название подставляется автоматически в формате D_[диаметр основного круга]")
        nameLayout.addWidget(labelName)
        nameLayout.addWidget(self.lineName)
        controlsLayout.addLayout(nameLayout)

        # Параметры основного круга
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

        # Метка для массива отверстий
        arraysLabel = QLabel("Массивы отверстий:")
        controlsLayout.addWidget(arraysLabel)

        # Прокручиваемая область для массивов
        self.scrollArea = QScrollArea()
        self.scrollArea.setWidgetResizable(True)
        self.arraysContainer = QWidget()
        self.arraysLayout = QVBoxLayout(self.arraysContainer)
        self.arraysLayout.setAlignment(Qt.AlignmentFlag.AlignTop)
        self.scrollArea.setWidget(self.arraysContainer)
        controlsLayout.addWidget(self.scrollArea, stretch=1)

        # Кнопка "Добавить массив"
        self.addArrayButton = QPushButton("Добавить массив")
        self.addArrayButton.clicked.connect(self.add_array)
        controlsLayout.addWidget(self.addArrayButton)

        # Кнопка "Сгенерировать DXF"
        self.generateButton = QPushButton("Сгенерировать DXF")
        self.generateButton.clicked.connect(self.generate_dxf)
        controlsLayout.addWidget(self.generateButton)
        
        # Кнопка "Сгенерировать в компас 3D"
        self.generateKompasButton = QPushButton("Сгенерировать в компас 3D")
        self.generateKompasButton.clicked.connect(self.generate_in_kompas)
        controlsLayout.addWidget(self.generateKompasButton)

        mainLayout.addWidget(controlsWidget, stretch=1)

        # Правая панель – предпросмотр (масштабируется, линии фиксированной толщины)
        self.previewScene = QGraphicsScene(self)
        self.previewView = QGraphicsView(self.previewScene)
        self.previewView.setRenderHint(QPainter.RenderHint.Antialiasing)
        self.previewView.setMinimumSize(400, 400)
        # Инвертируем ось Y для удобства (десятичная система координат)
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

        # Рисуем основной круг (с использованием косметического пера — толщина не меняется при масштабировании)
        main_diameter = self.spinMainCircle.value()
        main_radius = main_diameter / 2.0
        pen_main = QPen(Qt.GlobalColor.black)
        pen_main.setCosmetic(True)
        self.previewScene.addEllipse(-main_radius, -main_radius, main_diameter, main_diameter, pen_main)
        max_extent = max(max_extent, main_radius)

        # Рисуем массивы отверстий с учётом поворота
        for idx in range(self.arraysLayout.count()):
            widget = self.arraysLayout.itemAt(idx).widget()
            if widget is not None:
                array_diameter, holes_count, hole_diameter, rotation = widget.get_values()
                array_radius = array_diameter / 2.0
                max_extent = max(max_extent, array_radius + hole_diameter / 2.0)
                color_name = self.color_list[idx % len(self.color_list)]
                pen = QPen(QColor(color_name))
                pen.setCosmetic(True)
                # Устанавливаем цвет надписи "Массив:" для данного массива
                widget.label.setStyleSheet(f"color: {color_name};")
                rotation_rad = math.radians(rotation)
                for j in range(holes_count):
                    angle = 2 * math.pi * j / holes_count + rotation_rad
                    x = array_radius * math.cos(angle)
                    y = array_radius * math.sin(angle)
                    hole_radius = hole_diameter / 2.0
                    self.previewScene.addEllipse(x - hole_radius, y - hole_radius,
                                                 hole_diameter, hole_diameter, pen)
                # Рисуем линию, показывающую поворот (от центра до первой позиции отверстия)
                line_x = array_radius * math.cos(rotation_rad)
                line_y = array_radius * math.sin(rotation_rad)
                self.previewScene.addLine(0, 0, line_x, line_y, pen)

        self.previewScene.setSceneRect(-max_extent - margin, -max_extent - margin,
                                       2 * (max_extent + margin), 2 * (max_extent + margin))
        self.previewView.fitInView(self.previewScene.sceneRect(), Qt.AspectRatioMode.KeepAspectRatio)

        # Обновляем поле "Название" с основным диаметром круга (формат D_[диаметр])
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
                rotation_rad = math.radians(rotation)
                for j in range(holes_count):
                    angle = 2 * math.pi * j / holes_count + rotation_rad
                    x = array_radius * math.cos(angle)
                    y = array_radius * math.sin(angle)
                    msp.add_circle(center=(x, y), radius=hole_diameter / 2.0)

        designation = self.lineDesignation.text().strip()
        name = self.lineName.text().strip() or f"D_{self.spinMainCircle.value():.2f}"
        default_filename = f"{designation}_{name}.dxf" if designation else f"{name}.dxf"

        file_path, _ = QFileDialog.getSaveFileName(self, "Сохранить DXF", default_filename, filter="DXF файлы (*.dxf)")
        if file_path:
            if not file_path.lower().endswith(".dxf"):
                file_path += ".dxf"
            try:
                doc.saveas(file_path)
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

    def generate_in_kompas(self):
        # Запрос толщины детали
        thickness, ok = QInputDialog.getDouble(self, "Толщина", "Введите толщину (мм):", decimals=2)
        if not ok:
            return
        try:
            try:
                import win32com.client
            except ImportError:
                QMessageBox.critical(self, "Ошибка", "Модуль win32com не установлен. Установите его:\n\npip install pywin32")
                return

            # Используем ProgID "KOMPAS.Application.7" для Kompas 3D v21
            try:
                kompas = win32com.client.Dispatch("KOMPAS.Application.7")
            except Exception:
                kompas = win32com.client.DispatchEx("KOMPAS.Application.7")
            kompas.Visible = True

            # Создание нового документа детали
            doc = kompas.Documents.Add(4)
            # Получаем верхнюю часть детали (предполагается, что doc поддерживает API7)
            part7 = doc.TopPart

            # Создаем новый эскиз на плоскости XOY
            # Здесь используются гипотетические константы API7 – реальные значения могут отличаться.
            o3d_sketch = 1  # предположим, что 1 соответствует эскизу
            sketch = part7.NewEntity(o3d_sketch)
            sketch_def = sketch.GetDefinition()
            # Получаем плоскость XOY; метод GetDefaultEntity с параметром 0 – предполагается, что 0 соответствует XOY
            planeXOY = part7.GetDefaultEntity(0)
            sketch_def.SetPlane(planeXOY)
            sketch.Create()
            sketch_def.BeginEdit()
            # Получаем интерфейс для редактирования эскиза (ksDocument2D)
            # Здесь используется гипотетический метод Get2DDocument(); в реальном API он может называться иначе.
            doc2d = doc.Get2DDocument()
            # Рисуем основу детали – окружность с радиусом, равным половине диаметра основного круга
            base_radius = self.spinMainCircle.value() / 2.0
            doc2d.ksCircle(0, 0, base_radius, 1)
            # Для каждого массива отверстий рисуем отверстия по окружности
            for idx in range(self.arraysLayout.count()):
                widget = self.arraysLayout.itemAt(idx).widget()
                if widget is not None:
                    array_diameter, holes_count, hole_diameter, rotation = widget.get_values()
                    array_radius = array_diameter / 2.0
                    rotation_rad = math.radians(rotation)
                    for j in range(holes_count):
                        angle = 2 * math.pi * j / holes_count + rotation_rad
                        x = array_radius * math.cos(angle)
                        y = array_radius * math.sin(angle)
                        doc2d.ksCircle(x, y, hole_diameter / 2.0, 1)
            sketch_def.EndEdit()
            sketch.Update()

            # Создаем операцию выдавливания (Boss Extrusion)
            o3d_bossExtrusion = 2  # гипотетическая константа для операции выдавливания
            extrusion = part7.NewEntity(o3d_bossExtrusion)
            extr_def = extrusion.GetDefinition()
            extr_def.SetSketch(sketch)
            # Получаем параметры выдавливания и задаем толщину детали
            extr_param = extr_def.ExtrusionParam()
            extr_param.depthNormal = thickness
            # Устанавливаем дополнительные параметры выдавливания (если требуется)
            extr_def.ExtrusionParam = extr_param
            extrusion.Create()

            # Формируем имя детали из полей "Обозначение" и "Название"
            designation = self.lineDesignation.text().strip()
            main_diam = self.spinMainCircle.value()
            name = self.lineName.text().strip() or f"D_{main_diam:.2f}"
            detail_name = f"{designation}_{name}" if designation else name

            # Устанавливаем свойства детали: Marking и Name
            part7.Marking = detail_name
            part7.Name = detail_name
            part7.Update()

            QMessageBox.information(self, "Успех", f"Деталь создана в Компас 3D:\n{detail_name} с толщиной {thickness} мм")
        except Exception as e:
            QMessageBox.critical(self, "Ошибка", f"Компас не запущен или произошла ошибка:\n{str(e)}")

def main():
    app = QApplication(sys.argv)
    window = MainWindow()
    window.resize(1000, 600)
    window.show()
    sys.exit(app.exec())

if __name__ == '__main__':
    main()
