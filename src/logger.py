class Logger:
    def __init__(self, out_path):
        self.path = out_path
        self.sep = ','


    def write_header(self):
        header_lines = (
            'time',
            'blocked_IN1',
            'blocked_IN2',
            'throughput_P1',
            'throughput_P2',
            'throughput_P3'
        )
        with open(self.path, 'w') as f:
            f.write(self.sep.join(header_lines) + '\n')

    
    def write_data(self, data_dict):
        with open(self.path, 'a') as f:
            f.write(self.sep.join(
                str(x) for x in data_dict.values()
            ) + '\n')
