from data_hub.data_struct.unit import *
import sys
from collections import defaultdict
from data_hub.hub_controller.xx_sim.env_client import EnvClient
from instruction.datatypes import Request
from data_hub.hub_controller.xx_sim.data_trans import *
from typing import *
from instruction.player_brain.player_brain_pb2 import RequestAction
import time
from instruction.Function import Command
from instruction.Function.XXSimLogic import *
from data_hub.utils.watiting_indicator import WaitingIndicator
from data_hub.data_struct.contact import Contact
from sklearn.neighbors import KDTree
from data_hub.backend.send_unit_msg import *
from data_hub.hub_controller.controller import HubController

host, port = '127.0.0.1', str(sys.argv[1] if len(sys.argv) > 1 else 50051)


class XxSimRouter(HubController):
    def __init__(self, host=host, port=port):
        self.env_client = EnvClient(host, port)
        self.env_client.generate_observation(struction_of_obs)
        # self.env_client.execute(XXSimLogic.BehaviourTreeControl())

        self._obs_dict = {}
        self.red_obs: Dict[str: Dict[int: HubUnit]] = {'red': {}, 'blue': {}}  # 这里是obs的指针，数据只做定期跟新。
        self.blue_obs: Dict[str: Dict[int: HubUnit]] = {'red': {}, 'blue': {}}  # 这里是obs的指针，数据只做定期跟新。
        self._req = Request()
        self._obs = {}
        self.cmd_queue = []
        self.side_units_dict = defaultdict(lambda: defaultdict(dict))
        self._side_probed_target = defaultdict(lambda: defaultdict(dict))
        self._pos_2_unit = {}
        self._contact_id_2_unit_id = {}

        self._kd_tree: KDTree = None
        self._kd_inds: list = []
        self._cid2uid_mapping = defaultdict(dict)  # side: {cid: uid}
        self._dead_units = defaultdict(dict)  # side: {uid: unit}
        self._dead_contacts = defaultdict(dict)  # side: {uid: unit}

    def reset(self):
        req = Request()
        req.add(XXSimLogic.Reopen())
        self.env_client.execute(req.actions_request)

    def send_cmd(self, cmd_queue: list):
        self.identify_cmd(cmd_queue)

    def step(self):
        if self.cmd_queue:
            self.send_cmd(self.cmd_queue)
        if self._req.actions_request.request.entities:
            self.env_client.execute(self._req.actions_request)
            self._req.actions_request = RequestAction()
            self._req.actions_request.request.name = "ACTION"
        time.sleep(0.001)  # todo 指令处理和数据更新的间隔不同，最好是异步的
        # self.update_obs()

    def get_obs(self):
        self.update_obs()
        return self.side_units_dict

    def update_obs(self):

        t = time.time()
        # check and reset obs setting
        wi = WaitingIndicator('Unit key not found')

        # 处理仿真异常或者掉线的问题，直接等待
        while True:
            obs = self.env_client.get_observation()
            if 'Unit' in struction_of_obs:
                if 'OBS' in obs and 'Unit' in obs['OBS']:
                    unit_data = obs['OBS']['Unit']
                    if unit_data:
                        for k in struction_of_obs['Unit'].keys():
                            nm = {'Sensor', 'Sensors', 'Command', 'OverlapDetection'}
                            if k in nm:
                                continue
                            if k not in unit_data[0]:
                                wi.print_next(k)
                                self.env_client.generate_observation(struction_of_obs)
                                break
                        else:
                            wi.print_end()
                            break
                        time.sleep(0.1)
                        continue
                else:
                    if 'OBS' not in obs:
                        wi.print_next('OBS')
                    elif 'Unit' not in obs['OBS']:
                        wi.print_next('Unit')
                    else:
                        wi.print_next()
                    self.env_client.generate_observation(struction_of_obs)
                    time.sleep(0.1)
                    continue
            wi.print_end()
            break
        # print('obs_check time spent:', time.time() - t)
        self._obs_dict = obs
        obs_dict = dictData2unitsData(self._obs_dict)

        last_u2c = {side: {v: k for k, v in data.items()} for side, data in self._cid2uid_mapping.items()}

        '判断死亡，从后台拿数据，突然没了就是死了。 现在死了不删除数据，只是将单位状态改为死亡'
        diff_keys = set(self._obs.keys()).difference(obs_dict.keys())
        for k in diff_keys:
            u: HubUnit = self._obs[k]
            u.unit_state = u.unit_state.destroyed
            u.health = 0
            self._dead_units[u.side][u.unit_id] = u

            for side, u2c in last_u2c.items():
                if u.side != side and u.unit_id in u2c:
                    self._dead_contacts[side][u2c[u.unit_id]] = u

        if diff_keys:
            print('destroyed', diff_keys)

        # 对应死亡的敌方单位，对方死亡的同时也会失去目标。在这里通过对比上下帧数据来找到
        # for side, data in self._cid2uid_mapping.items():
        #     uid2cid = {uid: cid for cid, uid in data.items()}
        #     for uid, cid in uid2cid.items():
        #         if uid in diff_keys:
        #             self._dead_contacts[side][cid] = self._obs[uid]

        for k, d in obs_dict.items():  # 注意红蓝key不重叠
            u: HubUnit = self._obs.get(k)
            if u is None:
                u = HubUnit()._update_from_dict(d)
                u._cmd_queue = self.cmd_queue
                self._obs[k] = u
                self.side_units_dict[u.side][Side.our_side][u.unit_id] = u  # 这里先建立每个视角下自己方的单位

                # if u.side == u.side.red:
                #     self.red_obs['red'][k] = u
                #     self.blue_obs['red'][k] = u
                # else:
                #     self.red_obs['blue'][k] = u
                #     self.blue_obs['blue'][k] = u
            else:
                u._update_from_dict(d)

        p_ratio = np.array([100000, 100000, 1])
        self.kd_inds, kd_points = zip(*[(uid, unit.loc._trans2dict() * p_ratio) for uid, unit in self._obs.items()])
        self._kd_tree = KDTree(kd_points)

        # 更新各方的侦察数据
        self._side_probed_target.clear()
        for uid, unit_data in obs_dict.items():
            self._side_probed_target[unit_data['side']].update(unit_data['probed_target'])
            unit_data['probed_target'] = list(unit_data['probed_target'].keys())

        # 距离匹配target和unit
        self._cid2uid_mapping = defaultdict(dict)
        for side, side_probed_target in self._side_probed_target.items():
            if not side_probed_target:
                self.side_units_dict[side][Side.other_side] = {}
                continue
            contact_id_list, contact_loc_list = zip(
                *((k, v['LLHLocation'] * p_ratio) for k, v in side_probed_target.items()))
            contact_dis_list, unit_ind_list = self._kd_tree.query(contact_loc_list, k=1)  # 怎么样都能找到一个最近的单位
            contact_dis_list, unit_ind_list = contact_dis_list.flatten(), unit_ind_list.flatten()
            dis_verge = 0.1
            for i, contact_dis in enumerate(contact_dis_list):
                # if dis < dis_verge:  # todo 如果没找到咋办
                contact_id = contact_id_list[i]
                unit_id = self.kd_inds[unit_ind_list[i]]
                self._cid2uid_mapping[side][contact_id] = unit_id
            self.side_units_dict[side][Side.other_side] = {
                cid: self._obs[uid] for cid, uid in self._cid2uid_mapping[side].items()}
            self.side_units_dict[side][Side.other_side].update(self._dead_contacts[side])

        # # todo 如何结构化的记录敌方数据。
        # for side, side_unit_dict in self.side_units_dict.items():
        #     side_unit_dict[Side.other_side] = {
        #         ind for u in side_unit_dict[Side.our_side].values() for ind in u.probed_target if u.probed_target}
        self.red_obs['red'] = self.side_units_dict[UnitSide.red][Side.our_side]
        self.red_obs['blue'] = self.side_units_dict[UnitSide.red][Side.other_side]

        self.blue_obs['blue'] = self.side_units_dict[UnitSide.blue][Side.our_side]
        self.blue_obs['red'] = self.side_units_dict[UnitSide.blue][Side.other_side]

    def identify_cmd(self, cmd_queue):
        filtered_cmd_dict = {cmd['unit_id']: cmd for cmd in cmd_queue}
        cmd_queue.clear()
        # todo 处理指令层级的冲突
        # if filtered_cmd_dict:
        #     print("filtered_cmd_dict:", filtered_cmd_dict)

        for unit_id, cmd in filtered_cmd_dict.items():
            if cmd['command_type'] == 1 and cmd['command_subclass'] == 1:
                # 'command_name': '路径导航'
                self.__unit_move_cmd(cmd)
            if cmd['command_type'] == 2 and cmd['command_subclass'] == 3:
                # 'command_name': '目标打击'
                self.__unit_attack_cmd(cmd)
            # ---- 遥操作 ----
            if cmd['command_type'] == 3:
                # 3: 运动模式;
                pass
            if cmd['command_type'] == 4:
                # 4: 前后移动;
                pass  # todo
            if cmd['command_type'] == 5:
                # 5: 紧急刹车;
                pass  # todo
            if cmd['command_type'] == 6:
                # 6: 转向移动;
                pass  # todo
            if cmd['command_type'] == 7:
                # 7: 左右平移;
                pass
            if cmd['command_type'] == 8:
                # 8: 升降移动;
                pass
            if cmd['command_type'] == 9:
                # 9: 俯仰控制;
                pass  # todo
            if cmd['command_type'] == 10:
                # 10: 横摆控制;
                pass  # todo
            if cmd['command_type'] == 11:
                # 11: 开关控制;
                pass  # todo
            if cmd['command_type'] == 12:
                # 12: 开火模式;
                pass
            if cmd['command_type'] == 13:
                # 13: 弹药切换;
                pass
            if cmd['command_type'] == 14:
                # 14: 速度设置;
                pass
            if cmd['command_type'] == 15:
                # 15: 航向设置;
                pass
            if cmd['command_type'] == 16:
                # 16: 终止所有动作;
                unit_id = cmd['unit_id']
                self._req.add(Command.Stop(unit_id))
            if cmd['command_type'] == 17:
                self.__unit_attack_to_llh(cmd)
            if cmd['command_type'] == 18:
                # 18: 控制行为树是否开启（自动攻击）
                self.__unit_behavior_tree_pause(cmd)

        # if filtered_cmd_dict:
        #     print('exec action:', self._req.actions_request)

    def __unit_move_cmd(self, cmd):
        unit_id = cmd['unit_id']
        path = cmd['command_params']['maneuver_point']
        # transP2LLH = lambda p: [p['lon'], p['lat'], p['alt']]
        unit: HubUnit = self._obs.get(unit_id, None)
        if unit is None:
            logging.warning('unit id not found: {}'.format(unit_id))
            return
        # transP2LLH = lambda p: [p['lon'], p['lat'], 30.0 if unit.type in [301] else unit.loc.alt]
        # transP2LLH = lambda p: [p['lat'], p['lon'], 30.0]
        if len(path) == 1:
            point = path[0]
            if 'alt' not in point:
                cmd = Command.GoToLLH(unit_id, [point['lon'], point['lat']], AutoHeight=True)
            else:
                cmd = Command.GoToLLH(unit_id, [point['lon'], point['lat'], point['alt']])
            # llh = transP2LLH(path[0])
            # print(llh)
            # self._req.add(Command.GoToPosition(unit_id, llh))
            self._req.add(cmd)
        else:  # fixme 需要测试，可能有bug，目前暂时不支持多点输入
            first_point = True
            for llh in path:
                point = llh
                if 'alt' not in point:
                    cmd = Command.GoToLLH(unit_id, [point['lon'], point['lat']], AutoHeight=True)
                else:
                    cmd = Command.GoToLLH(unit_id, [point['lon'], point['lat'], point['alt']])
                if first_point:
                    self._req.add(cmd)
                    first_point = False
                else:  # fixme 可能有bug
                    entity = DoAction(entity_id=unit_id, ActionName="Command", Arguments="-CommandName BYMoveToCommand")
                    entity.entities.append(MakeLLHLocation("Location", llh))
                    self._req.add(entity)

    def __unit_attack_cmd(self, cmd):
        unit_id = cmd['unit_id']
        target_id = cmd['command_params']['target_id']
        move_while_attack = cmd['command_params']['move_while_attack'] \
            if 'move_while_attack' in cmd['command_params'] else False
        self._req.add(Command.AttackToUID(unit_id, target_id, move_while_attack=move_while_attack))

    def __unit_attack_to_llh(self, cmd):
        unit_id = cmd['unit_id']
        llh = cmd['command_params']['llh']
        move_while_attack = cmd['command_params']['move_while_attack']
        self._req.add(Command.AttackToLLHPosition(unit_id, llh, move_while_attack=move_while_attack))

    def __unit_behavior_tree_pause(self, cmd):
        unit_id = cmd['unit_id']
        is_pause = cmd['command_params']['is_pause']
        self._req.add(XXSimLogic.BehaviourTreeControl(unit_id, is_pause))


if __name__ == '__main__':
    env = XxSimRouter(host, port)

    env.update_obs()
    obs_dict = env.red_obs

    u1: HubUnit = obs_dict['red'][4]
    u2: HubUnit = obs_dict['red'][1]

    u1.move_to_llh(u2.loc)

    env.step()

    # for unit in env.obs:
    #     unit: HubUnit
    #     unit.unit_id

    # with open('obs_data.json', 'w') as f:
    #     json.dump(obs_dict, f)
    # print(obs_dict)
    # exit()
    #
    # for entity in obs.entities:
    #     entity: Entity
    #     print(entity)

    # -109770
    # print('======' * 10)

    # Unreal2LLH_Position([*loc, ])
