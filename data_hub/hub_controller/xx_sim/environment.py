import os
import time
from enum import Enum
import sys
from instruction.Function.XXSimLogic import *
from instruction.player_brain.player_brain_client import PlayerBrainClient

from instruction.player_brain.player_brain_pb2 import RequestAction, RequestObservation
from instruction.Function.Command import *
from instruction.Function.KeyboardInput import *
from instruction.Function.RayDetection import *

NECESSARY_FIELDS = ["id", "type", "subtype", "pno", "faction", "llh", "location", "rotation", "euler_ned", "islive",
                    "oilWeightg", "velocity", "movetargetllh", \
                    "isinmove", "entstates"]


class FVType(Enum):
    FVT_LONG = 0
    FVT_LONG_ARRAY = 1
    FVT_DOUBLE = 2
    FVT_DOUBLE_ARRAY = 3
    FVT_BYTES = 4
    FVT_BYTES_ARRAY = 5


def get_dilation_action_request(factor):
    actions_request = RequestAction()
    entities = actions_request.request.entities.add()
    entities.name = "set_time_scale"
    entities_fields = entities.fields.add()
    entities_fields.name = "scale"
    entities_fields.type = FVType.FVT_DOUBLE.value
    dv = entities_fields.dv
    dv.append(factor)  # 81 tick/s,0.5m/ticks
    return actions_request


class Unit(object):
    def __init__(self, entity):

        for field in entity.fields:
            if field.name == 'id':
                self.id = field.iv[0]
            if field.name == 'type':
                self.type = field.iv[0]
            if field.name == 'position':
                x, y, z = field.dv
                self.position = (x, y, z)
            self.missle_num = 4
        if entity.entities[0].name == 'weapons':
            for field in entity.entities[0].entities[0].entities[0].fields:
                if field.name == 'num':
                    self.missle_num = field.iv[0]

    def print_unit(self):
        print("id:{},type:{}, position:{},missle_num:{}" \
              .format(self.id, self.type, self.position, self.missle_num))


class State(object):
    def __init__(self, observation):
        self.frame = observation.entities[0].fields[0].dv[0]  # observation.fields[0].dv[0]
        self.units = [Unit(entity) for entity in observation.entities[1].entities]
        self.units.sort(key=lambda unit: unit.id)
        # print()

    def split_type(self):
        unit_dic = {}
        for unit in self.units:
            unit_type = unit.type
            if unit_type not in unit_dic:
                unit_dic[unit_type] = [unit.id]
            else:
                unit_dic[unit_type].append(unit.id)
        return unit_dic


class Action(object):
    def __init__(self):
        actions_request = RequestAction()
        actions_request.request.name = "ACTION"
        self.actions_request = actions_request

    def set_obs(self, obs_setting: list[str]):
        entities = self.actions_request.request.entities.add()
        entities.name = "SetOBS"
        entities_fields = entities.fields.add()
        entities_fields.name = "Info"
        entities_fields.type = FVType.FVT_BYTES_ARRAY.value
        bv = entities_fields.bv
        # bv.append('OBS PlayerBrainAction -ExecuteHistory'.encode('utf-8'))
        for ele in obs_setting:
            bv.append(ele.encode('utf-8'))

    def ModifyOBS(self):
        entities = self.actions_request.request.entities.add()
        entities.name = "ModifyOBS"
        entities_fields = entities.fields.add()
        entities_fields.name = "Info"
        entities_fields.type = FVType.FVT_BYTES_ARRAY.value
        bv = entities_fields.bv
        bv.append('98E4543D433650A392F22985C33096E0 Append -ExecuteHistory'.encode('utf-8'))

    def add_point_move_action(self, entity_id, targetX, targetY, targetZ):
        entities = self.actions_request.request.entities.add()
        entities.name = "push_command_move_to"
        entities_fields = entities.fields.add()
        entities_fields.name = "unit_id"
        entities_fields.type = FVType.FVT_LONG.value
        iv = entities_fields.iv
        iv.append(entity_id)

        entities_fields = entities.fields.add()
        entities_fields.name = "target"
        entities_fields.type = FVType.FVT_DOUBLE_ARRAY.value
        dv = entities_fields.dv

        dv.append(targetX)
        dv.append(targetY)
        dv.append(targetZ)

    def add_attack_target_action(self, entity_id, target_entity_id):  # （entity_id : int , target_entity_id: int）
        entities = self.actions_request.request.entities.add()

        entities.name = "push_command_attack_id"

        entities_fields = entities.fields.add()
        entities_fields.name = "unit_id"
        entities_fields.type = FVType.FVT_LONG.value
        iv = entities_fields.iv
        iv.append(entity_id)

        entities_fields = entities.fields.add()
        entities_fields.name = "target_id"
        entities_fields.type = FVType.FVT_LONG.value
        iv = entities_fields.iv
        iv.append(target_entity_id)

    def set_vehicle_steer(self, entity_id, steer):
        entities = self.actions_request.request.entities.add()
        entities.name = "InputSteer"
        entities_fields = entities.fields.add()
        entities_fields.name = "UnitUID"
        entities_fields.type = FVType.FVT_LONG.value
        iv = entities_fields.iv
        iv.append(entity_id)
        entities_fields = entities.fields.add()
        entities_fields.name = "Steer"
        entities_fields.type = FVType.FVT_DOUBLE.value
        dv = entities_fields.dv
        dv.append(steer)

    def SetHoldSpeed(self, entity_id, Speed):
        entities = self.actions_request.request.entities.add()
        entities.name = "SetHoldSpeed"
        entities_fields = entities.fields.add()
        entities_fields.name = "UnitUID"
        entities_fields.type = FVType.FVT_LONG.value
        iv = entities_fields.iv
        iv.append(entity_id)
        entities_fields = entities.fields.add()
        entities_fields.name = "Speed"
        entities_fields.type = FVType.FVT_DOUBLE.value
        dv = entities_fields.dv
        dv.append(Speed)

    def Tick(self):
        entities = self.actions_request.request.entities.add()
        entities.name = "Tick"
        entities_fields = entities.fields.add()
        entities_fields.name = "TickType"
        entities_fields.type = FVType.FVT_LONG.value
        iv = entities_fields.iv
        iv.append(2)
        entities_fields = entities.fields.add()
        entities_fields.name = "DeltaTime"
        entities_fields.type = FVType.FVT_DOUBLE.value
        dv = entities_fields.dv
        dv.append(0.0)

    def set_vehicle_controller_control(self, entity_id, IsControllerControl):
        entities = self.actions_request.request.entities.add()
        entities.name = "ControllerControl"
        entities_fields = entities.fields.add()
        entities_fields.name = "UnitUID"
        entities_fields.type = FVType.FVT_LONG.value
        iv = entities_fields.iv
        iv.append(entity_id)
        entities_fields = entities.fields.add()
        entities_fields.name = "IsControllerControl"
        entities_fields.type = FVType.FVT_LONG.value
        entities_fields.iv.append(IsControllerControl)

    def InputThrottle(self, entity_id, Throttle):
        entities = self.actions_request.request.entities.add()
        entities.name = "InputThrottle"
        entities_fields = entities.fields.add()
        entities_fields.name = "UnitUID"
        entities_fields.type = FVType.FVT_LONG.value
        iv = entities_fields.iv
        iv.append(entity_id)
        entities_fields = entities.fields.add()
        entities_fields.name = "Throttle"
        entities_fields.type = FVType.FVT_DOUBLE.value
        entities_fields.dv.append(Throttle)

    def InputHandbrake(self, entity_id, Handbrake):
        entities = self.actions_request.request.entities.add()
        entities.name = "InputHandbrake"
        entities_fields = entities.fields.add()
        entities_fields.name = "UnitUID"
        entities_fields.type = FVType.FVT_LONG.value
        iv = entities_fields.iv
        iv.append(entity_id)
        entities_fields = entities.fields.add()
        entities_fields.name = "Handbrake"
        entities_fields.type = FVType.FVT_DOUBLE.value
        entities_fields.dv.append(Handbrake)

    def InputBrake(self, entity_id, Brake):
        entities = self.actions_request.request.entities.add()
        entities.name = "InputBrake"
        entities_fields = entities.fields.add()
        entities_fields.name = "UnitUID"
        entities_fields.type = FVType.FVT_LONG.value
        iv = entities_fields.iv
        iv.append(entity_id)
        entities_fields = entities.fields.add()
        entities_fields.name = "Brake"
        entities_fields.type = FVType.FVT_DOUBLE.value
        entities_fields.dv.append(Brake)

    def ClearAllAction(self):
        entities = self.actions_request.request.entities.add()
        entities.name = "ClearAllAction"

    def GoToPositionV1(self, entity_id, Position):
        entities = self.actions_request.request.entities.add()
        entities.name = "GoToPosition"
        entities_fields = entities.fields.add()
        entities_fields.name = "UnitUID"
        entities_fields.type = FVType.FVT_LONG.value
        iv = entities_fields.iv
        iv.append(entity_id)
        entities_fields = entities.fields.add()
        entities_fields.name = "Position"
        entities_fields.type = FVType.FVT_DOUBLE_ARRAY.value
        for x in Position:
            entities_fields.dv.append(x)

    def DoAction(self, entity_id, ActionName, Arguments):
        entities = self.actions_request.request.entities.add()
        entities.name = "Do"
        entities_fields = entities.fields.add()
        entities_fields.name = "UnitUID"
        entities_fields.type = FVType.FVT_LONG.value
        iv = entities_fields.iv
        iv.append(entity_id)
        entities_fields = entities.fields.add()
        entities_fields.name = "ActionName"
        entities_fields.type = FVType.FVT_BYTES_ARRAY.value
        entities_fields.bv.append(ActionName.encode('utf-8'))
        entities_fields = entities.fields.add()
        entities_fields.name = "Arguments"
        entities_fields.type = FVType.FVT_BYTES_ARRAY.value
        entities_fields.bv.append(Arguments.encode('utf-8'))
        return entities

    def add_sync_action(self, frame_number):
        entities_fields = self.actions_request.request.fields.add()

        entities_fields.name = "sync"
        entities_fields.type = FVType.FVT_LONG.value
        iv = entities_fields.iv
        iv.append(frame_number)  # 81 tick/s,


class EnvironmentClient(object):
    def __init__(self, host, port):
        self.client = PlayerBrainClient(host, str(port), is_shipping=True)

    def reset(self):
        self.client.request_restart(False)

    def speedup(self):
        self.client.request_action(get_dilation_action_request(float(2)), is_reset=True)

    def execute(self, action, is_reset=False):
        self.client.request_action(action.actions_request)
        time.sleep(0.01)

    def get_observation(self, is_reset=False):
        response = self.client.request_observation(RequestObservation())
        print(response.observation.observation)
        state = State(response.observation.observation)
        return state


def start_server(env_id):
    server_cmd = "./run.sh"
    # server_cmd = "cd /home/ue4 && ./start.sh"

    server_cmd = f"bash -c \"{server_cmd}\""
    # server_cmd = f"/home/ue4/ bash start.sh"  
    server_name = f'env-{env_id}'
    docker_cmd = f'docker stop {server_name} && docker rm {server_name}'
    os.system(docker_cmd)
    time.sleep(2)
    port = env_id + 6100
    docker_image = "b5bb2e8f25d6"  # d2f8587c"
    docker_cmd = f'docker run --name {server_name} -p {port}:50051 -itd {docker_image} {server_cmd}'
    os.system(docker_cmd)
    time.sleep(15)
    host = os.popen("docker inspect --format '{{ .NetworkSettings.IPAddress }}' " + server_name).read().strip()
    host = '127.0.0.1'
    return host, port


EntityID = 2
SampleLocation = [12164.210938, 4268.624023, -109540.046875]
SampleLLH_LZY = [112.71692, 42.24008, 1219.156]

if __name__ == "__main__":
    host, port = '127.0.0.1', str(sys.argv[1] if len(sys.argv) > 1 else 50051)
    print(port)
    # host,port = start_server(1)
    client = EnvironmentClient(host, port)
    print('连接成功')
    while 1:
        # client.reset()
        # client.speedup()
        action_request = Action()
        action_request.set_obs()
        client.execute(action_request)
        state = client.get_observation(is_reset=False)
        # target_position = [command['x'],command['y'],command['z']]
        # action_request = Action()
        # action_request.set_vehicle_controller_control(entity_id=EntityID, IsControllerControl=1)
        # action_request.ModifyOBS()
        # client.execute(action_request)
        start_time = time.time()
        Count = 0
        while 1:
            Count += 1
            UserInput = input()
            UserInputSplit = UserInput.split(' ')
            action_request = Action()
            action_request.InputHandbrake(entity_id=1, Handbrake=0)
            client.execute(action_request)
            action_request.ClearAllAction()

            action_request = Action()
            if (UserInputSplit[0] == 'right'):
                action_request.set_vehicle_steer(entity_id=EntityID, steer=float(1))
            if (UserInputSplit[0] == 'left'):
                action_request.set_vehicle_steer(entity_id=EntityID, steer=float(-1))
            if (UserInputSplit[0] == 'stop'):
                action_request.set_vehicle_steer(entity_id=EntityID, steer=float(0))
                action_request.InputThrottle(entity_id=EntityID, Throttle=float(0))
            if (UserInputSplit[0] == 'forward'):
                action_request.InputThrottle(entity_id=EntityID, Throttle=float(1))
            if (UserInputSplit[0] == 'back'):
                action_request.InputThrottle(entity_id=EntityID, Throttle=float(-1))
            if (UserInputSplit[0] == 'h'):
                action_request.SetHoldSpeed(entity_id=EntityID, Speed=5000)
            if (UserInputSplit[0] == 'g'):
                action_request.GoToPosition(entity_id=EntityID,
                                            Position=(17115.0, 1545.0, -109765.0, 15805.0, 6895.0, -109765.0))
            if (UserInputSplit[0] == 'q'):
                KeyboardInput(action_request, Input="-Input q:IE_Pressed+w:IE_Pressed")
            if (UserInputSplit[0] == 'qoff'):
                action_request.DoAction(entity_id=0, ActionName="KeyboardInput", Arguments="-Input q:IE_Released")
            if (UserInputSplit[0] == '1'):
                action_request.DoAction(entity_id=EntityID, ActionName="VehicleInput", Arguments="-Input Steering:1")
            if (UserInputSplit[0] == '2'):
                action_request.DoAction(entity_id=EntityID, ActionName="VehicleInput", Arguments="-Input Steering:0")
            if (UserInputSplit[0] == '3'):
                action_request.actions_request.request.entities.append(GoToPosition(EntityID, SampleLocation))
            if (UserInputSplit[0] == '4'):
                action_request.actions_request.request.entities.append(GoToUID(EntityID, 2))
            if (UserInputSplit[0] == '5'):
                action_request.actions_request.request.entities.append(AttackPosition(EntityID, SampleLocation))
            if (UserInputSplit[0] == '6'):
                action_request.actions_request.request.entities.append(AttackUID(EntityID, 2))
            if (UserInputSplit[0] == '7'):
                action_request.actions_request.request.entities.append(
                    RayDetection(LLHLocation=[121.5133, 25.04007, 10000.0], ENU=[0.0, -90.0, 0.0], Length=2000000.0))
            if (UserInputSplit[0] == '8'):
                action_request.actions_request.request.entities.append(
                    SpawnEntity(3, 11301001, [14696, 1417, -109700], [0.0, 0.0, 0.0], 1))
            if (UserInputSplit[0] == 'pause'):
                action_request.actions_request.request.entities.append(GamePauseControl(Pause=0))
            if (UserInputSplit[0] == 'resume'):
                action_request.actions_request.request.entities.append(GamePauseControl(Pause=1))
            if (UserInputSplit[0] == 'Speed'):
                action_request.actions_request.request.entities.append(
                    TimeDilation(InTimeDilation=float(UserInputSplit[1])))
            if (UserInputSplit[0] == 'MaxFPS'):
                action_request.actions_request.request.entities.append(MaxFPS(InMaxFPS=float(UserInputSplit[1])))
            if (UserInputSplit[0] == 'UnrealToLLH'):
                action_request.actions_request.request.entities.append(
                    Unreal2LLH_Position([18805.0, 6795.0, -109744.0]))
            if (UserInputSplit[0] == 'GoToLLH'):
                action_request.actions_request.request.entities.append(GoToLLH(EntityID, InLocation=SampleLLH_LZY))
            if (UserInputSplit[0] == 'UIDAttackUID'):
                action_request.actions_request.request.entities.append(
                    AttackUID(int(UserInputSplit[1]), int(UserInputSplit[2])))
            if (UserInputSplit[0] == 'UIDAttackUUID'):
                action_request.actions_request.request.entities.append(
                    AttackUUID(int(UserInputSplit[1]), int(UserInputSplit[2])))
            if (UserInputSplit[0] == 'BehaviourTreeControl'):
                action_request.actions_request.request.entities.append(
                    BehaviourTreeControl(int(UserInputSplit[1]), int(UserInputSplit[2])))
            # action_request.DoAction(entity_id=EntityID, ActionName="Game", Arguments="-PutOffActionExecute")

            client.execute(action_request)

            time.sleep(0.5)

            state = client.get_observation()

'''
UENUM( BlueprintType, meta=(ScriptName="InputEventType"))
enum EInputEvent
{
	IE_Pressed              =0,
	IE_Released             =1,
	IE_Repeat               =2,
	IE_DoubleClick          =3,
	IE_Axis                 =4,
	IE_MAX                  =5,
};
'''
