from instruction.Function import XXSimLogic, Command
from data_hub.data_struct.meta_data import *
from data_hub.data_struct.enum_types import *
from data_hub.data_struct.vectors import *
from data_hub.utils.loc_transform import *
from data_hub.data_struct.components import *

class HubUnit(HubMetaData):
    unit_id: int = ...  # 单位编号

    side: UnitSide = ...
    # 类型
    type: UnitType = ...
    subtype: int = ...

    # 状态
    unit_state: UnitState = ...  # 单位状态
    health: int = ...  # 完好程度

    comm_quality: int = ...  # 信号强度
    oil_power: int = ...  #
    electricity_power: int = ...  #
    is_firing: bool = ...
    vel: float = ...  # 实体速度

    # 姿态
    turret_rot: HubRotation = ...  #
    rot: HubRotation = ...  #
    loc: HubLocation = ...  #
    uloc: HubLocation = ...  # fixme 临时用的ue location

    # 任务相关
    command_state: int = ...
    command_id: int = ...
    command_control_party: int = ...

    # 侦察信息
    probed_target: list = ...  # 观测到的敌方单位id

    # 指令缓存
    _cmd_queue: list[dict] = ...  # 需要通知的指令队列
    _curr_cmd: dict = ...  # 当前在做的主指令，需要处理冲突逻辑，并且处理主次。
    # TODO：临时解决获取当前正在做的仿真指令
    current_command: str = ...

    # 武器信息
    weapons: list[Weapon] = ...

    # 辅助信息
    collide: int = ...
    unit_size: list[float] = ...

    def apply_cmd(self, cmd):
        self._curr_cmd = cmd
        self._cmd_queue.append(cmd)

    def __move_to_cmd_dict(self, path):
        cmd = {
            'command_id': 14969,  # todo 外部写入时处理
            'unit_id': self.unit_id,
            'control_type': 1,  # todo 外部写入时处理
            'control_mode': 3,  # todo 外部写入时处理
            'command_params': {
                'maneuver_point': path,
            },
            'command_name': '路径导航',  # todo 协议对齐
            'command_type': 1,  # todo 协议对齐
            'command_subclass': 1  # todo 协议对齐
        }
        self.apply_cmd(cmd)

    def move_to_llh(self, llh, auto_height='auto'):
        """
        llh: 经纬度
        auto_height: 自动补齐高度。可以为auto / True / False
            auto模式下，len(llh) == 2 的时候为自动补齐高度；len(llh) == 3 的时候为指定高度。
            True模式下，强制自动高度。
            False模式下，强制指定高度，若没传高度则指定自身高度。
        """
        if isinstance(llh, HubLocation):
            llh = llh._trans2dict()
        if (auto_height == 'auto' and len(llh) == 2) or auto_height == True:
            llh = {'lon': llh[0], 'lat': llh[1]}
        elif auto_height in ('auto', False):
            if len(llh) == 3:
                llh = {'lon': llh[0], 'lat': llh[1], 'alt': llh[2]}
            elif len(llh) == 2:
                llh = {'lon': llh[0], 'lat': llh[1], 'alt': self.loc.alt}
            else:
                raise ValueError('llh: {}'.format(llh))
        else:
            raise ValueError('auto_height: {}'.format(auto_height))
        self.__move_to_cmd_dict([{'spd': 60, 'dir': 0, 'mode': 0, **llh}])

    def move_to_uloc(self, uloc, auto_height='auto'):  # fixme 不应该有这么个接口，智能体临时需要。
        if isinstance(uloc, HubLocation):
            uloc = uloc._trans2dict()

        llh = uloc2llh_transform.trans_point(uloc[:2])
        if len(uloc) == 3:
            llh = list(llh) + [trans_height(uloc[2])]
        self.move_to_llh(llh, auto_height)
        # llh = {'lon': llh[0], 'lat': llh[1], 'alt': trans_height(uloc[2])}
        # self.__move_to_cmd_dict([{'spd': 60, 'dir': 0, 'mode': 0, **llh}])

    def move_to_llh_path(self, llh_list, auto_height='auto'):  # todo 有问题，还没测试好
        path = []
        for llh in llh_list:
            if isinstance(llh, HubLocation):
                llh = llh._trans2dict()
            if (auto_height == 'auto' and len(llh) == 2) or auto_height == True:
                llh = {'lon': llh[0], 'lat': llh[1]}
            elif auto_height in ('auto', False):
                if len(llh) == 3:
                    llh = {'lon': llh[0], 'lat': llh[1], 'alt': llh[2]}
                elif len(llh) == 2:
                    llh = {'lon': llh[0], 'lat': llh[1], 'alt': self.loc.alt}
                else:
                    raise ValueError('llh: {}'.format(llh))
            else:
                raise ValueError('auto_height: {}'.format(auto_height))
            path.append({'spd': 60, 'dir': 0, 'mode': 0, **llh})
        self.__move_to_cmd_dict(path)

    def attack_target(self, target, move_while_attack=False):
        # if isinstance(target, HubUnit):
        #     target = target.unit_id
        # self._req.add(Command.AttackToUID(self.unit_id, target))

        # {1: {'command_id': 14967, 'unit_id': 1, 'control_type': 1, 'control_mode': 3,
        #      'command_params': {'target_id': 13, 'weapon_id': 0, 'mode': 0, 'num': 0, 'dis': 0},
        #      'command_name': '目标打击', 'command_type': 2, 'command_subclass': 3}}
        if isinstance(target, HubUnit):
            target = target.unit_id
        cmd = {
            'command_id': 14967,  # todo 外部写入时处理
            'unit_id': self.unit_id,
            'control_type': 1,  # todo 外部写入时处理
            'control_mode': 3,  # todo 外部写入时处理
            'command_params': {
                'target_id': target,
                'move_while_attack': move_while_attack,
                'weapon_id': 0,  # todo 规则补齐
                'mode': 0,  # todo 规则补齐
                'num': 0,  # todo 规则补齐
                'dis': 0,  # todo 规则补齐
            },
            'command_name': '目标打击',  # todo 协议对齐
            'command_type': 2,  # todo 协议对齐
            'command_subclass': 3  # todo 协议对齐
        }
        self.apply_cmd(cmd)

    def set_auto_attack(self, auto_attack: bool):
        cmd = {
            'unit_id': self.unit_id,
            'command_params': {
                'is_pause': auto_attack
            },
            'command_type': 18
        }
        self.apply_cmd(cmd)

    def stop(self):
        cmd = {
            'unit_id': self.unit_id,
            'command_type': 16
        }
        self.apply_cmd(cmd)

    def attack_to_llh(self, llh, move_while_attack=False):
        cmd = {
            'unit_id': self.unit_id,
            'command_type': 17,
            'command_params': {
                'llh': llh,
                'move_while_attack': move_while_attack
            }
        }
        self.apply_cmd(cmd)


if __name__ == "__main__":
    unit = HubUnit()._update_from_dict(
        {'unit_id': 7, 'loc': [121.51368713378906, 25.04267120361328, 137.98782348632812],
         'rot': [2.1919780124335375e-07, -4.568394797388449e-05, 88.93510638196706], 'health': 100.0,
         'uloc': [17490.331931313558, -27120.355879439376, -98902.02435711399], 'type': 117, 'subtype': 23,
         'vel': 1.0872842531129784e+67, 'side': 1, 'probed_target': [1, 2, 3, 4],
         'turret_rot': [0, 1.3649459902368376e-19, 3.975693351829395e-16]})
    unit.unit_state = unit.unit_state.perfect
    print('unit', unit)
    d = unit._trans2dict()
    print('unit_dict', d)
    import json

    d = json.dumps(d)
    print('unit_json', d)
    u = HubUnit()._update_from_dict(json.loads(d))
    print('new_unit', u)
