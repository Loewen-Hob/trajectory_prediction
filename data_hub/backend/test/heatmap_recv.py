import asyncio
import aioredis
import numpy as np
import matplotlib.pyplot as plt
import json

# 全局变量，用于在协程间共享热力图数据
heatmap_data = dict()
"""
{
    'points': [121.507167, 25.037037, 121.510275, 25.047642, 121.51402, 25.0356223, 121.517365, 25.04594],
    # 左上，右上，左下，右下
    'data': heatmap.tolist(),  # NumPy数组
    'shape': [1024, 1024],
    'name': '测试图层'
}
"""


async def update_heatmap(channel_name):
    global heatmap_data
    # client = await aioredis.Redis(host="192.168.3.52", port=6379, db=0)
    client = await aioredis.Redis(host="localhost", port=6379, db=0)
    sub = client.pubsub()
    await sub.subscribe(channel_name)

    while True:
        async for message in sub.listen():
            if message['type'] == 'message':
                data = json.loads(message['data'])
                heatmap_data.update(data)
                print("Heatmap data updated")


# ======================================
async def draw_heatmap(interval):
    global heatmap_data
    fig, ax = plt.subplots()
    heatmap = np.random.randint(0, 256, (100, 100))
    img = ax.imshow(heatmap, cmap='hot', interpolation='nearest')
    plt.axis('off')

    while True:
        if heatmap_data:
            heatmap = np.array(heatmap_data['data'], dtype=np.uint8).reshape(heatmap_data['shape'])
            # print(heatmap)
            img.set_data(heatmap)
        fig.canvas.draw_idle()  # 请求更新画布，但不阻塞
        plt.pause(interval)  # 暂停一段时间，允许图形更新
        await asyncio.sleep(interval)


async def main(channel_name, draw_interval):
    task1 = asyncio.create_task(update_heatmap(channel_name))
    task2 = asyncio.create_task(draw_heatmap(draw_interval))
    await asyncio.gather(task1, task2)


if __name__ == "__main__":
    asyncio.run(main('heatmap_channel_1', 0.1))
