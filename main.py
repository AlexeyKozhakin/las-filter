import sys
import os
import laspy
import numpy as np
from PyQt6.QtWidgets import QApplication, QWidget, QPushButton, QFileDialog, QLabel, QVBoxLayout, QTableWidget, QTableWidgetItem, QProgressBar

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
        
        self.table_files = QTableWidget(self)
        self.table_files.setColumnCount(8)
        self.table_files.setHorizontalHeaderLabels(
            ["Файл", "Точек", "dx", "dy", "dz", "dr", "dg", "db"]
        )
        
        self.table_stats = QTableWidget(self)
        self.table_stats.setColumnCount(3)
        self.table_stats.setHorizontalHeaderLabels(["Среднее", "Мин.", "Макс."])
        
        # Добавление прогресс-бара
        self.progress_bar = QProgressBar(self)
        self.progress_bar.setRange(0, 100)
        self.progress_bar.setValue(0)
        self.progress_bar.setTextVisible(True)
        
        self.btn_select_dir.clicked.connect(self.select_directory)
        self.btn_analyze.clicked.connect(self.analyze_files)
        
        layout = QVBoxLayout()
        layout.addWidget(self.label)
        layout.addWidget(self.btn_select_dir)
        layout.addWidget(self.btn_analyze)
        layout.addWidget(self.table_files)
        layout.addWidget(self.table_stats)
        layout.addWidget(self.progress_bar)  # Добавление прогресс-бара
        
        self.setLayout(layout)
        self.las_files = []
    
    def select_directory(self):
        directory = QFileDialog.getExistingDirectory(self, "Выберите папку с LAS-файлами")
        if directory:
            self.las_files = [os.path.join(directory, f) for f in os.listdir(directory) if f.endswith(".las")]
            self.table_files.setRowCount(len(self.las_files))
            for i, file in enumerate(self.las_files):
                self.table_files.setItem(i, 0, QTableWidgetItem(os.path.basename(file)))
    
    def analyze_files(self):
        if not self.las_files:
            self.table_files.setRowCount(0)
            return
        
        total_points = []
        dx_list, dy_list, dz_list = [], [], []
        dr_list, dg_list, db_list = [], [], []
        
        total_files = len(self.las_files)
        
        # Обновление диапазона прогресс-бара
        self.progress_bar.setRange(0, total_files)
        
        for i, file in enumerate(self.las_files):
            las = laspy.read(file)
            
            # Геометрические параметры
            dx, dy, dz = las.x.max() - las.x.min(), las.y.max() - las.y.min(), las.z.max() - las.z.min()
            dx_list.append(dx)
            dy_list.append(dy)
            dz_list.append(dz)
            
            # Цветовые параметры (если есть)
            if hasattr(las, 'red') and hasattr(las, 'green') and hasattr(las, 'blue'):
                dr = las.red.max() - las.red.min()
                dg = las.green.max() - las.green.min()
                db = las.blue.max() - las.blue.min()
                dr_list.append(dr)
                dg_list.append(dg)
                db_list.append(db)
            
            # Количество точек
            total_points.append(len(las.points))
            
            # Заполняем таблицу для каждого файла
            self.table_files.setItem(i, 1, QTableWidgetItem(str(total_points[-1])))
            self.table_files.setItem(i, 2, QTableWidgetItem(f"{dx:.2f}"))
            self.table_files.setItem(i, 3, QTableWidgetItem(f"{dy:.2f}"))
            self.table_files.setItem(i, 4, QTableWidgetItem(f"{dz:.2f}"))
            if dr_list:
                self.table_files.setItem(i, 5, QTableWidgetItem(f"{dr:.2f}"))
                self.table_files.setItem(i, 6, QTableWidgetItem(f"{dg:.2f}"))
                self.table_files.setItem(i, 7, QTableWidgetItem(f"{db:.2f}"))
            
            # Обновление прогресс-бара
            self.progress_bar.setValue(i + 1)
        
        # Итоговая статистика
        if total_points:
            avg_points = np.mean(total_points)
            min_points, max_points = min(total_points), max(total_points)
            self.table_stats.setRowCount(1)
            self.table_stats.setItem(0, 0, QTableWidgetItem(f"{avg_points:.0f}"))
            self.table_stats.setItem(0, 1, QTableWidgetItem(f"{min_points}"))
            self.table_stats.setItem(0, 2, QTableWidgetItem(f"{max_points}"))

if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = LasAnalyzerApp()
    window.show()
    sys.exit(app.exec())
