import redis
import json
from data_hub.data_struct.unit import HubUnit

pool = redis.ConnectionPool(host='192.168.3.52', port=6379, max_connections=5)
# pool = redis.ConnectionPool(host='192.168.3.77', port=15555, max_connections=5)
conn = redis.Redis(connection_pool=pool, db=0)

# unit_dynamic_info_stream = 'task_stream'

unit_dynamic_data = {  # 具体kv你来定
    'unit_state': 0,
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

# task_stream_data = [
#
#     {"set_id": 0,
#      "task": 0,
#      "task_id": 0,
#      "use_units": [1, 2, 3, 4]},
#     {"set_id": 1,
#      "task": 1,
#      "task_id": 1,
#      "use_units": [11, 22, 33, 44]},
# ]
#

unit_dynamic_info_key = 'unit:dynamic:info'
unit_dynamic_info_stream = 'unit_info_stream'  # 单位的动态数据mq

unit_dynamic_data = {  # 具体kv你来定
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


# def send_unit_info(unit_list):
#     for unit in unit_list:
#         unit: HubUnit
#         conn.xadd(unit_dynamic_info_stream, {"unit_id": str(unit.unit_id)})
#         data = {k: v for k, v in unit._trans2dict().items() if k in unit_dynamic_data}
#         print(data)
#         conn.hset(unit_dynamic_info_key, str(unit.unit_id), json.dumps(data))



def send_unit_info(unit_list):
    for unit in unit_list:
        unit: HubUnit
        conn.xadd(unit_dynamic_info_stream, {"data": json.dumps({"unit_id": unit.unit_id,})})
        data = {k: v for k, v in unit._trans2dict().items() if k in unit_dynamic_data}
        conn.hset(unit_dynamic_info_key, unit.unit_id, json.dumps(data))
        print(data)

        # unit_weapon_dynamic_info_key = 'unit:weapon:dynamic:info'
        # rds.hset(unit_weapon_dynamic_info_key, 1, json.dumps(unit_weapon_dynamic_data))


# # def send_unit
# # async def get_user(db: Session, user_id: int):
# #     result = await db.execute(select(models.UserInfo).filter(models.UserInfo.id == user_id))
# #     return result.scalar()
#
#
# conn.xadd('unit_info_stream', {"unit_id": 1})
#
# unit_ids = [1, 2, 3, 4, 5]
# for unit_id in unit_ids:
#     conn.hset(unit_dynamic_info_key, str(unit_id), json.dumps(unit_dynamic_data))


if __name__ == '__main__':
    import time
    while True:
        messages = conn.xread({unit_dynamic_info_stream: '0'}, block=0, count=10)

        for stream, message_list in messages:
            for message_id, message_data in message_list:
                print(time.time(), message_id, '---', message_data)
                conn.xdel(unit_dynamic_info_stream, message_id)
#
# unit_dynamic_info_key = 'unit:dynamic:info:test'
#
# for unit_id in unit_ids:
#     conn.hset(unit_dynamic_info_key, str(unit_id), json.dumps(unit_dynamic_data))
#
# res = conn.hget(unit_dynamic_info_key, 1)
# print(json.loads(res))
#
# all = conn.hgetall(unit_dynamic_info_key)
# print('all:--', all)
