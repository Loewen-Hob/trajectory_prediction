from data_hub.hub_controller.controller import HubController
from data_hub.data_struct.unit import *
import json
import time
import rclpy
from rclpy.node import Node
from std_msgs.msg import String
import threading
from data_hub.utils.loc_transform import *
from data_hub.hub_controller.roblab.getjson import *
from data_hub.hub_controller.roblab.sendjson import *

left_top = [-4.0, 3.0, 0]
right_top = [4.0, 3.0, 0]
left_down = [-4.0, -3.0, 0]
rightdown = [4.0, -3.0, 0]

s_p = [left_top, left_down, right_top, rightdown]

t_p = [
    [121.507167, 25.037037, 29.33],  # left top
    [121.51402, 25.0356223, 29.33],  # left bottom
    [121.510275, 25.047642, 29.33],  # right top
    [121.517365, 25.04594, 29.33],  # right bottom
]

# t_p = [
#     [121.507167, 25.037037, 29.33],  # left top
#     [121.51402, 25.0356223, 29.33],  # left bottom
#     [121.510275, 25.047642, 29.33],  # right top
#     [121.517365, 25.04594, 29.33],  # right bottom
# ]


def ros_spin(node):
    rclpy.spin(node)


# class StringSubscriber(Node):

#     def __init__(self):
#         super().__init__('string_subscriber')
#         self.subscription = self.create_subscription(
#             String,
#             '/json',
#             self.listener_callback,
#             10)
#         self.subscription  # prevent unused variable warning
#         self.data = None

#     def listener_callback(self, msg):
#         # self.get_logger().info('I heard: "%s"' % msg.data)
#         self.data = msg.data


class Client(HubController):
    def __init__(self, ip, port):
        rclpy.init()  # Initialize RCLPY
        self.json_subscriber = StringSubscriber()
        ros_thread = threading.Thread(target=ros_spin, args=(self.json_subscriber,))
        ros_thread.start()

        self.json_publisher = GoalPublisher()
        # ros_thread1 = threading.Thread(target=ros_spin, args=(self.json_publisher,))
        # ros_thread1.start()

        self._cloc2loc_m = LocTransform(s_p, t_p)
        self._loc2cloc_m = LocTransform(t_p, s_p)
        self._cmd_queue = []

    def get_obs(self):
        pass
        # todo recv obs
        obs = {
            'red': {
                7: {
                    'unit_id': 7,
                    # 'loc': (121.5102920532, 25.04561233520, 130.0),
                    'loc': left_top,
                    # 经纬高坐标。lon, lat, alt
                    'rot': (0.005366216815588132, -0.0015056756458803893, 89.99929643199312),
                    # 车身朝向 roll, pitch, yaw
                    'health': 100.0,  # 血量，没有可以不填
                    'type': 117,  # 类型，没有可以不填
                    'subtype': 23,  # 子类型，没有可以不填
                    'vel': 1.0872842531129784e+67,  # 标量速度
                    'side': 0,  # 归属方 0:红方， 1: 蓝方
                    'probed_target': {},
                    'turret_rot': (-0.0, 0.0, 0.0),  # 炮台相对车身的朝向
                    'current_command': 'idle',  # 当前指令状态，是空闲或者在做什么指令。比如可以写‘idle'/'moving'
                },
            },
            'blue': {}
        }
        obs = json.dumps(obs)
        
        unit_json = {
                    'unit_id': 7,
                    # 'loc': (121.5102920532, 25.04561233520, 130.0),
                    'loc': left_top,
                    # 经纬高坐标。lon, lat, alt
                    'rot': (0.005366216815588132, -0.0015056756458803893, 89.99929643199312),
                    # 车身朝向 roll, pitch, yaw
                    'health': 100.0,  # 血量，没有可以不填
                    'type': 301,  # 类型，没有可以不填
                    'subtype': 50,  # 子类型，没有可以不填
                    'vel': 1.0872842531129784e+67,  # 标量速度
                    'side': 0,  # 归属方 0:红方， 1: 蓝方
                    'probed_target': {},
                    'turret_rot': (0.0, 0.0, 0.0),  # 炮台相对车身的朝向
                    'current_command': 'idle',  # 当前指令状态，是空闲或者在做什么指令。比如可以写‘idle'/'moving'
                }
        obs = self.json_subscriber.data

        obs_dict = {}
        if obs is None:
            return obs_dict
        
        obs = json.loads(obs)
        for side_str, side_obs in obs.items():
            if side_str == 'red':
                side = UnitSide.red
            elif side_str == 'blue':
                side = UnitSide.blue
            else:
                raise Exception('side str error{}'.format(side))
            for d in side_obs.values():
                d['loc'] = list(self._cloc2loc_m.trans_point([n/1000 for n in d['loc']])) + [29.33]
                d['rot'] = (*d['rot'][:2], d['rot'][2] + 90)
            
            unit_data_list = [{**unit_json, **d} for d in side_obs.values()]
            unit_list = [HubUnit()._update_from_dict(d) for d in unit_data_list]
            for unit in unit_list:
                unit._cmd_queue = self._cmd_queue
            obs_dict[side] = {Side.our_side: {u.unit_id: u for u in unit_list}}
            obs_dict[side][Side.other_side] = {}
            # todo other side data
        # print('obs_dict:', obs_dict)
        return obs_dict

    def send_cmd(self, cmd_list):
        """
            'command_type': 1,  # todo 协议对齐
            'command_subclass': 1  # todo 协议对齐
        """
        for cmd in cmd_list:
            
            # cmd = {
            #     'unit_id': 7,
            #     'command_params': {
            #         'maneuver_point': [
            #             (121.4928970336914, 25.027910232543945, 30.2062377929688),
            #         ]
            #     },
            # }
            if 'maneuver_point' in cmd['command_params']:
                print('maneuver_point:', cmd['command_params']['maneuver_point'])
                maneuver_point = [list(self._loc2cloc_m.trans_point([d['lon'], d['lat'], d['alt']])) + [0.] for 
                                         d in cmd['command_params']['maneuver_point']]
                print(maneuver_point)
                maneuver_point = maneuver_point[-1]
                print(maneuver_point)
                cmd_json = {
                    "position": {
                        "x": float(maneuver_point[0]),
                        "y": float(maneuver_point[1]),
                        "z": float(maneuver_point[2]),
                    },
                    "orientation": {
                        "x": 0.0,
                        "y": 0.0,
                        "z": 0.0,
                        "w": 1.0
                    }
                }
                
                cmd_json = json.dumps(cmd_json)
                
                # cmd_json = '''{
                #         "position": {
                #             "x": 1.0,
                #             "y": 2.0,
                #             "z": 0.0
                #         },
                #         "orientation": {
                #             "x": 0.0,
                #             "y": 0.0,
                #             "z": 0.0,
                #             "w": 1.0
                #         }
                #     }'''
                print('cmd_json', cmd_json)
                # print(type(cmd_json))
                self.json_publisher.publish_goal_pose(cmd_json)


    def step(self, *args, **kwargs):
        time.sleep(0.1)
        self.send_cmd(self._cmd_queue)
        self._cmd_queue.clear()

    def reset(self):
        pass


if __name__ == '__main__':
    print('tttttttttttt'*10)
    c = Client(1, 2)
    result = c.get_obs()
    # print('result:', result)
    c.send_cmd([{
                'unit_id': 7,
                'command_params': {
                    'maneuver_point': [
                        (121.4928970336914, 25.027910232543945, 30.2062377929688),
                    ]
                },
            }])