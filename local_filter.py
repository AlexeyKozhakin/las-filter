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
"""Removed: functionality moved into the `las_filter` package.

This file kept as a placeholder for backward compatibility; import
functionality from `las_filter.core` instead.
"""

__all__ = []
