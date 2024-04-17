import numpy as np
import matplotlib.pyplot as plt
from numba import njit
import random
from PIL import Image

# 二值化并降采样图片的函数
def load_park_layout_from_image(image_path, downsample_size=(1024, 1024), threshold=128):
    with Image.open(image_path) as img:
        img_resized = img.resize(downsample_size)
        img_gray = img_resized.convert('L')
        image_array = np.array(img_gray)
        binary_image = (image_array > threshold).astype(int)
        park_layout = np.where(binary_image == 0, 0, -1)  # 0现代表可通行，-1代表障碍物
        return park_layout

@njit
def bresenham_line(x1, y1, x2, y2):
    points = []
    steep = abs(y2 - y1) > abs(x2 - x1)
    if steep:
        x1, y1, x2, y2 = y1, x1, y2, x2
    swapped = False
    if x1 > x2:
        x1, x2 = x2, x1
        y1, y2 = y2, y1
        swapped = True
    dx = x2 - x1
    dy = abs(y2 - y1)
    error = int(dx / 2.0)
    y = y1
    if y1 < y2:
        ystep = 1
    else:
        ystep = -1
    for x in range(x1, x2 + 1):
        coord = (y, x) if steep else (x, y)
        points.append(coord)
        error -= dy
        if error < 0:
            y += ystep
            error += dx
    if swapped:
        points.reverse()
    return points

def update_threat(park, unit_x, unit_y, threat_radius, show_updates=True):
    threat_map = np.copy(park)  # 开始时使用park地图的拷贝
    for angle in range(360):
        rad = np.radians(angle)
        x2 = int(unit_x + threat_radius * np.cos(rad))
        y2 = int(unit_y + threat_radius * np.sin(rad))
        for x, y in bresenham_line(unit_x, unit_y, x2, y2):
            if 0 <= x < park.shape[0] and 0 <= y < park.shape[1]:
                if park[x, y] == -1:
                    break
                threat_map[x, y] = 1  # 威胁区域标记为1
            else:
                break
        if show_updates:  # 显示每个角度的更新
            plt.clf()
            plt.imshow(park, cmap='gray', interpolation='none')
            plt.imshow(threat_map, alpha=0.7, cmap='magma', interpolation='none')
            plt.pause(0.01)  # 暂停时间可调
    return threat_map

# 加载图像并创建二值化图像
image_path = 'D:\\work\\trajectory_prediction\\threat_posture\\占位图.jpg'
park = load_park_layout_from_image(image_path, downsample_size=(512, 512), threshold=128)

# 在二值图中随机放置几个作战单位
num_units = 10  # 可调整单位数
threat_radius = 200  # 可调整威胁半径

for _ in range(num_units):
    unit_x, unit_y = np.random.randint(0, park.shape[0]), np.random.randint(0, park.shape[1])
    while park[unit_x, unit_y] == -1:  # 确保单位不在障碍物上
        unit_x, unit_y = np.random.randint(0, park.shape[0]), np.random.randint(0, park.shape[1])
    threat_map = update_threat(park, unit_x, unit_y, threat_radius, show_updates=False)
    plt.imshow(park, cmap='gray', interpolation='none')
    plt.imshow(threat_map, alpha=0.7, cmap='hot', interpolation='none')
    plt.title(f'Threat Map for Unit at ({unit_x}, {unit_y})')
    plt.show()
