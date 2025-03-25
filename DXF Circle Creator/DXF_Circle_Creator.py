
        # ������������ ������ ����������� ������
        for i in range(self.arraysLayout.count()):
            widget = self.arraysLayout.itemAt(i).widget()
            if widget is not None:
                try:
                    array_diameter, holes_count, hole_diameter = widget.get_values()
                except ValueError as e:
                    QMessageBox.critical(self, "������", str(e))
                    return

                array_radius = array_diameter / 2.0
                # ����������� ��������� ���������� �� ����������
                for j in range(holes_count):
                    angle = 2 * math.pi * j / holes_count
                    x = array_radius * math.cos(angle)
                    y = array_radius * math.sin(angle)
                    # ������ ��������� ��� ����
                    msp.add_circle(center=(x, y), radius=hole_diameter / 2.0)

        # ����� ���� ��� ���������� �����
        file_path, _ = QFileDialog.getSaveFileName(self, "��������� DXF", filter="DXF Files (*.dxf)")
        if file_path:
            try:
                doc.saveas(file_path)
                QMessageBox.information(self, "�����", f"���� ������� �������:\n{file_path}")
            except Exception as e:
                QMessageBox.critical(self, "������", f"������ ��� ���������� �����:\n{str(e)}")

def main():
    app = QApplication(sys.argv)
    window = MainWindow()
    window.resize(600, 400)
    window.show()
    sys.exit(app.exec())

if __name__ == '__main__':
    main()
