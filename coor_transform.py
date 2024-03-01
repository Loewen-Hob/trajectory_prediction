"""
CoordTransform模块用以实现大地坐标系与参心空间直角坐标系之间的坐标转换.

模块主要包括以下函数
BLH2XYZ
       该函数可以把某点的大地坐标(B, L, H)转换为空间直角坐标(X, Y, Z)
XYZ2BLH
       该函数可以把某点的空间直角坐标(X, Y, Z)转换为大地坐标（B, L, H)
rad2angle
       该函数把弧度转换为角度
angle2rad
       该函数把角度转换为弧度

"""
import pandas as pd
import math

# a, b使用WGS-84椭球参数
a = 6378137.0
b = 6356752.3142

'''以下为三角函数调用'''
sqrt = math.sqrt
sin = math.sin
cos = math.cos
atan = math.atan
atan2 = math.atan2
fabs = math.fabs

def BLH2XYZ(B, L, H):
    """
     该函数把某点的大地坐标(B, L, H)转换为空间直角坐标（X, Y, Z).
    :param B:  大地纬度, 角度制, 规定南纬为负，范围为[-90, 90]
    :param L:  大地经度, 角度制, 规定西经为负, 范围为[-180, 180]
    :param H:  海拔，大地高, 单位 m
    :param a:  地球长半轴，即赤道半径，单位 m
    :param b:  地球短半轴，即大地坐标系原点到两级的距离, 单位 m
    :return:   X, Y, Z, 空间直角坐标, 单位 m
    """
    B = math.radians(B)  # 角度转为弧度
    L = math.radians(L)  # 角度转为弧度
    e = sqrt((a ** 2 - b ** 2) / (a ** 2))  # 参考椭球的第一偏心率
    N = a / sqrt(1 - e * e * sin(B) * sin(B))  # 卯酉圈半径, 单位 m
    X = (N + H) * cos(B) * cos(L)
    Y = (N + H) * cos(B) * sin(L)
    Z = (N * (1 - e * e) + H) * sin(B)
    return X, Y, Z  # 返回空间直角坐标(X, Y, Z)

def XYZ2BLH(X, Y, Z,):
    """
    该函数实现把某点在参心空间直角坐标系下的坐标（X, Y, Z)转为大地坐标（B, L, H).
    :param X:  X方向坐标，单位 m
    :param Y:  Y方向坐标, 单位 m
    :param Z:  Z方向坐标, 单位 m
    :param a: 地球长半轴，即赤道半径，单位 m
    :param b: 地球短半轴，即大地坐标系原点到两级的距离, 单位 m
    :return:  B, L, H, 大地纬度、经度、海拔高度 (m)
    """
    e = sqrt((a**2-b**2)/(a**2))

    if X == 0 and Y > 0:
        L = 90
    elif X == 0 and Y < 0:
        L = -90
    elif X < 0 and Y >= 0:
        L = atan(Y/X)
        L = math.degrees(L)
        L = L+180
    elif X < 0 and Y <= 0:
        L = atan(Y/X)
        L = math.degrees(L)
        L = L-180
    else:
        L = atan(Y / X)
        L = math.degrees(L)

    b0 = atan(Z/sqrt(X**2+Y**2))
    N_temp = a/sqrt((1-e*e*sin(b0)*sin(b0)))
    b1 = atan((Z+N_temp*e*e*sin(b0))/sqrt(X**2+Y**2))

    while abs(b0-b1) > 1e-7:
        b0 = b1
        N_temp = a / sqrt((1 - e * e * sin(b0) * sin(b0)))
        b1 = atan((Z + N_temp * e * e * sin(b0)) / sqrt(X ** 2 + Y ** 2))

    B = b1
    N = a/sqrt((1-e*e*sin(B)*sin(B)))
    H = sqrt(X**2+Y**2)/cos(B)-N
    B = math.degrees(B)
    return B, L, H   # 返回大地纬度B、经度L、海拔高度H (m)

