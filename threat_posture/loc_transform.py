import cv2
import numpy as np


class LocTransform:
    def __init__(self, source_points, target_points, mode='a'):
        source_points = np.float32(source_points)
        target_points = np.float32(target_points)
        source_xy = np.float32([p[:2] for p in source_points])
        target_xy = np.float32([p[:2] for p in target_points])

        self.__point_dim = len(source_points[0])
        if self.__point_dim == 3:
            self._h_trans = np.polyfit(source_points[:, -1], target_points[:, -1], 1)  # 二阶变换就够了，精度为0.2左右。三阶是1.6e-10
            self._inv_h_trans = np.polyfit(target_points[:, -1], source_points[:, -1], 1)  # 二阶变换就够了，精度为0.2左右。三阶是1.6e-10
        elif self.__point_dim != 2:
            raise ValueError('point dimension error', self.__point_dim)

        self.__mode = mode
        if self.mode == 'a':
            self._m = cv2.getAffineTransform(source_xy[:3], target_xy[:3])
            self._inv_m = np.linalg.inv(np.vstack([self._m, [0, 0, 1]]))[:2, :]
        elif self.mode == 'p':
            self._m = cv2.getPerspectiveTransform(source_xy[:4], target_xy[:4])
            self._inv_m = np.linalg.inv(self._m)
        else:
            raise ValueError('mode error:', mode)

    def trans_point(self, point):
        result = self._cal_point(point, self._m).tolist()
        if self.__point_dim == 2 or len(point) == 2:
            return result
        return result + [np.polyval(self._h_trans, point[-1])]

    def inverse_point(self, point):
        result = self._cal_point(point, self._inv_m).tolist()
        if self.__point_dim == 2 or len(point) == 2:
            return result
        return result + [np.polyval(self._inv_h_trans, point[-1])]

    def _cal_point(self, point, m):
        result = m.dot([*point[:2], 1])
        if self.mode == 'a':
            return result
        if self.mode == 'p':
            return result[:2] / result[2]

    def trans_point_list(self, point_list):
        point_list = np.array(point_list)
        result = self._cal_point_list(point_list, self._m)
        if self.__point_dim == 2 or len(point_list[0]) == 2:
            return result.tolist()
        return np.hstack([result, np.polyval(self._h_trans, point_list[:, 2])[:, np.newaxis]]).tolist()

    def inverse_point_list(self, point_list):
        point_list = np.array(point_list)
        result = self._cal_point_list(point_list, self._inv_m)
        if self.__point_dim == 2 or len(point_list[0]) == 2:
            return result.tolist()
        return np.hstack([result, np.polyval(self._inv_h_trans, point_list[:, 2])[:, np.newaxis]]).tolist()

    def _cal_point_list(self, point_list, m):
        point_list = np.float32([p[:2] for p in point_list])
        points_matrix = np.hstack((point_list, np.ones((point_list.shape[0], 1))))
        result = np.dot(points_matrix, m.T)
        if self.mode == 'a':
            return result[:, :2]
        if self.mode == 'p':
            return result[:, :2] / result[:, 2, np.newaxis]

    @property
    def mode(self):
        return self.__mode


reference_points = [
    [
        (-47417.5058196354, 32863.62318664942, -99706.07427703217),
        (121.50725555419922, 25.037256240844727, 129.9655303955078),
    ],
    [
        (49210.60088006227, -59469.33987566117, -99316.92879768088),
        (121.51683044433594, 25.045591354370117, 133.8772735595703),
    ],
    [
        (21726.226516528117, 49999.79864655215, -98713.63066229969),
        (121.51410675048828, 25.035709381103516, 139.88731384277344),
    ],
    [
        (-16155.398658715128, -76096.97439863194, -99004.74070813507),
        (121.5103530883789, 25.04709243774414, 136.99990844726562),
    ],
]

if __name__ == '__main__':
    print('=-'*100)
    print('uloc2llh')
    uloc2llh = LocTransform(*zip(*reference_points), mode='p')
    print(uloc2llh.trans_point(reference_points[0][0]))
    print(uloc2llh.inverse_point(reference_points[0][1]))
    print(uloc2llh.trans_point_list([d[0] for d in reference_points]))
    print(uloc2llh.inverse_point_list([d[1] for d in reference_points]))

    print('=-'*100)
    print('llh2mloc')
    mloc = [[1958, 881], [2214, 7383], [13116, 896], [13145, 7656]]
    llh = [[121.507167, 25.037037], [121.51402, 25.0356223], [121.510275, 25.047642], [121.517365, 25.04594]]
    llh2mloc = LocTransform(llh, mloc)
    print(llh2mloc.trans_point((121.507167, 25.037037, 29.186290740966797)))

    print('=-'*100)
    print('llh2mloc')
    mloc = [[1958, 881], [2214, 7383], [13116, 896], [13145, 7656]]
    uloc = [[-48341.55514966407, 35293.61137836185], [20879.270770204294, 50971.807941216415], [-16925.256602461384, -82181.57705313397], [54599.84493756958, -63335.61025009134]]
    mloc2uloc = LocTransform(mloc, uloc)
    print(llh2mloc.trans_point((1958, 881)))

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
    print('=-'*100)
    print('=== test uloc2llh ===')
    result = uloc2llh.trans_point_list(a_p)
    print(result)
    result = np.array(result)
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

    print('-=' * 100)

    print('=== test llh2uloc ===')
    result = uloc2llh.inverse_point_list(r_p)
    result = np.array(result)
    print(result)
    print('-' * 100)
    diff = np.abs(result - a_p)
    print(diff)
    print('each axis diff')
    print('mean', np.mean(diff, axis=0))
    print('max', np.max(diff, axis=0))
    print('=' * 100)
    diff = np.linalg.norm(result - a_p, axis=1)
    print(diff)
    print('each point diff')
    print('mean', np.mean(diff))
    print('max', np.max(diff))

    print('-' * 100)
