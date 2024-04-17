# loc
# [121.50774383544922, 25.036832809448242, 29.32520866394043] -> (121.50734383544922, 25.037102809448243, 31)
# [121.51036071777344, 25.04780387878418, 29.351716995239258] -> (121.50998071777343, 25.047563878784178, 31)
# [121.51715087890625, 25.04477310180664, 29.337265014648438] -> (121.51727587890625, 25.044833101806642, 31)
# [121.5107192993164, 25.036195755004883, 29.316865921020508] -> (121.5105692993164, 25.036535755004884, 31)
# [121.51168823242188, 25.03955078125, 29.29998207092285] -> (121.51155323242187, 25.03974078125, 31)
#
# cmd
# [121.5067138671875, 25.037282943725586, 30.864830017089844] -> left_top = [121.507167, 25.037037]
# [121.5141372680664, 25.03604507446289, 31.07846450805664] -> left_bottom = [121.51402, 25.0356223]
# [121.50987243652344, 25.04743766784668, 31.263439178466797] -> right_top = [121.510275, 25.047642]
# [121.51758575439453, 25.045991897583008, 45.985477447509766] -> right_bottom = [121.517365, 25.04594]

import numpy as np
import collections
from data_hub.utils.loc_transform import LocTransform

# loc
# s_p = [
#     [121.50774383544922, 25.036832809448242, 29.32520866394043],
#     [121.51036071777344, 25.04780387878418, 29.351716995239258],
#     [121.51715087890625, 25.04477310180664, 29.337265014648438],
#     [121.5107192993164, 25.036195755004883, 29.316865921020508],
#     [121.51168823242188, 25.03955078125, 29.29998207092285],
# ]
#
# t_p = [
#     (121.50734383544922, 25.037102809448243, 31),
#     (121.50998071777343, 25.047563878784178, 31),
#     (121.51727587890625, 25.044833101806642, 31),
#     (121.5105692993164, 25.036535755004884, 31),
#     (121.51155323242187, 25.03974078125, 31),
# ]

# cmd
# s_p = [
#     [121.5067138671875, 25.037282943725586, 30.864830017089844],
#     [121.5141372680664, 25.03604507446289, 31.07846450805664],
#     [121.50987243652344, 25.04743766784668, 31.263439178466797],
#     [121.51758575439453, 25.045991897583008, 45.985477447509766],
# ]
#
# t_p = [
#     [121.507167, 25.037037],
#     [121.51402, 25.0356223],
#     [121.510275, 25.047642],
#     [121.517365, 25.04594],
# ]

# ======== uloc to llh ========
s_p = [(-47417.5058196354, 32863.62318664942, -99706.07427703217),
       (49210.60088006227, -59469.33987566117, -99316.92879768088),
       (21726.226516528117, 49999.79864655215, -98713.63066229969),
       (-16155.398658715128, -76096.97439863194, -99004.74070813507)]

t_p = [(121.50725555419922, 25.037256240844727, 129.9655303955078),
       (121.51683044433594, 25.045591354370117, 133.8772735595703),
       (121.51410675048828, 25.035709381103516, 139.88731384277344),
       (121.5103530883789, 25.04709243774414, 136.99990844726562)]

a_p = [(-12151.73801272729, -67031.5268708564, -109784.99573227018), (-12613.696908490672, -65172.22484538179, -109784.88800358027), (-13229.638465546012, -63270.667543232776, -109784.78045742959), (-13614.605074288263, -61855.06325216811, -109784.65500073507), (-9688.036071468085, -68827.4279769681, -109785.19379757345), (-7378.332995023518, -68362.58699336868, -109785.02515060827), (-5145.619539549513, -67644.20844308879, -109784.8564106971), (-3066.883894573837, -67115.99020456742, -109784.70861725509)]
r_p = [(121.51074981689453, 25.046274185180664, 29.186290740966797), (121.51070404052734, 25.046106338500977, 29.185529708862305), (121.5106430053711, 25.045934677124023, 29.184814453125), (121.51060485839844, 25.045806884765625, 29.18476104736328), (121.51099395751953, 25.046436309814453, 29.185802459716797), (121.51122283935547, 25.04639434814453, 29.18667984008789), (121.51144409179688, 25.046329498291016, 29.187381744384766), (121.51165008544922, 25.046281814575195, 29.188167572021484)]

s_p = np.float32([p[:2] for p in s_p])
t_p = np.float32([p[:2] for p in t_p])

a_p = np.float32([p[:2] for p in a_p])
r_p = np.float32([p[:2] for p in r_p])
# =======================

# test_p = s_p[-1]
# result_p = t_p[-1]
#
# m = cv2.getAffineTransform(s_p[:3], t_p[:3])
#
# res = cv2.transform(np.float32(s_p).reshape(-1, 1, 2), m).reshape(-1, 2)


def t_once(s_p, t_p, test_p, result_p):
    # 仿射变换
    # m = cv2.getAffineTransform(s_p[:3], t_p[:3])
    # # [121.51151804  25.03976441]
    # result1 = m.dot([*test_p, 1])
    # # print(result1)
    result1 = LocTransform(s_p, t_p, mode='a').trans_point(test_p)
    diff1 = np.linalg.norm(result1 - result_p)
    # print('Affine diff:', diff1)

    # 透视变换
    # m = cv2.getPerspectiveTransform(s_p[:4], t_p[:4])
    # result = m.dot([*test_p, 1])
    # result2 = result[:2] / result[2]
    result2 = LocTransform(s_p, t_p, mode='p').trans_point(test_p)
    # print(result2)
    diff2 = np.linalg.norm(result2 - result_p)
    # print(diff2)
    result = 'Affine' if diff1 < diff2 else 'Perspective'
    # print('Perspective diff:', diff1)
    # print('---' * 100)
    # print(result_p)
    # print(result)
    # print('===' * 100)
    return result, diff1, diff2


res_list = []
v_list = []
for i in range(10000):
    test_inds = list(range(len(s_p)))
    np.random.shuffle(test_inds)
    r, d1, d2 = t_once(s_p[test_inds[:4]], t_p[test_inds[:4]], s_p[test_inds[3]], t_p[test_inds[3]])
    res_list.append(r)
    v_list.append([d1, d2])
# for ap, rp in zip(a_p, r_p):
#     r, d1, d2 = t_once(s_p, t_p, ap, rp)
#     res_list.append(r)
#     v_list.append([d1, d2])

c = collections.Counter(res_list)
print(c)
if c:
    s = max(c.items(), key=lambda x: x[1])
    print(s[0], 'transform is better')
    # print(sorted(c.items(), key=lambda x: x[1], reverse=True)[0])

print('each mean diff:')
print(np.mean(v_list, axis=0).tolist())
print('each max diff:')
print(np.max(v_list, axis=0).tolist())
print('each sum diff:')
print(np.sum(v_list, axis=0).tolist())
print('='*100)

def t_batch(s_p, t_p, test_p, result_p):
    # 仿射变换
    result1 = LocTransform(s_p, t_p, mode='a').trans_point_list(test_p)
    diff1 = np.linalg.norm(result1 - result_p, axis=1)
    # print('Affine diff:', diff1)

    # 透视变换
    result2 = LocTransform(s_p, t_p, mode='p').trans_point_list(test_p)
    # print(result2)
    diff2 = np.linalg.norm(result2 - result_p, axis=1)
    # print(diff2)
    result = np.where(diff1 < diff2, 'Affine', 'Perspective')
    # print('Perspective diff:', diff1)
    # print('---' * 100)
    # print(result_p)
    # print(result)
    # print('===' * 100)
    return result, diff1, diff2

res_list, *v_list = t_batch(s_p, t_p, a_p, r_p)
v_list = np.stack(np.array(v_list)[:, :, np.newaxis], axis=2)


c = collections.Counter(res_list)
print(c)
if c:
    s = max(c.items(), key=lambda x: x[1])
    print(s[0], 'transform is better')
    # print(sorted(c.items(), key=lambda x: x[1], reverse=True)[0])

# print(np.mean(v_list))
# print(np.sum(v_list))

print('each mean diff:')
print(np.mean(v_list, axis=0).tolist())
print('each max diff:')
print(np.max(v_list, axis=0).tolist())
print('each sum diff:')
print(np.sum(v_list, axis=0).tolist())

# v_list_mean = np.mean(v_list, axis=0).tolist()
# v_list_sum = np.sum(v_list, axis=0).tolist()
# print(v_list_mean)
# print(v_list_sum)
# print('each mean diff: {}'.format('; '.join(['{:.9f}'.format(i) for i in v_list_mean])))
# print('each sum diff: {}'.format('; '.join(['{:.9f}'.format(i) for i in v_list_sum])))

# s = np.array([[test_p[0]], [test_p[1]], [1]])  # Convert to homogeneous coordinates
# transformed_point = np.dot(m, s)
# transformed_point = transformed_point[:2] / transformed_point[2]  # Convert back to cartesian coordinates
# result = transformed_point
# print(result)
# diff = np.linalg.norm(result - test_p)
# print(diff)


# dst = cv2.warpAffine(s_p[-1:], m, (100, 100))
# print(dst)
