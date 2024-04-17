import cv2
import numpy as np


class LocTransform:
    def __init__(self, source_points, target_points, mode='a'):
        source_points = np.float32([p[:2] for p in source_points])
        target_points = np.float32([p[:2] for p in target_points])

        self.__mode = mode
        if self.mode == 'a':
            self.__m = cv2.getAffineTransform(source_points[:3], target_points[:3])
        elif self.mode == 'p':
            self.__m = cv2.getPerspectiveTransform(source_points[:4], target_points[:4])

    def trans_point(self, point):
        result = self.__m.dot([*point[:2], 1])
        if self.mode == 'a':
            return result
        if self.mode == 'p':
            return result[:2] / result[2]

    def trans_point_list(self, point_list):
        point_list = np.float32([p[:2] for p in point_list])
        points_matrix = np.hstack((point_list, np.ones((point_list.shape[0], 1))))
        result = np.dot(points_matrix, self.__m.T)
        if self.mode == 'a':
            return result[:, :2]
        if self.mode == 'p':
            return result[:, :2] / result[:, 2, np.newaxis]

    @property
    def mode(self):
        return self.__mode


s_p = [(-47417.5058196354, 32863.62318664942, -99706.07427703217),
       (49210.60088006227, -59469.33987566117, -99316.92879768088),
       (21726.226516528117, 49999.79864655215, -98713.63066229969),
       (-16155.398658715128, -76096.97439863194, -99004.74070813507)]

t_p = [(121.50725555419922, 25.037256240844727, 129.9655303955078),
       (121.51683044433594, 25.045591354370117, 133.8772735595703),
       (121.51410675048828, 25.035709381103516, 139.88731384277344),
       (121.5103530883789, 25.04709243774414, 136.99990844726562)]

uloc2llh_transform = LocTransform(s_p, t_p, mode='p')

def find_transformation(ptsA, ptsB):
    ptsA, ptsB = np.float32(ptsA), np.float32(ptsB)
    return np.polyfit(ptsA, ptsB, 2)  # 二阶变换就够了，精度为0.2左右。三阶是1.6e-10


s_p, t_p = np.array(s_p), np.array(t_p),
ss = s_p[:, -1], t_p[:, -1]

p = find_transformation(*ss)


def trans_height(point):
    return np.polyval(p, point)

# for sp, tp in zip(*ss):
#     rp = trans_height(sp)
#     print(rp, tp, abs(rp - tp))
# exit()


if __name__ == '__main__':
    # s_p = [(121.50725555419922, 25.037256240844727, 129.9655303955078),
    #        (121.51683044433594, 25.045591354370117, 133.8772735595703),
    #        (121.51410675048828, 25.035709381103516, 139.88731384277344),
    #        (121.5103530883789, 25.04709243774414, 136.99990844726562)]
    #
    # t_p = [(-47417.5058196354, 32863.62318664942, -99706.07427703217),
    #        (49210.60088006227, -59469.33987566117, -99316.92879768088),
    #        (21726.226516528117, 49999.79864655215, -98713.63066229969),
    #        (-16155.398658715128, -76096.97439863194, -99004.74070813507)]

    a_p = [(-12151.73801272729, -67031.5268708564, -109784.99573227018),
           (-12613.696908490672, -65172.22484538179, -109784.88800358027),
           (-13229.638465546012, -63270.667543232776, -109784.78045742959),
           (-13614.605074288263, -61855.06325216811, -109784.65500073507),
           (-9688.036071468085, -68827.4279769681, -109785.19379757345),
           (-7378.332995023518, -68362.58699336868, -109785.02515060827),
           (-5145.619539549513, -67644.20844308879, -109784.8564106971),
           (-3066.883894573837, -67115.99020456742, -109784.70861725509)]

    r_p = [(121.51074981689453, 25.046274185180664, 29.186290740966797),
           (121.51070404052734, 25.046106338500977, 29.185529708862305),
           (121.5106430053711, 25.045934677124023, 29.184814453125),
           (121.51060485839844, 25.045806884765625, 29.18476104736328),
           (121.51099395751953, 25.046436309814453, 29.185802459716797),
           (121.51122283935547, 25.04639434814453, 29.18667984008789),
           (121.51144409179688, 25.046329498291016, 29.187381744384766),
           (121.51165008544922, 25.046281814575195, 29.188167572021484)]

    s_p = np.float32([p[:2] for p in s_p])
    t_p = np.float32([p[:2] for p in t_p])

    a_p = np.float32([p[:2] for p in a_p])
    r_p = np.float32([p[:2] for p in r_p])

    result = LocTransform(s_p, t_p, mode='p').trans_point_list(a_p)
    print(result)
    print('-' * 100)
    diff = np.abs(result - r_p)
    print(diff)
    print('each axis diff')
    print('mean', np.mean(diff, axis=0))
    print('max', np.max(diff, axis=0))
    print('=' * 100)
    diff = np.linalg.norm(result - r_p, axis=1)
    print(diff)
    print('each point diff')
    print('mean', np.mean(diff))
    print('max', np.max(diff))

    print('-' * 100)
    print('each height and diff')
    for sp, tp in zip(*ss):
        rp = trans_height(sp)
        print(rp, tp, abs(rp - tp))
