import numpy as np
import matplotlib.pyplot as plt
from numba import njit
import random

def create_park(size, obstacle_rate=0.1):
    park = np.ones((size, size))
    for i in range(size):
        for j in range(size):
            if random.random() < obstacle_rate:
                park[i, j] = 0  # 设定障碍物
    return park

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
    threat_map = np.zeros_like(park)
    for angle in range(360):
        rad = np.radians(angle)
        x2 = int(unit_x + threat_radius * np.cos(rad))
        y2 = int(unit_y + threat_radius * np.sin(rad))
        for x, y in bresenham_line(unit_x, unit_y, x2, y2):
            if 0 <= x < park.shape[0] and 0 <= y < park.shape[1]:
                if park[x, y] == 0:
                    break
                threat_map[x, y] += 1
            else:
                break
        if show_updates:  # 显示每个角度的更新
            plt.clf()
            plt.imshow(park, cmap='gray', interpolation='none')
            plt.imshow(threat_map, alpha=0.7, cmap='magma', interpolation='none')
            plt.pause(0.001)  # 暂停时间可调
    return threat_map

size = 50
park = create_park(size)
unit1_x, unit1_y = 20, 20
unit2_x, unit2_y = 25, 25
threat_radius = 20

threat_map1 = update_threat(park, unit1_x, unit1_y, threat_radius, show_updates=False)
threat_map2 = update_threat(park, unit2_x, unit2_y, threat_radius, show_updates=False)

total_threat = threat_map1 + threat_map2

plt.imshow(park, cmap='gray', interpolation='none')
plt.imshow(total_threat, alpha=0.7, cmap='hot', interpolation='none')
plt.show()
