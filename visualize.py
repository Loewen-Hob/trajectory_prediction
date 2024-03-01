import matplotlib.pyplot as plt
from mpl_toolkits.mplot3d import Axes3D
import pandas as pd

from coor_transform import BLH2XYZ

a = 6378137.0  # 参考椭球的长半轴, 单位 m
b = 6356752.31414  # 参考椭球的短半轴, 单位 m

columns_name = [
    "vehicle_id",
    "datetime",
    "vehicle_type",
    "velocity",
    "traffic_lane",
    "longitube",
    "latitude",
    "kilopost",
]
df = pd.read_csv("./data/test.csv")
df.columns = columns_name
df[["x", "y", "z"]] = df.apply(
    lambda row: BLH2XYZ(row["longitube"], row["latitude"], 0,),
    axis=1,
    result_type="expand",
)
df["x"] = df["x"] - df["x"].min()
df["y"] = df["y"] - df["y"].min()
df["z"] = df["z"] - df["z"].min()

fig = plt.figure()
ax = fig.add_subplot(111, projection="3d")
all_vehicle_id = df["vehicle_id"].unique()
for vehicle_id in all_vehicle_id[:5]:
    print("vehicle_id: ", vehicle_id)
    result = df[df["vehicle_id"] == vehicle_id]
    plt.plot(result["x"], result["y"], result["z"], label=vehicle_id)
plt.show()
