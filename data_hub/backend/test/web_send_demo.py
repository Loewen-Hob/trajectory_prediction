import requests
import json

ip, port = ('192.168.3.52', '10088')
# ip, port = ('127.0.0.1', '10088')
print(ip, port)
url = f"http:/{ip}:{port}/user/login"
# url = "http://localhost:8888/user/login"
headers = {
    'content-type': "application/json"
}
payload = {
    "username": "admin",
    "mac_address": "172.16.10.172",
    "password": "123456",
    "seat_id": 1
}
response = requests.post(url, json=payload, headers=headers)
print(response.text)
token = json.loads(response.text)["data"]["token"]

url2 = f"http://{ip}:{port}/plan_task/send_command"
# url2 = "http://192.168.3.52:10088/plan_task/send_command"
# url2 = "http://localhost:8888/plan_task/send_command"
headers = {
    'content-type': "application/json",
    'Authorization': f'Bearer {token}'
}
payload = {
    "plan_id": 1,
    "plan_task_id": 1,
    "control_type": 1,
    "command_name": "路径导航",
    "command_type": 1,
    "command_params": json.dumps(
        {
            'task_id': 1,
            'unit_id': 1,
            'plan_id': 1,
            'command_subclass': 1,
            'maneuver_point': [
                {
                    'lon': 1.11,
                    'lat': 1.12,
                    'alt': 1.23,
                    'spd': 10.1,
                    'dir': 0,
                    'mode': 0
                }
            ]
        }
    )
}
response = requests.post(url2, json=payload, headers=headers)
print(response.text)
