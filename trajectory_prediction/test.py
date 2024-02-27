
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
        """
        self.csv_filepath = csv_filepath
        self.degree = degree
        self.grid_size = grid_size
        self.longitude, self.latitude, self.velocity = self.read_csv_for_fitting()  # 更新这行
        self.coefs = None
        self.fit_longitude = None
        self.fit_latitude = None
        self.probabilities = None
    def read_csv_for_fitting(self):
        """
        从CSV文件中读取经纬度和速度数据。
        :return: 经度、纬度和速度的numpy数组。
        """
        data = pd.read_csv(self.csv_filepath)
        if 'longitude' in data.columns and 'latitude' in data.columns and 'velocity' in data.columns:
            longitude = data['longitude'].to_numpy()
            latitude = data['latitude'].to_numpy()
            velocity = data['velocity'].to_numpy()  # 读取速度数据
            return longitude, latitude, velocity
        else:
            raise ValueError("CSV文件中缺少'longitude', 'latitude'或'velocity'列。")

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
        self.coefs = Polynomial.fit(self.longitude, self.latitude, self.degree).convert().coef
        self.fit_longitude = np.linspace(self.longitude.min(), self.longitude.max(), 100)
        self.fit_latitude = sum(self.coefs[i] * self.fit_longitude ** i for i in range(len(self.coefs)))

    def predict_future_trajectory(self, seconds_ahead=5):
        """
        预测未来一段时间内的轨迹。
        :param seconds_ahead: 预测的时间长度（秒）。
        :return: 预测的经度和纬度数组。
        """
        future_time = np.linspace(0, seconds_ahead, 20)  # 减少到20个等间距的时间点
        if len(self.velocity) > 0:  # 确保有速度数据
            avg_velocity = np.mean(self.velocity)  # 使用平均速度作为未来速度的估计
        else:
            avg_velocity = 0.0001  # 如果没有速度数据，使用默认值
        future_longitude = self.longitude[-1] + future_time * avg_velocity  # 使用实际速度计算
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
        根据速度信息和预测的未来位置来计算栅格化地图上的概率分布。
        """
        # 预测未来位置
        future_longitude, future_latitude = self.predict_future_trajectory(seconds_ahead=60)  # 假设未来60秒的轨迹

        # 创建栅格边界
        x_edges = np.linspace(future_longitude.min() - 5 * 0.0001, future_longitude.max() + 5 * 0.0001,
                              self.grid_size + 1)
        y_edges = np.linspace(future_latitude.min() - 5 * 0.0001, future_latitude.max() + 5 * 0.0001,
                              self.grid_size + 1)

        # 计算栅格中心点
        x_centers = (x_edges[:-1] + x_edges[1:]) / 2
        y_centers = (y_edges[:-1] + y_edges[1:]) / 2
        X, Y = np.meshgrid(x_centers, y_centers)

        self.probabilities = np.zeros((self.grid_size, self.grid_size))

        # 计算每个栅格的概率
        for i in range(self.grid_size):
            for j in range(self.grid_size):
                distance = np.sqrt((X[i, j] - future_longitude.mean())**2 + (Y[i, j] - future_latitude.mean())**2)
                self.probabilities[i, j] = np.exp(-distance * 10)  # 使用指数衰减函数调整概率

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
