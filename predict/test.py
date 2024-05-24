import pandas as pd
from predict.nonlinear_fitting import TrajectoryPredictor
import numpy as np

data = pd.read_csv('../data_old/test.csv')

prediction_results = pd.DataFrame()

window_size = 30  # 滑动窗口的大小，30秒
predict_steps = 15  # 预测未来15步

unit_ids = data['unit_id'].unique()

for unit_id in unit_ids:
    unit_data = data[data['unit_id'] == unit_id]

    unit_data = unit_data.sort_values(by='datetime')

    if len(unit_data) < window_size:
        continue

    end = len(unit_data)
    window_data = unit_data.iloc[end - window_size:end]
    # 读取经纬度并进行坐标转换


prediction_results.to_csv('prediction_results.csv', index=False)

print("预测完成，结果已保存到 prediction_results.csv")
