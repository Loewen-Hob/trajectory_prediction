import threading
import time
import pandas as pd
from data_hub.hub_manager.hub_manager import HubManager
from data_hub.data_struct.unit import UnitSide, Side

class Unit:
    def __init__(self, unit_id):
        self.unit_id = unit_id  # 单位ID
        self.trajectory = []  # 轨迹列表
        self.min_consecutive_size = 0

    def add_observation(self, run_time, scene_time, longitude, latitude, altitude, time_threshold):
        """
        添加新的观测数据。
        只有scene_time小于阈值的情况下，才会增加观测数据。
        """
        if not self.trajectory or scene_time != self.trajectory[-1][1]:  # 检查以防止重复计时
            if not self.trajectory or ((scene_time - self.trajectory[-1][1]) <= time_threshold):
                self.min_consecutive_size += 1
            self.trajectory.append((run_time, scene_time, longitude, latitude, altitude))

    def to_dataframe(self):
        """
        将轨迹数据转换为DataFrame格式。
        """
        df = pd.DataFrame(self.trajectory, columns=['run_time', 'scene_time', 'longitude', 'latitude', 'altitude'])
        df['unit_id'] = self.unit_id
        df['min_consecutive_size'] = self.min_consecutive_size
        return df

    def get_trajectory(self):
        """
        获取轨迹数据。
        """
        return self.trajectory

class DatasetCollector:
    def __init__(self, time_threshold):
        self.hub_manager = HubManager()  # HubManager实例
        self.units = {}  # 存储所有单位的字典
        self.lock = threading.Lock()  # 线程锁
        self.time_threshold = time_threshold  # 时间阈值

    def collect_trajectory_data(self):
        """
        从观测结果中提取车辆ID、经度、纬度和高度信息，并更新单位的轨迹数据。
        """
        obs = self.hub_manager.get_obs(UnitSide.red)
        current_time = obs[Side.stats_info]  # 假设 current_time 是 {'run_time': x, 'scene_time': y}

        run_time = current_time['run_time']
        scene_time = current_time['scene_time']

        with self.lock:
            for side in [Side.our_side, Side.other_side]:
                for uid, value in obs[side].items():
                    units = value if isinstance(value, list) else [value]
                    if uid not in self.units:
                        self.units[uid] = Unit(uid)
                    for unit in units:
                        unit_id = unit.unit_id
                        longitude = unit.loc.lon
                        latitude = unit.loc.lat
                        altitude = unit.loc.alt
                        self.units[uid].add_observation(run_time, scene_time, longitude, latitude, altitude, self.time_threshold)

    def get_all_trajectory_data(self):
        """
        获取所有单位的轨迹数据并合并为一个DataFrame。
        """
        with self.lock:
            all_data_frames = [unit.to_dataframe() for unit in self.units.values() if unit.trajectory]
            return pd.concat(all_data_frames, ignore_index=True) if all_data_frames else pd.DataFrame()

    def get_unit_trajectory(self, unit_id):
        """
        获取指定单位的轨迹数据。
        """
        with self.lock:
            if unit_id in self.units:
                return self.units[unit_id].to_dataframe()
            else:
                return pd.DataFrame()

def data_collector_thread(collector, frequency):
    """
    数据采集线程，定期调用数据采集方法。
    """
    try:
        while True:
            collector.collect_trajectory_data()
            time.sleep(frequency)
    except KeyboardInterrupt:
        print("数据采集终止。")

def collect_data_for_duration(duration=60):
    collector = DatasetCollector()
    for _ in range(duration):
        collector.collect_trajectory_data()
    data = collector.get_all_trajectory_data()
    return data

if __name__ == "__main__":
    time_threshold = 5  # 设置时间阈值，单位为秒
    collector = DatasetCollector(time_threshold)
    frequency = 0.1  # 设置数据收集频率，单位为秒

    # 启动数据收集子线程
    thread = threading.Thread(target=data_collector_thread, args=(collector, frequency))
    thread.daemon = True  # 设置为守护线程
    thread.start()

    # 主线程用于处理数据
    try:
        while True:
            data = collector.get_all_trajectory_data()
            if not data.empty:
                unit_id = '1'  # 替换为实际的unit_id
                trajectory = collector.get_unit_trajectory(unit_id)
                print(trajectory)
                data.to_csv('data.csv', index=False, mode='a', header=False)
            else:
                print("没有数据可写入CSV文件。")
            time.sleep(1)  # 模拟主线程处理间隔
    except KeyboardInterrupt:
        print("主线程终止。")
