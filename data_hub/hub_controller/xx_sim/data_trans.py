import numpy as np
from instruction.datatypes import FVType
from data_hub.data_struct.unit import *
from data_hub.data_struct.enum_types import UnitState

struction_of_obs = {
    'Unit':
        {
            'UID': FVType.FVT_LONG,
            'Camp': FVType.FVT_LONG,
            'Type': FVType.FVT_LONG,
            'SubType': FVType.FVT_LONG,
            'HP': FVType.FVT_LONG,
            'ENU': FVType.FVT_LONG,
            'LLHLocation': FVType.FVT_LONG,
            'UnrealLocation': FVType.FVT_LONG,
            'UnrealRotation': FVType.FVT_LONG,
            # 'LLHRotation': FVType.FVT_LONG,
            'UnrealVelocity': FVType.FVT_DOUBLE_ARRAY,
            # 车辆信息
            'Vehicles': {
                'WheelSteerAngles': FVType.FVT_LONG,
                'Throttle': FVType.FVT_LONG,
                'Brake': FVType.FVT_LONG,
                'Handbrake': FVType.FVT_LONG,
                "AxleBase": FVType.FVT_DOUBLE,
            },
            # 传感器信息
            'Sensor': {
                "Type": FVType.FVT_LONG,
                'DetectionRange': FVType.FVT_LONG,
                'ProbedTarget': {
                    'Camp': FVType.FVT_LONG,
                    'Type': FVType.FVT_LONG,
                    'SubType': FVType.FVT_LONG,
                    'HP': FVType.FVT_LONG,
                    'LLHLocation': FVType.FVT_LONG,
                    "UnrealLocation": FVType.FVT_DOUBLE_ARRAY,
                },
            },
            # 武器信息
            'Weapon': {
                'Type': FVType.FVT_LONG,
                'CoolDown': FVType.FVT_LONG,
                'Ammo': {
                    'Type': FVType.FVT_LONG,
                    'Remain': FVType.FVT_LONG,
                    'Spare': FVType.FVT_LONG,
                    'MaxSpare': FVType.FVT_LONG,
                },
                'RelativeRotation': FVType.FVT_LONG,
            },
            "Command": {
                "Name": FVType.FVT_LONG
            },

            "OverlapDetection": {
                "OtherComponentName": FVType.FVT_BYTES_ARRAY,
                "OtherActorName": FVType.FVT_BYTES_ARRAY,
            },
            "OverlapShapeInfo": {
                "Shape": FVType.FVT_BYTES_ARRAY,
            },

            #
            # 'Character': {
            #     'CharacterPostureStatus': FVType.FVT_LONG,
            #     'CharacterWeaponStatus': FVType.FVT_LONG,
            #     'CharacterEnvironment': FVType.FVT_LONG,
            # },
            # 'PlayerBrainAction': {
            #     'Arguments': FVType.FVT_LONG,
            #     # 'PushHistory': FVType.FVT_LONG,
            #     # 'PopHistory': FVType.FVT_LONG,
            #     # 'ExecuteHistory': FVType.FVT_LONG,
            #     # 'SetupEntity': FVType.FVT_LONG,
            # }
        }
}


def get_probed_target_from_sensors_data(sensors_data):
    res = {}
    if not isinstance(sensors_data, list):
        sensors_data = [sensors_data]
    for sensor_data in sensors_data:
        if "ProbedTarget" not in sensor_data:
            continue
        probed_target = sensor_data.get("ProbedTarget", [])
        if not isinstance(probed_target, list):
            probed_target = [probed_target]
        for target_data in probed_target:
            res[target_data["ID"]] = target_data
    return res


# 这里都是能找到的数据，能直接拿
_unit_process_mapping = {
    'unit_id': 'UID',
    'loc': 'LLHLocation',
    'rot': 'ENU',
    'health': 'HP',
    'uloc': 'UnrealLocation',
    'type': 'Type',
    'subtype': 'SubType',
    'vel': lambda x: np.linalg.norm(x['UnrealVelocity']).tolist(),
    'side': lambda x: {1: UnitSide.red, 2: UnitSide.blue}[x['Camp']],
    'probed_target': lambda x: get_probed_target_from_sensors_data(x['Sensors']),
    'turret_rot': lambda x: x['Weapon'][0]['RelativeRotation'] if len(x['Weapon']) else [0, 0, 0],
    'current_command': lambda x: x.get('Command', 'idle'),
    'unit_state': lambda x: UnitState.perfect,
    'collide': lambda x: True if hasattr(x, 'OverlapDetection') else False,
    'weapons': lambda x: [{
        'type': w['Type'], 'cool_down': w['CoolDown'], 'rel_rot': w['RelativeRotation'],
        'ammo': [{'type': a['Type'], 'remain': a['Remain'], 'max': a['Max'],
                  'spare': a['Spare'], 'max_spare': a['MaxSpare']} for a in w['Ammo']]
    } for w in x['Weapon']],
    'unit_size': lambda x: [200, 200, 100] if 'OverlapShapeInfo' not in x else x['OverlapShapeInfo'][0]['Scale']
}

# 'Weapon': {
#     'Type': FVType.FVT_LONG,
#     'CoolDown': FVType.FVT_LONG,
#     'Ammo': {
#         'Type': FVType.FVT_LONG,
#         'Remain': FVType.FVT_LONG,
#         'Spare': FVType.FVT_LONG,
#         'MaxSpare': FVType.FVT_LONG,
#     },
#     'RelativeRotation': FVType.FVT_LONG,
# },

# _contact_process_mapping = {
#     'contact_id': 'ID',
#     'loc': 'LLHLocation',
#     'rot': 'ENU',
#     'health': 'HP',
#     'uloc': 'UnrealLocation',
#     'type': 'Type',
#     'subtype': 'SubType',
#     'vel': lambda x: np.linalg.norm(x['UnrealVelocity']).tolist(),
#     'side': lambda x: {1: UnitSide.red, 2: UnitSide.blue}[x['Camp']],
#     'probed_target': lambda x: get_probed_target_from_sensors_data(x['Sensors']),
#     'turret_rot': lambda x: x['Weapon'][0]['RelativeRotation'] if len(x['Weapon']) else [0, 0, 0],
# }


def dictData2unitsData(sim_obs):
    units_data_dict = {}

    if sim_obs and "OBS" in sim_obs and "Unit" in sim_obs["OBS"]:
        for unit in sim_obs['OBS']['Unit']:
            # for k, v in name_mapping.items():
            #     assert v in unit, f"{unit} has no key named {v}"
            unit_data = {k: unit[v] if type(v) is str else v(unit) for k, v in _unit_process_mapping.items()}
            units_data_dict[unit_data['unit_id']] = unit_data
    return units_data_dict


if __name__ == '__main__':
    import json

    with open('obs_data.json', 'r') as f:
        obs_data = json.load(f)

    res = dictData2unitsData(obs_data)
    print(res)

    # from devtools import debug
    # debug(res)
