from data_hub.data_struct.unit import *
from data_hub.backend.send_unit_msg import *
from data_hub.backend.read_command_stream import consume_command
from data_hub.backend.send_unit_command import send_command
from data_hub.backend.analysis_recv_cmd import analysis_cmd
from data_hub.utils.watiting_indicator import WaitingIndicator
from collections import defaultdict
from data_hub.hub_player import HubPlayer
from data_hub.hub_controller.controller import HubController
from data_hub.hub_controller.roblab.client import Client

import logging

default_ip = "127.0.0.1"
# default_ip = "192.168.1.101"
default_port = 50051


class HubRunner:
    """
    这里作为新的流程管理器，集合各个系统的功能和逻辑流转
    """

    def __init__(self, ip=default_ip, port=default_port) -> None:
        # self._env: HubController = XxSimRouter(ip, port)
        self._env: HubController = Client(ip, port)

        self.wi = WaitingIndicator('updating obs')
        self.wi.on = False

        self.last_send_id = defaultdict(lambda: defaultdict(dict))

        self.last_time = time.time()
        self.all_players = []
        self.obs = {}

    def reset(self, reset_scenario=False) -> dict:
        # 实际使用应该没有重置的需求，这里先给训练留着
        if reset_scenario:
            self._env.reset()

        self._env.step()
        obs = self._env.get_obs()

        for player in self.all_players:
            player: HubPlayer
            player.step(obs.get(player.player_side, {}))

    def step(self):
        self.handle_client_cmd()

        self._env.step()
        self.obs = self._env.get_obs()

        # 向前端推送udp数据  红方视角
        self.send_unit_state2client(UnitSide.red)

        self.wi.print_next()

        # 这里是runner的逻辑，理论上不应该出现在这里，先临时放着
        for player in self.all_players:
            player: HubPlayer
            player.step(self.obs.get(player.player_side, {}))

    def handle_client_cmd(self):
        # t = Timer()
        # step1 消费指令
        cmd_queue = consume_command()
        # (t.get_spend_time('consume_command'))
        # step2 todo 解析指令
        rec_cmd = analysis_cmd(cmd_queue)
        # (t.get_spend_time('analysis_cmd'))
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
        # (t.get_spend_time('send_command'))

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
        side_obs = self.obs[side]
        for name in [Side.our_side, Side.other_side]:
            obs = side_obs[name]
            uids = [u.unit_id for u in obs.values()]
            # if uids and name == 'other_side':
            #     print(uids)
            diff_id = set(self.last_send_id[side][name]).difference(uids)
            # if diff_id:
            #     print('diff_id', diff_id)
            send_unit_info(list(obs.values()) + [self._env._obs[did] for did in diff_id], diff_id)
            self.last_send_id[side][name] = set(uids)


if __name__ == '__main__':
    import time
    # from players.rule_player import RedRulePlayerV2, BlueRulePlayerV2

    env = HubRunner()
    env.reset(reset_scenario=True)
    # env.all_players = [
    #     RedRulePlayerV1('test_red', UnitSide.red),
    #     HubPlayer('test_blue', UnitSide.blue),
    # ]
    env.all_players = [
        # RedRulePlayerV2('test_red', UnitSide.red),
        # BlueRulePlayerV2('test_blue', UnitSide.blue)
    ]
    while True:
        env.step()
        time.sleep(0.001)
