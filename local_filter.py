import os
import numpy as np
import laspy
from scipy.spatial import cKDTree
from scipy.interpolate import LinearNDInterpolator

def load_las_points(file_path):
    """Загрузить точки из LAS-файла"""
    las = laspy.read(file_path)
    points = np.vstack((las.x, las.y, las.z)).T
    return points, las.header, las

def save_las_points(file_path, las, mask):
    """Сохранить отфильтрованные точки в новый LAS-файл"""
    filtered_points = las.points[mask]
    las.points = filtered_points
    las.write(file_path)

def calculate_grid_bounds(points):
    """Найти диапазоны координат"""
    xmin, xmax = points[:,0].min(), points[:,0].max()
    ymin, ymax = points[:,1].min(), points[:,1].max()
    return xmin, xmax, ymin, ymax

def generate_grid(xmin, xmax, ymin, ymax, M):
    """Сформировать равномерную сетку"""
    xi = np.linspace(xmin, xmax, M)
    yi = np.linspace(ymin, ymax, M)
    grid_x, grid_y = np.meshgrid(xi, yi)
    grid_points = np.vstack((grid_x.ravel(), grid_y.ravel())).T
    return grid_points

def compute_mean_heights(grid_points, original_points, K):
    """Найти K ближайших точек для каждого узла сетки и усреднить"""
    tree = cKDTree(original_points[:, :2])
    distances, indices = tree.query(grid_points, k=K)
    z_means = np.mean(original_points[indices, 2], axis=1)
    return z_means

def interpolate_surface(grid_points, z_means):
    """Построить линейную интерполяцию"""
    interpolator = LinearNDInterpolator(grid_points, z_means)
    return interpolator

def filter_points(points, z_pred, sigma_multiplier=2):
    """Отфильтровать точки по отклонению"""
    residuals = np.abs(points[:, 2] - z_pred)
    sigma = np.std(residuals)
    mask = residuals <= (sigma_multiplier * sigma)
    return mask

def downsample_las(las, points_limit):
    selected_indices = np.random.choice(len(las), points_limit, replace=False)
    las.points = las.points[selected_indices]
    return las

def apply_zor(las, threshold=0.1, z_sigma_threshold=3):
    original_count = len(las.points)
    z = las.z
    outlets_count = original_count
    while outlets_count/original_count > threshold:
        mu_z = np.mean(z)
        std_z = np.std(z)
        lower_bound = mu_z - z_sigma_threshold * std_z
        upper_bound = mu_z + z_sigma_threshold * std_z
        valid_indices = np.where((z >= lower_bound) & (z <= upper_bound))[0]
        if len(valid_indices) == len(z):
            break
        las.points = las.points[valid_indices]
        z = las.z
        outlets_count = original_count - len(valid_indices)
    return las

def local_filter_las(las, M=100, K=10, sigma_multiplier=2):

    points = np.vstack((las.x, las.y, las.z)).T
    xmin, xmax, ymin, ymax = calculate_grid_bounds(points)
    grid_points = generate_grid(xmin, xmax, ymin, ymax, M)
    z_means = compute_mean_heights(grid_points, points, K)
    interpolator = interpolate_surface(grid_points, z_means)

    z_pred = interpolator(points[:, 0], points[:, 1])

    z_pred[np.isnan(z_pred)] = points[np.isnan(z_pred), 2]  # fallback на оригинальные z

    mask = filter_points(points, z_pred, sigma_multiplier)
    las.points = las.points[mask]
    return las

def full_filter_las(las, N_points):
    if len(las)>2*N_points:
        las = downsample_las(las, 2*N_points)
        print('1st Downsapling...')

    print(f'Global filtering')
    las = apply_zor(las, threshold=0.1, z_sigma_threshold=3)
    print(f'Local filtering')
    las = local_filter_las(las, M=100, K=10, sigma_multiplier=2)
    
    if len(las)>N_points:
        las = downsample_las(las, N_points)
        print('Final filtering')

    return las

def process_las_file(input_file, output_file, M=100, K=10, sigma_multiplier=2):
    """Основная функция обработки одного файла"""
    print(f"Processing {input_file}...")

    points, header, las = load_las_points(input_file)
    xmin, xmax, ymin, ymax = calculate_grid_bounds(points)
    grid_points = generate_grid(xmin, xmax, ymin, ymax, M)
    z_means = compute_mean_heights(grid_points, points, K)
    interpolator = interpolate_surface(grid_points, z_means)

    z_pred = interpolator(points[:, 0], points[:, 1])
    valid_pred = ~np.isnan(z_pred)
    
    if not np.any(valid_pred):
        print(f"Warning: no valid interpolation for {input_file}. Skipping.")
        return

    z_pred[np.isnan(z_pred)] = points[np.isnan(z_pred), 2]  # fallback на оригинальные z

    mask = filter_points(points, z_pred, sigma_multiplier)
    print(f"Points before: {len(points)}, after filtering: {np.sum(mask)}")

    save_las_points(output_file, las, mask)
    print(f"Saved cleaned file to {output_file}")

def process_directory(input_dir, output_dir, M=100, K=10, sigma_multiplier=2):
    """Обработать все LAS-файлы в папке"""
    os.makedirs(output_dir, exist_ok=True)
    for filename in os.listdir(input_dir):
        if filename.lower().endswith(".las") or filename.lower().endswith(".laz"):
            input_file = os.path.join(input_dir, filename)
            output_file = os.path.join(output_dir, filename)
            process_las_file(input_file, output_file, M, K, sigma_multiplier)

if __name__ == "__main__":
    # 👉 Здесь задаются пути и параметры
    input_dir = r"C:\Users\alexe\VSCprojects\lidar-visual-interface\temp_h3\las"       # Папка с исходными LAS
    output_dir = r"C:\Users\alexe\VSCprojects\lidar-visual-interface\temp_h3\cleaned_las"    # Папка для сохранения очищенных LAS
    M = 100                         # Количество шагов сетки по каждой оси
    K = 10                          # Количество ближайших точек для усреднения
    sigma_multiplier = 2            # Множитель σ для фильтрации

    process_directory(input_dir, output_dir, M, K, sigma_multiplier)
