import redis

# 连接到Redis服务器
# redis_client = redis.StrictRedis(host='localhost', port=6379, db=0)
redis_client = redis.StrictRedis(host="192.168.3.52", port=6379, db=0)

# Stream和Consumer Group名称
stream_name = 'mystream'
consumer_group_name = 'mygroup'
consumer_name = 'consumer1'

# 创建Consumer Group
redis_client.xgroup_create(stream_name, consumer_group_name, id='0', mkstream=True)

# 消费者从Consumer Group中读取消息
while True:
    # 从Stream中读取消息
    messages = redis_client.xreadgroup(consumer_group_name, consumer_name, {stream_name: '>'}, count=1, block=0)

    if messages:
        stream, data = messages[0][0]
        message_id, message = data[0]

        # 处理消息
        print(f"Received message from stream '{stream}' with ID {message_id}: {message}")

        # 确认消息已被处理
        redis_client.xack(stream_name, consumer_group_name, message_id)