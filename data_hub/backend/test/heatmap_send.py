import matplotlib.pyplot as plt
import numpy as np
import redis
import time
import json
import sys

# 连接到Redis
# client = redis.Redis(host="192.168.3.52", port=6379, db=0)
client = redis.Redis(host='localhost', port=6379, db=0)


def send_heatmap():
    # 生成热力图并发布数据
    while True:
        heatmap: np.ndarray = generate_heatmap()  # 使用先前定义的 generate_heatmap 函数
        data = json.dumps({
            'points': [121.507167, 25.037037, 121.510275, 25.047642, 121.51402, 25.0356223, 121.517365, 25.04594],
            # 左上，右上，左下，右下
            'data': heatmap.tolist(),  # NumPy数组
            'shape': [1024, 1024],
            'name': '测试图层'
        })

        # print('json', sys.getsizeof(data))
        # print('byte', sys.getsizeof(heatmap.tobytes()))
        client.publish('heatmap_channel_1', data)
        print('sent heat_map')
        time.sleep(0.2)  # 每 0.2 秒发布一次


# ======================================
n = 3
centers = np.random.randint(0, 1024, (n, 2))
std_devs = np.random.randint(50, 100, n)

width, height = 1024, 1024


def generate_heatmap():
    """
    Generate a heatmap with Gaussian hotspots that can move randomly.

    :param width: Width of the heatmap.
    :param height: Height of the heatmap.
    :param centers: List of tuples representing the initial centers of the Gaussian hotspots.
    :param std_devs: List of standard deviations for the Gaussian hotspots.
    :param movement_range: The range in which the center of each hotspot can move.
    :return: A uint8 heatmap array.
    """

    # Example usage
    movement_range = 10  # The centers can move within a range of +/- 10 pixels

    # Initialize an empty heatmap array.
    heatmap = np.zeros((height, width), dtype=np.float)

    # Move each center randomly.
    new_centers = []
    for center in centers:
        new_x = np.clip(center[0] + np.random.randint(-movement_range, movement_range), 0, width)
        new_y = np.clip(center[1] + np.random.randint(-movement_range, movement_range), 0, height)
        new_centers.append((new_x, new_y))
    # print(new_centers)
    # Add Gaussian hotspots to the heatmap.
    for center, std_dev in zip(new_centers, std_devs):
        # print(center)
        x = np.arange(0, width, 1, float)
        y = np.arange(0, height, 1, float)
        y = y[:, np.newaxis]

        x0 = center[0]
        y0 = center[1]

        # Calculate the Gaussian function.
        gaussian = np.exp(-((x - x0) ** 2 + (y - y0) ** 2) / (2 * std_dev ** 2))
        heatmap += gaussian * np.random.randint(-1, 2)

    # Normalize the heatmap.
    # heatmap /= np.max(heatmap)

    # Convert to 8-bit unsigned integer.
    # heatmap_uint8 = np.uint8(heatmap * 255)
    heatmap_uint8 = heatmap

    return heatmap_uint8


if __name__ == "__main__":
    img = generate_heatmap()
    plt.imshow(img)
    # plt.imshow(img, cmap='hot')
    # with open('test_img.png', 'wb') as f:
    #     plt.imsave(f, img)
    plt.show()
    exit()
    send_heatmap()
