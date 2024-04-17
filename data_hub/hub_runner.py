import time
from drill.pipeline.interface import ObsData

from data_hub.hub_controller.xx_sim.sim_router import XxSimRouter
from data_hub.data_struct.unit import *
from data_hub.backend.send_unit_msg import *
from data_hub.backend.read_command_stream import consume_command
from data_hub.backend.send_unit_command import send_command
from data_hub.backend.analysis_recv_cmd import analysis_cmd
from data_hub.utils.watiting_indicator import WaitingIndicator
from collections import defaultdict
from data_hub.hub_player import HubPlayer
from data_hub.hub_controller.controller import HubController
import threading

import logging

default_ip = "127.0.0.1"
# default_ip = "192.168.1.101"
default_port = 50051


class HubRunner:
    """
    这里作为新的流程管理器，集合各个系统的功能和逻辑流转
    """

    def __init__(self, ip=default_ip, port=default_port) -> None:
        self._env: HubController = XxSimRouter(ip, port)
        self.last_time = time.time()
        self.wi = WaitingIndicator('updating obs')
        self.wi.on = False
        self.last_send_id = defaultdict(lambda: defaultdict(dict))
        self.last_cmd_id = 1

        # todo tmp 临时这么跳转obs的获取
        self.red_obs = self._env.red_obs
        self.blue_obs = self._env.blue_obs
        self.side_obs = self._env.side_units_dict

        self.all_players = []
        self.uid2cmd = {}

        # self.player_thread = threading.Thread(target=self.run_players)
        # self.player_thread.setDaemon(True)
        self._player_start = True

        self._unit_ai_ctrl = defaultdict(dict)  # {unit_side: {uid: True/False}}

    def reset(self, reset_scenario=False) -> dict[str, ObsData]:
        # 实际使用应该没有重置的需求，这里先给训练留着
        if reset_scenario:
            self._env.reset()
        self._env.step()
        for player in self.all_players:
            player: HubPlayer
            player.reset(self.side_obs[player.player_side])

    def run_players(self):
        # 这里是runner的逻辑，理论上不应该出现在这里，先临时放着
        for player in self.all_players:
            player: HubPlayer
            obs = self.side_obs[player.player_side]
            unit: HubUnit
            obs = {side: {uid: unit for uid, unit in side_data.items()
                          if unit.unit_state != unit.unit_state.destroyed}
                   for side, side_data in obs.items()}
            player.step(obs)

    def start_players(self):
        self._player_start = True

    def send_ai_cmd(self):
        for side in [UnitSide.red]:  # 显示红方单位的指令
            unit_obs = self.side_obs[side][Side.our_side]
            unit: HubUnit

            cmd_dict = {}
            for uid, unit in unit_obs.items():
                if unit.unit_state == unit.unit_state.destroyed:
                    continue
                cmd = unit._curr_cmd
                if cmd == ... or 'command_subclass' not in cmd:
                    continue
                last_cmd = self.uid2cmd.get(cmd['unit_id'], {})
                if str(last_cmd) == str(cmd):
                    continue
                self.uid2cmd[cmd['unit_id']] = cmd

                cmd = {**cmd}
                cmd['command_id'] = self.last_cmd_id
                cmd['command_control_party'] = 0
                self.last_cmd_id += 1
                # fixme: 临时处理，单位id映射
                cmd['unit_id'] = unit_id_mapping[cmd['unit_id']]
                # fixme: 临时处理，位置矫正,仿射变换
                if 'command_params' in cmd and 'maneuver_point' in cmd['command_params']:
                    for point_data in cmd['command_params']['maneuver_point']:
                        llh = point_data['lon'], point_data['lat'], point_data['alt']
                        llh = (*m.dot([*llh[:2], 1]).tolist(), llh[2])
                        point_data['lon'], point_data['lat'], point_data['alt'] = llh
                cmd_dict[cmd['unit_id']] = cmd
                self._unit_ai_ctrl[unit.side][unit.unit_id] = True
            send_command(cmd_dict)

    def step(self):
        # self.handle_agent_action(action_dict)
        self.handle_client_cmd()

        self._env.step()
        self._env.update_obs()
        # t.get_spend_time('_env.step')

        self.wi.print_next()
        if self._player_start:
            self.run_players()

        # t.get_spend_time('player.step')
        # print('-' * 100)
        self.send_ai_cmd()

        # 向前端推送udp数据  红方视角
        self.send_unit_state2client(UnitSide.red)

    def handle_client_cmd(self):

        # step1 消费指令
        cmd_queue = consume_command()

        # step2 todo 解析指令
        rec_cmd = analysis_cmd(cmd_queue)
        # rec_cmd = cmd_queue

        # step3 todo 判断指令合法性
        cmd_dict = {}
        for cmd in rec_cmd:
            # todo if 合法
            cmd_dict[cmd['unit_id']] = cmd

        # step4 回复指令
        if cmd_dict:
            send_command(cmd_dict)
            # todo send_log

        # step5 存储指令
        # 目前只对接红方的控制指令 todo 蓝方id对齐和 contact 对齐
        for unit_id, cmd in cmd_dict.items():
            if unit_id not in unit_id_mapping_reversed:
                logging.warning(f'错误的unit_id: {unit_id}')  # fixme 手动转换
                continue

            curr_side = UnitSide.red
            if curr_side in self.obs:
                unit_dict: dict[int: HubUnit] = self.obs[curr_side][Side.our_side]
                hash_unit_id = unit_id_mapping_reversed[unit_id]
                cmd = {**cmd}
                cmd['unit_id'] = hash_unit_id  # fixme 手动转换t
                if hash_unit_id in unit_dict:
                    unit: HubUnit = unit_dict[hash_unit_id]
                    unit.apply_cmd(cmd)
                else:
                    logging.warning(f'错误的unit_id: {unit_id}')

    def send_unit_state2client(self, side: UnitSide):  # todo 放在前端单独处理，因为是前端引发的问题
        side_obs = self._env.side_units_dict[side]
        for name in [Side.our_side, Side.other_side]:
            obs = side_obs[name]
            uids = [u.unit_id for u in obs.values()]
            # if uids and name == 'other_side':
            #     print(uids)
            diff_id = set(self.last_send_id[side][name]).difference(uids)
            # if diff_id:
            #     print('diff_id', diff_id)
            additional_data = {
                'off_show': diff_id,
                'ai_control': [unit_id_mapping[uid] for uid, value in self._unit_ai_ctrl[side].items() if value],
            }
            unit_list = list(obs.values()) + [self._env._obs[did] for did in diff_id]
            send_unit_info(unit_list, additional_data)
            self.last_send_id[side][name] = set(uids)


if __name__ == '__main__':
    import time
    from players.rule_player import RedRulePlayerV1, RedRulePlayerV2, BlueRulePlayerV2

    env = HubRunner()
    env.reset(reset_scenario=True)
    # env.all_players = [
    #     RedRulePlayerV1('test_red', UnitSide.red),
    #     HubPlayer('test_blue', UnitSide.blue),
    # ]
    env.all_players = [
        RedRulePlayerV2('test_red', UnitSide.red),
        BlueRulePlayerV2('test_blue', UnitSide.blue)
    ]
    while True:
        env.step()
        time.sleep(0.001)
