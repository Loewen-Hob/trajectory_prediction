from data_hub.data_struct.enum_types import *
from data_hub.data_struct.vectors import *
from data_hub.data_struct.meta_data import *


class Contact(HubMetaData):  # 接触单位
    contact_id: int = ...  # 接触单位id

    side: UnitSide = ...  # 单位归属推测
    type: UnitType = ...  # 单位类型推测
    subtype: int = ...  # 单位类型推测
    unit_state: UnitState = ...  # 单位状态
    health: int = ...  # 完好程度
    is_firing: bool = ...  # 是否正在开火
    vel: float = ...  # 实体速度

    turret_rot: HubRotation = ...  # 炮台相对朝向
    loc: HubLocation = ...  # 位置
    rot: HubRotation = ...  # 姿态

    command_state: int = ...  # 推测指令状态
