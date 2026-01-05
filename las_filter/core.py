import os
import numpy as np
import laspy
from scipy.spatial import cKDTree
from scipy.interpolate import LinearNDInterpolator

def load_las_points(file_path):
    las = laspy.read(file_path)
    points = np.vstack((las.x, las.y, las.z)).T
    return points, las.header, las

def save_las_points(file_path, las, mask):
    filtered_points = las.points[mask]
    las.points = filtered_points
    las.write(file_path)

def calculate_grid_bounds(points):
    xmin, xmax = points[:,0].min(), points[:,0].max()
    ymin, ymax = points[:,1].min(), points[:,1].max()
    return xmin, xmax, ymin, ymax

def generate_grid(xmin, xmax, ymin, ymax, M):
    xi = np.linspace(xmin, xmax, M)
    yi = np.linspace(ymin, ymax, M)
    grid_x, grid_y = np.meshgrid(xi, yi)
    grid_points = np.vstack((grid_x.ravel(), grid_y.ravel())).T
    return grid_points

def compute_mean_heights(grid_points, original_points, K):
    tree = cKDTree(original_points[:, :2])
    distances, indices = tree.query(grid_points, k=K)
    z_means = np.mean(original_points[indices, 2], axis=1)
    return z_means

def interpolate_surface(grid_points, z_means):
    interpolator = LinearNDInterpolator(grid_points, z_means)
    return interpolator

def filter_points(points, z_pred, sigma_multiplier=2):
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

    z_pred[np.isnan(z_pred)] = points[np.isnan(z_pred), 2]

    mask = filter_points(points, z_pred, sigma_multiplier)
    las.points = las.points[mask]
    return las

def full_filter_las(las, N_points):
    if len(las)>2*N_points:
        las = downsample_las(las, 2*N_points)

    las = apply_zor(las, threshold=0.1, z_sigma_threshold=3)
    las = local_filter_las(las, M=100, K=10, sigma_multiplier=2)
    if len(las)>N_points:
        las = downsample_las(las, N_points)
    return las

def process_las_file(input_file, output_file, M=100, K=10, sigma_multiplier=2):
    points, header, las = load_las_points(input_file)
    xmin, xmax, ymin, ymax = calculate_grid_bounds(points)
    grid_points = generate_grid(xmin, xmax, ymin, ymax, M)
    z_means = compute_mean_heights(grid_points, points, K)
    interpolator = interpolate_surface(grid_points, z_means)

    z_pred = interpolator(points[:, 0], points[:, 1])
    valid_pred = ~np.isnan(z_pred)
    if not np.any(valid_pred):
        raise RuntimeError(f"No valid interpolation for {input_file}")

    z_pred[np.isnan(z_pred)] = points[np.isnan(z_pred), 2]
    mask = filter_points(points, z_pred, sigma_multiplier)
    save_las_points(output_file, las, mask)
    return np.sum(mask)

def process_directory(input_dir, output_dir, M=100, K=10, sigma_multiplier=2):
    os.makedirs(output_dir, exist_ok=True)
    results = {}
    for filename in os.listdir(input_dir):
        if filename.lower().endswith((".las", ".laz")):
            input_file = os.path.join(input_dir, filename)
            output_file = os.path.join(output_dir, filename)
            kept = process_las_file(input_file, output_file, M, K, sigma_multiplier)
            results[filename] = kept
    return results
