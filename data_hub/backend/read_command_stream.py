import time
import json
import redis
import logging
from data_hub.backend.constants import host_ip, host_port

# rds = redis.StrictRedis(host="localhost", port=6379, db=0, decode_responses=True)
conn = redis.StrictRedis(host=host_ip, port=host_port, db=0, decode_responses=True)


def consume_command(conn=conn):
    """
    指令接收
    """
    # messages = conn.xread({'user_send_command_stream': '0'}, block=0)  # Block until a new message arrives
    try:
        messages = conn.xread({'user_send_command_stream': '0'})  # Block until a new message arrives
    except Exception as e:
        logging.warning('{}'.format(e))
        return []
    # result: {int: dict} = {}

    result: list = []
    for stream, message_list in messages:
        for message_id, message_data in message_list:
            # Process the message
            # print(f"Received message: {message_data}")

            # Acknowledge the message by removing it from the stream
            data = message_data['data']
            data = json.loads(data)

            # result[data['unit_id']] = data
            result.append(data)
            conn.xdel('user_send_command_stream', message_id)

    return result


# command_id, 生效状态：成功：1/失败：0， 原因：str，
if __name__ == "__main__":
    import redis
    import time

    # rds = redis.StrictRedis(host="localhost", port=6379, db=0, decode_responses=True)
    conn = redis.StrictRedis(host="192.168.3.52", port=6379, db=0, decode_responses=True)

    while True:
        result = consume_command(conn)
        time.sleep(0.5)
        print('---' * 100)
        print(result)
        print('---' * 100)
