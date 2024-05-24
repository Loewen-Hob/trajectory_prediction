import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
from numpy.polynomial.polynomial import Polynomial
from sklearn.metrics import mean_squared_error
from data.coor_transform import BLH2XYZ

plt.rcParams['font.sans-serif'] = ['SimHei']  # 如果是在Windows系统使用'SimHei'
plt.rcParams['axes.unicode_minus'] = False  # 正确显示负号

class TrajectoryPredictor:
    def __init__(self, data, degree=3, grid_size=10):
        self.data = data
        self.degree = degree
        self.grid_size = grid_size
        self.longitude, self.latitude = self.get_data_for_fitting()
        self.coefs = None
        self.fit_longitude = None
        self.fit_latitude = None

    def get_data_for_fitting(self):
        data = self.data
        if 'x' in data.columns and 'y' in data.columns:
            longitude = data['x'].to_numpy()
            latitude = data['y'].to_numpy()
            return longitude, latitude
        else:
            raise ValueError("CSV文件中缺少转换后的经坐标")

    def polynomial_fit(self):
        p = Polynomial.fit(self.longitude, self.latitude, self.degree)
        self.coefs = p.convert().coef

        self.fit_longitude = np.linspace(self.longitude.min(), self.longitude.max(), 100)
        self.fit_latitude = sum(self.coefs[i] * self.fit_longitude ** i for i in range(len(self.coefs)))

    def predict_future_trajectory(self, seconds_ahead=10):
        future_time = np.linspace(0, seconds_ahead, 50)
        future_longitude = np.linspace(self.longitude[-1], self.longitude[-1] + future_time[-1] * 0.0001, 50)
        future_latitude = sum(self.coefs[i] * future_longitude ** i for i in range(len(self.coefs)))
        return future_longitude, future_latitude

    def calculate_rmse(self, actual_longitude, actual_latitude):
        predicted_latitude = sum(self.coefs[i] * actual_longitude ** i for i in range(len(self.coefs)))
        return np.sqrt(mean_squared_error(actual_latitude, predicted_latitude))

data = pd.read_csv("D:\\work\\trajectory_prediction\\data_old\\test.csv")

data[["x", "y", "z"]] = data.apply(
    lambda row: BLH2XYZ(row["longitude"], row["latitude"], 0),
    axis=1,
    result_type="expand",
)

data["x"] = data["x"] - data["x"].min()
data["y"] = data["y"] - data["y"].min()
data["z"] = data["z"] - data["z"].min()

grouped = data.groupby('vehicle_id')
results = []

for vehicle_id, group in grouped:
    print(f"Processing vehicle_id: {vehicle_id}")

    # 划分不同大小的训练集
    for size in range(10, len(group), 10):
        train_data = group.iloc[:size]
        test_data = group.iloc[size:]

        predictor = TrajectoryPredictor(train_data)
        predictor.polynomial_fit()

        # 计算RMSE
        rmse = predictor.calculate_rmse(test_data['x'].to_numpy(), test_data['y'].to_numpy())
        results.append((vehicle_id, size, rmse))

# 将结果转换为DataFrame并打印
results_df = pd.DataFrame(results, columns=['vehicle_id', 'data_size', 'rmse'])
print(results_df)

# 可视化结果
plt.figure(figsize=(10, 6))
for vehicle_id in results_df['vehicle_id'].unique():
    vehicle_data = results_df[results_df['vehicle_id'] == vehicle_id]
    plt.plot(vehicle_data['data_size'], vehicle_data['rmse'], label=f'Vehicle {vehicle_id}')

plt.xlabel('输入数据量')
plt.ylabel('RMSE')
plt.legend()
plt.title('不同输入数据量下的RMSE')
plt.show()
