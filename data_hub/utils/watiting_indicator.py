class WaitingIndicator:
    def __init__(self, data_str, mode=0):
        self.data_str = data_str
        self.i = 0
        self.mode = mode
        self.shown_flag = False
        self.on = True

    @property
    def i_list(self):
        if self.mode == 0:
            return ['-', '\\', '|', '/']
        elif self.mode == 1:
            n = 3  # 3个点
            return ['.' * i for i in range(n+1)]

    def print_next(self, s=''):
        self.i = (self.i + 1) % len(self.i_list)
        if self.on:
            print('\r{}'.format(' '.join([d for d in [self.data_str, s, self.i_list[self.i]] if d])), end='')
            self.shown_flag = True

    def print_end(self):
        if self.shown_flag and self.on:
            print()
