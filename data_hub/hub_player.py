from data_hub.data_struct.enum_types import *


class HubPlayer:
    def __init__(self, player_name: str, player_side: UnitSide):
        self.player_name = player_name
        self.player_side = player_side
        self.info_manager = None  # todo 后面会更新进来同阵营共享的数据处理结果

    def step(self, side_obs):
        """
        side_obs: {
            'our_side': {id: hub_unit},
            'other_side': {id: hub_unit}
        }
        """
        pass

    def reset(self, side_obs):
        """
        side_obs: {
            'our_side': {id: hub_unit},
            'other_side': {id: hub_unit}
        }
        """
        pass
