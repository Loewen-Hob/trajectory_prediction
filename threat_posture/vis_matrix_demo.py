import numpy as np
import matplotlib.pyplot as plt
from numba import jit

from PIL import Image
import numpy as np

def load_park_layout_from_image(image_path):
    """
    从给定路径的图像文件加载园区布局。
    参数:
    image_path: str, 图像文件的路径。
    返回:
    numpy.ndarray, 代表园区布局的二维数组。
    """
    # 打开图像文件
    with Image.open(image_path) as img:
        # 将图像转换为灰度格式
        img_gray = img.convert('L')
        # 将灰度图像转换为numpy数组
        img_array = np.array(img_gray)
        # 将图像二值化，设置阈值为127，大于阈值的为1（建筑物），小于等于阈值的为0（空地）
        layout = (img_array > 127).astype(int)
    return layout

"""
Bresenham算法模块
"""

# 实现 Bresenham 算法
@jit(nopython=True)
def bresenham(x1, y1):
    """
    使用Bresenham算法在二维平面上从原点到(x1, y1)绘制一条直线。

    参数:
    x1: int, 目标点的x坐标。
    y1: int, 目标点的y坐标。

    返回:
    list, 包含沿线所有经过的点坐标的列表。
    """
    dx = abs(x1)
    dy = -abs(y1)
    sx = 1 if 0 < x1 else -1
    sy = 1 if 0 < y1 else -1
    err = dx + dy
    x0, y0 = 0, 0
    line = []
    while True:
        line.append([x0, y0])
        if x0 == x1 and y0 == y1:
            break
        e2 = 2 * err
        if e2 >= dy:
            err += dy
            x0 += sx
        if e2 <= dx:
            err += dx
            y0 += sy
    return line


"""
边缘方向计算模块
"""

# 计算边缘方向
@jit(nopython=True)
def calculate_edge_directions(visibility_range):
    """
    根据视野范围计算所有可能的边缘方向。

    参数:
    visibility_range: int, 视野的半径。

    返回:
    list, 每个元素都是一个二元组，表示一个可能的边缘方向。
    """
    directions = [(dx, dy) for dx in range(-visibility_range, visibility_range + 1)
                  for dy in [-visibility_range, visibility_range]] + \
                  [(dx, dy) for dy in range(-visibility_range + 1, visibility_range)
                   for dx in [-visibility_range, visibility_range]]
    return directions


"""
光线投射模块
"""

# 光线投射计算
@jit(nopython=True)
def ray_casting(layout, x, y, bresenham_lines, visibility_range_squared):
    """
    从给定点(x, y)向各个方向投射光线，并计算可见的建筑数量。

    参数:
    layout: numpy.ndarray, 园区的布局数组。
    x: int, 投射起点的x坐标。
    y: int, 投射起点的y坐标。
    bresenham_lines: list, 由bresenham算法计算得到的线段列表。
    visibility_range_squared: int, 视野范围的平方。

    返回:
    int, 从给定点可见的建筑数量。
    """
    if layout[x, y] == 1:
        return 0
    # 使用numpy数组代替集合以提高性能
    visible_cells = np.zeros((2 * visibility_range + 1, 2 * visibility_range + 1))
    visible_cnt = 0
    for line in bresenham_lines:
        for lx, ly in line:
            nx, ny = x + lx, y + ly
            if (lx ** 2 + ly ** 2) > visibility_range_squared:
                break  # 超出视野范围
            if layout[nx, ny] == 1 or not (0 <= nx < layout.shape[0] and 0 <= ny < layout.shape[1]):
                break
            # 更新可见建筑数量
            sf_x, sf_y = int(lx + visibility_range), int(ly + visibility_range),
            if visible_cells[sf_x, sf_y] == 1:
                continue
            else:
                visible_cells[sf_x, sf_y] = 1
                visible_cnt += 1
    return visible_cnt


"""
可见性矩阵计算模块
"""

# 计算整个园区的可见性矩阵
@jit(nopython=True)
def calculate_visibility(layout, visibility_range):
    """
    计算整个园区的可见性矩阵，即每个点能够看到的建筑数量。

    参数:
    layout: numpy.ndarray, 园区的布局数组。
    visibility_range: int, 视野的半径。

    返回:
    numpy.ndarray, 代表可见性矩阵的二维数组。
    """
    directions = calculate_edge_directions(visibility_range)
    bresenham_lines = [bresenham(dx, dy) for dx, dy in directions]
    visibility_range_squared = visibility_range ** 2

    visibility_matrix = np.zeros(layout.shape)
    for i in range(layout.shape[0]):
        for j in range(layout.shape[1]):
            visibility_matrix[i, j] = ray_casting(layout, i, j, bresenham_lines, visibility_range_squared)
    return visibility_matrix


"""
主程序模块
"""

image_path = 'D:\work\\trajectory_prediction\\threat_posture\占位图.jpg'  # 替换为你的图像文件路径
layout = load_park_layout_from_image(image_path)

# 打印园区布局查看结果
print(layout)

import time

t = time.time()
# 计算可见性矩阵
visibility_range = 100
visibility_matrix = calculate_visibility(layout, visibility_range)
print(time.time() - t)
# 展示结果
plt.figure(figsize=(10, 10))
plt.imshow(visibility_matrix, cmap='viridis')
plt.colorbar()
plt.title('Optimized Ray Casting Visibility Matrix with Bresenham and Numba')
plt.show()

