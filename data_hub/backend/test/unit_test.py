import time
import redis
import json

# rds = redis.StrictRedis(host="localhost", port=6379, db=0, decode_responses=True)
rds = redis.StrictRedis(host="192.168.3.52", port=6379, db=0, decode_responses=True)

# mredis = Redis()

unit_dynamic_info_stream = 'unit_info_stream'  # 单位的动态数据mq
unit_dynamic_info_key = 'unit:dynamic:info'
unit_weapon_dynamic_info_key = 'unit:weapon:dynamic:info'


def deal_redis():
    rds.xadd(unit_dynamic_info_stream, {"data": json.dumps({"unit_id": 1, "weapon_id": 1})}, maxlen=20)
    unit_dynamic_data = {
        'unit_state': 0,
        'camp': 0,
        'health': 100,
        'comm_quality': 80,
        'elevation': 100.25,
        'vel': 82.5,
        'rotation_vel': 32.5,
        'oil_power': 88.5,
        'electricity_power': 38.5,
        'horizon_angle': 30,
        'vertical_angle': 30,
        'lateral_angle_to_platform': 60,
        'vertical_angle_to_platform': 60,
        'loc': [10, 10, 0],
        'rot': [0, 0, 0],
    }
    rds.hset(unit_dynamic_info_key, 1, json.dumps(unit_dynamic_data))
    unit_weapon_dynamic_data = {
        'weapon_status': 0,  # 武器状态
        'used_channel': 1,  # 可用通道
        'bullet_num': 60,  # 剩余弹药
        'lateral_angle': 30.2,  # 横摆角
        'vertical_angle': 30.2  # 俯仰角
    }
    unit_weapon_dynamic_info_key = 'unit:weapon:dynamic:info'
    rds.hset(unit_weapon_dynamic_info_key, 1, json.dumps(unit_weapon_dynamic_data))


if __name__ == '__main__':
    deal_redis()
