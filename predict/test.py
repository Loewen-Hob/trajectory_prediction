import pandas as pd
from PIL import Image
from predict.nonlinear_fitting import TrajectoryPredictor
from threat_posture.threat_posture import LocTransform
import numpy as np

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

def convert2maploc(data, scaling_factor):
    for index, row in data.iterrows():
        # 将当期的经纬度转换到地图坐标
        data.at[index, 'map_longitude'] = row['converted_longitude'] * scaling_factor
        data.at[index, 'map_latitude'] = row['converted_latitude'] * scaling_factor
    return data

if __name__ == '__main__':
    data = pd.read_csv('../data_old/test.csv')
    map_layout, scaling_factor = load_park_layout_from_image('../data_old/map.png')
    window_size = 30  # 滑动窗口的大小，30秒
    predict_steps = 15  # 预测未来15步
    # 判断连续
    unit_ids = data['unit_id'].unique()
    for unit_id in unit_ids:
        unit_data = data[data['unit_id'] == unit_id]
        unit_data = unit_data.sort_values(by='datetime')# 排序
        if len(unit_data) < window_size:
            continue
        end = len(unit_data)
        window_data = unit_data.iloc[end - window_size:end]
        window_data = convert2maploc(convert_coordinates(window_data))

        print(f"Processing vehicle_id: {unit_id}")
        predictor = TrajectoryPredictor(unit_id, window_data)
        predictor.polynomial_fit()
        future_longitude, future_latitude = predictor.predict_future_trajectory()
        predictor.plot_future_trajectory(future_longitude, future_latitude)
        probabilities, x_centers, y_centers = predictor.calculate_probabilities()
        print(f"{unit_id} Probabilities:")
        predictor.print_probability_distribution()
        predictor.plot_probability_distribution()
