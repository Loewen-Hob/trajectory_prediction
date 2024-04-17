from data_hub.data_struct.meta_data import *


class HubLocation(HubMetaData):
    lon: float = ...  # 经度
    lat: float = ...  # 纬度
    alt: float = ...  # 高度

    def _update_from_dict(self, data_list):
        assert len(data_list) == 3
        self.lon, self.lat, self.alt = data_list
        return self

    def _trans2dict(self):
        return self.lon, self.lat, self.alt


class HubRotation(HubMetaData):
    roll: float = ...
    pitch: float = ...
    yaw: float = ...

    def _update_from_dict(self, data_list):
        assert len(data_list) == 3
        self.roll, self.pitch, self.yaw = data_list
        return self

    def _trans2dict(self):
        return self.roll, self.pitch, self.yaw
