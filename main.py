import sys
import os
import laspy
import numpy as np
from PyQt6.QtWidgets import QApplication, QWidget, QPushButton, QFileDialog, QLabel, QVBoxLayout, QTableWidget, QTableWidgetItem, QProgressBar, QComboBox, QLineEdit
from datetime import datetime
#from scipy.spatial import KDTree

class LasAnalyzerApp(QWidget):
    def __init__(self):
        super().__init__()
        self.init_ui()

    def init_ui(self):
        self.setWindowTitle("LAS File Analyzer")
        self.setGeometry(100, 100, 800, 600)

        self.label = QLabel("Выберите директорию с LAS-файлами:", self)
        self.btn_select_dir = QPushButton("Выбрать директорию", self)
        self.btn_analyze = QPushButton("Анализировать файлы", self)
        self.btn_clean = QPushButton("Старт очистки", self)

        self.path_label = QLabel("", self)  # Метка для отображения пути директории
        self.save_path_label = QLabel("Выберите каталог для сохранения обработанных файлов", self)
        self.btn_select_save_dir = QPushButton("Выбрать каталог для сохранения", self)

        self.table_files = QTableWidget(self)
        self.table_files.setColumnCount(9)
        self.table_files.setHorizontalHeaderLabels(
            ["Файл", "Точек", "dx", "dy", "dz", "dr", "dg", "db", "Удалено точек"]
        )

        self.table_stats = QTableWidget(self)
        self.table_stats.setColumnCount(3)
        self.table_stats.setHorizontalHeaderLabels(["Среднее", "Мин.", "Макс."])

        # Добавление прогресс-бара
        self.progress_bar = QProgressBar(self)
        self.progress_bar.setRange(0, 100)
        self.progress_bar.setValue(0)
        self.progress_bar.setTextVisible(True)

        # Метка для отображения текущего файла и количества обработанных файлов
        self.label_processing = QLabel("Обрабатывается: 0 файлов", self)

        # Метка для отображения времени окончания
        self.label_end_time = QLabel("", self)

        # Метка для отображения времени всей обработки
        self.label_total_time = QLabel("", self)

        # Поле для ввода количества точек
        self.label_points = QLabel("Количество точек для обработки (по умолчанию 5M):", self)
        self.points_input = QLineEdit("5000000", self)

        self.btn_select_dir.clicked.connect(self.select_directory)
        self.btn_analyze.clicked.connect(self.analyze_files)
        self.btn_clean.clicked.connect(self.start_cleaning)
        self.btn_select_save_dir.clicked.connect(self.select_save_directory)

        # Dropdown для выбора алгоритма очистки
        self.cleaning_algo_combo = QComboBox(self)
        self.cleaning_algo_combo.addItems(["ZOR", "SOR", "ROR"])

        layout = QVBoxLayout()
        layout.addWidget(self.label)
        layout.addWidget(self.btn_select_dir)
        layout.addWidget(self.path_label)
        layout.addWidget(self.btn_analyze)
        layout.addWidget(self.table_files)
        layout.addWidget(self.table_stats)
        layout.addWidget(self.progress_bar)
        layout.addWidget(self.label_processing)
        layout.addWidget(self.label_end_time)
        layout.addWidget(self.label_total_time)
        layout.addWidget(self.cleaning_algo_combo)
        layout.addWidget(self.label_points)
        layout.addWidget(self.points_input)  # Поле для ввода количества точек
        layout.addWidget(self.btn_select_save_dir)
        layout.addWidget(self.save_path_label)
        layout.addWidget(self.btn_clean)

        self.setLayout(layout)
        self.las_files = []
        self.files_names = []  # Список для хранения имен файлов
        self.save_directory = ""
    
    def select_directory(self):
        directory = QFileDialog.getExistingDirectory(self, "Выберите папку с LAS-файлами")
        if directory:
            self.las_files = [os.path.join(directory, f) for f in os.listdir(directory) if f.endswith(".las")]
            self.files_names = [os.path.basename(f) for f in self.las_files]
            self.path_label.setText(f"Путь: {directory}")

            # Заполняем таблицу названиями файлов
            self.table_files.setRowCount(len(self.las_files))
            for i, file in enumerate(self.files_names):
                self.table_files.setItem(i, 0, QTableWidgetItem(file))

    def select_save_directory(self):
        directory = QFileDialog.getExistingDirectory(self, "Выберите каталог для сохранения обработанных файлов")
        if directory:
            self.save_directory = directory
            self.save_path_label.setText(f"Путь для сохранения: {directory}")

    def analyze_files(self):
        if not self.las_files:
            self.table_files.setRowCount(0)
            return

        # Очистка предыдущей информации
        self.progress_bar.setValue(0)
        self.label_processing.setText("Обрабатывается: 0 файлов")
        self.label_end_time.setText("")
        self.label_total_time.setText("")

        total_points = []
        dx_list, dy_list, dz_list = [], [], []
        dr_list, dg_list, db_list = [], [], []

        total_files = len(self.las_files)

        self.progress_bar.setRange(0, total_files)

        start_time = datetime.now()

        for i, file in enumerate(self.las_files):
            las = laspy.read(file)

            # Геометрические параметры
            dx, dy, dz = las.x.max() - las.x.min(), las.y.max() - las.y.min(), las.z.max() - las.z.min()
            dx_list.append(dx)
            dy_list.append(dy)
            dz_list.append(dz)

            # Цветовые параметры
            if hasattr(las, 'red') and hasattr(las, 'green') and hasattr(las, 'blue'):
                dr = las.red.max() - las.red.min()
                dg = las.green.max() - las.green.min()
                db = las.blue.max() - las.blue.min()
                dr_list.append(dr)
                dg_list.append(dg)
                db_list.append(db)

            total_points.append(len(las.points))

            self.table_files.setItem(i, 1, QTableWidgetItem(str(total_points[-1])))
            self.table_files.setItem(i, 2, QTableWidgetItem(f"{dx:.2f}"))
            self.table_files.setItem(i, 3, QTableWidgetItem(f"{dy:.2f}"))
            self.table_files.setItem(i, 4, QTableWidgetItem(f"{dz:.2f}"))
            if dr_list:
                self.table_files.setItem(i, 5, QTableWidgetItem(f"{dr:.2f}"))
                self.table_files.setItem(i, 6, QTableWidgetItem(f"{dg:.2f}"))
                self.table_files.setItem(i, 7, QTableWidgetItem(f"{db:.2f}"))

            self.progress_bar.setValue(i + 1)
            self.label_processing.setText(f"Обрабатывается: {i + 1} из {total_files} файлов ({self.files_names[i]})")

        if total_points:
            avg_points = np.mean(total_points)
            min_points, max_points = min(total_points), max(total_points)
            self.table_stats.setRowCount(1)
            self.table_stats.setItem(0, 0, QTableWidgetItem(f"{avg_points:.0f}"))
            self.table_stats.setItem(0, 1, QTableWidgetItem(f"{min_points}"))
            self.table_stats.setItem(0, 2, QTableWidgetItem(f"{max_points}"))

        end_time = datetime.now()
        processing_duration = end_time - start_time

        processing_duration = processing_duration.total_seconds()
        processing_duration = round(processing_duration, 1)

        self.label_end_time.setText(f"Дата завершения: {end_time.strftime('%Y-%m-%d %H:%M:%S')}")
        self.label_total_time.setText(f"Время обработки: {str(processing_duration)} секунд")

    def start_cleaning(self):
        if not self.las_files or not self.save_directory:
            return

        algorithm = self.cleaning_algo_combo.currentText()

        # Получаем количество точек из поля ввода
        try:
            points_limit = int(self.points_input.text())
        except ValueError:
            points_limit = 5000000  # Если введено неправильное значение, используем 5M точек по умолчанию

        self.progress_bar.setValue(0)
        self.label_processing.setText("Обрабатывается: 0 файлов")
        total_files = len(self.las_files)
        self.progress_bar.setRange(0, total_files)

        start_time = datetime.now()

        for i, file in enumerate(self.las_files):
            las = laspy.read(file)

            # Ограничение количества точек
            if len(las.points) > points_limit:
                selected_indices = np.random.choice(len(las.points), points_limit, replace=False)
                las.points = las.points[selected_indices]

            if algorithm == "ZOR":
                name = os.path.basename(file)  # Имя файла
                print(name)
                original_point_count = len(las.points)
                removed_points = self.apply_zor(las, name)
                self.table_files.setItem(i, 8, QTableWidgetItem(str(removed_points)))

            self.progress_bar.setValue(i + 1)
            self.label_processing.setText(f"Обрабатывается: {i + 1} из {total_files} файлов ({self.files_names[i]})")

        end_time = datetime.now()
        processing_duration = end_time - start_time

        processing_duration = processing_duration.total_seconds()
        processing_duration = round(processing_duration, 1)

        self.label_end_time.setText(f"Дата завершения: {end_time.strftime('%Y-%m-%d %H:%M:%S')}")
        self.label_total_time.setText(f"Время обработки: {str(processing_duration)} секунд")

    def apply_zor(self, las, name):
        # Применение алгоритма ZOR (Z-Score Outlier Rejection)
        mean_z = np.mean(las.z)
        std_z = np.std(las.z)
        z_scores = (las.z - mean_z) / std_z
        original_count = len(las.points)

        # Удаление точек, Z-score которых больше 3
        mask = np.abs(z_scores) <= 3
        las.points = las.points[mask]

        removed_points = original_count - len(las.points)


        # Сохранение очищенного файла
        if self.save_directory:
            save_path = os.path.join(self.save_directory, os.path.basename(name))
            las.write(save_path)

        return removed_points

if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = LasAnalyzerApp()
    window.show()
    sys.exit(app.exec())
