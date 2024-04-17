"""此demo用于测试指令放入redis以及读取
"""
import os
import sys
import json
import aioredis
import asyncio

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

user_send_command_stream = 'user_send_command_stream'


class AsyncRedis(object):

    def __init__(self):
        self.host = "127.0.0.1"
        self.port = "6379"
        self.conn = None

    async def connect(self):
        # 创建异步 Redis 连接池
        self.conn = await aioredis.from_url('redis://{}:{}'.format(self.host, self.port), max_connections=30, db=0)
    
    async def close(self):
        if self.conn:
            self.conn.close()


aredis = AsyncRedis()


async def set_message():
    """放入信息
    """
    await aredis.connect()
    # 放入
    command_data = {
        'command_id': 2,
        'unit_id': 1,
        'control_type': 1,
        'control_mode': 0,
        'command_name': '路径导航',
        'command_type': 1,
        'command_subclass': 1,
        'command_params': {'maneuver_point': [{'lon': 1.111, 'lat': 1.222, 'alt': -1, 'spd': 1.11, 'dir': 0, 'mode': 0}]}
    }
    print("---------------------->>>>>>>>>>>>>>>>>>>input")
    await aredis.conn.xadd(user_send_command_stream, {"data": json.dumps(command_data)}, maxlen=20)
    print("---------------------->>>>>>>>>>>>>>>>>>>sucess")

    # 消费
    messages = await aredis.conn.xread({user_send_command_stream: 0}, block=0, count=3)
    print('get task need confrim result in:{}, data:{}'.format(user_send_command_stream, messages))
    message_ids = []
    for stream, message_list in messages:
        for message_id, message_data in message_list:
            message_ids.append(message_id)
    await aredis.conn.xdel(user_send_command_stream, *message_ids)


if __name__ == '__main__':
    loop = asyncio.new_event_loop()
    loop.run_until_complete(set_message())
    loop.close()
    # loop = asyncio.new_event_loop()
    # loop.run_until_complete(user_send_command_handler())
    # loop.close()