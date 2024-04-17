class HubController:

    def send_cmd(self, cmd_queue: list):
        raise NotImplementedError

    def get_obs(self):
        raise NotImplementedError

    def step(self, *args, **kwargs):
        pass

    def reset(self):
        pass
