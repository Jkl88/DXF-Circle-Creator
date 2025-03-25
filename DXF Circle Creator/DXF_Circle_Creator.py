import sys
import math
import ezdxf
from PyQt6.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
    QLabel, QLineEdit, QPushButton, QFileDialog, QMessageBox, QScrollArea,
    QGraphicsView, QGraphicsScene
)
from PyQt6.QtCore import Qt
from PyQt6.QtGui import QPainter, QTransform

# Виджет для ввода параметров массива отверстий
class ArrayEntry(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        layout = QHBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)

        self.label = QLabel("Array:")
        self.arrayDiameterEdit = QLineEdit()
        self.arrayDiameterEdit.setPlaceholderText("Array Diameter")
        self.holesCountEdit = QLineEdit()
        self.holesCountEdit.setPlaceholderText("Holes Count")
        self.holeDiameterEdit = QLineEdit()
        self.holeDiameterEdit.setPlaceholderText("Hole Diameter")
        self.removeButton = QPushButton("Remove")
        self.removeButton.setFixedWidth(70)

        layout.addWidget(self.label)
        layout.addWidget(self.arrayDiameterEdit)
        layout.addWidget(self.holesCountEdit)
        layout.addWidget(self.holeDiameterEdit)
        layout.addWidget(self.removeButton)

        # При нажатии на кнопку «Remove» удаляем данный виджет
        self.removeButton.clicked.connect(self.remove_self)

    def remove_self(self):
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
        self.setWindowTitle("DXF Constructor: Circles & Holes")

        centralWidget = QWidget()
        self.setCentralWidget(centralWidget)
        mainLayout = QVBoxLayout(centralWidget)

        # Ввод параметров основного круга
        mainCircleLayout = QHBoxLayout()
        mainCircleLabel = QLabel("Main Circle Diameter:")
        self.mainCircleEdit = QLineEdit()
        self.mainCircleEdit.setPlaceholderText("Enter diameter")
        mainCircleLayout.addWidget(mainCircleLabel)
        mainCircleLayout.addWidget(self.mainCircleEdit)
        mainLayout.addLayout(mainCircleLayout)

        # Обновление превью при изменении значения основного круга
        self.mainCircleEdit.textChanged.connect(self.update_preview)

        # Раздел для добавления массивов отверстий
        arraysLabel = QLabel("Hole Arrays:")
        mainLayout.addWidget(arraysLabel)

        self.scrollArea = QScrollArea()
        self.scrollArea.setWidgetResizable(True)
        self.arraysContainer = QWidget()
        self.arraysLayout = QVBoxLayout(self.arraysContainer)
        self.arraysLayout.setAlignment(Qt.AlignmentFlag.AlignTop)
        self.scrollArea.setWidget(self.arraysContainer)
        mainLayout.addWidget(self.scrollArea, stretch=1)

        # Кнопка для добавления нового массива
        self.addArrayButton = QPushButton("Add Array")
        self.addArrayButton.clicked.connect(self.add_array)
        mainLayout.addWidget(self.addArrayButton)

        # Кнопка для генерации DXF файла
        self.generateButton = QPushButton("Generate DXF")
        self.generateButton.clicked.connect(self.generate_dxf)
        mainLayout.addWidget(self.generateButton)

        # Реальное время просмотра чертежа с использованием QGraphicsView
        self.previewScene = QGraphicsScene(self)
        self.previewView = QGraphicsView(self.previewScene)
        self.previewView.setRenderHint(QPainter.RenderHint.Antialiasing)
        self.previewView.setMinimumSize(400, 400)
        # Инвертируем ось Y для привычной декартовой системы координат
        self.previewView.setTransform(QTransform().scale(1, -1))
        mainLayout.addWidget(self.previewView)

    def add_array(self):
        array_entry = ArrayEntry(self.arraysContainer)
        self.arraysLayout.addWidget(array_entry)
        # Обновляем превью при изменении параметров массива
        array_entry.arrayDiameterEdit.textChanged.connect(self.update_preview)
        array_entry.holesCountEdit.textChanged.connect(self.update_preview)
        array_entry.holeDiameterEdit.textChanged.connect(self.update_preview)
        array_entry.removeButton.clicked.connect(self.update_preview)
        self.update_preview()

    def update_preview(self):
        self.previewScene.clear()
        margin = 10
        max_extent = 0

        # Рисуем основной круг, если введено корректное значение
        try:
            main_diameter = float(self.mainCircleEdit.text())
            main_radius = main_diameter / 2.0
            self.previewScene.addEllipse(-main_radius, -main_radius, main_diameter, main_diameter)
            max_extent = max(max_extent, main_radius)
        except ValueError:
            pass

        # Рисуем каждый массив отверстий
        for i in range(self.arraysLayout.count()):
            widget = self.arraysLayout.itemAt(i).widget()
            if widget is not None:
                try:
                    array_diameter, holes_count, hole_diameter = widget.get_values()
                    array_radius = array_diameter / 2.0
                    max_extent = max(max_extent, array_radius + hole_diameter/2.0)
                    for j in range(holes_count):
                        angle = 2 * math.pi * j / holes_count
                        x = array_radius * math.cos(angle)
                        y = array_radius * math.sin(angle)
                        hole_radius = hole_diameter / 2.0
                        self.previewScene.addEllipse(x - hole_radius, y - hole_radius, hole_diameter, hole_diameter)
                except ValueError:
                    continue

        # Настраиваем область отображения с учётом отступа
        self.previewScene.setSceneRect(-max_extent - margin, -max_extent - margin,
                                       2*(max_extent + margin), 2*(max_extent + margin))

    def generate_dxf(self):
        try:
            main_diameter = float(self.mainCircleEdit.text())
        except ValueError:
            QMessageBox.critical(self, "Error", "Please enter a valid main circle diameter.")
            return

        doc = ezdxf.new(dxfversion="R2010")
        msp = doc.modelspace()

        main_radius = main_diameter / 2.0
        msp.add_circle(center=(0, 0), radius=main_radius)

        for i in range(self.arraysLayout.count()):
            widget = self.arraysLayout.itemAt(i).widget()
            if widget is not None:
                try:
                    array_diameter, holes_count, hole_diameter = widget.get_values()
                except ValueError as e:
                    QMessageBox.critical(self, "Error", str(e))
                    return

                array_radius = array_diameter / 2.0
                for j in range(holes_count):
                    angle = 2 * math.pi * j / holes_count
                    x = array_radius * math.cos(angle)
                    y = array_radius * math.sin(angle)
                    msp.add_circle(center=(x, y), radius=hole_diameter / 2.0)

        file_path, _ = QFileDialog.getSaveFileName(self, "Save DXF", filter="DXF Files (*.dxf)")
        if file_path:
            try:
                doc.saveas(file_path)
                QMessageBox.information(self, "Success", f"File saved successfully:\n{file_path}")
            except Exception as e:
                QMessageBox.critical(self, "Error", f"Error saving file:\n{str(e)}")

def main():
    app = QApplication(sys.argv)
    window = MainWindow()
    window.resize(800, 600)
    window.show()
    sys.exit(app.exec())

if __name__ == '__main__':
    main()
