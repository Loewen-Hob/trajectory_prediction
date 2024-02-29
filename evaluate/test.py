import pandas as pd
import numpy as np


def calculate_MAE(df):
    # 计算x方向和y方向误差的绝对值
    df['abs_error_x'] = (df['x'] - df['pred_x']).abs()
    df['abs_error_y'] = (df['y'] - df['pred_y']).abs()

    # 计算x方向和y方向误差的平均值
    mae_x = df['abs_error_x'].mean()
    mae_y = df['abs_error_y'].mean()

    # 计算总的MAE
    mae = (mae_x + mae_y) / 2.0
    return mae


def calculate_FDE(df):
    # 计算FDE，假设实际值为最后一行的'y'和'x'列，预测值为'pred_y'和'pred_x'
    last_index = df.index[-1]
    fde = np.sqrt((df.at[last_index, 'y'] - df.at[last_index, 'pred_y']) ** 2 +
                  (df.at[last_index, 'x'] - df.at[last_index, 'pred_x']) ** 2)
    return fde

def calculate_ADE(df):
    # 计算ADE
    ade = np.sqrt((df['y'] - df['pred_y']) ** 2 + (df['x'] - df['pred_x']) ** 2).mean()
    return ade


def evaluate(df):
    mae = calculate_MAE(df)
    fde = calculate_FDE(df)
    ade = calculate_ADE(df)

    print(f"MAE: {mae}")
    print(f"FDE: {fde}")
    print(f"ADE: {ade}")

# 测试用例，后续将修改为实际数据集
data = {
    'y': [10, 20, 30, 40],
    'pred_y': [12, 19, 29, 42],
    'x': [50, 60, 70, 80],
    'pred_x': [52, 59, 71, 84]
}

# 预测函数的结果为一个DataFrame
# 评估每辆车的时候可以写个grouped，然后调用循环
df = pd.DataFrame(data)
evaluate(df)