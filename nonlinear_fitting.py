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
        if self.coefs is None:
            raise ValueError("请先执行polynomial_fit方法进行多项式拟合")

        center_longitude = self.longitude[-1]
        center_latitude = self.latitude[-1]

        direction_vector = np.array([1, self.get_curve_derivative_at_point(center_longitude)])
        direction_vector /= np.linalg.norm(direction_vector)

        grid_size = self.grid_size
        x_edges = np.linspace(center_longitude - 5 * 0.0001, center_longitude + 5 * 0.0001, grid_size + 1)
        y_edges = np.linspace(center_latitude - 5 * 0.0001, center_latitude + 5 * 0.0001, grid_size + 1)

        self.probabilities = np.zeros((grid_size, grid_size))
        for i in range(grid_size):
            for j in range(grid_size):
                grid_vector = np.array([x_edges[i] - center_longitude, y_edges[j] - center_latitude])
                distance = np.linalg.norm(grid_vector)
                grid_vector /= distance if distance > 0 else 1
                cos_angle = np.dot(grid_vector, direction_vector)
                # 直接使用余弦相似度作为概率的基础，考虑到方向的一致性
                self.probabilities[j, i] = max(cos_angle, 0)

        # 归一化概率，使得总和为1
        total_prob = self.probabilities.sum()
        self.probabilities /= total_prob
        return self.probabilities, x_edges, y_edges

    def get_curve_derivative_at_point(self, x):
        """
        计算给定点x处曲线的导数。
        :param x: 经度点，用于计算导数
        :return: 在点x处的导数值
        """
        # 获取多项式的导数对象
        p_derivative = Polynomial(self.coefs).deriv()
        # 直接使用导数对象在点x处评估导数值
        derivative_at_x = p_derivative(x)
        return derivative_at_x

    def plot_probability_distribution(self):
        if self.probabilities is None:
            raise ValueError("概率矩阵尚未计算。请先调用 calculate_probabilities 方法。")

        grid_size = self.grid_size
        x_min, x_max = self.longitude.min(), self.longitude.max()
        y_min, y_max = self.latitude.min(), self.latitude.max()

        # 创建栅格的边界坐标
        x_edges = np.linspace(x_min, x_max, grid_size + 1)
        y_edges = np.linspace(y_min, y_max, grid_size + 1)

        plt.figure(figsize=(8, 6))
        # 注意这里将概率矩阵转置，以确保与x_edges和y_edges的方向一致
        plt.pcolormesh(x_edges, y_edges, self.probabilities, cmap='RdYlBu', shading='auto')
        plt.colorbar(label='概率')
        plt.xlabel('经度')
        plt.ylabel('纬度')
        plt.title('概率分布')

        # 在图上显示每个栅格的概率
        x_centers = (x_edges[:-1] + x_edges[1:]) / 2
        y_centers = (y_edges[:-1] + y_edges[1:]) / 2
        for i in range(grid_size):
            for j in range(grid_size):
                plt.text(x_centers[i], y_centers[j], "{:.2f}".format(self.probabilities[j, i]),
                         ha='center', va='center', color='white' if self.probabilities[j, i] > 0.5 else 'black',
                         fontsize=8)

        plt.xlim(x_min, x_max)
        plt.ylim(y_min, y_max)
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
