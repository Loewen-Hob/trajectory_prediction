import time
import json
import logging
import redis
from data_hub.backend.constants import *


conn = redis.StrictRedis(host=host_ip, port=host_port, db=0, decode_responses=True)


def trans_maneuver_point(cmd_params_dict):
    # point_data = [[d['lon'], d['lat']] for d in cmd_params_dict['maneuver_point']]
    # res = cv2.transform(np.float32(point_data).reshape(-1, 1, 2), m).reshape(-1, 2)
    # for res_p, d in zip(res, cmd_params_dict['maneuver_point']):
    #     d['lon'], d['lat'] = res_p.tolist()
    #     d['alt'] = 31.
    cpd = {**cmd_params_dict}
    for d in cpd['maneuver_point']:
        # d['lon'], d['lat'] = res_p.tolist()
        d['alt'] = 31.
    return cpd


_cmd_param_preprocess = {  # command_subclass: command_type
    1: {  # 机动
        1: trans_maneuver_point,  # 路径点导航
    },
    3: {
        # 2: 0,  # 目标打击
    },
}


def send_command(cmd_dict, conn=conn):
    """
    指令接收
    """
    for cmd in cmd_dict.values():
        cmd = {**cmd}
        # print('send message:', cmd)
        cs, ct = cmd['command_subclass'], cmd['command_type']
        if cs in _cmd_param_preprocess and ct in _cmd_param_preprocess[cs]:
            cmd['command_params'] = _cmd_param_preprocess[cs][ct](cmd['command_params'])  # 原地预处理数据
        try:
            conn.xadd('confirmed_command_stream', {"data": json.dumps(cmd)}, maxlen=200)
        except Exception as e:
            logging.warning('{}'.format(e))


# command_id, 生效状态：成功：1/失败：0， 原因：str，
if __name__ == "__main__":
    import redis
    import time

    unit_command_data = {
        'command_id': 10000,  # 指令唯一标识
        'command_control_party': 0,  # 指令发出对象：0:ai唯一表示1:人工唯一标识
        'unit_id': 1,  # 单位id
        'command_name': '机动',  # 指令名称
        'control_type': 1,  # 指令模式,
        'command_type': 1,  # 实体执行指令类型
        'command_subclass': 1,  # 实体执行指令子类型
        'command_params': {
            'maneuver_point': [
                {'lon': 1.111, 'lat': 1.222, 'alt': -1, 'spd': 1.11, 'dir': 0, 'mode': 0}
            ]
        },  # 指令详细参数
    }
    send_command({"1": unit_command_data})
