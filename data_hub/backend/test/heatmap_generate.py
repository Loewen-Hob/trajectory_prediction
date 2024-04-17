import matplotlib.pyplot as plt
import numpy as np
import time

# 假设 heatmap_data 是动态更新的全局变量
heatmap_data = np.random.rand(1024, 1024)

def update_heatmap_data():
    # 这个函数模拟更新 heatmap_data 的逻辑
    # 在实际应用中，应当替换为接收新数据并更新 heatmap_data 的逻辑
    global heatmap_data
    heatmap_data = np.random.rand(1024, 1024)

def draw_heatmap():
    # plt.ion()  # 开启交互模式
    fig, ax = plt.subplots()
    img = ax.imshow(heatmap_data, cmap='hot', interpolation='nearest')
    plt.axis('off')

    while True:
        update_heatmap_data()  # 模拟数据更新
        img.set_data(heatmap_data)  # 更新图像数据
        fig.canvas.draw_idle()  # 请求更新画布，但不阻塞
        plt.pause(0.1)  # 短暂暂停以允许图形更新

# 调用 draw_heatmap 函数以开始绘制和更新热力图
draw_heatmap()
