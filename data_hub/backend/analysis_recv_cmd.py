import numpy as np
import cv2

# cmd
s_p = [
    [121.5067138671875, 25.037282943725586, 30.864830017089844],
    [121.5141372680664, 25.03604507446289, 31.07846450805664],
    [121.50987243652344, 25.04743766784668, 31.263439178466797],
    [121.51758575439453, 25.045991897583008, 45.985477447509766],
]

t_p = [
    [121.507167, 25.037037],
    [121.51402, 25.0356223],
    [121.510275, 25.047642],
    [121.517365, 25.04594],
]
s_p = np.float32([p[:2] for p in s_p])
t_p = np.float32([p[:2] for p in t_p])
m = cv2.getAffineTransform(s_p[:3], t_p[:3])


def trans_point(pdd: dict):
    """pdd: point_data_dict"""  # todo: 可以后面直接变换整条路径
    pdd['lon'], pdd['lat'] = m.dot([pdd['lon'], pdd['lat'], 1]).tolist()


def trans_maneuver_point(cmd_params_dict):
    point_data = [[d['lon'], d['lat']] for d in cmd_params_dict['maneuver_point']]
    res = cv2.transform(np.float32(point_data).reshape(-1, 1, 2), m).reshape(-1, 2)
    for res_p, d in zip(res, cmd_params_dict['maneuver_point']):
        d['lon'], d['lat'] = res_p.tolist()
        d['alt'] = 29.


_cmd_param_preprocess = {  # command_subclass: command_type
    1: {  # 机动
        1: trans_maneuver_point,  # 路径点导航
    },
    3: {
        # 2: 0,  # 目标打击
    },
}

_cmd_type_mapping = {  # command_type: agg_cmd_type  todo???
    3: 6,  # 模式切换
    4: 3,  # 车身控制
    5: 3,
    6: 3,
    7: 3,
    8: 3,
    9: 4,
    10: 4,
    11: 5,  # 开关控制
    12: 6,  # 模式切换
    13: 6,  # 模式切换
}


def analysis_cmd(cmd_queue):
    for cmd in cmd_queue:
        cs, ct = cmd['command_subclass'], cmd['command_type']
        if cs in _cmd_param_preprocess and ct in _cmd_param_preprocess[cs]:
            _cmd_param_preprocess[cs][ct](cmd['command_params'])  # 原地预处理数据

    # todo: 指令的聚合按键的叠加和互斥逻辑：
    #  车身和炮台不互斥，左右和上下不互斥，同向的数据要累加，但是同维度不同方向的数据要替换。
    # if cmd_queue:
    #     print('trans message:', cmd_queue)
    return cmd_queue

