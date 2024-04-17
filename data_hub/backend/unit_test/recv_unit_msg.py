import redis

pool = redis.ConnectionPool(host='192.168.3.52', port=6379, max_connections=5)
conn = redis.Redis(connection_pool=pool, db=0)

unit_dynamic_info_stream = 'unit_info_stream'  # 单位的动态数据mq

if __name__ == '__main__':
    import time

    while True:
        messages = conn.xread({unit_dynamic_info_stream: '0'}, block=0, count=10)

        for stream, message_list in messages:
            for message_id, message_data in message_list:
                print(time.time(), message_id, '---', message_data)
                # conn.xdel(unit_dynamic_info_stream, message_id)
        time.sleep(0.5)
