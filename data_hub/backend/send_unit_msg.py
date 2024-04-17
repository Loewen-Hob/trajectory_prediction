import redis
import json
import cv2
import numpy as np
from data_hub.data_struct.unit import HubUnit
import logging
from data_hub.backend.constants import *


pool = redis.ConnectionPool(host=host_ip, port=host_port, max_connections=5)
conn = redis.Redis(connection_pool=pool, db=0)

# 这里定要什么数据，并且给出默认数值
_unit_dynamic_data = {
    'unit_id': 0,
    'fire': 0,  # 是否开火 1是 0：否 新增 2024-02-24
    'show': 1,  # 单位是否展示：1:是 0:否 新增 2024-02-24 原因1
    'unit_name': 'test',  # 单位动态名称
    'unit_type': 1,  # 单位动态类型
    'unit_state': 0,  # 状态

    'group_num': '1',  # 编号

    'camp_type': 0,  # 阵营，0红 1蓝

    'health': 100,  # 完好程度
    'comm_quality': 80,  # 信号强度
    'elevation': 100.25,  # 高程信息  # fixme 要删掉吧？
    'rotation_vel': 32.5,  # 转动方向  # fixme
    'vel': 82.5,  # 实体速度'
    'oil_power': 0.8,  # 当前油量百分比
    'electricity_power': 0.35,  # 当前电量百分比

    'horizon_angle': 0,  # 炮台水平角度
    'vertical_angle': 0,  # 炮台俯仰角度

    'lateral_angle_to_platform': 60,  # 上装相对平台的横摆角
    'vertical_angle_to_platform': 60,  # 上装相对平台的俯仰角
    'loc': [10, 10, 0],  # 位置信息
    'rot': [0, 0, 0],  # roll, pitch, yaw
    'command_state': 0,  # 指令执行状态
    'command_id': 10000,  # 指令唯一表示
    'command_control_party': 0,  # 指令发出对象：0:ai唯一表示1:人工唯一标识

    'weapon_info': {
        '1': {  # dynamic_weapon_id
            'name': '武器1',  # 武器名称
            'weapon_id': 1,  # 用于静态武器数据guid关联
            'weapon_status': 0,  # 武器状态
            'used_channel': 1,  # 可用通道
            'bullet_num': 60,  # 剩余弹药
            'lateral_angle': 30.2,  # 横摆角
            'vertical_angle': 30.2,  # 俯仰角
            'weapon_type': 1,  # 武器类型
        },
        # '2': {  # dynamic_weapon_id
        #     'name': '武器2',  # 武器名称
        #     'weapon_id': 1,  # 用于静态武器数据guid关联
        #     'weapon_status': 0,  # 武器状态
        #     'used_channel': 1,  # 可用通道
        #     'bullet_num': 60,  # 剩余弹药
        #     'lateral_angle': 30.2,  # 横摆角
        #     'vertical_angle': 30.2  # 俯仰角
        # },
        # '3': {  # dynamic_weapon_id
        #     'name': '武器3',  # 武器名称
        #     'weapon_id': 1,  # 用于静态武器数据guid关联
        #     'weapon_status': 0,  # 武器状态
        #     'used_channel': 1,  # 可用通道
        #     'bullet_num': 60,  # 剩余弹药
        #     'lateral_angle': 30.2,  # 横摆角
        #     'vertical_angle': 30.2  # 俯仰角
        # }
    }
}

_unit_type_mapping = {
    # type
    301: {
        # subtype: unit_type
        50: 2,  # 坦克
    },
    117: {
        23: 9,  # 低空突击
    }
}

_max_health_mapping = {
    # type
    301: {
        # subtype: unit_type
        50: lambda x: x/1350,  # 坦克
    },
    117: {
        23: lambda x: x/100,  # 低空突击
    }
}

# 位置矫正，仿射变换的效果居然比透视变换的要好哎
s_p = [
    [121.50774383544922, 25.036832809448242, 29.32520866394043],
    [121.51036071777344, 25.04780387878418, 29.351716995239258],
    [121.51715087890625, 25.04477310180664, 29.337265014648438],
    [121.5107192993164, 25.036195755004883, 29.316865921020508],
    [121.51168823242188, 25.03955078125, 29.29998207092285],
]
t_p = [
    (121.50734383544922, 25.037102809448243, 31),
    (121.50998071777343, 25.047563878784178, 31),
    (121.51727587890625, 25.044833101806642, 31),
    (121.5105692993164, 25.036535755004884, 31),
    (121.51155323242187, 25.03974078125, 31),
]
s_p = np.float32([p[:2] for p in s_p])
t_p = np.float32([p[:2] for p in t_p])
m = cv2.getAffineTransform(s_p[:3], t_p[:3])


_unit_name_mapping = {
    7: 'WRJ01',
    8: 'WRJ02',
    9: 'WRJ03',
    10: 'WRJ04',
    62: 'GJD01',
    63: 'GJD02',
    64: 'GJD03',
    65: 'GJD04',
    68: 'GJD05',
    69: 'GJD06',
    70: 'GJD07',
    71: 'GJD08',
    18: 'TK01',
    56: 'TK02',
    57: 'TK03',
    67: 'TK04',

}

unit_id_mapping = {
    7: 1,
    8: 2,
    9: 3,
    10: 4,

    62: 5,
    63: 6,
    64: 7,
    65: 8,

    68: 9,
    69: 10,
    70: 11,
    71: 12,
}
unit_id_mapping_reversed = {v: k for k, v in unit_id_mapping.items()}

# 这里处理字段转换
_process_mapping = {  # 这里处理数据格式和内容的hash
    'unit_id': lambda x: int(unit_id_mapping[x['unit_id']] if x['unit_id'] in unit_id_mapping else x['unit_id']),
    # 'fire': 'is_firing',
    # 'show': 'is_visible',
    # 'fire': lambda x: int(random.randint(0, 1)),
    'fire': lambda x: int(0),

    'show': lambda x: int(1),

    'unit_type': lambda x: int(_unit_type_mapping[x['type']][x['subtype']])  # 单位动态类型
    if x['type'] in _unit_type_mapping and x['subtype'] in _unit_type_mapping[x['type']] else 1,  # 单位动态类型
    # 0 狗, 1 坦克, 2 轮式, 3 军用卡车, 4 智能网联大白卡,
    # 5 固定翼侦察, fixme bug 这些无人机的高度都是写死的
    # 6 固定翼打击, fixme bug 这些无人机的高度都是写死的
    # 7 四旋翼侦察，
    # 8 fixme 不知名3旋翼飞机？, fixme bug 这些无人机的高度都是写死的
    # 9 四旋翼攻击, fixme bug 这些无人机的高度都是写死的
    # 10 士兵

    # 'unit_state': lambda x: int(np.random.randint(0, 3)),  # 状态
    'unit_state': lambda x: int(x['unit_state']),  # 状态  0:完好 1:损毁 2:瘫痪
    # 'unit_state': lambda x: int(x['unit_id'] % 3),  # 状态
    # 0 健康, 1 故障等级1

    'camp_type': lambda x: int(x['side']),  # 阵营，0红 1蓝 2灰
    'health': lambda x: int(_max_health_mapping[x['type']][x['subtype']](x['health'])*100
                            if x['type'] in _max_health_mapping and x['subtype'] in _max_health_mapping[x['type']]
                            else x['health']),  # 完好程度
    'comm_quality': lambda x: int(x['comm_quality']),  # 信号强度
    'electricity_power': lambda x: float(x['electricity_power']),  # 当前电量百分比

    # 'command_state': lambda x: int(x['command_state']),  # 指令执行状态  # fixme 要对新类型
    'command_state': lambda x: int(x['unit_id'] % 3),  # 指令执行状态  # fixme 要对新类型
    # 0 无任务， 1 任务完成， 2 任务中断， 3 机动中， 4 开火中， 5 侦察中， 6 电抗中， 7 人工操作中， 8 返航中

    'command_id': lambda x: int(x['command_id']),  # 指令唯一表示
    'command_control_party': lambda x: int(x['command_control_party']),  # 指令发出对象：0:ai唯一表示1:人工唯一标识
    'unit_name': lambda x: _unit_name_mapping[x['unit_id']],  # 指令发出对象：0:ai唯一表示1:人工唯一标识
}


def _preprocess(data_dict: dict):
    """
    data_dict 协议转换。这里要求全量数据
    step 0: 对齐数据模板
    step 1: 数据内容、格式转换
    step 2: 字段转换
    """
    merged_data = {**_unit_dynamic_data, **data_dict}
    result = {k: merged_data[k] for k in _unit_dynamic_data.keys()}
    result.update({k: merged_data[v] if type(v) == str else v(merged_data) for k, v in _process_mapping.items()})

    result['loc'] = list(result['loc'])

    # fixme: --------- tmp setting 临时设置区 ---------
    # fixme: 手动修复高度问题, 抬高位置
    result['loc'][2] += 1.82

    # # fixme: 手动修复高度问题, 地面车辆都手动设置高度
    # if result['unit_type'] in [0, 1, 2, 3, 4, 11]:
    #     result['loc'] = result['loc'][0], result['loc'][1], 31

    # # fixme: 手动修复无人机高度问题: 9-无人机的高度加了22
    if result['unit_type'] in [9]:
        result['loc'][2] -= 22
        # print(result['unit_state'])

    # # fixme: 手动设置红方坦克为高机动外观d
    # if result['camp_type'] == 0 and result['unit_type'] == 1:
    #     result['unit_type'] = 2

    # fixme: 朝向矫正
    result['rot'] = (*result['rot'][:2], result['rot'][2] - 90)

    # fixme: 位置矫正,仿射变换
    result['loc'] = (*m.dot([*result['loc'][:2], 1]).tolist(), result['loc'][2])

    # # todo: 设置单位死亡的时候为灰色
    # if result['unit_state'] == 2:
    #     result['camp_type'] = 2

    return result


def send_unit_info(unit_list, additional_data_list, conn=conn):
    """
    单位实时数据接
    """

    # print('all_unit_id:', [unit.unit_id for unit in unit_list])
    for unit in unit_list:
        unit: HubUnit

        unit_data_dict = unit._trans2dict()
        # if unit_data_dict['unit_id'] not in _unit_id_mapping:
        #     logging.warning('unit id error: {}'.format(unit_data_dict['unit_id']))
        #     continue
        data = _preprocess(unit_data_dict)
        data['show'] = 0 if data['unit_id'] in additional_data_list['off_show'] else 1
        data['command_control_party'] = 0 if data['unit_id'] in additional_data_list['ai_control'] else 1

            # print('off_show:', data)
        # print('send_unit_info', data)

        # todo: debug 专用 -------
        loc = [*unit.loc._trans2dict()]

        def offset(x, y, d):
            d['loc'] = (loc[0] + x, loc[1] + y, 31)
            print(d['loc'])
            conn.xadd('unit_info_stream', {"data": json.dumps(d)})

        # todo: -----------------
        # if data['camp_type'] == 1:
        #     print(data)
        if data:
            try:
                d = {"data": json.dumps(data)}
                # t.get_spend_time('json.dumps')
                # print('xadd:', d)
                conn.xadd('unit_info_stream', d, maxlen=200)
                # conn.xadd('unit_info_stream', {"data": json.dumps(data)}, maxlen=200)
            except Exception as e:
                logging.warning('{}'.format(e))
        else:
            logging.warning('unit data error occurred: {}'.format(unit))


if __name__ == '__main__':
    pool = redis.ConnectionPool(host='192.168.3.52', port=6379, max_connections=5)
    # pool = redis.ConnectionPool(host='192.168.3.77', port=15555, max_connections=5)
    conn = redis.Redis(connection_pool=pool, db=0)

    # 单位的动态信息
    hu = HubUnit()
    hu._update_from_dict({'unit_id': 1101})
    send_unit_info([hu], conn)
