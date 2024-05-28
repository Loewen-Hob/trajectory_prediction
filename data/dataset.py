from data_hub.hub_manager import HubManager
from data_hub.data_struct.unit import UnitSide, Side
import pandas as pd
import time

class Unit:
    def __init__(self, unit_id):
        self.unit_id = unit_id
        self.trajectory = []
        self.min_consecutive_size = 0

    def add_observation(self, time_counter, longitude, latitude, altitude):
        if not self.trajectory:
            self.trajectory.append((time_counter, longitude, latitude, altitude))
        else:
            last_time_counter = self.trajectory[-1][0]
            if time_counter == last_time_counter + 1:
                self.trajectory.append((time_counter, longitude, latitude, altitude))
            else:
                self.check_min_consecutive_length()
                self.trajectory = [(time_counter, longitude, latitude, altitude)]

    def check_min_consecutive_length(self):
        if len(self.trajectory) > self.min_consecutive_size:
            self.min_consecutive_size = len(self.trajectory)

    def finalize(self):
        self.check_min_consecutive_length()

    def to_dataframe(self):
        df = pd.DataFrame(self.trajectory, columns=['time_counter', 'longitude', 'latitude', 'altitude'])
        df['unit_id'] = self.unit_id
        df['min_consecutive_size'] = self.min_consecutive_size
        return df

    def get_trajectory(self):
        return self.trajectory

class DatasetCollector:
    def __init__(self):
        self.hub_manager = HubManager()
        self.time_counter = 0
        self.units = {}

    def collect_trajectory_data(self):
        """
        从观测结果中提取车辆ID、经度、纬度和高度信息，以便于轨迹预测。
        使用HubManager实例的get_obs方法得到车辆的数据。
        """
        obs = self.hub_manager.get_obs(UnitSide.red)

        merged_obs = {}
        for side in [Side.our_side, Side.other_side]:
            for key, value in obs[side].items():
                if key not in merged_obs:
                    merged_obs[key] = value
                else:
                    if isinstance(merged_obs[key], list):
                        merged_obs[key].append(value)
                    else:
                        merged_obs[key] = [merged_obs[key], value]

        for uid, units in merged_obs.items():
            units = units if isinstance(units, list) else [units]
            for unit in units:
                unit_id = unit.unit_id
                longitude = unit.loc.lon
                latitude = unit.loc.lat
                altitude = unit.loc.alt

                if unit_id not in self.units:
                    self.units[unit_id] = Unit(unit_id)

                self.units[unit_id].add_observation(self.time_counter, longitude, latitude, altitude)

        self.time_counter += 1

    def get_all_trajectory_data(self):
        all_data_frames = []
        for unit in self.units.values():
            unit.finalize()
            df = unit.to_dataframe()
            all_data_frames.append(df)
        final_df = pd.concat(all_data_frames, ignore_index=True)
        return final_df

    def get_unit_trajectory(self, unit_id):
        if unit_id in self.units:
            unit = self.units[unit_id]
            return unit.get_trajectory()
        else:
            return []

def collect_data_for_duration(duration=60):
    collector = DatasetCollector()
    for _ in range(duration):
        collector.collect_trajectory_data()
    data = collector.get_all_trajectory_data()
    return data

def data_generator(collector):
    try:
        while True:
            collector.collect_trajectory_data()
            yield collector.get_all_trajectory_data()
            time.sleep(1)
    except KeyboardInterrupt:
        print("数据采集终止。")

if __name__ == "__main__":
    collector = DatasetCollector()
    for data in data_generator(collector):
        unit_id = 1  # 替换为实际的unit_id
        trajectory = collector.get_unit_trajectory(unit_id)
        print(trajectory)
        if len(data) > 0:
            data.to_csv('data.csv', index=False, mode='a', header=False)
        else:
            print("没有数据可写入CSV文件。")