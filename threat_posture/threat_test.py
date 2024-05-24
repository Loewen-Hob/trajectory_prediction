import pandas as pd
from numba import njit
import numpy as np
import matplotlib.pyplot as plt
from PIL import Image
from data.dataset import collect_data_for_duration
import cv2

class LocTransform:
    def __init__(self, source_points, target_points, mode='a'):
        source_points = np.float32(source_points)
        target_points = np.float32(target_points)
        source_xy = np.float32([p[:2] for p in source_points])
        target_xy = np.float32([p[:2] for p in target_points])

        self.__point_dim = len(source_points[0])
        if self.__point_dim == 3:
            self._h_trans = np.polyfit(source_points[:, -1], target_points[:, -1], 1)  # 二阶变换就够了，精度为0.2左右。三阶是1.6e-10
            self._inv_h_trans = np.polyfit(target_points[:, -1], source_points[:, -1], 1)  # 二阶变换就够了，精度为0.2左右。三阶是1.6e-10
        elif self.__point_dim != 2:
            raise ValueError('point dimension error', self.__point_dim)

        self.__mode = mode
        if self.mode == 'a':
            self._m = cv2.getAffineTransform(source_xy[:3], target_xy[:3])
            self._inv_m = np.linalg.inv(np.vstack([self._m, [0, 0, 1]]))[:2, :]
        elif self.mode == 'p':
            self._m = cv2.getPerspectiveTransform(source_xy[:4], target_xy[:4])
            self._inv_m = np.linalg.inv(self._m)
        else:
            raise ValueError('mode error:', mode)

    def trans_point(self, point):
        result = self._cal_point(point, self._m).tolist()
        if self.__point_dim == 2 or len(point) == 2:
            return result
        return result + [np.polyval(self._h_trans, point[-1])]

    def inverse_point(self, point):
        result = self._cal_point(point, self._inv_m).tolist()
        if self.__point_dim == 2 or len(point) == 2:
            return result
        return result + [np.polyval(self._inv_h_trans, point[-1])]

    def _cal_point(self, point, m):
        result = m.dot([*point[:2], 1])
        if self.mode == 'a':
            return result
        if self.mode == 'p':
            return result[:2] / result[2]

    def trans_point_list(self, point_list):
        point_list = np.array(point_list)
        result = self._cal_point_list(point_list, self._m)
        if self.__point_dim == 2 or len(point_list[0]) == 2:
            return result.tolist()
        return np.hstack([result, np.polyval(self._h_trans, point_list[:, 2])[:, np.newaxis]]).tolist()

    def inverse_point_list(self, point_list):
        point_list = np.array(point_list)
        result = self._cal_point_list(point_list, self._inv_m)
        if self.__point_dim == 2 or len(point_list[0]) == 2:
            return result.tolist()
        return np.hstack([result, np.polyval(self._inv_h_trans, point_list[:, 2])[:, np.newaxis]]).tolist()

    def _cal_point_list(self, point_list, m):
        point_list = np.float32([p[:2] for p in point_list])
        points_matrix = np.hstack((point_list, np.ones((point_list.shape[0], 1))))
        result = np.dot(points_matrix, m.T)
        if self.mode == 'a':
            return result[:, :2]
        if self.mode == 'p':
            return result[:, :2] / result[:, 2, np.newaxis]

    @property
    def mode(self):
        return self.__mode
def load_park_layout_from_image(image_path, max_dimension=1024, threshold=128):
    with Image.open(image_path) as img:
        original_width, original_height = img.size
        scaling_factor = min(max_dimension / original_width, max_dimension / original_height)
        new_width = int(original_width * scaling_factor)
        new_height = int(original_height * scaling_factor)
        img_resized = img.resize((new_width, new_height))
        img_gray = img_resized.convert('L')
        image_array = np.array(img_gray)
        binary_image = (image_array > threshold).astype(int)
        park_layout = np.where(binary_image == 0, 0, -1)
        return park_layout, scaling_factor
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

@njit
def midpoint_circle_algorithm(x0, y0, radius):
    x = radius
    y = 0
    points = []
    error = 1 - x

    while x >= y:
        points.extend([
            (x0 + x, y0 + y), (x0 - x, y0 + y), (x0 + x, y0 - y), (x0 - x, y0 - y),
            (x0 + y, y0 + x), (x0 - y, y0 + x), (x0 + y, y0 - x), (x0 - y, y0 - x)
        ])
        y += 1
        if error < 0:
            error += 2 * y + 1
        else:
            x -= 1
            error += 2 * (y - x + 1)
    return points
@njit
def line_of_sight(park, cx, cy, x, y):
    points = bresenham_line(cx, cy, x, y)
    for (px, py) in points:
        if park[px, py] == -1:  # 遇到障碍
            return False
    return True

@njit
def update_threat_with_cover(park, unit_x, unit_y, threat_radius):
    threat_map = np.copy(park)
    for dx in range(-threat_radius, threat_radius + 1):
        for dy in range(-threat_radius, threat_radius + 1):
            if dx**2 + dy**2 <= threat_radius**2:
                x, y = unit_x + dx, unit_y + dy
                if 0 <= x < park.shape[0] and 0 <= y < park.shape[1]:
                    if line_of_sight(park, unit_x, unit_y, x, y):
                        threat_map[x, y] = 1  # 可视区域标记为1
    return threat_map

def convert_coordinates(data):
    # 地图坐标和地理坐标的示例数据
    mloc = [[1958, 881], [2214, 7383], [13116, 896], [13145, 7656]]
    llh = [[121.507167, 25.037037], [121.51402, 25.0356223], [121.510275, 25.047642], [121.517365, 25.04594]]
    llh2mloc = LocTransform(llh, mloc)

    for index, row in data.iterrows():
        # 将经纬度坐标转换为地图坐标
        converted_point = llh2mloc.trans_point((row['longitude'], row['latitude'], row.get('altitude', 0)))
        # 将新的坐标存到别的列
        data.at[index, 'converted_longitude'] = converted_point[0]
        data.at[index, 'converted_latitude'] = converted_point[1]
    return data

def process_park_data(image_path, converted_data, threat_radius=100):
    park, scaling_factor = load_park_layout_from_image(image_path, max_dimension=1024, threshold=128)
    park_total = np.copy(park)
    # 按time_counter字段分组
    for _, group in converted_data.groupby('time_counter'):
        for index, row in group.iterrows():
            unit_x, unit_y = int(row['converted_longitude']), int(row['converted_latitude'])
            unit_x_scaled = int(unit_x * scaling_factor)
            unit_y_scaled = int(unit_y * scaling_factor)
            threat_radius_scaled = int(threat_radius * scaling_factor)
            threat_map = update_threat_with_cover(park, unit_x_scaled, unit_y_scaled, threat_radius_scaled)
            park_total = np.where(park != -1, park_total + threat_map, -1)
            plt.imshow(park_total, cmap='gray', interpolation='none')

    return park_total

if __name__ == '__main__':
    converted_data = convert_coordinates(collect_data_for_duration(20))
    process_park_data('占位图.jpg', converted_data)


