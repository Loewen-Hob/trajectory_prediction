from data_hub.data_struct.meta_data import *


class UnitState(HubIntEnum):
    perfect = 0
    destroyed = 1
    impaired = 2


class UnitSubtype(HubIntEnum):
    pass


class GroundSubtype(UnitSubtype):
    ZTZ99A = 1


class AirSubtype(UnitSubtype):
    DKTJPT = 9


class UnitType(HubIntEnum):
    ground = 301
    air = 117


class UnitSide(HubIntEnum):
    red = 0
    blue = 1


class Side(HubIntEnum):
    our_side = 0
    other_side = 1
