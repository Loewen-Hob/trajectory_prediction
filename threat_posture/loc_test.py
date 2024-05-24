from data.dataset import collect_data_for_duration
import pandas as pd
import cv2
import numpy as np

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

data = collect_data_for_duration(10)

convert_coordinates(data)
