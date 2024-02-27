import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
from numpy.polynomial.polynomial import Polynomial
from scipy.optimize import curve_fit

# 设置matplotlib支持中文显示
plt.rcParams['font.sans-serif'] = ['SimHei']  # 如果是在Windows系统使用'SimHei'
plt.rcParams['axes.unicode_minus'] = False  # 正确显示负号


class TrajectoryPredictor:
    def __init__(self, csv_filepath, degree=2, grid_size=5):
        """
        初始化轨迹预测器。
        :param csv_filepath: CSV文件路径。
        :param degree: 多项式拟合的度数。
        :param grid_size: 栅格化地图的大小。
        :param coefficients: 多项式系数，从最高次幂到常数项
        """
        self.csv_filepath = csv_filepath
        self.degree = degree
        self.grid_size = grid_size
        self.longitude, self.latitude = self.read_csv_for_fitting()
        self.coefs = None
        self.fit_longitude = None
        self.fit_latitude = None
        self.probabilities = None

    def get_curve_derivative_at_point(self, x):
        """
        计算给定点x处曲线的导数。
        :param x: 经度点，用于计算导数
        :return: 在点x处的导数值
        """
        # 创建多项式的导数对象
        derivative_coefs = np.polyder(self.coefs)
        # 计算并返回导数值
        derivative_at_x = np.polyval(derivative_coefs, x)
        return derivative_at_x


    def read_csv_for_fitting(self):
        """
        从CSV文件中读取经纬度数据。
        :return: 经度和纬度的numpy数组。
        """
        data = pd.read_csv(self.csv_filepath)
        if 'longitude' in data.columns and 'latitude' in data.columns:
            longitude = data['longitude'].to_numpy()
            latitude = data['latitude'].to_numpy()
            return longitude, latitude
        else:
            raise ValueError("CSV文件中缺少'longitude'和'latitude'列。")

    def print_probability_distribution(self):
        # 确保概率矩阵已经被计算
        if not hasattr(self, 'probabilities'):
            raise ValueError("概率矩阵尚未计算。请先调用 calculate_probabilities 方法。")

        # 遍历概率矩阵并打印每个栅格的概率
        for i in range(len(self.probabilities)):
            for j in range(len(self.probabilities[0])):
                print(f"栅格({i},{j})的概率: {self.probabilities[i, j]:.4f}")

    def polynomial_fit(self):
        """
        使用numpy的多项式工具进行多项式拟合。
        """
        # 使用经度和纬度数据进行多项式拟合
        p = Polynomial.fit(self.longitude, self.latitude, self.degree)
        self.coefs = p.convert().coef
        # 生成拟合数据用于绘图或其他目的
        self.fit_longitude = np.linspace(self.longitude.min(), self.longitude.max(), 100)
        self.fit_latitude = sum(self.coefs[i] * self.fit_longitude ** i for i in range(len(self.coefs)))


    def predict_future_trajectory(self, seconds_ahead=5):
        """
        预测未来一段时间内的轨迹。
        :param seconds_ahead: 预测的时间长度（秒）。
        :return: 预测的经度和纬度数组。
        """
        future_time = np.linspace(0, seconds_ahead, 50)  # 假设数据中每个点代表1秒
        future_longitude = np.linspace(self.longitude[-1], self.longitude[-1] + future_time[-1] * 0.0001,
                                       50)  # 假设速度大约是0.0001度/秒
        future_latitude = sum(self.coefs[i] * future_longitude ** i for i in range(len(self.coefs)))
        return future_longitude, future_latitude

    def plot_future_trajectory(self, future_longitude, future_latitude):
        """
        绘制车辆的当前拟合轨迹和未来轨迹。
        """
        plt.figure(figsize=(10, 6))
        plt.plot(self.longitude, self.latitude, 'o', label='原始数据')
        plt.plot(self.fit_longitude, self.fit_latitude, '-', label='拟合轨迹')
        plt.plot(future_longitude, future_latitude, '--', label='未来轨迹')
        plt.xlabel('经度')
        plt.ylabel('纬度')
        plt.legend()
        plt.title('车辆轨迹预测')
        plt.show()

    def calculate_probabilities(self):
        """
        计算栅格化地图上的概率分布，以最后一个点为中心创建设置好大小的栅格图，并考虑通过非线性拟合曲线确定的车辆行驶方向。
        """
        if self.coefs is None:
            raise ValueError("请先执行polynomial_fit方法进行多项式拟合")

        # 以最后一个经纬度点为中心
        center_longitude = self.longitude[-1]
        center_latitude = self.latitude[-1]

        # 计算在最后一个点的曲线导数
        curve_slope = self.get_curve_derivative_at_point(center_longitude)

        # 考虑曲线的实际方向，修正方向向量
        direction_vector = np.array([1, -curve_slope]) if curve_slope < 0 else np.array([1, curve_slope])
        direction_vector /= np.linalg.norm(direction_vector)  # 单位化方向向量

        # 创建栅格的边界和中心
        x_edges = np.linspace(center_longitude - 5 * 0.0001, center_longitude + 5 * 0.0001, self.grid_size + 1)
        y_edges = np.linspace(center_latitude - 5 * 0.0001, center_latitude + 5 * 0.0001, self.grid_size + 1)
        x_centers = (x_edges[:-1] + x_edges[1:]) / 2
        y_centers = (y_edges[:-1] + y_edges[1:]) / 2
        X, Y = np.meshgrid(x_centers, y_centers)

        # 初始化概率矩阵
        self.probabilities = np.zeros((self.grid_size, self.grid_size))
        for i in range(self.grid_size):
            for j in range(self.grid_size):
                # 计算每个栅格中心到车辆当前位置的向量
                grid_vector = np.array([X[i, j] - center_longitude, Y[i, j] - center_latitude])
                # 计算向量与行驶方向的夹角余弦值
                norm_product = np.linalg.norm(grid_vector) * np.linalg.norm(direction_vector)
                if norm_product > 1e-6:  # 避免除以零
                    cos_angle = np.dot(grid_vector, direction_vector) / norm_product
                else:
                    cos_angle = 0
                self.probabilities[i, j] = max(0, cos_angle)  # 保证概率非负

        # 归一化概率分布
        self.probabilities /= self.probabilities.sum()

        return self.probabilities, x_centers, y_centers
    def plot_probability_distribution(self):
        """
        绘制概率分布的热力图。
        """
        # 确保概率矩阵已经被计算
        if self.probabilities is None:
            raise ValueError("概率矩阵尚未计算。请先调用 calculate_probabilities 方法。")

        # 计算栅格的大小和范围
        grid_size = self.grid_size
        x_min, x_max = self.longitude.min(), self.longitude.max()
        y_min, y_max = self.latitude.min(), self.latitude.max()
        x_range = x_max - x_min
        y_range = y_max - y_min

        # 创建栅格的中心坐标
        x_centers = np.linspace(x_min + x_range / 2 / grid_size, x_max - x_range / 2 / grid_size, grid_size)
        y_centers = np.linspace(y_min + y_range / 2 / grid_size, y_max - y_range / 2 / grid_size, grid_size)

        # 创建用于绘图的X和Y数组
        X, Y = np.meshgrid(x_centers, y_centers)

        # 绘制热力图
        plt.figure(figsize=(8, 6))
        plt.contourf(X, Y, self.probabilities, levels=50, cmap='RdYlBu')
        plt.colorbar(label='概率')
        plt.xlabel('经度')
        plt.ylabel('纬度')
        plt.title('概率分布')
        # 在图上显示每个栅格的概率
        for i in range(len(x_centers)):
            for j in range(len(y_centers)):
                plt.text(x_centers[i], y_centers[j], "{:.4f}".format(self.probabilities[j, i]),
                         ha='center', va='center', color='black', fontsize=8)
        plt.show()


predictor = TrajectoryPredictor('test.csv')
predictor.polynomial_fit()

# 绘制车辆的当前拟合轨迹和未来轨迹
future_longitude, future_latitude = predictor.predict_future_trajectory()
predictor.plot_future_trajectory(future_longitude, future_latitude)

# 计算概率分布并绘制栅格化地图的概率分布图
probabilities, x_centers, y_centers = predictor.calculate_probabilities()
print("Probabilities:")
predictor.print_probability_distribution()

predictor.plot_probability_distribution()
