import time
from typing import Optional

from instruction.env_cmd import CommandBase
from instruction.player_brain.player_brain_client import PlayerBrainClient
from instruction.player_brain.player_brain_pb2 import RequestObservation, RequestAction
from instruction.Function import Command
from instruction.datatypes import FVType, Request


class EnvClient:
    def __init__(self, ip="127.0.0.1", port=50051):
        self.ip = ip
        self.port = port
        self.client = PlayerBrainClient(ip, str(port))
        self.unit_attrs = []
        self.request = Request()

    def set_unit_attrs(self, attrs: list[str]):
        self.unit_attrs = attrs

    def generate_observation(self, obs_struction):
        command = CommandBase()
        command.set_obs(obs_struction)
        self.execute(command.actions_request)

    def execute(self, action):
        if isinstance(action, RequestAction):
            action = action
        elif isinstance(action, dict):
            if action['CmdType'] == 'move':
                action = self.request.add(Command.GoToLLH(action['id'], action['position']))
            elif action['CmdType'] == 'attack':
                action = self.request.add(Command.AttackUUID(action['id'], action['target_id']))
        else:
            raise TypeError(f'传入命令的类型错误, 命令: {action}, 类型: {type(action)}')
        # print('exec action:', action)
        self.client.request_action(action)
        time.sleep(0.01)

    def get_observation(
        self, unit_attrs: Optional[list[str]] = None
    ) -> dict[str, list[dict[str, any]]]:
        """
        Retrieves an observation from the client.

        Parameters
        ----------
        unit_attrs : Optional[list[str]], optional
            A list of unit attributes to include in the observation. Defaults to None.

        Returns
        -------
        dict[str, list[dict[str, any]]]
            A dictionary containing the observation data. The keys of the dictionary are the following:
                - "units": A list of dictionaries representing the units in the observation. Each dictionary contains the specified unit attributes.
                  The keys of the unit dictionaries are the unit attribute names, and the values are the corresponding attribute values.
        """
        if unit_attrs is None:
            unit_attrs = self.unit_attrs

        response = self.client.request_observation(RequestObservation())

        ' ---- 以下加了异常数据处理 ---- '  # 仿真没开
        if response is None:
            return {}
        '---------------------------'

        observation = parse_entity_to_dict(response.observation.observation)

        ' ---- 以下加了异常数据处理 ---- '  # 仿真没载入想定
        if 'OBS' not in observation or len(observation['OBS']) == 0 or 'Unit' not in observation['OBS'][0]:
            return {}
        observation['OBS'] = observation['OBS'][0]
        '---------------------------'

        units = observation["OBS"]["Unit"]
        if not isinstance(units, list):
            units = [units]

        state = {"units": []}
        for unit in units:
            unit_state = {attr: unit[attr] for attr in unit_attrs}
            state["units"].append(unit_state)

        return observation


def parse_entity_to_dict(entity):
    # parse response to python dict format
    raw_obs = {}
    for entity_ in entity.entities:
        if entity_.name not in raw_obs:
            raw_obs[entity_.name] = []
        raw_obs[entity_.name].append(parse_entity_to_dict(entity_))

    ' ---- 以下代码去掉了，以保证数据结构稳定 ---- '  # 仿真没开
    # for k, v in raw_obs.items():
    #     if len(v) == 1:
    #         raw_obs[k] = v[0]
    # parse all field in the same level as one dict
    '---------------------------'

    for field in entity.fields:
        if field.type == FVType.FVT_LONG:
            raw_obs[field.name] = field.iv[0]
        elif field.type == FVType.FVT_LONG_ARRAY:
            raw_obs[field.name] = list(field.iv)
        elif field.type == FVType.FVT_DOUBLE:
            raw_obs[field.name] = field.dv[0]
        elif field.type == FVType.FVT_DOUBLE_ARRAY:
            raw_obs[field.name] = list(field.dv)
        elif field.type == FVType.FVT_BYTES:
            raw_obs[field.name] = field.bv[0]
        elif field.type == FVType.FVT_BYTES_ARRAY:
            raw_obs[field.name] = list(field.bv)
        elif field.type == FVType.FVT_STRING:
            raw_obs[field.name] = field.bv[0].decode('utf-8')
        elif field.type == FVType.FVT_STRING_ARRAY:
            raw_obs[field.name] = list(field.bv.decode('utf-8'))
    return raw_obs