import sys
import os
import laspy
import numpy as np
from PyQt6.QtWidgets import (
    QApplication, QWidget, QPushButton, QFileDialog, QLabel, QVBoxLayout,
    QTableWidget, QTableWidgetItem, QProgressBar, QComboBox, QLineEdit
)
from datetime import datetime

class LasAnalyzerApp(QWidget):
    def __init__(self):
        super().__init__()
        self.init_ui()

    def init_ui(self):
        self.setWindowTitle("LAS File Analyzer")
        self.setGeometry(100, 100, 800, 600)

        self.label = QLabel("Select a directory with LAS files:", self)
        self.btn_select_dir = QPushButton("Select Directory", self)
        self.btn_analyze = QPushButton("Analyze Files", self)
        self.btn_clean = QPushButton("Start Cleaning", self)

        self.path_label = QLabel("", self)
        self.save_path_label = QLabel("Select a directory to save cleaned files:", self)
        self.btn_select_save_dir = QPushButton("Select Save Directory", self)

        self.table_files = QTableWidget(self)
        self.table_files.setColumnCount(9)
        self.table_files.setHorizontalHeaderLabels(
            ["File", "Points", "dx", "dy", "dz", "dr", "dg", "db", "Removed Points"]
        )

        self.table_stats = QTableWidget(self)
        self.table_stats.setColumnCount(3)
        self.table_stats.setHorizontalHeaderLabels(["Average", "Min", "Max"])

        self.progress_bar = QProgressBar(self)
        self.progress_bar.setRange(0, 100)
        self.progress_bar.setValue(0)
        self.progress_bar.setTextVisible(True)

        self.label_processing = QLabel("Processing: 0 files", self)
        self.label_end_time = QLabel("", self)
        self.label_total_time = QLabel("", self)

        self.label_points = QLabel("Number of points to process (default 5M):", self)
        self.points_input = QLineEdit("5000000", self)

        self.btn_select_dir.clicked.connect(self.select_directory)
        self.btn_analyze.clicked.connect(self.analyze_files)
        self.btn_clean.clicked.connect(self.start_cleaning)
        self.btn_select_save_dir.clicked.connect(self.select_save_directory)

        self.cleaning_algo_combo = QComboBox(self)
        self.cleaning_algo_combo.addItems(["ZOR"])

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
        layout.addWidget(self.points_input)
        layout.addWidget(self.btn_select_save_dir)
        layout.addWidget(self.save_path_label)
        layout.addWidget(self.btn_clean)

        self.setLayout(layout)
        self.las_files = []
        self.files_names = []
        self.save_directory = ""

    def select_directory(self):
        directory = QFileDialog.getExistingDirectory(self, "Select LAS file folder")
        if directory:
            self.las_files = [os.path.join(directory, f) for f in os.listdir(directory) if f.endswith(".las")]
            self.files_names = [os.path.basename(f) for f in self.las_files]
            self.path_label.setText(f"Path: {directory}")
            self.table_files.setRowCount(len(self.las_files))
            for i, file in enumerate(self.files_names):
                self.table_files.setItem(i, 0, QTableWidgetItem(file))

    def select_save_directory(self):
        directory = QFileDialog.getExistingDirectory(self, "Select save directory")
        if directory:
            self.save_directory = directory
            self.save_path_label.setText(f"Save path: {directory}")

    def analyze_files(self):
        if not self.las_files:
            self.table_files.setRowCount(0)
            return

        self.progress_bar.setValue(0)
        self.label_processing.setText("Processing: 0 files")
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
            dx, dy, dz = las.x.max() - las.x.min(), las.y.max() - las.y.min(), las.z.max() - las.z.min()
            dx_list.append(dx)
            dy_list.append(dy)
            dz_list.append(dz)

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
            self.label_processing.setText(f"Processing: {i + 1} of {total_files} files ({self.files_names[i]})")

        if total_points:
            avg_points = np.mean(total_points)
            min_points, max_points = min(total_points), max(total_points)
            self.table_stats.setRowCount(1)
            self.table_stats.setItem(0, 0, QTableWidgetItem(f"{avg_points:.0f}"))
            self.table_stats.setItem(0, 1, QTableWidgetItem(f"{min_points}"))
            self.table_stats.setItem(0, 2, QTableWidgetItem(f"{max_points}"))

        end_time = datetime.now()
        duration = round((end_time - start_time).total_seconds(), 1)
        self.label_end_time.setText(f"Finished: {end_time.strftime('%Y-%m-%d %H:%M:%S')}")
        self.label_total_time.setText(f"Processing time: {duration} seconds")

    def start_cleaning(self):
        if not self.las_files or not self.save_directory:
            return

        algorithm = self.cleaning_algo_combo.currentText()

        try:
            points_limit = int(self.points_input.text())
        except ValueError:
            points_limit = 5000000

        self.progress_bar.setValue(0)
        self.label_processing.setText("Processing: 0 files")
        total_files = len(self.las_files)
        self.progress_bar.setRange(0, total_files)

        start_time = datetime.now()

        for i, file in enumerate(self.las_files):
            las = laspy.read(file)
            if len(las.points) > points_limit:
                selected_indices = np.random.choice(len(las.points), points_limit, replace=False)
                las.points = las.points[selected_indices]

            if algorithm == "ZOR":
                name = os.path.basename(file)
                original_point_count = len(las.points)
                removed_points = self.apply_zor(las, name)
                self.table_files.setItem(i, 8, QTableWidgetItem(str(removed_points)))

            self.progress_bar.setValue(i + 1)
            self.label_processing.setText(f"Processing: {i + 1} of {total_files} files ({self.files_names[i]})")

        end_time = datetime.now()
        duration = round((end_time - start_time).total_seconds(), 1)
        self.label_end_time.setText(f"Finished: {end_time.strftime('%Y-%m-%d %H:%M:%S')}")
        self.label_total_time.setText(f"Processing time: {duration} seconds")

    def apply_zor(self, las, name, max_iter=100, z_sigma_threshold=3):
        original_count = len(las.points)
        z = las.z
        for iteration in range(max_iter):
            mu_z = np.mean(z)
            std_z = np.std(z)
            lower_bound = mu_z - z_sigma_threshold * std_z
            upper_bound = mu_z + z_sigma_threshold * std_z
            valid_indices = np.where((z >= lower_bound) & (z <= upper_bound))[0]
            if len(valid_indices) == len(z):
                break
            las.points = las.points[valid_indices]
            z = las.z
        removed_points = original_count - len(las.points)
        if self.save_directory:
            save_path = os.path.join(self.save_directory, os.path.basename(name))
            las.write(save_path)
        return removed_points

if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = LasAnalyzerApp()
    window.show()
    sys.exit(app.exec())
