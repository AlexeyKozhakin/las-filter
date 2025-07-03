import os
import sys
import ctypes
import laspy
import numpy as np
from datetime import datetime
import tkinter as tk
from tkinter import ttk, filedialog, messagebox
from local_filter import full_filter_las

# --- Отключение размытия на Windows ---
try:
    ctypes.windll.shcore.SetProcessDpiAwareness(1)
except Exception:
    pass

class LasAnalyzerApp(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("LAS File Analyzer")
        
        # --- Разворачиваем окно на весь экран ---
        self.state('zoomed')
        
        self.las_files = []
        self.files_names = []
        self.save_directory = ""

        self.create_widgets()
        self.create_layout()
        
        # Подстройка ширины колонок при изменении размера окна
        self.table_files.bind("<Configure>", self.adjust_column_widths)
        
        # DPI масштабирование Tkinter
        self.tk.call('tk', 'scaling', 1.0)

    def create_widgets(self):
        self.label = tk.Label(self, text="Select a directory with LAS files:")
        self.btn_select_dir = tk.Button(self, text="Select Directory", command=self.select_directory)
        self.btn_analyze = tk.Button(self, text="Analyze Files", command=self.analyze_files)
        self.btn_clean = tk.Button(self, text="Start Cleaning", command=self.start_cleaning)

        self.path_label = tk.Label(self, text="")
        self.save_path_label = tk.Label(self, text="Select a directory to save cleaned files:")
        self.btn_select_save_dir = tk.Button(self, text="Select Save Directory", command=self.select_save_directory)

        columns_files = ["File", "Points", "dx", "dy", "dz", "dr", "dg", "db", "Removed Points"]
        self.table_files = ttk.Treeview(self, columns=columns_files, show='headings')

        for col in columns_files:
            self.table_files.heading(col, text=col)
            self.table_files.column(col, stretch=True)  # Колонки растягиваются

        columns_stats = ["Average", "Min", "Max"]
        self.table_stats = ttk.Treeview(self, columns=columns_stats, show='headings', height=1)
        for col in columns_stats:
            self.table_stats.heading(col, text=col)
            self.table_stats.column(col, stretch=True)

        self.progress_var = tk.DoubleVar()
        self.progress_bar = ttk.Progressbar(self, variable=self.progress_var, maximum=100)

        self.label_processing = tk.Label(self, text="Processing: 0 files")
        self.label_end_time = tk.Label(self, text="")
        self.label_total_time = tk.Label(self, text="")

        self.label_points = tk.Label(self, text="Number of points to process (default 5M):")
        self.points_input = tk.Entry(self)
        self.points_input.insert(0, "5000000")

        self.cleaning_algo_combo = ttk.Combobox(self, values=["ZOR"])
        self.cleaning_algo_combo.current(0)

    def create_layout(self):
        # Используем grid для гибкой компоновки
        self.label.grid(row=0, column=0, sticky='w', padx=10, pady=5)
        self.btn_select_dir.grid(row=1, column=0, sticky='w', padx=10)
        self.path_label.grid(row=2, column=0, sticky='w', padx=10)

        self.btn_analyze.grid(row=3, column=0, sticky='w', padx=10, pady=5)
        self.table_files.grid(row=4, column=0, sticky='nsew', padx=10, pady=5)
        self.table_stats.grid(row=5, column=0, sticky='ew', padx=10, pady=5)

        self.progress_bar.grid(row=6, column=0, sticky='ew', padx=10, pady=5)
        self.label_processing.grid(row=7, column=0, sticky='w', padx=10)
        self.label_end_time.grid(row=8, column=0, sticky='w', padx=10)
        self.label_total_time.grid(row=9, column=0, sticky='w', padx=10)

        self.cleaning_algo_combo.grid(row=10, column=0, sticky='w', padx=10, pady=5)
        self.label_points.grid(row=11, column=0, sticky='w', padx=10)
        self.points_input.grid(row=12, column=0, sticky='w', padx=10)

        self.btn_select_save_dir.grid(row=13, column=0, sticky='w', padx=10, pady=5)
        self.save_path_label.grid(row=14, column=0, sticky='w', padx=10)

        self.btn_clean.grid(row=15, column=0, sticky='w', padx=10, pady=10)

        # Настраиваем веса строк и колонок, чтобы table_files и table_stats растягивались
        self.grid_rowconfigure(4, weight=10)  # table_files занимает много места по вертикали
        self.grid_rowconfigure(5, weight=1)   # table_stats по высоте меньше
        self.grid_columnconfigure(0, weight=1)

    def adjust_column_widths(self, event=None):
        # Автоматически подгоняем ширину колонок table_files под ширину окна
        total_width = self.table_files.winfo_width()
        if total_width <= 0:
            return
        columns = self.table_files["columns"]
        width_per_col = int(total_width / len(columns))
        for col in columns:
            self.table_files.column(col, width=width_per_col)

        # Аналогично для таблицы статистики
        total_width_stats = self.table_stats.winfo_width()
        if total_width_stats > 0:
            columns_stats = self.table_stats["columns"]
            width_per_col_stats = int(total_width_stats / len(columns_stats))
            for col in columns_stats:
                self.table_stats.column(col, width=width_per_col_stats)

    def select_directory(self):
        directory = filedialog.askdirectory(title="Select LAS file folder")
        if directory:
            self.las_files = [os.path.join(directory, f) for f in os.listdir(directory) if f.endswith(".las")]
            self.files_names = [os.path.basename(f) for f in self.las_files]
            self.path_label.config(text=f"Path: {directory}")

            self.table_files.delete(*self.table_files.get_children())
            for file in self.files_names:
                self.table_files.insert("", "end", values=(file,) + ("",)*8)  # заполняем пустыми столбцами

    def select_save_directory(self):
        directory = filedialog.askdirectory(title="Select save directory")
        if directory:
            self.save_directory = directory
            self.save_path_label.config(text=f"Save path: {directory}")

    def analyze_files(self):
        if not self.las_files:
            messagebox.showwarning("Warning", "No LAS files selected.")
            return

        self.progress_var.set(0)
        self.label_processing.config(text="Processing: 0 files")
        self.label_end_time.config(text="")
        self.label_total_time.config(text="")

        total_points = []
        dx_list, dy_list, dz_list = [], [], []
        dr_list, dg_list, db_list = [], [], []

        total_files = len(self.las_files)
        self.progress_bar.config(maximum=total_files)

        start_time = datetime.now()

        for i, file in enumerate(self.las_files):
            print(f'Now is analysing {file}')
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

            # Обновляем таблицу
            values = list(self.table_files.item(self.table_files.get_children()[i])['values'])
            values[1] = str(total_points[-1])
            values[2] = f"{dx:.2f}"
            values[3] = f"{dy:.2f}"
            values[4] = f"{dz:.2f}"
            if dr_list:
                values[5] = f"{dr:.2f}"
                values[6] = f"{dg:.2f}"
                values[7] = f"{db:.2f}"
            self.table_files.item(self.table_files.get_children()[i], values=values)

            self.progress_var.set(i + 1)
            self.label_processing.config(text=f"Processing: {i + 1} of {total_files} files ({self.files_names[i]})")
            self.update_idletasks()

        if total_points:
            avg_points = np.mean(total_points)
            min_points, max_points = min(total_points), max(total_points)
            self.table_stats.delete(*self.table_stats.get_children())
            self.table_stats.insert("", "end", values=(f"{avg_points:.0f}", min_points, max_points))

        end_time = datetime.now()
        duration = round((end_time - start_time).total_seconds(), 1)
        self.label_end_time.config(text=f"Finished: {end_time.strftime('%Y-%m-%d %H:%M:%S')}")
        self.label_total_time.config(text=f"Processing time: {duration} seconds")

    def start_cleaning(self):
        if not self.las_files:
            messagebox.showwarning("Warning", "No LAS files selected.")
            return

        algorithm = self.cleaning_algo_combo.get()

        try:
            points_limit = int(self.points_input.get())
        except ValueError:
            points_limit = 5000000

        self.progress_var.set(0)
        self.label_processing.config(text="Processing: 0 files")
        total_files = len(self.las_files)
        self.progress_bar.config(maximum=total_files)
        print(f'Starting processing {total_files} files')

        start_time = datetime.now()

        for i, file in enumerate(self.las_files):
            print(f'loading file: {file}')
            las = laspy.read(file)

            if algorithm == "ZOR":
                name = os.path.basename(file)
                removed_points = self.apply_filter(las, name, points_limit)

                # Обновляем таблицу с количеством удаленных точек
                values = list(self.table_files.item(self.table_files.get_children()[i])['values'])
                values[8] = str(removed_points)
                self.table_files.item(self.table_files.get_children()[i], values=values)

            self.progress_var.set(i + 1)
            self.label_processing.config(text=f"Processing: {i + 1} of {total_files} files ({self.files_names[i]})")
            self.update_idletasks()

        end_time = datetime.now()
        duration = round((end_time - start_time).total_seconds(), 1)
        self.label_end_time.config(text=f"Finished: {end_time.strftime('%Y-%m-%d %H:%M:%S')}")
        self.label_total_time.config(text=f"Processing time: {duration} seconds")

    def apply_filter(self, las, name, N_points):
        org_points = len(las)
        print(f'file: {name} is cleaning')
        print(f'from {org_points} points to {N_points} points')
        las = full_filter_las(las, N_points)

        if self.save_directory:
            save_path = os.path.join(self.save_directory, os.path.basename(name))
            las.write(save_path)
        return org_points-N_points

if __name__ == "__main__":
    app = LasAnalyzerApp()
    app.mainloop()
