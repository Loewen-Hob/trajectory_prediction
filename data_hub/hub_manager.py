from data_hub.hub_controller.xx_sim.sim_router import XxSimRouter
from data_hub.data_struct.unit import *
from data_hub.backend.send_unit_msg import *
from data_hub.backend.read_command_stream import consume_command
from data_hub.backend.send_unit_command import send_command
from data_hub.backend.analysis_recv_cmd import analysis_cmd
from data_hub.utils.watiting_indicator import WaitingIndicator
from collections import defaultdict
from data_hub.hub_controller.controller import HubController
import logging

default_ip = "127.0.0.1"
# default_ip = "192.168.1.101"
default_port = 50051


class HubManager:
    """
    这里作为新的流程管理器，集合各个系统的功能和逻辑流转
    """

    def __init__(self, ip=default_ip, port=default_port) -> None:
        self._env: HubController = XxSimRouter(ip, port)
        self.wi = WaitingIndicator('updating obs')
        self.wi.on = False
        self.last_send_id = defaultdict(lambda: defaultdict(dict))
        self.time_counter = 0
    def get_obs(self, side: UnitSide):
        """
        params side: UnitSide
        return: {UnitSide: {Side: {id: HubUnit}}}
        """
        self._env.update_obs()
        return self._env.side_units_dict[side]

    def _reset(self, reset_scenario=False):
        if reset_scenario:
            self._env.reset_scenario()
        self._env.step()

    def step(self):
        self._env.step()
        self.wi.print_next()

    def collect_trajectory_data(self, obs):
        """
        从观测结果中提取车辆ID、经度、纬度和高度信息，以便于轨迹预测，使用累加的数字替代时间戳。
        """
        trajectory_data = []  # 初始化列表以存储结果

        for uid, unit in obs.items():
            # 假设HubUnit有相应的属性并且可以直接访问
            unit_id = unit.unit_id
            longitude = unit.loc.lon
            latitude = unit.loc.lat
            altitude = unit.loc.alt

            # 将提取的信息及当前计数器值添加到列表中
            trajectory_data.append((unit_id, self.time_counter, longitude, latitude, altitude))

        self.time_counter += 1  # 调用方法后递增计数器

        return trajectory_data

if __name__ == '__main__':
    import time
    hub_manager = HubManager()
    hub_manager._reset(reset_scenario=False)
    data = []
    while True:
        obs = hub_manager.get_obs(UnitSide.red)
        _obs = {**obs[Side.our_side], **obs[Side.other_side]}
        trajectory_data = hub_manager.collect_trajectory_data(_obs)
        data = data + trajectory_data
        for uid, unit in obs[Side.our_side].items():
            unit: HubUnit
            unit.move_to_llh((121.50725555419922, 25.037256240844727, 29.9655303955078))
            # unit.move_to_uloc((-47417.5058196354, 32863.62318664942, -99706.07427703217))
        hub_manager.step()
        time.sleep(1)


