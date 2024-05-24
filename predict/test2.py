from data import dataset
from predict.nonlinear_fitting import TrajectoryPredictor
all_data = []
collector = dataset.DatasetCollector()
while True:
    # 将数据收集到all_data中
    data_tuples = collector.collect_trajectory_data()
    all_data.extend(data_tuples)
    # 接下来我有个需求，就是将收集到的数据进行拟合，选择30秒为拟合的时间，然后预测未来15
    # 写个滑动窗口
    if len(all_data) > 30:
        # 获取30秒的数据
        data = all_data[-30:]
        # 创建一个拟合器
        predictor = TrajectoryPredictor(data)
        # 拟合
        predictor.polynomial_fit()
        # 预测未来15秒的数据
        future_longitude, future_latitude = predictor.predict_future_trajectory(seconds_ahead=15)
        # 绘制未来15秒的数据
        predictor.plot_future_trajectory()
